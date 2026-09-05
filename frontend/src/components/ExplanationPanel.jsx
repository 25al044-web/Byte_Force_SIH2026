import React from 'react'

export function ExplanationPanel({ explanations = [] }) {
  return (
    <div className="explanation-section">
      <div className="card-header-bar">
        <div className="header-title-box">
          <div className="section-icon-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="16" x2="12" y2="12" />
              <line x1="12" y1="8" x2="12.01" y2="8" />
            </svg>
          </div>
          <div>
            <span className="card-eyebrow">AUDITABLE AI EXPLAINABILITY</span>
            <h3 className="card-main-title">Risk Scoring Explanations</h3>
          </div>
        </div>
        <span className="explainability-pill">RULE ENGINE LOG</span>
      </div>

      <div className="explanation-content">
        {explanations && explanations.length > 0 ? (
          <div className="explanation-items-list">
            {explanations.map((exp, idx) => (
              <div key={idx} className="explanation-entry">
                <div className="entry-bullet">
                  <span className="bullet-point" />
                </div>
                <p className="entry-text">{exp}</p>
              </div>
            ))}
          </div>
        ) : (
          <p className="no-explanation-note">
            No specific anomaly triggers recorded. Baseline operational metrics were maintained across all evaluation checks.
          </p>
        )}
      </div>
    </div>
  )
}
