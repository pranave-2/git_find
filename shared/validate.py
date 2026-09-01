"""Validate every fixture in shared/fixtures against its schema."""
import json
import pathlib
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

SHARED = pathlib.Path(__file__).parent
FIXTURES = SHARED / "fixtures"

# (schema file, fixture file, anchor within schema or None)
PAIRS = [
    ("ingestion.raw_features.schema.json", "ingestion.raw_features.json", None),
    ("llm_evidence.schema.json", "llm_evidence.json", None),
    ("scoring.repository_skill.schema.json", "scoring.repository_skill.json", None),
    ("scoring.ranking_result.schema.json", "scoring.ranking_result.json", None),
    ("genie.retrieval.schema.json", "genie.retrieval.json", None),
    ("app.recruiter_result.schema.json", "app.recruiter_result.json", None),
    ("app.placement_dashboard.schema.json", "app.placement_dashboard.json", None),
    ("app.requests.schema.json", "app.requests.student_registration.json", "student_registration"),
    ("app.requests.schema.json", "app.requests.job_submission.json", "job_submission"),
]


def main():
    schemas = {p.name: json.loads(p.read_text()) for p in SHARED.glob("*.schema.json")}
    registry = Registry().with_resources(
        [(s["$id"], Resource.from_contents(s)) for s in schemas.values()]
    )

    failed = False
    for schema_file, fixture_file, anchor in PAIRS:
        schema = schemas[schema_file]
        target = {"$ref": schema["$id"] + "#" + anchor} if anchor else schema
        validator = Draft202012Validator(target, registry=registry)
        instance = json.loads((FIXTURES / fixture_file).read_text())
        errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))
        if errors:
            failed = True
            print(f"FAIL {fixture_file}")
            for err in errors:
                print(f"    {list(err.path)}: {err.message}")
        else:
            print(f"ok   {fixture_file}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
