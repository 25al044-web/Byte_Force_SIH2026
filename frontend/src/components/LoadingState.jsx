import React, { useEffect, useState } from 'react'

const PIPELINE_STAGES = [
  {
    step: 1,
    title: 'Extracting document details',
    detail: 'Transcribing text, MRZ zones, and document metadata via Gemini',
  },
  {
    step: 2,
    title: 'Verifying face',
    detail: 'Comparing document portrait crop against applicant selfie via ArcFace',
  },
  {
    step: 3,
    title: 'Running document checks',
    detail: 'Evaluating ICAO TD3 checksums, expiration, tampering, and blacklist stores',
  },
  {
    step: 4,
    title: 'Calculating risk',
    detail: 'Synthesizing auditable risk score and multi-factor triage decision',
  },
]

export function LoadingState() {
  const [activeStep, setActiveStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveStep((prev) => (prev + 1) % PIPELINE_STAGES.length)
    }, 1100)
    return () => clearInterval(timer)
  }, [])

  const progressPercent = Math.min(100, Math.round(((activeStep + 1) / PIPELINE_STAGES.length) * 100))

  return (
    <div className="loading-card-container">
      <div className="loading-surface">
        {/* Radar Scanner Visual */}
        <div className="radar-visual">
          <div className="radar-ring ring-1" />
          <div className="radar-ring ring-2" />
          <div className="radar-ring ring-3" />
          <div className="radar-sweep" />
          <div className="radar-center-shield">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
        </div>

        {/* Progress Information */}
        <div className="loading-content">
          <div className="loading-headline">
            <span className="live-status-pill">
              <span className="live-pulse" />
              LIVE SCREENING IN PROGRESS
            </span>
            <span className="stage-counter">
              STAGE {activeStep + 1} OF {PIPELINE_STAGES.length}
            </span>
          </div>

          <h3 className="active-stage-title">
            {PIPELINE_STAGES[activeStep].title}
          </h3>
          <p className="active-stage-detail">
            {PIPELINE_STAGES[activeStep].detail}
          </p>

          <div className="loading-progress-bar">
            <div
              className="loading-progress-fill"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* Stepper Dots */}
          <div className="stepper-row">
            {PIPELINE_STAGES.map((s, idx) => {
              const isDone = idx < activeStep
              const isCurrent = idx === activeStep

              return (
                <div
                  key={s.step}
                  className={`stepper-item ${isDone ? 'done' : ''} ${isCurrent ? 'current' : ''}`}
                >
                  <div className="stepper-indicator">
                    {isDone ? (
                      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <span>{s.step}</span>
                    )}
                  </div>
                  <span className="stepper-label">{s.title}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>
    </div>
  )
}
