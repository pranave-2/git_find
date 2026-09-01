"""Stand-in for a live Databricks Genie space.

Simulates what Genie *should* return once configured with the layers in
config/ (metadata, relationships, synonyms, instructions, examples), by
applying the same synonym vocabulary and instructions to seed_data.json.

This lets Module D test and demo the retrieval contract before a real Genie
space and real ingested data (Modules A/B/C) exist, and gives Person C a
schema-valid input to build their ranking scorer against.

Usage:
    python3 scripts/mock_genie.py --job-id J001
    python3 scripts/mock_genie.py --jd-text "..." --job-id J001 --registered S001,S002

The output conforms to /shared/genie.retrieval.schema.json: no score, no
rank, ever — retrieval only (Layer 4, instruction 8).
"""
import argparse
import hashlib
import json
import pathlib
from datetime import datetime, timezone

import yaml

HERE = pathlib.Path(__file__).parent
ROOT = HERE.parent


def load_seed():
    return json.loads((ROOT / "seed" / "seed_data.json").read_text())


def load_synonyms():
    return yaml.safe_load((ROOT / "config" / "synonyms.yaml").read_text())


def interpret_jd(jd_text: str, synonyms_cfg: dict):
    """Layer 3: map JD terminology to canonical skills + requirement level.

    A real Genie space does this via its LLM reasoning over the configured
    synonym vocabulary and instructions; this is a literal-substring
    stand-in so the retrieval *shape* can be tested without one.
    """
    text = jd_text.lower()
    markers = synonyms_cfg["requirement_markers"]
    mapped = []
    buckets = {"required": [], "preferred": [], "bonus": []}

    for entry in synonyms_cfg["synonyms"]:
        hit_term = next((m for m in entry["match"] if m in text), None)
        if not hit_term:
            continue

        # naive nearest-marker heuristic: look at the sentence containing the hit
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


def retrieve_evidence(seed: dict, job: dict, mapped_skills: list):
    """Layers 1, 2, 4: join student -> repository -> repository_skill ->
    skill_evidence, restricted to registered candidates and mapped skills."""
    students = {s["student_id"]: s for s in seed["students"]}
    repos = {r["repo_id"]: r for r in seed["repositories"]}
    skill_id_to_name = {m["skill_id"]: m["skill_name"] for m in mapped_skills}
    requirement_by_skill = {m["skill_id"]: m["requirement_level"] for m in mapped_skills}
    evidence_by_key = {
        (e["repo_id"], e["skill_id"]): e["evidence"] for e in seed["skill_evidence"]
    }

    registered = set(job["registered_student_ids"])
    rows = []
    for rs in seed["repository_skill"]:
        if rs["skill_id"] not in skill_id_to_name:
            continue
        repo = repos[rs["repo_id"]]
        if repo["student_id"] not in registered:
            continue
        student = students[repo["student_id"]]
        rows.append({
            "student_id": student["student_id"],
            "name": student["name"],
            "repo_id": repo["repo_id"],
            "repo_name": repo["repo_name"],
            "skill_id": rs["skill_id"],
            "skill_name": skill_id_to_name[rs["skill_id"]],
            "confidence": rs["confidence"],
            "evidence": evidence_by_key.get((repo["repo_id"], rs["skill_id"]), ""),
            "requirement_level": requirement_by_skill[rs["skill_id"]],
        })
    return rows


def build_generated_sql(job_id: str, skill_names: list) -> str:
    in_clause = ", ".join(f"'{n}'" for n in skill_names)
    return (
        "SELECT jr.job_id, s.student_id, s.name, r.repo_id, r.repo_name, "
        "sk.skill_name, rs.confidence, se.evidence "
        "FROM job_registration jr "
        "JOIN student s ON jr.student_id = s.student_id "
        "JOIN repository r ON s.student_id = r.student_id "
        "JOIN repository_skill rs ON r.repo_id = rs.repo_id "
        "JOIN skill sk ON rs.skill_id = sk.skill_id "
        "JOIN skill_evidence se ON rs.repo_id = se.repo_id AND rs.skill_id = se.skill_id "
        f"WHERE jr.job_id = '{job_id}' AND sk.skill_name IN ({in_clause})"
    )


def run(job_id: str, jd_text: str | None, registered_override: list[str] | None):
    seed = load_seed()
    synonyms_cfg = load_synonyms()

    job = next((j for j in seed["jobs"] if j["job_id"] == job_id), None)
    if job is None:
        job = {"job_id": job_id, "registered_student_ids": registered_override or []}
    if jd_text is None:
        jd_text = job["jd_text"]
    if registered_override:
        job = {**job, "registered_student_ids": registered_override}

    buckets, mapped = interpret_jd(jd_text, synonyms_cfg)
    evidence_rows = retrieve_evidence(seed, job, mapped)

    warnings = []
    known_terms = {t for e in synonyms_cfg["synonyms"] for t in e["match"]}
    if not mapped:
        warnings.append("no JD terms matched the synonym vocabulary")

    return {
        "schema_version": "1.0.0",
        "job_id": job_id,
        "genie_space_id": "mock-genie-offline",
        "jd_text_hash": "sha256:" + hashlib.sha256(jd_text.encode()).hexdigest()[:12] + "...",
        "interpreted_requirements": buckets,
        "mapped_skills": mapped,
        "generated_sql": build_generated_sql(job_id, [m["skill_name"] for m in mapped]),
        "evidence_rows": evidence_rows,
        "registered_student_ids": job["registered_student_ids"],
        "retrieved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "warnings": warnings,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", default="J001")
    parser.add_argument("--jd-text", default=None, help="Raw JD text. Defaults to the seeded job's jd_text.")
    parser.add_argument("--registered", default=None, help="Comma-separated student_ids to override job_registration.")
    parser.add_argument("--out", default=None, help="Write JSON to this path instead of stdout.")
    args = parser.parse_args()

    registered = args.registered.split(",") if args.registered else None
    result = run(args.job_id, args.jd_text, registered)
    output = json.dumps(result, indent=2)

    if args.out:
        pathlib.Path(args.out).write_text(output + "\n")
        print(f"wrote {args.out}")
    else:
        print(output)


if __name__ == "__main__":
    main()
