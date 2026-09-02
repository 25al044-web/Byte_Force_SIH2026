import React from 'react'

export function ExplanationPanel({ explanations = [] }) {
  return (
    <div className="explanation-card">
      <div className="section-header">
        <div className="header-label-group">
          <span className="section-eyebrow">AUDITABLE AI EXPLAINABILITY</span>
          <h2 className="section-title">WHY WAS THIS RESULT PRODUCED?</h2>
        </div>
      </div>

      <div className="explanation-body">
        {explanations && explanations.length > 0 ? (
          <ul className="explanation-list">
            {explanations.map((exp, idx) => (
              <li key={idx} className="explanation-item">
                <div className="bullet-dot" />
                <span className="explanation-text">{exp}</span>
              </li>
            ))}
          </ul>
        ) : (
          <p className="no-explanations">No specific reasoning entries returned by the screening pipeline.</p>
        )}
      </div>
    </div>
  )
}
