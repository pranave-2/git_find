"""Call the REAL Databricks Genie Agent Conversation API for a job description
and shape the response into /shared/genie.retrieval.schema.json.

No mock, no offline path. Every field in the output either comes straight
from the live API response or is computed from real data fetched from the
same warehouse in this same run:

  - evidence_rows           <- Genie's actual SQL result rows (statement_id)
  - generated_sql           <- Genie's actual generated SQL, verbatim
  - registered_student_ids  <- a real query against job_registration
  - id fields (student_id, repo_id, skill_id)
                             <- a real lookup query against student/
                                repository/skill, joined onto Genie's
                                name-keyed rows in Python (Genie's table
                                columns are names, not surrogate keys —
                                see config/instructions.md bullet 6)
  - interpreted_requirements,
    mapped_skills           <- computed from the JD text using
                                config/synonyms.yaml, the same vocabulary
                                already loaded into Genie's Instructions.
                                Genie does the retrieval; this is
                                orchestration around its real output, not
                                a simulation of it.

Setup:
    pip install databricks-sdk pyyaml jsonschema referencing
    export DATABRICKS_HOST=https://<your-workspace>.cloud.databricks.com
    export DATABRICKS_TOKEN=<personal access token>   # never pass on argv

Usage:
    python3 scripts/run_genie_query.py --job-id J001
    python3 scripts/run_genie_query.py --job-id J001 --out out.json
    python3 scripts/run_genie_query.py --job-id J001 | python3 scripts/validate_retrieval.py -
"""
import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import time

import yaml

try:
    from databricks.sdk import WorkspaceClient
except ImportError:
    print(
        "Missing dependency: pip install databricks-sdk",
        file=sys.stderr,
    )
    raise

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent

DEFAULT_SPACE_ID = "01f1a5d3223e1258b9e41ee12e60b7a8"
DEFAULT_CATALOG = "workspace"
DEFAULT_SCHEMA = "recruitment_genie"

POLL_INTERVAL_S = 2
POLL_MAX_INTERVAL_S = 30
POLL_TIMEOUT_S = 300


# ---------------------------------------------------------------------------
# Genie conversation
# ---------------------------------------------------------------------------

def ask_genie(w: WorkspaceClient, space_id: str, question: str):
    """Start a conversation, poll until the message is done, return it."""
    msg = w.genie.start_conversation(space_id=space_id, content=question)
    conversation_id = msg.conversation_id
    message_id = msg.message_id if hasattr(msg, "message_id") else msg.id

    deadline = time.monotonic() + POLL_TIMEOUT_S
    interval = POLL_INTERVAL_S
    terminal = {"COMPLETED", "FAILED", "CANCELLED", "QUERY_RESULT_EXPIRED"}

    while True:
        result = w.genie.get_message(
            space_id=space_id,
            conversation_id=conversation_id,
            message_id=message_id,
        )
        status = str(result.status.value if hasattr(result.status, "value") else result.status)
        if status in terminal:
            if status != "COMPLETED":
                raise RuntimeError(f"Genie message ended with status={status}: {getattr(result, 'error', None)}")
            return result
        if time.monotonic() > deadline:
            raise TimeoutError(f"Genie message still {status} after {POLL_TIMEOUT_S}s")
        time.sleep(interval)
        interval = min(interval * 1.5, POLL_MAX_INTERVAL_S)


def extract_sql_and_statement_id(message):
    """Pull the generated SQL and statement_id off the message's query attachment."""
    for attachment in getattr(message, "attachments", None) or []:
        query = getattr(attachment, "query", None)
        if query is not None:
            return query.query, query.statement_id
    raise RuntimeError("Genie response has no query attachment — check that the "
                        "question actually requires a SQL retrieval, and that "
                        "Instructions still says 'respond with a table.'")


