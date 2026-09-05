import React from 'react'

/**
 * StatusPill — reusable status badge
 * status: 'PASS' | 'WARNING' | 'FAIL' | 'NOT_AVAILABLE'
 * size: 'sm' | 'md' | 'lg'
 */
export function StatusPill({ status, size = 'md' }) {
  const meta = {
    PASS: {
      label: 'PASS',
      cls: 'pill-pass',
      icon: (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      ),
    },
    WARNING: {
      label: 'WARNING',
      cls: 'pill-warn',
      icon: (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
          <line x1="12" y1="9" x2="12" y2="13" />
          <line x1="12" y1="17" x2="12.01" y2="17" />
        </svg>
      ),
    },
    FAIL: {
      label: 'FAIL',
      cls: 'pill-fail',
      icon: (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      ),
    },
    NOT_AVAILABLE: {
      label: 'N/A',
      cls: 'pill-na',
      icon: (
        <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
          <circle cx="12" cy="12" r="10" />
          <line x1="8" y1="12" x2="16" y2="12" />
        </svg>
      ),
    },
  }[status] || {
    label: status || 'N/A',
    cls: 'pill-na',
    icon: null,
  }

  return (
    <span className={`status-pill ${meta.cls} pill-${size}`}>
      {meta.icon}
      <span>{meta.label}</span>
    </span>
  )
}
