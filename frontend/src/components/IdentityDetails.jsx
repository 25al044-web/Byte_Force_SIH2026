import React from 'react'

export function IdentityDetails({ screeningId, document }) {
  const formatValue = (val) => {
    if (val === null || val === undefined || val === '') {
      return <span className="val-not-available">Not available</span>
    }
    return <span className="val-present">{val}</span>
  }

  const fields = [
    { label: 'Document Type', value: document?.document_type },
    { label: 'Full Name', value: document?.full_name },
    { label: 'Document Number', value: document?.document_number },
    { label: 'Nationality', value: document?.nationality },
    { label: 'Date of Birth', value: document?.date_of_birth },
    { label: 'Expiry Date', value: document?.expiry_date },
    { label: 'Sex', value: document?.sex },
  ]

  const isExtractionUnavailable = !document?.full_name && !document?.document_number

  return (
    <div className="identity-details-card">
      <div className="section-header">
        <div className="header-label-group">
          <span className="section-eyebrow">PASSPORT / ID RECOGNITION</span>
          <h2 className="section-title">Extracted Document Information</h2>
        </div>
        <div className="screening-id-pill">
          <span className="id-label">SCREENING ID:</span>
          <span className="id-value">{screeningId || 'Not available'}</span>
        </div>
      </div>

      {isExtractionUnavailable && (
        <div className="extraction-warning-banner">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div className="banner-text">
            <strong>Document extraction service unavailable or unreadable.</strong>
            <span> Dependent checks report NOT_AVAILABLE. Biometric face comparison and forensic tamper analysis remain active.</span>
          </div>
        </div>
      )}

      <div className="details-grid">
        {fields.map((f, i) => (
          <div key={i} className="detail-item">
            <span className="detail-label">{f.label}</span>
            <div className="detail-value">{formatValue(f.value)}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
