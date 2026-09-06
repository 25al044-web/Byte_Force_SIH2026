import React from 'react'
import { useTranslation } from '../i18n'

export function ErrorMessage({ message, onDismiss }) {
  const { t } = useTranslation()
  if (!message) return null

  return (
    <div className="error-banner" role="alert" aria-live="assertive">
      <div className="error-icon">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      </div>
      <div className="error-body">
        <span className="error-heading">{t('systemNotice')}</span>
        <span className="error-msg">{message}</span>
      </div>
      {onDismiss && (
        <button
          type="button"
          className="error-dismiss"
          onClick={onDismiss}
          aria-label={t('dismiss')}
        >
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        </button>
      )}
    </div>
  )
}
