import React, { useEffect, useState } from 'react';
import { getJobResults } from '../api/mockApi';
import { useApi } from '../hooks/useApi';
import ScoreRing from '../components/ScoreRing/ScoreRing';
import SkillBadge from '../components/SkillBadge/SkillBadge';
import EvidenceCard from '../components/EvidenceCard/EvidenceCard';
import './Pages.css';
import './RecruiterResults.css';

function CandidateCard({ candidate, idx, defaultExpanded = false }) {
  const [expanded, setExpanded] = useState(defaultExpanded);

  const { rank, student_id, name, github_username, score_pct, skill_breakdown, justification } = candidate;

  return (
    <div className={`glass-card candidate-card animate-in stagger-${Math.min(idx + 2, 5)} ${expanded ? 'is-expanded' : ''}`}>
      {/* Candidate Header Summary */}
      <div className="candidate-header" onClick={() => setExpanded(!expanded)}>
        <div className="candidate-rank-badge mono">#{rank}</div>

        <div className="candidate-identity">
          <h3>{name}</h3>
          <div className="candidate-meta mono">
            <span>ID: {student_id}</span>
            {github_username && <span>• GitHub: @{github_username}</span>}
          </div>
        </div>

        <div className="candidate-score-block">
          <ScoreRing scorePct={score_pct} size={76} strokeWidth={6} />
        </div>

        <button className="dropdown-toggle-btn btn btn-ghost btn-sm" aria-label="Toggle details">
          <span className="toggle-label">{expanded ? 'Hide Details' : 'View Details'}</span>
          <span className="toggle-arrow">{expanded ? '▲' : '▼'}</span>
        </button>
      </div>

      {/* Expandable Dropdown Container (Justification + Skill Evidence Breakdown) */}
      {expanded && (
        <div className="candidate-dropdown-content animate-in">
          {/* AI Summarize Justification */}
          {justification && (
            <div className="justification-box">
              <div className="justification-title">
                <span className="sparkle-icon">✨</span>
                <strong>Databricks ai_summarize Justification</strong>
              </div>
              <p className="justification-text">"{justification}"</p>
            </div>
          )}

          {/* Skill Evidence Breakdown */}
          <div className="skill-breakdown-section">
            <h4 className="breakdown-title">Skill Evidence Breakdown</h4>

            <div className="skills-grid">
              {skill_breakdown.map((skill) => (
                <div key={skill.skill_name} className="skill-item-block">
                  <SkillBadge skill={skill} />

                  {/* Repository Evidence Drill-Down */}
                  {skill.repos && skill.repos.length > 0 && (
                    <div className="repo-evidence-list">
                      {skill.repos.map((repo) => (
                        <EvidenceCard key={repo.repo_id || repo.repo_name} repo={repo} />
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default function RecruiterResults() {
  const { execute, loading, error, data } = useApi(getJobResults);

  useEffect(() => {
    execute('J001');
  }, [execute]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="skeleton-container">
          <div className="skeleton" style={{ height: '80px', marginBottom: '24px' }} />
          <div className="skeleton" style={{ height: '300px' }} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-container">
        <div className="toast toast-error">{error || 'Failed to load recruiter results.'}</div>
      </div>
    );
  }

  const { job_title, job_id, interpreted_requirements, scoring_policy, candidates, generated_at } = data;

  return (
    <div className="page-container">
      {/* Top Banner */}
      <div className="results-header animate-in">
        <div>
          <div className="job-badge-line">
            <span className="badge badge-required mono">{job_id}</span>
            <span className="meta-time">Generated {new Date(generated_at).toLocaleString()}</span>
          </div>
          <h1>{job_title}</h1>
          <p className="results-subtitle">Ranked Candidates & Deterministic Evidence Breakdown</p>
        </div>

        <button className="btn btn-secondary btn-sm" onClick={() => execute('J001')}>
          🔄 Refresh Results
        </button>
      </div>

      {/* Interpreted Requirements & Policy Section */}
      <div className="grid-2 margin-bottom-lg animate-in stagger-1">
        {/* Requirement Interpretation */}
        {interpreted_requirements && (
          <div className="glass-card policy-card">
            <h4>Genie JD Interpretation</h4>
            <p className="policy-desc">How Recruitment Genie read requirement levels from raw text:</p>

            <div className="req-groups">
              <div className="req-group">
                <span className="req-label text-error">Required:</span>
                <div className="req-pills">
                  {interpreted_requirements.required.map((s) => (
                    <span key={s} className="badge badge-required">{s}</span>
                  ))}
                </div>
              </div>

              <div className="req-group">
                <span className="req-label text-warning">Preferred:</span>
                <div className="req-pills">
                  {interpreted_requirements.preferred.map((s) => (
                    <span key={s} className="badge badge-preferred">{s}</span>
                  ))}
                </div>
              </div>

              {interpreted_requirements.bonus?.length > 0 && (
                <div className="req-group">
                  <span className="req-label text-info">Bonus:</span>
                  <div className="req-pills">
                    {interpreted_requirements.bonus.map((s) => (
                      <span key={s} className="badge badge-bonus">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Scoring Policy */}
        {scoring_policy && (
          <div className="glass-card policy-card">
            <h4>Deterministic Scoring Policy</h4>
            <p className="policy-desc">Scores are policy-driven mathematical outcomes, not LLM opinion:</p>

            <div className="policy-details mono">
              <div>
                <span>Policy Version:</span> <strong>{scoring_policy.policy_version}</strong>
              </div>
              <div>
                <span>Aggregation Rule:</span> <strong>{scoring_policy.aggregation?.toUpperCase()} across repos</strong>
              </div>
              <div className="weights-row">
                <span>Weights:</span>
                <strong>Required: {scoring_policy.requirement_weights?.required}</strong> | 
                <strong> Preferred: {scoring_policy.requirement_weights?.preferred}</strong> | 
                <strong> Bonus: {scoring_policy.requirement_weights?.bonus}</strong>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Candidates List */}
      <div className="candidates-section">
        <div className="section-header-flex margin-bottom-md">
          <h2 className="section-title">Ranked Candidate Profiles ({candidates.length})</h2>
          <span className="hint-text">Click any candidate row to toggle skill breakdown dropdown</span>
        </div>

        {candidates.map((cand, idx) => (
          <CandidateCard
            key={cand.student_id}
            candidate={cand}
            idx={idx}
            defaultExpanded={idx === 0} // Expand #1 by default for clear preview
          />
        ))}
      </div>
    </div>
  );
}
