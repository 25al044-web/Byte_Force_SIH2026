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