def fetch_statement_rows(w: WorkspaceClient, statement_id: str):
    """Read back the literal result rows Genie's SQL produced, as a list of dicts."""
    result = w.statement_execution.get_statement(statement_id)
    columns = [c.name for c in result.manifest.schema.columns]
    rows = []
    data = result.result.data_array if result.result else []
    for raw_row in data or []:
        rows.append(dict(zip(columns, raw_row)))
    if result.result and getattr(result.result, "next_chunk_index", None) is not None:
        print(
            "warning: result set is chunked and this script only reads the "
            "first chunk — fine for the seeded demo data, not for a large "
            "production result set",
            file=sys.stderr,
        )
    return rows


# ---------------------------------------------------------------------------
# Real ID lookups + registered students (separate, real SQL — not fabricated)
# ---------------------------------------------------------------------------

def run_sql(w: WorkspaceClient, warehouse_id: str, statement: str):
    result = w.statement_execution.execute_statement(
        warehouse_id=warehouse_id,
        statement=statement,
        wait_timeout="30s",
    )
    columns = [c.name for c in result.manifest.schema.columns]
    data = result.result.data_array if result.result else []
    return [dict(zip(columns, row)) for row in (data or [])]


def pick_warehouse_id(w: WorkspaceClient, explicit: str | None):
    if explicit:
        return explicit
    for wh in w.warehouses.list():
        if str(getattr(wh, "state", "")).upper() in ("RUNNING", "STATE_RUNNING"):
            return wh.id
    # none confirmed running — just take the first and let Databricks wake it
    warehouses = list(w.warehouses.list())
    if not warehouses:
        raise RuntimeError("No SQL warehouse found in this workspace.")
    return warehouses[0].id


def fetch_id_lookups(w: WorkspaceClient, warehouse_id: str, catalog: str, schema: str):
    students = run_sql(w, warehouse_id, f"SELECT student_id, name FROM {catalog}.{schema}.student")
    repos = run_sql(w, warehouse_id, f"SELECT repo_id, repo_name FROM {catalog}.{schema}.repository")
    skills = run_sql(w, warehouse_id, f"SELECT skill_id, skill_name FROM {catalog}.{schema}.skill")
    return (
        {r["name"]: r["student_id"] for r in students},
        {r["repo_name"]: r["repo_id"] for r in repos},
        {r["skill_name"]: r["skill_id"] for r in skills},
    )


def fetch_registered_students(w: WorkspaceClient, warehouse_id: str, catalog: str, schema: str, job_id: str):
    rows = run_sql(
        w, warehouse_id, catalog and
        f"SELECT student_id FROM {catalog}.{schema}.job_registration WHERE job_id = '{job_id}'"
    )
    return [r["student_id"] for r in rows]


def fetch_job_text(w: WorkspaceClient, warehouse_id: str, catalog: str, schema: str, job_id: str):
    rows = run_sql(w, warehouse_id, f"SELECT jd_text FROM {catalog}.{schema}.job WHERE job_id = '{job_id}'")
    if not rows:
        raise RuntimeError(f"No job row found for job_id={job_id!r}")
    return rows[0]["jd_text"]


# ---------------------------------------------------------------------------
# JD -> requirement-level classification (adapter logic, not Genie output —
# Genie's table no longer surfaces this since round 4's "table only" fix)
# ---------------------------------------------------------------------------

def load_synonyms():
    return yaml.safe_load((ROOT / "config" / "synonyms.yaml").read_text())


def interpret_jd(jd_text: str, synonyms_cfg: dict):
    text = jd_text.lower()
    markers = synonyms_cfg["requirement_markers"]
    mapped = []
    buckets = {"required": [], "preferred": [], "bonus": []}

    for entry in synonyms_cfg["synonyms"]:
        hit_term = next((m for m in entry["match"] if m in text), None)
        if not hit_term:
            continue
        sentence = next((s for s in text.split(".") if hit_term in s), text)
        level = "preferred"
        for lvl in ("required", "bonus", "preferred"):
            if any(marker in sentence for marker in markers[lvl]):
                level = lvl
                break
        buckets[level].append(entry["skill_name"])
        mapped.append({
            "jd_term": hit_term,
            "skill_id": entry["skill_id"],
            "skill_name": entry["skill_name"],
            "requirement_level": level,
            "mapping_source": "exact" if hit_term == entry["skill_name"].lower() else "synonym",
        })
    return buckets, mapped


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------

