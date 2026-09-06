import React from 'react'
import { useTranslation } from '../i18n'

export function Sidebar({ backendOnline, demoMode, currentView = 'screening', onSelectView }) {
  const { t } = useTranslation()

  const navItems = [
    {
      id: 'screening',
      label: t('screening'),
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <path d="M9 12l2 2 4-4" />
        </svg>
      ),
    },
    {
      id: 'watchlist',
      label: t('watchlist'),
      badge: 'LIVE',
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
        </svg>
      ),
    },
    {
      id: 'case_review',
      label: t('caseReview'),
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
          <line x1="16" y1="13" x2="8" y2="13" />
          <line x1="16" y1="17" x2="8" y2="17" />
        </svg>
      ),
    },
    {
      id: 'audit_trail',
      label: t('auditTrail'),
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      id: 'system_status',
      label: t('systemStatus'),
      icon: (
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      ),
    },
  ]

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
          <span className="brand-sub">{t('identityScreening')}</span>
        </div>
      </div>

      <div className="sidebar-divider" />

      {/* Navigation */}
      <nav className="sidebar-nav" aria-label={t('dashboard')}>
        <span className="nav-section-label">{t('dashboard')}</span>
        <ul className="nav-list">
          {navItems.map((item) => {
            const isActive = currentView === item.id
            return (
              <li key={item.id}>
                <button
                  type="button"
                  className={`nav-item ${isActive ? 'nav-active' : ''}`}
                  onClick={() => onSelectView && onSelectView(item.id)}
                  aria-current={isActive ? 'page' : undefined}
                  title={item.label}
                >
                  <span className="nav-icon">{item.icon}</span>
                  <span className="nav-label">{item.label}</span>
                  {item.badge && <span className="nav-live-badge">{item.badge}</span>}
                  {isActive && <span className="nav-active-dot" />}
                </button>
              </li>
            )
          })}
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
