# Module C — Deterministic Scoring Engine

This module implements the deterministic ranking scorer (**Module C.2**) and the canonical platform database schema DDL (**`schema.sql`**).

---

## 📁 Layout

```text
scoring/
├── db/
│   └── schema.sql                 # Canonical database schema DDL for all 7 tables
├── models/
│   ├── common.py                  # Standard ID patterns, Enums, UnitInterval
│   ├── genie_input.py             # Pydantic input model (Module D: genie.retrieval)
│   └── ranking_output.py          # Pydantic output model (Module C: scoring.ranking_result)
├── core/
│   ├── policies.py                # Requirement weight defaults & aggregation functions
│   └── ranking_scorer.py          # Pure scoring function: compute_ranking()
├── cli.py                         # Standalone CLI runner
└── tests/
    └── test_ranking_scorer.py     # Unit tests & JSON Schema conformance tests
```

---

## 🚀 How to Use

### In Python Code (e.g. from Module E Backend API)

```python
from scoring import compute_ranking

# Pass the JSON dict from Module D (Genie)
genie_payload = {...}

ranking_result = compute_ranking(genie_payload)

# Dump to validated JSON dict matching shared/scoring.ranking_result.schema.json
response_dict = ranking_result.model_dump()
```

### Via CLI

```bash
# Score directly from a Genie retrieval JSON file
python -m scoring.cli shared/fixtures/genie.retrieval.json

# Save output to a file
python -m scoring.cli shared/fixtures/genie.retrieval.json -o output.json
```

---

## 🧪 Running Unit Tests

```bash
pytest scoring/tests/
```
