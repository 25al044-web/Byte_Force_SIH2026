import React from 'react'

const PIPELINE_MODULES = [
  { id: 'doc-ext', label: 'Document Extraction', tech: 'Gemini Multimodal' },
  { id: 'mrz', label: 'MRZ Validation', tech: 'ICAO TD3 Checksum' },
  { id: 'expiry', label: 'Expiry Validation', tech: 'Temporal Rule Engine' },
  { id: 'face', label: 'Face Verification', tech: 'InsightFace ArcFace' },
  { id: 'dup', label: 'Duplicate Identity', tech: 'Vector Store Search' },
  { id: 'blacklist', label: 'Blacklist Screening', tech: 'SQLite Cross-Reference' },
  { id: 'tamper', label: 'Tamper Analysis', tech: 'OpenCV Forensic ELA' },
  { id: 'risk', label: 'Explainable Risk Engine', tech: 'Multi-Factor Weighted' },
]

export function EmptyState() {
  return (
    <div className="empty-state">
      {/* CSS geometric composition */}
      <div className="empty-state-visual" aria-hidden="true">
        <div className="es-outer-ring">
          <div className="es-inner-ring">
            <div className="es-shield-icon">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
          </div>
          {/* Orbit elements */}
          <div className="es-orbit-dot es-dot-1" />
          <div className="es-orbit-dot es-dot-2" />
          <div className="es-orbit-dot es-dot-3" />
        </div>

        {/* Document + Selfie icons flanking */}
        <div className="es-flanking">
          <div className="es-flank-card">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
            <span>Identity Document</span>
          </div>
          <div className="es-connector-line" aria-hidden="true" />
          <div className="es-flank-card">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <circle cx="12" cy="8" r="4" />
              <path d="M20 21a8 8 0 1 0-16 0" />
            </svg>
            <span>Applicant Selfie</span>
          </div>
        </div>
      </div>

      {/* Copy */}
      <div className="empty-state-copy">
        <h2 className="es-heading">Begin a New Identity Screening</h2>
        <p className="es-body">
          Upload an identity document scan and applicant selfie photograph to initiate
          multimodal biometric verification and document intelligence analysis.
        </p>
      </div>

      {/* Pipeline modules */}
      <div className="es-modules-label">8 active verification modules</div>
      <div className="es-modules-grid">
        {PIPELINE_MODULES.map((m) => (
          <div key={m.id} className="es-module-chip" title={m.tech}>
            <span className="es-module-dot" />
            <span className="es-module-name">{m.label}</span>
          </div>
        ))}
      </div>

      <p className="es-disclaimer">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
        Operational screening aid — final decision requires authorized human review.
      </p>
    </div>
  )
}
