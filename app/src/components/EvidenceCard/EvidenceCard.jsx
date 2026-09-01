import React, { useState } from 'react';
import './EvidenceCard.css';

export default function EvidenceCard({ repo }) {
  const [expanded, setExpanded] = useState(false);

  const { repo_id, repo_name, repo_url, confidence, evidence, signals } = repo;
  const confPct = Math.round((confidence || 0) * 100);

  return (
    <div className={`evidence-card ${expanded ? 'expanded' : ''}`}>
      <div className="evidence-header" onClick={() => setExpanded(!expanded)}>
        <div className="evidence-title">
          <span className="repo-icon">📁</span>
          <span className="repo-name">{repo_name}</span>
          <span className="repo-id mono">{repo_id}</span>
        </div>

        <div className="evidence-meta">
          <div className="confidence-pill mono">
            <span>Confidence</span>
            <strong>{confPct}%</strong>
          </div>
          <button className="expand-btn btn-ghost btn-sm" aria-label="Toggle details">
            {expanded ? '▲' : '▼'}
          </button>
        </div>
      </div>

      <p className="evidence-text">"{evidence}"</p>

      {expanded && (
        <div className="evidence-details animate-in">
          {repo_url && (
            <div className="detail-row">
              <span className="detail-label">Repository:</span>
              <a href={repo_url} target="_blank" rel="noopener noreferrer" className="repo-url">
                {repo_url} ↗
              </a>
            </div>
          )}

          {signals && (
            <div className="signals-grid">
              <h5 className="signals-title">Evidence Score Decomposition (6 Signals):</h5>
              <div className="signals-list">
                {Object.entries(signals).map(([key, val]) => (
                  <div key={key} className="signal-item">
                    <span className="signal-name">{key.replace(/_/g, ' ')}</span>
                    <span className="signal-val mono">
                      {typeof val === 'number' ? (val <= 1 ? (val * 100).toFixed(0) + '%' : val) : String(val)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
