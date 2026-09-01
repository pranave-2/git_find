"""Pydantic model for Module C.2 (Ranking Result) output conforming to shared/scoring.ranking_result.schema.json."""

from typing import List, Optional
from pydantic import BaseModel, Field
from scoring.models.common import StudentId, RepoId, SkillId, JobId, SkillName, UnitInterval, RequirementLevel, AggregationMode


class RequirementWeights(BaseModel):
    required: float = Field(default=1.0, ge=0.0)
    preferred: float = Field(default=0.6, ge=0.0)
    bonus: float = Field(default=0.3, ge=0.0)


class ContributingRepo(BaseModel):
    repo_id: RepoId
    repo_name: str
    confidence: UnitInterval
    evidence: Optional[str] = None
    selected: Optional[bool] = None


class SkillScore(BaseModel):
    skill_id: SkillId
    skill_name: SkillName
    requirement_level: RequirementLevel
    weight: float = Field(ge=0.0)
    strength: UnitInterval
    has_evidence: bool
    contribution: float = Field(ge=0.0)
    contributing_repos: List[ContributingRepo] = Field(default_factory=list)


class RankedCandidate(BaseModel):
    rank: int = Field(ge=1)
    student_id: StudentId
    name: str
    score: UnitInterval
    numerator: float = Field(ge=0.0)
    denominator: float = Field(gt=0.0)
    skill_scores: List[SkillScore]


class RankingResult(BaseModel):
    """Output payload conforming to shared/scoring.ranking_result.schema.json."""
    schema_version: str = "1.0.0"
    job_id: JobId
    policy_version: str = "ranking-v1"
    requirement_weights: RequirementWeights = Field(default_factory=RequirementWeights)
    aggregation: AggregationMode = AggregationMode.MAX
    ranked_candidates: List[RankedCandidate]
    computed_at: str
