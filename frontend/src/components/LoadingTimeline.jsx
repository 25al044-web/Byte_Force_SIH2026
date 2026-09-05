import React, { useEffect, useState } from 'react'

const STAGES = [
  {
    id: 1,
    label: 'Extracting identity data',
    detail: 'Transcribing text, MRZ zones, and metadata via Gemini multimodal intelligence',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
      </svg>
    ),
  },
  {
    id: 2,
    label: 'Validating document integrity',
    detail: 'Parsing ICAO TD3 checksums and verifying document structure compliance',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <line x1="7" y1="13" x2="17" y2="13" />
        <line x1="7" y1="17" x2="17" y2="17" />
      </svg>
    ),
  },
  {
    id: 3,
    label: 'Comparing facial biometrics',
    detail: 'Measuring cosine similarity between document portrait and applicant selfie',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="8" r="4" />
        <path d="M20 21a8 8 0 1 0-16 0" />
      </svg>
    ),
  },
  {
    id: 4,
    label: 'Checking watchlist records',
    detail: 'Cross-referencing name, document number, and nationality against SQLite watchlist',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <circle cx="12" cy="12" r="10" />
        <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
      </svg>
    ),
  },
  {
    id: 5,
    label: 'Searching duplicate identities',
    detail: 'Querying face embedding vector store for near-duplicate matches',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
  },
  {
    id: 6,
    label: 'Evaluating tamper indicators',
    detail: 'Running OpenCV forensic analysis: Laplacian variance, ELA, edge irregularity',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
        <line x1="12" y1="8" x2="12" y2="12" />
        <line x1="12" y1="16" x2="12.01" y2="16" />
      </svg>
    ),
  },
  {
    id: 7,
    label: 'Calculating risk assessment',
    detail: 'Synthesizing deterministic weighted penalty score and triage classification',
    icon: (
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
  },
]

export function LoadingTimeline() {
  const [activeIdx, setActiveIdx] = useState(0)

  useEffect(() => {
    const t = setInterval(() => {
      setActiveIdx((p) => Math.min(p + 1, STAGES.length - 1))
    }, 950)
    return () => clearInterval(t)
  }, [])

  const progress = Math.round(((activeIdx + 1) / STAGES.length) * 100)

  return (
    <div className="loading-timeline-card">
      {/* Header */}
      <div className="lt-header">
        <div className="lt-live-badge">
          <span className="lt-pulse" />
          <span>LIVE ANALYSIS</span>
        </div>
        <span className="lt-stage-counter">
          {activeIdx + 1} / {STAGES.length} stages
        </span>
      </div>

      {/* Progress bar */}
      <div className="lt-progress-bar">
        <div className="lt-progress-fill" style={{ width: `${progress}%` }} />
      </div>

      {/* Timeline */}
      <div className="lt-stages">
        {STAGES.map((stage, idx) => {
          const isDone = idx < activeIdx
          const isActive = idx === activeIdx
          const isPending = idx > activeIdx

          return (
            <div
              key={stage.id}
              className={`lt-stage ${isDone ? 'lt-done' : ''} ${isActive ? 'lt-active' : ''} ${isPending ? 'lt-pending' : ''}`}
            >
              <div className="lt-stage-indicator">
                {isDone ? (
                  <div className="lt-indicator-done">
                    <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                  </div>
                ) : isActive ? (
                  <div className="lt-indicator-active">
                    <span className="lt-active-ring" />
                    <span className="lt-active-core" />
                  </div>
                ) : (
                  <div className="lt-indicator-pending">
                    <span className="lt-pending-dot" />
                  </div>
                )}
                {idx < STAGES.length - 1 && (
                  <div className={`lt-connector ${isDone ? 'lt-conn-done' : ''}`} />
                )}
              </div>

              <div className="lt-stage-content">
                <div className="lt-stage-icon">{stage.icon}</div>
                <div className="lt-stage-text">
                  <span className="lt-stage-label">{stage.label}</span>
                  {isActive && (
                    <span className="lt-stage-detail">{stage.detail}</span>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
