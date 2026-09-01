"""Common types, regex patterns, and enums matching shared/common.schema.json."""

from enum import Enum
from typing import Annotated
from pydantic import BaseModel, Field, StringConstraints

# Standard ID Regex Patterns
StudentId = Annotated[str, StringConstraints(pattern=r"^S[0-9]{3,}$")]
RepoId = Annotated[str, StringConstraints(pattern=r"^R[0-9]{3,}$")]
SkillId = Annotated[str, StringConstraints(pattern=r"^SK[0-9]{2,}$")]
JobId = Annotated[str, StringConstraints(pattern=r"^J[0-9]{3,}$")]
EvidenceId = Annotated[str, StringConstraints(pattern=r"^E[0-9]{3,}$")]

# Normalized score in [0.0, 1.0]
UnitInterval = Annotated[float, Field(ge=0.0, le=1.0)]

# Canonical skill name
SkillName = Annotated[str, StringConstraints(min_length=1, max_length=64)]


class RequirementLevel(str, Enum):
    REQUIRED = "required"
    PREFERRED = "preferred"
    BONUS = "bonus"


class AggregationMode(str, Enum):
    MAX = "max"
    MEAN = "mean"
    TOP_K_MEAN = "top_k_mean"
