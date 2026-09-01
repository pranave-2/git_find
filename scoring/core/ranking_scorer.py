"""Module C.2 — Deterministic Ranking Scorer.

Consumes Module D's retrieved evidence, aggregates per-skill across repositories (MAX by default),
applies requirement weights from the JD, and produces the final deterministic candidate score.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Union
from collections import defaultdict

from scoring.models.common import AggregationMode, RequirementLevel, SkillId, SkillName, StudentId
from scoring.models.genie_input import EvidenceRow, GenieRetrievalInput, MappedSkill
from scoring.models.ranking_output import (
    ContributingRepo,
    RankedCandidate,
    RankingResult,
    RequirementWeights,
    SkillScore,
)
from scoring.core.policies import (
    DEFAULT_POLICY_VERSION,
    DEFAULT_REQUIREMENT_WEIGHTS,
    aggregate_repo_confidences,
)


def compute_ranking(
    retrieval_input: Union[GenieRetrievalInput, dict],
    policy_version: str = DEFAULT_POLICY_VERSION,
    custom_weights: Optional[RequirementWeights] = None,
    aggregation_mode: AggregationMode = AggregationMode.MAX,
    computed_at: Optional[str] = None,
) -> RankingResult:
    """Pure scoring function to rank candidates deterministically from Genie retrieval data.
    
    Args:
        retrieval_input: Module D Genie retrieval payload (Pydantic model or dict).
        policy_version: Version tag of the scoring policy used.
        custom_weights: Optional overrides for requirement weights.
        aggregation_mode: Multi-repo aggregation mode (MAX, MEAN, TOP_K_MEAN).
        computed_at: Optional ISO timestamp override (defaults to current UTC time).
        
    Returns:
        RankingResult conforming to shared/scoring.ranking_result.schema.json.
    """
    if isinstance(retrieval_input, dict):
        retrieval_input = GenieRetrievalInput.model_validate(retrieval_input)

    weights = custom_weights or RequirementWeights()
    weight_map = {
        RequirementLevel.REQUIRED: weights.required,
        RequirementLevel.PREFERRED: weights.preferred,
        RequirementLevel.BONUS: weights.bonus,
    }

    # Canonical skill vocabulary lookup
    CANONICAL_SKILLS: Dict[str, str] = {
        "python": "SK01",
        "fastapi": "SK02",
        "flask": "SK03",
        "rest api": "SK04",
        "postgresql": "SK05",
        "docker": "SK06",
        "aws": "SK07",
    }

    # 1. Build skill_id lookup from canonical dictionary, mapped skills, and evidence rows
    skill_id_lookup: Dict[str, str] = dict(CANONICAL_SKILLS)
    for mapped in retrieval_input.mapped_skills:
        skill_id_lookup[mapped.skill_name.lower()] = mapped.skill_id
        skill_id_lookup[mapped.jd_term.lower()] = mapped.skill_id

    # Also extract skill_id from evidence_rows if present
    for row in retrieval_input.evidence_rows:
        skill_id_lookup[row.skill_name.lower()] = row.skill_id

    def resolve_skill_id(name: str, index: int) -> str:
        lower = name.lower()
        if lower in skill_id_lookup:
            return skill_id_lookup[lower]
        # Generate valid SK## format
        return f"SK{10 + (index % 90):02d}"

    jd_skills: List[Dict[str, Union[str, RequirementLevel, float]]] = []
    seen_skills: Set[str] = set()

    interp = retrieval_input.interpreted_requirements
    skill_counter = len(skill_id_lookup)
    for level, skill_list in [
        (RequirementLevel.REQUIRED, interp.required),
        (RequirementLevel.PREFERRED, interp.preferred),
        (RequirementLevel.BONUS, interp.bonus),
    ]:
        for s_name in skill_list:
            s_lower = s_name.lower()
            if s_lower not in seen_skills:
                seen_skills.add(s_lower)
                skill_counter += 1
                s_id = resolve_skill_id(s_name, skill_counter)
                w = weight_map[level]
                jd_skills.append({
                    "skill_name": s_name,
                    "skill_id": s_id,
                    "requirement_level": level,
                    "weight": w,
                })

    # Calculate Total Denominator: sum of weights of ALL JD skills
    denominator = sum(float(s["weight"]) for s in jd_skills)
    if denominator == 0:
        denominator = 1.0  # Safeguard against empty requirements

    # 2. Group evidence rows by candidate
    candidate_names: Dict[str, str] = {}
    candidate_evidence: Dict[str, Dict[str, List[EvidenceRow]]] = defaultdict(lambda: defaultdict(list))

    for row in retrieval_input.evidence_rows:
        candidate_names[row.student_id] = row.name
        candidate_evidence[row.student_id][row.skill_name.lower()].append(row)

    # 3. Form the complete candidate pool (including registered students with 0 evidence)
    all_student_ids = list(retrieval_input.registered_student_ids)
    for s_id in candidate_names:
        if s_id not in all_student_ids:
            all_student_ids.append(s_id)

    # 4. Score each candidate
    candidate_scores: List[RankedCandidate] = []

    for student_id in all_student_ids:
        c_name = candidate_names.get(student_id, f"Candidate {student_id}")
        c_evidence = candidate_evidence.get(student_id, {})

        skill_scores_list: List[SkillScore] = []
        candidate_numerator = 0.0

        for s_info in jd_skills:
            s_name = str(s_info["skill_name"])
            s_id = str(s_info["skill_id"])
            req_level = RequirementLevel(s_info["requirement_level"])
            s_weight = float(s_info["weight"])

            matching_rows = c_evidence.get(s_name.lower(), [])

            if matching_rows:
                has_evidence = True
                confidences = [r.confidence for r in matching_rows]
                strength = aggregate_repo_confidences(confidences, aggregation_mode)
                contribution = strength * s_weight
                candidate_numerator += contribution

                # Build contributing_repos breakdown
                contributing_repos: List[ContributingRepo] = []
                selected_marked = False
                for r in matching_rows:
                    is_selected = (r.confidence == strength) and not selected_marked
                    if is_selected:
                        selected_marked = True
                    contributing_repos.append(
                        ContributingRepo(
                            repo_id=r.repo_id,
                            repo_name=r.repo_name,
                            confidence=r.confidence,
                            evidence=r.evidence,
                            selected=is_selected,
                        )
                    )

                skill_scores_list.append(
                    SkillScore(
                        skill_id=s_id,
                        skill_name=s_name,
                        requirement_level=req_level,
                        weight=s_weight,
                        strength=round(strength, 4),
                        has_evidence=True,
                        contribution=round(contribution, 4),
                        contributing_repos=contributing_repos,
                    )
                )
            else:
                # No evidence for this required JD skill
                skill_scores_list.append(
                    SkillScore(
                        skill_id=s_id,
                        skill_name=s_name,
                        requirement_level=req_level,
                        weight=s_weight,
                        strength=0.0,
                        has_evidence=False,
                        contribution=0.0,
                        contributing_repos=[],
                    )
                )

        final_score = candidate_numerator / denominator

        candidate_scores.append(
            RankedCandidate(
                rank=1,  # Temporary, assigned after sorting
                student_id=student_id,
                name=c_name,
                score=round(min(1.0, max(0.0, final_score)), 4),
                numerator=round(candidate_numerator, 4),
                denominator=round(denominator, 4),
                skill_scores=skill_scores_list,
            )
        )

    # 5. Sort candidates descending by score, then numerator
    candidate_scores.sort(key=lambda c: (c.score, c.numerator), reverse=True)

    # 6. Assign final sequential ranks
    for idx, cand in enumerate(candidate_scores, start=1):
        cand.rank = idx

    timestamp = computed_at or datetime.now(timezone.utc).isoformat()

    return RankingResult(
        schema_version="1.0.0",
        job_id=retrieval_input.job_id,
        policy_version=policy_version,
        requirement_weights=weights,
        aggregation=aggregation_mode,
        ranked_candidates=candidate_scores,
        computed_at=timestamp,
    )
