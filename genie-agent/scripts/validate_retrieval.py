"""Validate a REAL genie retrieval JSON file against /shared/genie.retrieval.schema.json.

Run this against the actual response from the live Databricks Genie space
(exported from the Conversation API or copied from the UI's JSON view), to
confirm Module D's output still honours the contract Module C builds
against — in particular that no score/rank field has crept in. There is no
offline/mock path: this only means something once it runs against the real
Genie space's real output.

Usage:
    python3 scripts/validate_retrieval.py path/to/genie_response.json
    databricks genie ... | python3 scripts/validate_retrieval.py -
"""
import json
import pathlib
import sys

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

HERE = pathlib.Path(__file__).parent
SHARED = HERE.parent.parent / "shared"


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        return 1
    src = sys.argv[1]

    schemas = {p.name: json.loads(p.read_text()) for p in SHARED.glob("*.schema.json")}
    registry = Registry().with_resources(
        [(s["$id"], Resource.from_contents(s)) for s in schemas.values()]
    )
    schema = schemas["genie.retrieval.schema.json"]
    validator = Draft202012Validator(schema, registry=registry)

    instance = json.loads(sys.stdin.read()) if src == "-" else json.loads(pathlib.Path(src).read_text())
    errors = sorted(validator.iter_errors(instance), key=lambda e: list(e.path))

    if errors:
        print(f"FAIL {src}")
        for err in errors:
            print(f"    {list(err.path)}: {err.message}")
        return 1

    print(f"ok   {src}  ({len(instance.get('evidence_rows', []))} evidence rows, "
          f"{len(instance.get('mapped_skills', []))} mapped skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
