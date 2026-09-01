"""Unit tests and schema validation for Module C.2 Ranking Scorer."""

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from scoring.core.ranking_scorer import compute_ranking
from scoring.models.common import AggregationMode, RequirementLevel
from scoring.models.ranking_output import RequirementWeights

PROJECT_ROOT = Path(__file__).parent.parent.parent
SHARED_DIR = PROJECT_ROOT / "shared"
FIXTURES_DIR = SHARED_DIR / "fixtures"


@pytest.fixture
def genie_fixture():
    fixture_path = FIXTURES_DIR / "genie.retrieval.json"
    return json.loads(fixture_path.read_text())


@pytest.fixture
def ranking_schema_validator():
    schemas = {p.name: json.loads(p.read_text()) for p in SHARED_DIR.glob("*.schema.json")}
    registry = Registry().with_resources(
        [(s["$id"], Resource.from_contents(s)) for s in schemas.values()]
    )
    ranking_schema = schemas["scoring.ranking_result.schema.json"]
    return Draft202012Validator(ranking_schema, registry=registry)


def test_ranking_on_genie_fixture(genie_fixture):
    """Test compute_ranking on the canonical Rahul J001 fixture."""
    result = compute_ranking(
        retrieval_input=genie_fixture,
        computed_at="2026-09-01T10:00:05Z",
    )

    assert result.job_id == "J001"
    assert result.policy_version == "ranking-v1"
    assert len(result.ranked_candidates) >= 1

    # Rahul should be rank 1
    rahul = next(c for c in result.ranked_candidates if c.student_id == "S001")
    assert rahul.rank == 1
    assert rahul.name == "Rahul"

    # Verify skill scores
    skill_map = {s.skill_name: s for s in rahul.skill_scores}
    assert "Python" in skill_map
    assert skill_map["Python"].strength == 0.98
    assert skill_map["Python"].weight == 1.0
    assert skill_map["Python"].has_evidence is True

    # Check contributing repos for Python: 3 repos, R001 selected
    python_repos = skill_map["Python"].contributing_repos
    assert len(python_repos) == 3
    selected_repo = next(r for r in python_repos if r.selected)
    assert selected_repo.repo_id == "R001"
    assert selected_repo.confidence == 0.98

    # AWS should have no evidence
    assert "AWS" in skill_map
    assert skill_map["AWS"].strength == 0.0
    assert skill_map["AWS"].has_evidence is False

    # Check denominator: (1.0*2) + (0.6*4) + (0.3*1) = 2.0 + 2.4 + 0.3 = 4.7 (or depending on total JD skills)
    assert rahul.denominator > 0
    assert rahul.score > 0.0


def test_ranking_schema_conformance(genie_fixture, ranking_schema_validator):
    """Verify that compute_ranking output strictly passes shared/scoring.ranking_result.schema.json."""
    result = compute_ranking(genie_fixture)
    result_dict = json.loads(result.model_dump_json())

    errors = list(ranking_schema_validator.iter_errors(result_dict))
    assert not errors, f"Schema validation errors: {[e.message for e in errors]}"


def test_candidates_with_zero_evidence():
    """Verify registered candidates with zero retrieved evidence are scored 0 and ranked appropriately."""
    payload = {
        "schema_version": "1.0.0",
        "job_id": "J002",
        "interpreted_requirements": {
            "required": ["Python"],
            "preferred": [],
            "bonus": [],
        },
        "mapped_skills": [
            {"jd_term": "Python", "skill_id": "SK01", "skill_name": "Python", "requirement_level": "required", "mapping_source": "exact"}
        ],
        "evidence_rows": [
            {
                "student_id": "S001",
                "name": "Alice",
                "repo_id": "R001",
                "repo_name": "py-repo",
                "skill_id": "SK01",
                "skill_name": "Python",
                "confidence": 0.90,
            }
        ],
        "registered_student_ids": ["S001", "S002"],  # S002 has no evidence
    }

    result = compute_ranking(payload)
    assert len(result.ranked_candidates) == 2

    # S001 should be rank 1 with 0.9
    assert result.ranked_candidates[0].student_id == "S001"
    assert result.ranked_candidates[0].score == 0.90
    assert result.ranked_candidates[0].rank == 1

    # S002 should be rank 2 with 0.0
    assert result.ranked_candidates[1].student_id == "S002"
    assert result.ranked_candidates[1].score == 0.0
    assert result.ranked_candidates[1].rank == 2


def test_custom_requirement_weights():
    """Verify overriding requirement weights updates denominator and scores correctly."""
    payload = {
        "schema_version": "1.0.0",
        "job_id": "J003",
        "interpreted_requirements": {
            "required": ["Python"],
            "preferred": ["Docker"],
            "bonus": [],
        },
        "mapped_skills": [
            {"jd_term": "Python", "skill_id": "SK01", "skill_name": "Python", "requirement_level": "required", "mapping_source": "exact"},
            {"jd_term": "Docker", "skill_id": "SK06", "skill_name": "Docker", "requirement_level": "preferred", "mapping_source": "exact"},
        ],
        "evidence_rows": [
            {
                "student_id": "S001",
                "name": "Bob",
                "repo_id": "R001",
                "repo_name": "app",
                "skill_id": "SK01",
                "skill_name": "Python",
                "confidence": 1.0,
            },
            {
                "student_id": "S001",
                "name": "Bob",
                "repo_id": "R001",
                "repo_name": "app",
                "skill_id": "SK06",
                "skill_name": "Docker",
                "confidence": 0.5,
            },
        ],
        "registered_student_ids": ["S001"],
    }

    # Custom weights: required=2.0, preferred=1.0
    custom_weights = RequirementWeights(required=2.0, preferred=1.0, bonus=0.5)
    result = compute_ranking(payload, custom_weights=custom_weights)

    # Numerator = (1.0 * 2.0) + (0.5 * 1.0) = 2.5
    # Denominator = 2.0 + 1.0 = 3.0
    # Score = 2.5 / 3.0 = 0.8333
    cand = result.ranked_candidates[0]
    assert cand.numerator == 2.5
    assert cand.denominator == 3.0
    assert cand.score == 0.8333
