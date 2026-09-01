import React, { useEffect } from 'react';
import { getPlacementOverview } from '../api/mockApi';
import { useApi } from '../hooks/useApi';
import './Pages.css';
import './PlacementDashboard.css';

export default function PlacementDashboard() {
  const { execute, loading, error, data } = useApi(getPlacementOverview);

  useEffect(() => {
    execute();
  }, [execute]);

  if (loading) {
    return (
      <div className="page-container">
        <div className="skeleton-container">
          <div className="skeleton" style={{ height: '120px', marginBottom: '24px' }} />
          <div className="skeleton" style={{ height: '300px' }} />
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="page-container">
        <div className="toast toast-error">{error || 'Failed to load placement overview.'}</div>
      </div>
    );
  }

  const { cohort_size, repos_ingested, students_with_no_repos, skill_coverage, skill_gaps, job_summary, generated_at } = data;

  return (
    <div className="page-container">
      {/* Header */}
      <div className="page-header animate-in">
        <div className="privacy-badge-line">
          <span className="badge badge-success">Privacy-Enforced Contract</span>
          <span className="meta-time">As of {new Date(generated_at).toLocaleString()}</span>
        </div>
        <h1>Placement Cell Dashboard</h1>
        <p>
          Cohort-level skill coverage & gap analytics. By design, no individual candidate identities or filtering exist in this contract.
        </p>
      </div>

      {/* KPI Cards */}
      <div className="grid-3 margin-bottom-xl animate-in stagger-1">
        <div className="glass-card kpi-card">
          <span className="kpi-value">{cohort_size}</span>
          <span className="kpi-label">Total Cohort Students</span>
        </div>

        <div className="glass-card kpi-card">
          <span className="kpi-value">{repos_ingested}</span>
          <span className="kpi-label">GitHub Repos Ingested</span>
        </div>

        <div className="glass-card kpi-card">
          <span className="kpi-value">{students_with_no_repos}</span>
          <span className="kpi-label">Students Without Public Repos</span>
        </div>
      </div>

      {/* Skill Gaps Alert Panel */}
      {skill_gaps && skill_gaps.length > 0 && (
        <div className="glass-card alert-panel margin-bottom-xl animate-in stagger-2">
          <div className="alert-header">
            <span className="alert-icon">⚠️</span>
            <div>
              <h3>Actionable Skill Gaps Detected</h3>
              <p>Skills demanded in recent recruiter JDs where cohort coverage is low:</p>
            </div>
          </div>

          <div className="gaps-list">
            {skill_gaps.map((gap) => (
              <div key={gap.skill_name} className="gap-item">
                <div className="gap-skill-name">
                  <strong>{gap.skill_name}</strong>
                  <span className="badge badge-warning">{gap.demand_count} Recent JDs</span>
                </div>
                <div className="gap-metric mono">
                  Cohort Coverage: <strong>{gap.coverage_pct}%</strong>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="grid-2 animate-in stagger-3">
        {/* Cohort Skill Coverage */}
        <div className="glass-card page-card">
          <h3>Cohort Skill Distribution</h3>
          <p className="card-subtitle">Student count and median evidence strength per canonical skill:</p>

          <div className="coverage-list">
            {skill_coverage.map((sc) => (
              <div key={sc.skill_name} className="coverage-item">
                <div className="coverage-header">
                  <span className="coverage-skill-name">{sc.skill_name}</span>
                  <span className="coverage-cat badge badge-bonus">{sc.category || 'Skill'}</span>
                  <span className="coverage-stats mono">
                    {sc.student_count} / {cohort_size} students ({sc.coverage_pct}%)
                  </span>
                </div>

                <div className="coverage-bar-track">
                  <div
                    className="coverage-bar-fill"
                    style={{ width: `${sc.coverage_pct}%` }}
                  />
                </div>

                {sc.median_strength !== undefined && (
                  <div className="median-strength-label mono">
                    Median Evidence Strength: <strong>{(sc.median_strength * 100).toFixed(1)}%</strong>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Job Summary Table */}
        <div className="glass-card page-card">
          <h3>Active Job Pipeline Overview</h3>
          <p className="card-subtitle">Recruiter JDs submitted & median cohort match scores:</p>

          <div className="table-wrapper margin-top-md">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Job ID</th>
                  <th>Title</th>
                  <th>Candidates</th>
                  <th>Median Match Score</th>
                </tr>
              </thead>
              <tbody>
                {job_summary.map((job) => (
                  <tr key={job.job_id}>
                    <td className="mono font-bold text-cyan">{job.job_id}</td>
                    <td>{job.title}</td>
                    <td className="mono">{job.registered_count}</td>
                    <td className="mono text-emerald">
                      <strong>{job.median_score_pct}%</strong>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
