import React, { useEffect, useState } from 'react'

function LiveClock() {
  const [time, setTime] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setTime(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  return (
    <span className="topbar-clock">
      {time.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })}
      &nbsp;IST
    </span>
  )
}

export function TopBar({ backendOnline, demoMode, onResetDemo, resettingDemo }) {
  return (
    <header className="topbar">
      <div className="topbar-left">
        <div className="topbar-title-group">
          <h1 className="topbar-page-title">Identity Screening</h1>
          <p className="topbar-page-sub">
            Multimodal document &amp; biometric verification
          </p>
        </div>
      </div>

      <div className="topbar-right">
        <LiveClock />

        <div className="topbar-divider-v" />

        <div className={`topbar-status-pill ${backendOnline ? 'status-online' : 'status-offline'}`}>
          <span className="topbar-status-dot" />
          <span>{backendOnline ? 'Systems Operational' : 'Service Unavailable'}</span>
        </div>

        {demoMode && (
          <span className="topbar-mode-pill">DEMO MODE</span>
        )}

        <div className="topbar-divider-v" />

        {onResetDemo && (
          <button
            type="button"
            className="topbar-reset-btn"
            onClick={onResetDemo}
            disabled={resettingDemo || !backendOnline}
            title="Clear duplicate identity scan history"
          >
            <svg
              className={resettingDemo ? 'spin-icon' : ''}
              width="13"
              height="13"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.25"
            >
              <polyline points="1 4 1 10 7 10" />
              <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
            </svg>
            <span>{resettingDemo ? 'Resetting…' : 'Reset Demo'}</span>
          </button>
        )}
      </div>
    </header>
  )
}
