"""Ranking policies, default weights, and aggregation algorithms."""

from typing import List
from scoring.models.common import AggregationMode, RequirementLevel

DEFAULT_POLICY_VERSION = "ranking-v1"

DEFAULT_REQUIREMENT_WEIGHTS = {
    RequirementLevel.REQUIRED: 1.0,
    RequirementLevel.PREFERRED: 0.6,
    RequirementLevel.BONUS: 0.3,
}


def aggregate_repo_confidences(confidences: List[float], mode: AggregationMode = AggregationMode.MAX) -> float:
    """Aggregate confidence numbers across multiple repositories for a single skill.
    
    Default is MAX, which measures the candidate's peak demonstrated competence.
    """
    if not confidences:
        return 0.0
    
    if mode == AggregationMode.MAX:
        return max(confidences)
    elif mode == AggregationMode.MEAN:
        return sum(confidences) / len(confidences)
    elif mode == AggregationMode.TOP_K_MEAN:
        top_k = sorted(confidences, reverse=True)[:2]
        return sum(top_k) / len(top_k)
    else:
        return max(confidences)
