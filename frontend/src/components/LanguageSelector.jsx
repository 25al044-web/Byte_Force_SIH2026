import React from 'react'
import { LANGUAGE_OPTIONS, useTranslation } from '../i18n'

export function LanguageSelector() {
  const { language, setLanguage, t } = useTranslation()
  return (
    <label className="language-selector" title={t('language')}>
      <span className="language-selector-label">{t('language')}</span>
      <select value={language} onChange={(event) => setLanguage(event.target.value)} aria-label={t('language')}>
        {LANGUAGE_OPTIONS.map(({ code, name }) => <option key={code} value={code}>{name}</option>)}
      </select>
    </label>
  )
}
