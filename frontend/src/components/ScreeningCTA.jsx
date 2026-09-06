import React from 'react'
import { useTranslation } from '../i18n'

export function ScreeningCTA({ disabled, loading, onClick }) {
  const { t } = useTranslation()
  return (
    <div className="cta-wrapper">
      <button
        type="button"
        className={`cta-btn ${disabled ? 'cta-disabled' : ''} ${loading ? 'cta-loading' : ''}`}
        disabled={disabled || loading}
        onClick={onClick}
      >
        {loading ? (
          <>
            <span className="cta-spinner" aria-hidden="true" />
            <span className="cta-text">{t('processing')}</span>
          </>
        ) : (
          <>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <path d="M9 12l2 2 4-4" />
            </svg>
            <span className="cta-text">{t('startScreening')}</span>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="9 18 15 12 9 6" />
            </svg>
          </>
        )}
      </button>

      {disabled && !loading && (
        <p className="cta-hint">
          {t('uploadIdentityDocument')} · {t('applicantSelfie')}
        </p>
      )}
    </div>
  )
}
