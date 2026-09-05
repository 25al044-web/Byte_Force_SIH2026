import React from 'react'

const MODULE_CHIPS = [
  { id: 'doc-ext', label: 'Document Extraction', tech: 'Gemini Multimodal' },
  { id: 'mrz-val', label: 'MRZ Validation', tech: 'ICAO Doc 9303 TD3' },
  { id: 'exp-val', label: 'Expiry Validation', tech: 'Temporal Rule' },
  { id: 'face-ver', label: 'Face Verification', tech: 'InsightFace ArcFace' },
  { id: 'dup-id', label: 'Duplicate Identity', tech: 'Vector Match' },
  { id: 'blacklist', label: 'Blacklist', tech: 'SQLite Exact/Fuzzy' },
  { id: 'tamper', label: 'Tamper Screening', tech: 'OpenCV Forensic ELA' },
  { id: 'risk-eng', label: 'Explainable Risk Engine', tech: 'Multi-Factor' },
]

export function HeroIntro() {
  return (
    <section className="hero-section">
      <div className="hero-content">
        <div className="hero-badge">
          <span className="hero-badge-dot" />
          <span>BORDER IDENTITY DEFENSE &amp; CREDENTIAL TRIAGE</span>
        </div>
        <p className="hero-description">
          Automated multi-factor screening engine combining neural visual extraction, ICAO TD3 checksum verification, biometric face match, duplicate facial vector indexing, and OpenCV digital forensic analysis to detect counterfeit credentials and watchlist matches in real time.
        </p>

        <div className="module-chips-row">
          {MODULE_CHIPS.map((mod) => (
            <div key={mod.id} className="module-chip" title={`${mod.label} (${mod.tech})`}>
              <span className="chip-bullet" />
              <span className="chip-label">{mod.label}</span>
              <span className="chip-tech">{mod.tech}</span>
            </div>
          ))}
        </div>

        <div className="hero-disclaimer">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>Operational screening aid — final decision requires authorized human review.</span>
        </div>
      </div>
    </section>
  )
}
