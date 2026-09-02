import React, { useEffect, useState } from 'react'

const PIPELINE_STEPS = [
  'Analyzing document structure & optical characters...',
  'Validating Machine Readable Zone (MRZ) checksums...',
  'Running forgery & digital tamper screening...',
  'Performing biometric facial consistency comparison...',
  'Cross-referencing demonstration identity databases...',
  'Synthesizing explainable risk score & evaluation...',
]

export function LoadingState() {
  const [currentStep, setCurrentStep] = useState(0)

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentStep((prev) => (prev + 1) % PIPELINE_STEPS.length)
    }, 1200)

    return () => clearInterval(timer)
  }, [])

  return (
    <div className="loading-container">
      <div className="loading-card">
        <div className="loading-radar">
          <div className="radar-circle circle-1" />
          <div className="radar-circle circle-2" />
          <div className="radar-scanner" />
          <svg
            className="radar-center-icon"
            width="28"
            height="28"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
        </div>

        <div className="loading-info">
          <h3 className="loading-title">SCREENING IN PROGRESS</h3>
          <p className="loading-step-text">{PIPELINE_STEPS[currentStep]}</p>
          <span className="loading-note">
            Communicating with FastAPI screening pipeline (`POST /api/screen`). Please wait.
          </span>
        </div>
      </div>
    </div>
  )
}
