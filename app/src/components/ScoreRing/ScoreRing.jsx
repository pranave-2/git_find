import React from 'react';
import './ScoreRing.css';

export default function ScoreRing({ scorePct, size = 90, strokeWidth = 8 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (scorePct / 100) * circumference;

  // Color gradient based on score
  let strokeColor = '#06b6d4'; // default primary
  if (scorePct >= 80) strokeColor = '#10b981'; // emerald
  else if (scorePct >= 60) strokeColor = '#f59e0b'; // amber
  else strokeColor = '#f43f5e'; // rose

  return (
    <div className="score-ring-container" style={{ width: size, height: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} className="score-ring-svg">
        <circle
          className="score-ring-bg"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
        />
        <circle
          className="score-ring-fill"
          cx={size / 2}
          cy={size / 2}
          r={radius}
          strokeWidth={strokeWidth}
          stroke={strokeColor}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
        />
      </svg>
      <div className="score-ring-text">
        <span className="score-ring-number">{scorePct.toFixed(1)}</span>
        <span className="score-ring-percent">%</span>
      </div>
    </div>
  );
}
