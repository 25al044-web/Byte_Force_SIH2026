import React from 'react'

export function Sidebar({ backendOnline, demoMode, onOpenBlacklist }) {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="brand-mark">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            <path d="M9 12l2 2 4-4" />
          </svg>
        </div>
        <div className="brand-text">
          <span className="brand-name">Sentinel ID</span>
          <span className="brand-sub">Identity Screening Platform</span>
        </div>
      </div>

      <div className="sidebar-divider" />

      {/* Navigation */}
      <nav className="sidebar-nav" aria-label="Main navigation">
        <span className="nav-section-label">NAVIGATION</span>
        <ul className="nav-list">
          {/* Active: Screening */}
          <li>
            <div className="nav-item nav-active" aria-current="page">
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                  <path d="M9 12l2 2 4-4" />
                </svg>
              </span>
              <span className="nav-label">Screening</span>
              <span className="nav-active-dot" />
            </div>
          </li>

          {/* Live: Watchlist / Blacklist Management */}
          <li>
            <button
              type="button"
              className="nav-item nav-live-btn"
              onClick={onOpenBlacklist}
              title="Open Blacklist Management"
            >
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
                </svg>
              </span>
              <span className="nav-label">Watchlist</span>
              <span className="nav-live-badge">LIVE</span>
            </button>
          </li>

          {/* Locked: Case Review */}
          <li>
            <div className="nav-item nav-disabled" title="Not available in this demo">
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              </span>
              <span className="nav-label">Case Review</span>
              <span className="nav-lock-badge">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
            </div>
          </li>

          {/* Locked: Audit Trail */}
          <li>
            <div className="nav-item nav-disabled" title="Not available in this demo">
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                </svg>
              </span>
              <span className="nav-label">Audit Trail</span>
              <span className="nav-lock-badge">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
            </div>
          </li>

          {/* Locked: System Status */}
          <li>
            <div className="nav-item nav-disabled" title="Not available in this demo">
              <span className="nav-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                  <line x1="8" y1="21" x2="16" y2="21" />
                  <line x1="12" y1="17" x2="12" y2="21" />
                </svg>
              </span>
              <span className="nav-label">System Status</span>
              <span className="nav-lock-badge">
                <svg width="9" height="9" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                  <path d="M7 11V7a5 5 0 0 1 10 0v4" />
                </svg>
              </span>
            </div>
          </li>
        </ul>
      </nav>

      {/* Spacer */}
      <div className="sidebar-spacer" />

      <div className="sidebar-divider" />

      {/* Bottom metadata */}
      <div className="sidebar-bottom">
        <div className="sidebar-status-row">
          <span className={`sidebar-conn-dot ${backendOnline ? 'conn-online' : 'conn-offline'}`} />
          <span className="sidebar-conn-label">
            {backendOnline ? 'API Connected' : 'API Offline'}
          </span>
        </div>

        <div className="sidebar-badges">
          <span className="sidebar-badge badge-sih">SIH 2026</span>
          <span className="sidebar-badge badge-problem">SIH26188</span>
          {demoMode && <span className="sidebar-badge badge-demo">DEMO</span>}
        </div>

        <div className="sidebar-meta-stack">
          <span className="sidebar-version">Sentinel ID v1.0-MVP</span>
          <span className="sidebar-tech">InsightFace · Gemini · OpenCV</span>
        </div>
      </div>
    </aside>
  )
}
