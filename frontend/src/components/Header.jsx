import React from 'react'

export function Header({ backendOnline, demoMode, onResetDemo, resettingDemo }) {
  return (
    <header className="app-header">
      <div className="header-top">
        <div className="system-identity">
          <div className="emblem">
            <svg
              width="24"
              height="24"
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
          <div className="system-titles">
            <div className="meta-row">
              <span className="badge-problem">Problem Statement: SIH26188</span>
              <span className={`badge-dev ${demoMode ? 'badge-demo' : ''}`}>
                {demoMode ? 'DEVELOPMENT / DEMO MODE' : 'PRODUCTION MODE'}
              </span>
              <span className={`badge-status ${backendOnline ? 'online' : 'offline'}`}>
                <span className="pulse-dot" />
                {backendOnline ? 'Backend Connected' : 'Backend Disconnected'}
              </span>

              {demoMode && onResetDemo && (
                <button
                  type="button"
                  className="demo-reset-header-btn"
                  onClick={onResetDemo}
                  disabled={resettingDemo || !backendOnline}
                  title="Clear duplicate identity scan history while keeping blacklist intact"
                >
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                  <span>{resettingDemo ? 'Resetting...' : 'Reset Demo Data'}</span>
                </button>
              )}
            </div>
            <h1 className="system-title">AI-Based Fake Identity &amp; Document Screening System</h1>
            <p className="system-subtitle">Multimodal Document &amp; Biometric Border Security Platform</p>
          </div>
        </div>
      </div>
    </header>
  )
}
