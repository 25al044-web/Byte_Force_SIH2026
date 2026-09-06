import React from 'react'
import { SectionHeader } from './SectionHeader'
import { translateReason, useTranslation } from '../i18n'

export function ExplanationList({ explanations = [] }) {
  const { t } = useTranslation()
  return (
    <div className="explanation-panel">
      <SectionHeader
        eyebrow="AUDITABLE AI EXPLAINABILITY"
        title={t('riskFactors')}
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        }
        right={
          <div className="exp-audit-badge">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
            <span>{t('reasons')}</span>
          </div>
        }
      />

      <div className="exp-content">
        {explanations && explanations.length > 0 ? (
          <ul className="exp-list" aria-label={t('riskFactors')}>
            {explanations.map((exp, idx) => {
              // Detect if it's a penalty (deduction) or positive
              const isPenalty = exp.includes('+') || exp.includes('penal') || exp.includes('deduct') || exp.includes('flag') || exp.includes('mismatch') || exp.includes('expired') || exp.includes('blacklist') || exp.includes('tamper') || exp.includes('duplicate')
              const isNeutral = exp.toLowerCase().includes('base') || exp.toLowerCase().includes('start')

              return (
                <li key={idx} className="exp-item">
                  <span className={`exp-bullet ${isPenalty ? 'bullet-penalty' : isNeutral ? 'bullet-neutral' : 'bullet-info'}`} />
                  <span className="exp-text">{translateReason(exp, t)}</span>
                </li>
              )
            })}
          </ul>
        ) : (
          <p className="exp-empty">
            {t('noSignificantAnomaly')}
          </p>
        )}
      </div>

      <div className="exp-footer">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
        <span>Deterministic rule engine — no probabilistic black-box scoring. Each factor is independently auditable.</span>
      </div>
    </div>
  )
}
