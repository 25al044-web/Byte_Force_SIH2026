import React from 'react'

export function ScreeningButton({ disabled, loading, onClick }) {
  return (
    <div className="screening-action-container">
      <button
        type="button"
        className={`screening-btn ${disabled ? 'disabled' : ''} ${loading ? 'loading' : ''}`}
        disabled={disabled || loading}
        onClick={onClick}
      >
        {loading ? (
          <>
            <span className="spinner" />
            <span>PROCESSING SCREENING PIPELINE...</span>
          </>
        ) : (
          <>
            <svg
              className="btn-icon"
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <span>RUN IDENTITY SCREENING</span>
          </>
        )}
      </button>
      {disabled && !loading && (
        <p className="btn-hint">
          Please upload both a travel/identity document and a live selfie to proceed with screening.
        </p>
      )}
    </div>
  )
}
