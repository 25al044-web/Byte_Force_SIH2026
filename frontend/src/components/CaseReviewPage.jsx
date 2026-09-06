import React, { useEffect, useState } from 'react'
import { getCases } from '../services/api'
import { useTranslation } from '../i18n'

export function CaseReviewPage({ backendOnline }) {
  const { t } = useTranslation()
  const [cases, setCases] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [selectedCase, setSelectedCase] = useState(null)

  const fetchCases = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getCases(true)
      setCases(data.cases || [])
    } catch (err) {
      setError(err.message || 'Failed to load screening cases.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCases()
  }, [])

  const getRiskBadge = (level, score) => {
    const lvl = (level || '').toUpperCase()
    if (lvl === 'HIGH') {
      return <span className="risk-pill pill-high">HIGH RISK ({score ?? 0})</span>
    }
    if (lvl === 'REVIEW' || lvl === 'WARNING') {
      return <span className="risk-pill pill-review">MANUAL REVIEW ({score ?? 0})</span>
    }
    return <span className="risk-pill pill-low">LOW RISK ({score ?? 0})</span>
  }

  const getRecommendationBadge = (rec) => {
    if (rec === 'SECONDARY_INSPECTION_RECOMMENDED') {
      return <span className="rec-pill rec-secondary">SECONDARY INSPECTION</span>
    }
    if (rec === 'MANUAL_REVIEW_RECOMMENDED') {
      return <span className="rec-pill rec-manual">MANUAL REVIEW</span>
    }
    return <span className="rec-pill rec-clear">CLEAR</span>
  }

  return (
    <section className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <span className="stage-pill">OFFICER TRIAGE</span>
          <h2 className="stage-title">{t('caseReview')}</h2>
          <p className="stage-sub">
            Flagged cases requiring secondary inspection, manual officer review, or forensic examination.
          </p>
        </div>
        <button
          type="button"
          className="btn-refresh"
          onClick={fetchCases}
          disabled={loading || !backendOnline}
          title="Refresh review cases"
        >
          <svg
            className={loading ? 'spin-icon' : ''}
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.25"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          <span>Refresh Queue</span>
        </button>
      </div>

      {error && (
        <div className="toast-offline" role="alert">
          <span>{error}</span>
        </div>
      )}

      {/* Case List / Empty State */}
      {loading && cases.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-spinner" />
          <p>Loading officer case review queue…</p>
        </div>
      ) : cases.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-icon empty-icon-check">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <h3 className="empty-title">No cases currently require review.</h3>
          <p className="empty-desc">
            All recent identity screenings passed automated security thresholds or no flagged cases are currently pending inspection.
          </p>
        </div>
      ) : (
        <div className="case-grid">
          {cases.map((c) => (
            <div
              key={c.screening_id}
              className={`case-card ${selectedCase?.screening_id === c.screening_id ? 'case-card-active' : ''}`}
              onClick={() => setSelectedCase(c)}
              role="button"
              tabIndex={0}
            >
              <div className="case-card-top">
                <span className="case-id">{c.screening_id}</span>
                <span className="case-time">{c.timestamp}</span>
              </div>

              <div className="case-card-badges">
                {getRiskBadge(c.risk_level, c.risk_score)}
                {getRecommendationBadge(c.recommendation)}
                <span className="case-status-badge">{c.review_status || 'PENDING'}</span>
              </div>

              <div className="case-card-reason">
                <span className="reason-label">Primary Flag:</span>
                <p className="reason-text">{c.main_reason || 'Automated forensic inspection anomaly'}</p>
              </div>

              <div className="case-card-footer">
                <button
                  type="button"
                  className="btn-view-summary"
                  onClick={(e) => {
                    e.stopPropagation()
                    setSelectedCase(c)
                  }}
                >
                  <span>Review Case Details</span>
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="9 18 15 12 9 6" />
                  </svg>
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Case Summary Panel Modal */}
      {selectedCase && (
        <div className="modal-backdrop" onClick={() => setSelectedCase(null)}>
          <div className="modal-dialog case-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <div className="modal-title-group">
                <span className="stage-pill">CASE DOSSIER</span>
                <h3 className="modal-title">Case Review: {selectedCase.screening_id}</h3>
              </div>
              <button
                type="button"
                className="modal-close-btn"
                onClick={() => setSelectedCase(null)}
                aria-label="Close panel"
              >
                ✕
              </button>
            </div>

            <div className="case-modal-body">
              {/* Top summary stats */}
              <div className="case-stats-row">
                <div className="case-stat-box">
                  <span className="stat-label">Risk Rating</span>
                  <div className="stat-value-group">
                    {getRiskBadge(selectedCase.risk_level, selectedCase.risk_score)}
                  </div>
                </div>
                <div className="case-stat-box">
                  <span className="stat-label">Operational Recommendation</span>
                  <div className="stat-value-group">
                    {getRecommendationBadge(selectedCase.recommendation)}
                  </div>
                </div>
                <div className="case-stat-box">
                  <span className="stat-label">Review Status</span>
                  <span className="case-status-badge">{selectedCase.review_status || 'PENDING'}</span>
                </div>
              </div>

              {/* 1. Extracted Identity Summary */}
              <div className="dossier-section">
                <h4 className="dossier-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" />
                    <circle cx="12" cy="7" r="4" />
                  </svg>
                  <span>Extracted Identity Summary</span>
                </h4>
                <div className="identity-summary-grid">
                  <div className="id-item">
                    <span className="id-key">Full Name</span>
                    <span className="id-val">{selectedCase.extracted_identity?.full_name || 'Not available'}</span>
                  </div>
                  <div className="id-item">
                    <span className="id-key">Document Number</span>
                    <span className="id-val mono">{selectedCase.extracted_identity?.document_number || 'Not available'}</span>
                  </div>
                  <div className="id-item">
                    <span className="id-key">Document Type</span>
                    <span className="id-val">{selectedCase.extracted_identity?.document_type || 'Travel Document'}</span>
                  </div>
                  <div className="id-item">
                    <span className="id-key">Nationality</span>
                    <span className="id-val">{selectedCase.extracted_identity?.nationality || 'Not available'}</span>
                  </div>
                  <div className="id-item">
                    <span className="id-key">Date of Birth</span>
                    <span className="id-val">{selectedCase.extracted_identity?.date_of_birth || 'Not available'}</span>
                  </div>
                  <div className="id-item">
                    <span className="id-key">Expiry Date</span>
                    <span className="id-val">{selectedCase.extracted_identity?.expiry_date || 'Not available'}</span>
                  </div>
                </div>
              </div>

              {/* 2. Detected Issues */}
              <div className="dossier-section">
                <h4 className="dossier-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>Detected Issues & Explanations</span>
                </h4>
                {selectedCase.detected_issues && selectedCase.detected_issues.length > 0 ? (
                  <ul className="issues-list">
                    {selectedCase.detected_issues.map((issue, idx) => (
                      <li key={idx} className="issue-item">
                        <span className="issue-bullet">⚠</span>
                        <span>{issue}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-inline-text">No explicit explanation strings recorded.</p>
                )}
              </div>

              {/* 3. Verification Check Results (Integrity & Biometrics) */}
              <div className="dossier-section">
                <h4 className="dossier-heading">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  </svg>
                  <span>Inspection Engine Verdicts</span>
                </h4>
                <div className="engine-verdict-grid">
                  <div className="engine-card">
                    <span className="engine-title">Document Integrity Result</span>
                    <span className={`engine-badge badge-${(selectedCase.document_integrity_status || 'normal').toLowerCase()}`}>
                      {selectedCase.document_integrity_status || 'PASS'}
                    </span>
                    <p className="engine-sub">{selectedCase.main_reason || 'Forensic screening verdict'}</p>
                  </div>
                  <div className="engine-card">
                    <span className="engine-title">Biometric Face Match</span>
                    <span className={`engine-badge badge-${(selectedCase.face_match_status || 'pass').toLowerCase()}`}>
                      {selectedCase.face_match_status || 'PASS'}
                    </span>
                    <p className="engine-sub">Facial portrait comparison against applicant selfie</p>
                  </div>
                </div>
              </div>

              {/* 4. Action Recommendation Directive */}
              <div className="dossier-section directive-box">
                <h4 className="dossier-heading" style={{ color: 'var(--accent-cyan)' }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
                  </svg>
                  <span>Officer Directive</span>
                </h4>
                <p className="directive-text">
                  {selectedCase.recommendation === 'SECONDARY_INSPECTION_RECOMMENDED'
                    ? 'CRITICAL ALERT: Significant forensic or identity inconsistencies detected. Hold the applicant and conduct physical document inspection with high-magnification ultraviolet/infrared examination.'
                    : selectedCase.recommendation === 'MANUAL_REVIEW_RECOMMENDED'
                    ? 'ATTENTION: Minor inconsistencies or image degradation detected. Direct the applicant to secondary inspection to verify visual document features manually.'
                    : 'CLEARED: Automated verification satisfied standard border inspection criteria.'}
                </p>
              </div>
            </div>

            <div className="modal-footer">
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setSelectedCase(null)}
              >
                Close Dossier
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
