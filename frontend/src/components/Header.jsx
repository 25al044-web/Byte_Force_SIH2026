import React from 'react'

export function Header({ backendOnline, demoMode, onResetDemo, resettingDemo }) {
  return (
    <header className="app-header">
      <div className="header-container">
        <div className="header-brand">
          <div className="brand-emblem">
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
          </div>
          <div className="brand-titles">
            <div className="brand-meta-row">
              <span className="meta-tag tag-sih">SIH 2026 DEMO</span>
              <span className="meta-tag tag-problem">SIH26188</span>
              <span className={`meta-tag ${demoMode ? 'tag-demo' : 'tag-prod'}`}>
                {demoMode ? 'DEMO MODE' : 'PRODUCTION'}
              </span>
            </div>
            <h1 className="brand-heading">AI-Based Fake Identity &amp; Document Screening System</h1>
            <p className="brand-subheading">Real-time Border Identity Risk Screening</p>
          </div>
        </div>

        <div className="header-controls">
          <div className={`connection-pill ${backendOnline ? 'online' : 'offline'}`}>
            <span className="connection-dot">
              <span className="connection-pulse" />
            </span>
            <span className="connection-text">
              {backendOnline ? 'Backend Connected' : 'Backend Disconnected'}
            </span>
          </div>

          {demoMode && onResetDemo && (
            <button
              type="button"
              className="btn-reset-demo"
              onClick={onResetDemo}
              disabled={resettingDemo || !backendOnline}
              title="Clear duplicate identity scan history while keeping watchlist intact"
            >
              <svg
                className={resettingDemo ? 'animate-spin' : ''}
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
              <span>{resettingDemo ? 'Resetting...' : 'Reset Demo Data'}</span>
            </button>
          )}
        </div>
      </div>
    </header>
  )
}

