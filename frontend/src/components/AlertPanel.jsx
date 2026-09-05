import React from 'react'

/**
 * AlertPanel — critical alert for blacklist / duplicate identity hits
 * type: 'danger' | 'warning'
 */
export function AlertPanel({ type = 'danger', title, detail, metadata = [] }) {
  return (
    <div className={`alert-panel alert-${type}`} role="alert">
      <div className="alert-icon-col">
        {type === 'danger' ? (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
            <line x1="12" y1="9" x2="12" y2="13" />
            <line x1="12" y1="17" x2="12.01" y2="17" />
          </svg>
        ) : (
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        )}
      </div>
      <div className="alert-body">
        <p className="alert-title">{title}</p>
        {detail && <p className="alert-detail">{detail}</p>}
        {metadata.length > 0 && (
          <div className="alert-meta-row">
            {metadata.map((m, i) => (
              <span key={i} className="alert-meta-chip">
                <span className="alert-meta-label">{m.label}</span>
                <span className="alert-meta-value">{m.value}</span>
              </span>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
