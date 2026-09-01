"""Pydantic model for Module D (Genie Retrieval) output received as input by Module C.2."""

from typing import List, Optional
from pydantic import BaseModel, Field
from scoring.models.common import StudentId, RepoId, SkillId, JobId, SkillName, UnitInterval, RequirementLevel


class InterpretedRequirements(BaseModel):
    required: List[SkillName] = Field(default_factory=list)
    preferred: List[SkillName] = Field(default_factory=list)
    bonus: List[SkillName] = Field(default_factory=list)


class MappedSkill(BaseModel):
    jd_term: str
    skill_id: SkillId
    skill_name: SkillName
    requirement_level: RequirementLevel
    mapping_source: str = "exact"


class EvidenceRow(BaseModel):
    student_id: StudentId
    name: str
    repo_id: RepoId
    repo_name: str
    skill_id: SkillId
    skill_name: SkillName
    confidence: UnitInterval
    evidence: Optional[str] = None
    requirement_level: Optional[RequirementLevel] = None


class GenieRetrievalInput(BaseModel):
    """Input payload conforming to shared/genie.retrieval.schema.json."""
    schema_version: str = "1.0.0"
    job_id: JobId
    genie_space_id: Optional[str] = None
    jd_text_hash: Optional[str] = None
    interpreted_requirements: InterpretedRequirements
    mapped_skills: List[MappedSkill] = Field(default_factory=list)
    generated_sql: Optional[str] = None
    evidence_rows: List[EvidenceRow] = Field(default_factory=list)
    registered_student_ids: List[StudentId] = Field(default_factory=list)
    retrieved_at: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
