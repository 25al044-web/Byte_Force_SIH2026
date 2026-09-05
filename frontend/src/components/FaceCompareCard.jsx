import React from 'react'
import { StatusPill } from './StatusPill'

/**
 * FaceCompareCard — shows document portrait + selfie side-by-side with similarity
 * Uses the uploaded preview URLs from App state (no backend crops needed)
 */
export function FaceCompareCard({ check, documentPreview, selfiePreview }) {
  const status = check?.status || 'NOT_AVAILABLE'
  const similarity = check?.similarity
  const reason = check?.reason || 'No biometric comparison data available.'

  const hasSimilarity = typeof similarity === 'number'

  const barColor = hasSimilarity
    ? similarity >= 70
      ? '#10b981'
      : similarity >= 50
        ? '#f59e0b'
        : '#e05252'
    : '#445066'

  return (
    <div className={`face-compare-card vcard-status-${status.toLowerCase()}`}>
      <div className="vc-header">
        <div className="vc-title-group">
          <span className="vc-category">BIOMETRIC COMPARISON</span>
          <div className="vc-title-row">
            <div className="vc-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="8" r="5" />
                <path d="M20 21a8 8 0 1 0-16 0" />
                <polyline points="16 11 18 13 22 9" />
              </svg>
            </div>
            <h4 className="vc-name">Face Verification</h4>
          </div>
        </div>
        <StatusPill status={status} />
      </div>

      {/* Visual face comparison */}
      <div className="fc-compare-row">
        <div className="fc-face-slot">
          <span className="fc-slot-label">Document Portrait</span>
          {documentPreview ? (
            <div className="fc-img-frame">
              <img src={documentPreview} alt="Document" className="fc-img" />
              <span className="fc-img-badge">ID DOC</span>
            </div>
          ) : (
            <div className="fc-img-placeholder">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <rect x="3" y="4" width="18" height="16" rx="2" />
                <circle cx="9" cy="10" r="2" />
              </svg>
              <span>No preview</span>
            </div>
          )}
        </div>

        <div className="fc-connector">
          <div className="fc-conn-line" />
          <div className="fc-conn-score" style={{ color: barColor }}>
            {hasSimilarity ? (
              <>
                <span className="fc-sim-num">{similarity.toFixed(1)}%</span>
                <span className="fc-sim-label">similarity</span>
              </>
            ) : (
              <span className="fc-sim-na">—</span>
            )}
          </div>
          <div className="fc-conn-line" />
        </div>

        <div className="fc-face-slot">
          <span className="fc-slot-label">Applicant Selfie</span>
          {selfiePreview ? (
            <div className="fc-img-frame">
              <img src={selfiePreview} alt="Selfie" className="fc-img" />
              <span className="fc-img-badge">SELFIE</span>
            </div>
          ) : (
            <div className="fc-img-placeholder">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <circle cx="12" cy="8" r="4" />
                <path d="M20 21a8 8 0 1 0-16 0" />
              </svg>
              <span>No preview</span>
            </div>
          )}
        </div>
      </div>

      {hasSimilarity && (
        <div className="vc-mini-bar-wrap">
          <div className="vc-mini-bar">
            <div className="vc-mini-fill" style={{ width: `${similarity}%`, backgroundColor: barColor }} />
          </div>
          <span className="vc-mini-label" style={{ color: barColor }}>{similarity.toFixed(1)}%</span>
        </div>
      )}

      <p className="vc-reason">{reason}</p>
    </div>
  )
}
