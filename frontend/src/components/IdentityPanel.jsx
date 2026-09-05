import React from 'react'
import { SectionHeader } from './SectionHeader'

function FieldCell({ label, value }) {
  const isEmpty = value === null || value === undefined || value === ''
  return (
    <div className="idn-field">
      <span className="idn-label">{label}</span>
      <span className={`idn-value ${isEmpty ? 'idn-value-na' : ''}`}>
        {isEmpty ? 'Not available' : value}
      </span>
    </div>
  )
}

export function IdentityPanel({ screeningId, document, mrzLine1, mrzLine2 }) {
  const fields = [
    { label: 'FULL NAME', value: document?.full_name },
    { label: 'DOCUMENT TYPE', value: document?.document_type ? document.document_type.replace(/_/g, ' ').toUpperCase() : null },
    { label: 'DOCUMENT NUMBER', value: document?.document_number },
    { label: 'NATIONALITY', value: document?.nationality },
    { label: 'DATE OF BIRTH', value: document?.date_of_birth },
    { label: 'EXPIRY DATE', value: document?.expiry_date },
    { label: 'SEX', value: document?.sex },
    { label: 'ISSUING AUTHORITY', value: document?.issuing_authority },
    { label: 'INSTITUTION / ORG', value: document?.institution_or_organization },
  ]

  const isUnavailable = !document?.full_name && !document?.document_number
  const hasMrz = mrzLine1 || mrzLine2

  return (
    <div className="identity-panel">
      <SectionHeader
        eyebrow="CREDENTIAL TRANSCRIPTION"
        title="Extracted Document Information"
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <rect x="3" y="4" width="18" height="16" rx="2" />
            <circle cx="9" cy="10" r="2" />
            <line x1="15" y1="8" x2="17" y2="8" />
            <line x1="15" y1="12" x2="17" y2="12" />
            <line x1="7" y1="16" x2="17" y2="16" />
          </svg>
        }
        right={
          <span className={`idn-status-pill ${isUnavailable ? 'pill-degraded' : 'pill-extracted'}`}>
            {isUnavailable ? 'EXTRACTION DEGRADED' : 'EXTRACTED VIA GEMINI'}
          </span>
        }
      />

      {isUnavailable && (
        <div className="idn-alert">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
          <div>
            <strong>Document intelligence service temporarily unavailable.</strong>
            <span> Dependent checks report NOT_AVAILABLE. Biometric face comparison and forensic tamper analysis remain active.</span>
          </div>
        </div>
      )}

      <div className="idn-fields-grid">
        {fields.map((f, i) => (
          <FieldCell key={i} label={f.label} value={f.value} />
        ))}
      </div>

      <div className={`idn-mrz-block ${!hasMrz ? 'idn-mrz-empty' : ''}`}>
        <div className="idn-mrz-header">
          <span className="idn-mrz-tag">ICAO TD3 MACHINE READABLE ZONE (MRZ)</span>
          {hasMrz ? (
            <span className="idn-mrz-detected">DETECTED</span>
          ) : (
            <span className="idn-mrz-absent">NOT DETECTED</span>
          )}
        </div>
        {hasMrz ? (
          <div className="idn-mrz-lines">
            {mrzLine1 && <div className="idn-mrz-line">{mrzLine1}</div>}
            {mrzLine2 && <div className="idn-mrz-line">{mrzLine2}</div>}
          </div>
        ) : (
          <p className="idn-mrz-empty-text">
            MRZ not detected on this document type or image quality.
          </p>
        )}
      </div>
    </div>
  )
}