def build_retrieval_result(job_id, space_id, jd_text, genie_rows, generated_sql,
                            registered_ids, student_ids, repo_ids, skill_ids,
                            interpreted_requirements, mapped_skills, warnings):
    requirement_by_skill_name = {m["skill_name"]: m["requirement_level"] for m in mapped_skills}

    evidence_rows = []
    for row in genie_rows:
        name = row.get("name") or row.get("student_name")
        repo_name = row.get("repo_name") or row.get("repository_name")
        skill_name = row.get("skill_name")
        confidence = row.get("confidence")
        evidence = row.get("evidence") or row.get("evidence_text")

        if name is None or repo_name is None or skill_name is None:
            warnings.append(f"row missing expected columns, skipped: {row}")
            continue

        student_id = student_ids.get(name)
        repo_id = repo_ids.get(repo_name)
        skill_id = skill_ids.get(skill_name)
        if not all([student_id, repo_id, skill_id]):
            warnings.append(f"could not resolve id(s) for row: {row}")

        evidence_rows.append({
            "student_id": student_id or "UNKNOWN",
            "name": name,
            "repo_id": repo_id or "UNKNOWN",
            "repo_name": repo_name,
            "skill_id": skill_id or "UNKNOWN",
            "skill_name": skill_name,
            "confidence": float(confidence) if confidence is not None else 0.0,
            "evidence": evidence or "",
            "requirement_level": requirement_by_skill_name.get(skill_name, "preferred"),
        })

    return {
        "schema_version": "1.0.0",
        "job_id": job_id,
        "genie_space_id": space_id,
        "jd_text_hash": "sha256:" + hashlib.sha256(jd_text.encode()).hexdigest()[:12] + "...",
        "interpreted_requirements": interpreted_requirements,
        "mapped_skills": mapped_skills,
        "generated_sql": generated_sql,
        "evidence_rows": evidence_rows,
        "registered_student_ids": registered_ids,
        "retrieved_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--space-id", default=DEFAULT_SPACE_ID)
    parser.add_argument("--warehouse-id", default=None, help="Defaults to the first running warehouse found.")
    parser.add_argument("--catalog", default=DEFAULT_CATALOG)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()

    w = WorkspaceClient()  # reads DATABRICKS_HOST / DATABRICKS_TOKEN from env

    warehouse_id = pick_warehouse_id(w, args.warehouse_id)
    jd_text = fetch_job_text(w, warehouse_id, args.catalog, args.schema, args.job_id)
    registered_ids = fetch_registered_students(w, warehouse_id, args.catalog, args.schema, args.job_id)
    student_ids, repo_ids, skill_ids = fetch_id_lookups(w, warehouse_id, args.catalog, args.schema)

    synonyms_cfg = load_synonyms()
    interpreted_requirements, mapped_skills = interpret_jd(jd_text, synonyms_cfg)

    message = ask_genie(w, args.space_id, jd_text)
    generated_sql, statement_id = extract_sql_and_statement_id(message)
    genie_rows = fetch_statement_rows(w, statement_id)

    warnings = []
    result = build_retrieval_result(
        job_id=args.job_id,
        space_id=args.space_id,
        jd_text=jd_text,
        genie_rows=genie_rows,
        generated_sql=generated_sql,
        registered_ids=registered_ids,
        student_ids=student_ids,
        repo_ids=repo_ids,
        skill_ids=skill_ids,
        interpreted_requirements=interpreted_requirements,
        mapped_skills=mapped_skills,
        warnings=warnings,
    )

    output = json.dumps(result, indent=2)
    if args.out:
        pathlib.Path(args.out).write_text(output + "\n")
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
