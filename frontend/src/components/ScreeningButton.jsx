import React from 'react'

export function ScreeningButton({ disabled, loading, onClick }) {
  return (
    <div className="screening-cta-wrapper">
      <button
        type="button"
        className={`btn-start-screening ${disabled ? 'disabled' : ''} ${loading ? 'loading' : ''}`}
        disabled={disabled || loading}
        onClick={onClick}
      >
        {loading ? (
          <span className="btn-content-loading">
            <span className="screening-spinner" />
            <span className="btn-text">Processing Screening Pipeline...</span>
          </span>
        ) : (
          <span className="btn-content-idle">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            <span className="btn-text">Start Screening</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </span>
        )}
      </button>

      {disabled && !loading && (
        <p className="cta-helper-text">
          Upload both a valid identity document and applicant selfie to initiate automated screening.
        </p>
      )}
    </div>
  )
}
