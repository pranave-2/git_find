import React from 'react';
import './SkillBadge.css';

export default function SkillBadge({ skill }) {
  const { skill_name, requirement_level, strength, has_evidence } = skill;

  const strengthPct = Math.round((strength || 0) * 100);

  return (
    <div className={`skill-badge ${has_evidence ? 'has-evidence' : 'no-evidence'}`}>
      <div className="skill-badge-header">
        <span className={`skill-status-icon ${has_evidence ? 'icon-check' : 'icon-cross'}`}>
          {has_evidence ? '✓' : '✗'}
        </span>
        <span className="skill-name">{skill_name}</span>
        <span className={`badge badge-${requirement_level}`}>
          {requirement_level}
        </span>
      </div>

      <div className="skill-badge-strength">
        <div className="strength-bar-track">
          <div
            className={`strength-bar-fill level-${requirement_level}`}
            style={{ width: `${has_evidence ? strengthPct : 0}%` }}
          />
        </div>
        <span className="strength-value mono">
          {has_evidence ? `${strengthPct}%` : 'No evidence'}
        </span>
      </div>
    </div>
  );
}
