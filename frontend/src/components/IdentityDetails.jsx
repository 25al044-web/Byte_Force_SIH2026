import React from 'react'

export function IdentityDetails({ screeningId, document, mrzLine1, mrzLine2 }) {
  const formatValue = (val) => {
    if (val === null || val === undefined || val === '') {
      return <span className="val-na">Not available</span>
    }
    return <span className="val-text">{val}</span>
  }

  const fields = [
    { label: 'Full Name', value: document?.full_name, icon: 'user' },
    { label: 'Document Type', value: document?.document_type ? document.document_type.replace('_', ' ').toUpperCase() : null, icon: 'file' },
    { label: 'Document Number', value: document?.document_number, icon: 'hash' },
    { label: 'Nationality', value: document?.nationality, icon: 'globe' },
    { label: 'Date of Birth', value: document?.date_of_birth, icon: 'calendar' },
    { label: 'Expiry Date', value: document?.expiry_date, icon: 'clock' },
    { label: 'Sex', value: document?.sex, icon: 'user-check' },
    { label: 'Issuing Authority', value: document?.issuing_authority, icon: 'shield' },
    { label: 'Institution / Organization', value: document?.institution_or_organization, icon: 'building' },
  ]

  const isExtractionUnavailable = !document?.full_name && !document?.document_number

  return (
    <div className="identity-card">
      <div className="card-header-bar">
        <div className="header-title-box">
          <div className="section-icon-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="16" rx="2" />
              <circle cx="9" cy="10" r="2" />
              <line x1="15" y1="8" x2="17" y2="8" />
              <line x1="15" y1="12" x2="17" y2="12" />
              <line x1="7" y1="16" x2="17" y2="16" />
            </svg>
          </div>
          <div>
            <span className="card-eyebrow">CREDENTIAL TRANSCRIPTION</span>
            <h3 className="card-main-title">Extracted Document Information</h3>
          </div>
        </div>
        <span className="extracted-status-pill">
          {isExtractionUnavailable ? 'EXTRACTION DEGRADED' : 'EXTRACTED VIA GEMINI'}
        </span>
      </div>

      {isExtractionUnavailable && (
        <div className="extraction-alert-box">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div className="alert-text">
            <strong>Document extraction service temporarily unavailable.</strong>
            <span> Dependent checks report NOT_AVAILABLE. Biometric face comparison and forensic tamper analysis remain active.</span>
          </div>
        </div>
      )}

      {/* Grid of 9 Identity Fields */}
      <div className="identity-fields-grid">
        {fields.map((f, i) => (
          <div key={i} className="field-cell">
            <span className="field-label">{f.label}</span>
            <div className="field-value-wrapper">{formatValue(f.value)}</div>
          </div>
        ))}
      </div>

      {/* MRZ Zone Display if present */}
      {(mrzLine1 || mrzLine2) ? (
        <div className="mrz-panel">
          <div className="mrz-header">
            <span className="mrz-label">ICAO TD3 MACHINE READABLE ZONE (MRZ)</span>
            <span className="mrz-status-ok">DETECTED</span>
          </div>
          <div className="mrz-code-block">
            {mrzLine1 && <div className="mrz-line">{mrzLine1}</div>}
            {mrzLine2 && <div className="mrz-line">{mrzLine2}</div>}
          </div>
        </div>
      ) : (
        <div className="mrz-panel mrz-panel-empty">
          <span className="mrz-empty-text">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="8" y1="12" x2="16" y2="12" />
            </svg>
            MRZ not detected on this document type or image.
          </span>
        </div>
      )}
    </div>
  )
}
