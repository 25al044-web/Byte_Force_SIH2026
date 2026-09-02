import React from 'react'

export function RiskMeter({ risk }) {
  const score = typeof risk?.score === 'number' ? Math.max(0, Math.min(100, risk.score)) : 0
  const level = risk?.level || 'REVIEW'

  const getLevelMeta = (lvl) => {
    switch (lvl) {
      case 'LOW':
        return {
          title: 'LOW RISK',
          subtext: 'Document meets automated verification criteria. Standard clearance.',
          className: 'risk-level-low',
          color: '#10b981',
        }
      case 'HIGH':
        return {
          title: 'HIGH RISK',
          subtext: 'Critical anomalies or policy violations detected. Immediate intervention required.',
          className: 'risk-level-high',
          color: '#ef4444',
        }
      case 'REVIEW':
      default:
        return {
          title: 'MANUAL REVIEW REQUIRED',
          subtext: 'Minor discrepancies or compression anomalies detected. Secondary inspection advised.',
          className: 'risk-level-review',
          color: '#f59e0b',
        }
    }
  }

  const meta = getLevelMeta(level)

  return (
    <div className={`risk-meter-card ${meta.className}`}>
      <div className="section-header">
        <div className="header-label-group">
          <span className="section-eyebrow">COMPOSITE FRAUD RISK ENGINE</span>
          <h2 className="section-title">Risk Assessment</h2>
        </div>
        <div className={`risk-level-pill ${meta.className}`}>
          <span className="pulse-indicator" />
          <span className="level-text">{meta.title}</span>
        </div>
      </div>

      <div className="risk-body">
        <div className="risk-score-display">
          <span className="score-lead">Risk Score:</span>
          <div className="score-numbers">
            <span className="score-value">{score}</span>
            <span className="score-denominator">/ 100</span>
          </div>
        </div>

        <div className="meter-track-container">
          <div className="meter-track">
            <div
              className="meter-fill"
              style={{
                width: `${score}%`,
                backgroundColor: meta.color,
              }}
            />
          </div>
          <div className="meter-scale-markers">
            <span className="marker marker-low">0 (Low Risk)</span>
            <span className="marker marker-mid">50 (Review)</span>
            <span className="marker marker-high">100 (High Risk)</span>
          </div>
        </div>

        <div className="risk-description-banner">
          <p className="risk-subtext">{meta.subtext}</p>
        </div>
      </div>
    </div>
  )
}
