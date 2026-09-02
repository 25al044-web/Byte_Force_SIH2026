import React from 'react'

export function ErrorMessage({ message, onDismiss }) {
  if (!message) return null

  return (
    <div className="error-banner" role="alert">
      <div className="error-icon-wrapper">
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>

      <div className="error-content">
        <strong className="error-title">Screening Operation Error</strong>
        <p className="error-text">{message}</p>
      </div>

      {onDismiss && (
        <button
          type="button"
          className="error-dismiss-btn"
          onClick={onDismiss}
          aria-label="Dismiss error"
        >
          &times;
        </button>
      )}
    </div>
  )
}
