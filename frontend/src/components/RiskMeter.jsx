import React from 'react'

export function RiskMeter({ risk, screeningId }) {
  const score = typeof risk?.score === 'number' ? Math.max(0, Math.min(100, Math.round(risk.score))) : 0
  const level = (risk?.level || 'REVIEW').toUpperCase()

  const getTriageMeta = (lvl) => {
    switch (lvl) {
      case 'LOW':
        return {
          outcome: 'LOW RISK',
          decisionTitle: 'Routine Review Recommended',
          decisionDetail:
            'All biometric and document checks satisfied automated screening thresholds. No active watchlist flags detected. Proceed with standard border inspection clearance.',
          className: 'triage-low',
          color: '#10b981',
          accentBg: 'rgba(16, 185, 129, 0.08)',
          borderColor: 'rgba(16, 185, 129, 0.35)',
          zone: 'LOW RISK (0 - 24)',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <polyline points="9 12 11 14 15 10" />
            </svg>
          ),
        }
      case 'HIGH':
        return {
          outcome: 'HIGH RISK',
          decisionTitle: 'Immediate Officer Review Required',
          decisionDetail:
            'Critical anomalies detected: one or more checks (watchlist match, biometric mismatch, severe digital tampering, or expired credential) failed. Hold applicant and escalate to supervisory officer immediately.',
          className: 'triage-high',
          color: '#ef4444',
          accentBg: 'rgba(239, 68, 68, 0.08)',
          borderColor: 'rgba(239, 68, 68, 0.35)',
          zone: 'HIGH RISK (60 - 100)',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <line x1="12" y1="9" x2="12" y2="13" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
          ),
        }
      case 'REVIEW':
      default:
        return {
          outcome: 'REVIEW REQUIRED',
          decisionTitle: 'Secondary Inspection Recommended',
          decisionDetail:
            'Minor discrepancies, borderline biometric confidence, or compression artifacts detected. Direct applicant to secondary screening counter for physical document examination and officer interview.',
          className: 'triage-review',
          color: '#f59e0b',
          accentBg: 'rgba(245, 158, 11, 0.08)',
          borderColor: 'rgba(245, 158, 11, 0.35)',
          zone: 'REVIEW REQUIRED (25 - 59)',
          icon: (
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ),
        }
    }
  }

  const triage = getTriageMeta(level)

  return (
    <div className={`results-summary-card ${triage.className}`}>
      {/* Top Meta Bar */}
      <div className="summary-header-row">
        <div className="screening-id-tag">
          <span className="id-title">SCREENING REF:</span>
          <span className="id-code">{screeningId || 'SCR-2026-0001'}</span>
        </div>
        <div className="protocol-tag">
          <span className="protocol-dot" />
          <span>BORDER SCREENING PROTOCOL ACTIVE</span>
        </div>
      </div>

      {/* Main Metric Hero */}
      <div className="summary-hero-grid">
        {/* Left: Verification Outcome & Score */}
        <div className="outcome-block">
          <span className="block-eyebrow">VERIFICATION OUTCOME</span>
          <div className="outcome-badge-large">
            {triage.icon}
            <span className="outcome-text">{triage.outcome}</span>
          </div>

          <div className="score-stat-group">
            <div className="score-number-row">
              <span className="score-big">{score}</span>
              <span className="score-max">/ 100</span>
            </div>
            <span className="score-caption">Composite Fraud Risk Score</span>
          </div>
        </div>

        {/* Right: Risk Meter Gauge & Zones */}
        <div className="meter-block">
          <div className="meter-header">
            <span className="meter-title">Risk Scale Distribution</span>
            <span className="active-zone-badge">{triage.zone}</span>
          </div>

          {/* Meter Track with dynamic marker */}
          <div className="meter-track-wrapper">
            <div className="meter-track-bg">
              <div className="zone-segment zone-low" title="0-24 Low Risk" />
              <div className="zone-segment zone-review" title="25-59 Review Required" />
              <div className="zone-segment zone-high" title="60-100 High Risk" />
            </div>

            <div
              className="meter-pointer"
              style={{ left: `${score}%` }}
              title={`Risk Score: ${score}`}
            >
              <div className="pointer-tip" style={{ borderColor: `${triage.color} transparent transparent transparent` }} />
              <div className="pointer-tag" style={{ backgroundColor: triage.color }}>{score}</div>
            </div>
          </div>

          <div className="meter-scale-legend">
            <div className="legend-item legend-low">
              <span className="legend-swatch" />
              <span className="legend-label">0 - 24 LOW</span>
            </div>
            <div className="legend-item legend-mid">
              <span className="legend-swatch" />
              <span className="legend-label">25 - 59 REVIEW</span>
            </div>
            <div className="legend-item legend-high">
              <span className="legend-swatch" />
              <span className="legend-label">60 - 100 HIGH</span>
            </div>
          </div>
        </div>
      </div>

      {/* Final Decision Panel (Requirement 9) */}
      <div className="decision-panel">
        <div className="decision-header">
          <div className="decision-icon-wrapper" style={{ color: triage.color }}>
            {triage.icon}
          </div>
          <div className="decision-title-group">
            <span className="decision-eyebrow">FINAL TRIAGE DIRECTIVE</span>
            <h4 className="decision-headline">{triage.decisionTitle}</h4>
          </div>
        </div>
        <p className="decision-text">{triage.decisionDetail}</p>
      </div>
    </div>
  )
}
