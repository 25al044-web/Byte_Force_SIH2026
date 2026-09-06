import React from 'react'
import { useTranslation } from '../i18n'

const TRIAGE_META = {
  LOW: {
    label: 'LOW RISK',
    directive: 'Routine Review Recommended',
    detail: 'All biometric and document checks satisfied automated screening thresholds. No watchlist flags. Proceed with standard clearance.',
    cls: 'hero-low',
    color: '#10b981',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <polyline points="9 12 11 14 15 10" />
      </svg>
    ),
  },
  REVIEW: {
    label: 'REVIEW REQUIRED',
    directive: 'Secondary Inspection Recommended',
    detail: 'Minor discrepancies or borderline biometric confidence detected. Direct applicant to secondary screening for physical document examination.',
    cls: 'hero-review',
    color: '#f59e0b',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
  },
  HIGH: {
    label: 'HIGH RISK',
    directive: 'Immediate Officer Review Required',
    detail: 'Critical anomalies detected: watchlist match, biometric mismatch, severe tamper indicators, or expired credential. Hold applicant and escalate immediately.',
    cls: 'hero-high',
    color: '#e05252',
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
    ),
  },
}

export function ResultHero({ risk, screeningId }) {
  const { t } = useTranslation()
  const score = typeof risk?.score === 'number' ? Math.max(0, Math.min(100, Math.round(risk.score))) : 0
  const level = (risk?.level || 'REVIEW').toUpperCase()
  const meta = TRIAGE_META[level] || TRIAGE_META.REVIEW
  const metaCopy = level === 'LOW' ? { label: t('lowRisk'), directive: t('lowDirective'), detail: t('lowDetail') } : level === 'HIGH' ? { label: t('highRisk'), directive: t('highDirective'), detail: t('highDetail') } : { label: t('manualReviewRequired'), directive: t('reviewDirective'), detail: t('reviewDetail') }

  return (
    <div className={`result-hero ${meta.cls}`}>
      {/* Top row: ID + protocol */}
      <div className="rh-meta-bar">
        <div className="rh-screening-id">
          <span className="rh-id-label">SCREENING REF</span>
          <span className="rh-id-value">{screeningId || 'SCR-2026-0001'}</span>
        </div>
        <div className="rh-protocol-tag">
          <span className="rh-proto-dot" />
          <span>Border Screening Protocol Active</span>
        </div>
      </div>

      {/* Main: outcome + score */}
      <div className="rh-main">
        <div className="rh-outcome-block">
          <span className="rh-eyebrow">VERIFICATION OUTCOME</span>
          <div className="rh-outcome-badge" style={{ color: meta.color }}>
            {meta.icon}<span className="rh-outcome-label">{metaCopy.label}</span>
          </div>
          <div className="rh-score-row">
            <span className="rh-score-num">{score}</span>
            <span className="rh-score-denom">/&nbsp;100</span>
            <span className="rh-score-caption">{t('riskScore')}</span>
          </div>
        </div>

        <div className="rh-directive-block">
          <span className="rh-eyebrow">TRIAGE DIRECTIVE</span>
          <div className="rh-directive-badge" style={{ borderLeftColor: meta.color }}>
            <div className="rh-directive-icon" style={{ color: meta.color }}>
              {meta.icon}
            </div>
            <div>
              <p className="rh-directive-title">{metaCopy.directive}</p><p className="rh-directive-detail">{metaCopy.detail}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
