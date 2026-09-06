import React, { useRef, useState } from 'react'
import { useTranslation } from '../i18n'

export function UploadPanel({
  id,
  title,
  subtitle,
  file,
  previewUrl,
  onFileSelect,
  onRemove,
  iconType = 'document',
}) {
  const { t } = useTranslation()
  const [isDragging, setIsDragging] = useState(false)
  const [localError, setLocalError] = useState(null)
  const inputRef = useRef(null)

  const ALLOWED = ['image/jpeg', 'image/png']
  const MAX_BYTES = 15 * 1024 * 1024

  const handleFile = (f) => {
    setLocalError(null)
    if (!f) return
    if (!ALLOWED.includes(f.type)) {
      setLocalError(t('unsupportedFormat'))
      return
    }
    if (f.size > MAX_BYTES) {
      setLocalError(t('fileTooLarge'))
      return
    }
    onFileSelect(f)
  }

  const onDragOver = (e) => { e.preventDefault(); setIsDragging(true) }
  const onDragLeave = (e) => { e.preventDefault(); setIsDragging(false) }
  const onDrop = (e) => {
    e.preventDefault(); setIsDragging(false)
    if (e.dataTransfer.files?.[0]) handleFile(e.dataTransfer.files[0])
  }
  const onInput = (e) => { if (e.target.files?.[0]) handleFile(e.target.files[0]) }

  const fmtSize = (b) => {
    if (!b) return '0 B'
    const k = 1024, s = ['B', 'KB', 'MB']
    const i = Math.floor(Math.log(b) / Math.log(k))
    return `${(b / k ** i).toFixed(1)} ${s[i]}`
  }

  const DocumentIcon = () => (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
      <polyline points="14 2 14 8 20 8" />
      <line x1="16" y1="13" x2="8" y2="13" />
      <line x1="16" y1="17" x2="8" y2="17" />
    </svg>
  )

  const SelfieIcon = () => (
    <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <circle cx="12" cy="8" r="4" />
      <path d="M20 21a8 8 0 1 0-16 0" />
    </svg>
  )

  const UploadArrowIcon = () => (
    <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
      <polyline points="17 8 12 3 7 8" />
      <line x1="12" y1="3" x2="12" y2="15" />
    </svg>
  )

  return (
    <div className={`upload-panel ${isDragging ? 'up-dragging' : ''} ${file ? 'up-filled' : ''}`}>
      {/* Panel header */}
      <div className="up-header">
        <div className="up-icon-badge">
          {iconType === 'document' ? <DocumentIcon /> : <SelfieIcon />}
        </div>
        <div className="up-title-group">
          <h3 className="up-title">{title}</h3>
          <span className="up-subtitle">{subtitle}</span>
        </div>
        {file && (
          <div className="up-header-actions">
            <button
              type="button"
              className="up-icon-btn up-btn-replace"
              onClick={() => inputRef.current?.click()}
              title={t('replaceImage')}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
            </button>
            <button
              type="button"
              className="up-icon-btn up-btn-remove"
              onClick={onRemove}
              title={t('removeImage')}
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}
      </div>

      <input
        ref={inputRef}
        id={id}
        type="file"
        accept="image/jpeg,image/png"
        className="up-hidden-input"
        onChange={onInput}
      />

      {!file ? (
        <div
          className={`up-dropzone ${isDragging ? 'up-dz-active' : ''}`}
          onDragOver={onDragOver}
          onDragLeave={onDragLeave}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
          aria-label={`${t('uploadIdentityDocument')}: ${title}`}
        >
          <div className="up-dz-icon">
            <UploadArrowIcon />
          </div>
          <p className="up-dz-primary">
            <strong>{t('clickToUpload')}</strong> · {t('dragDrop')}
          </p>
          <p className="up-dz-hint">{t('supportedFormats')}</p>
        </div>
      ) : (
        <div className="up-preview">
          <div className="up-preview-img-wrap">
            <img src={previewUrl} alt={`${title} preview`} className="up-preview-img" />
            <div className="up-preview-overlay">
              <span className="up-preview-badge">
                <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                  <polyline points="20 6 9 17 4 12" />
                </svg>
                {t('attached')}
              </span>
            </div>
          </div>
          <div className="up-file-meta">
            <span className="up-filename" title={file.name}>{file.name}</span>
            <span className="up-filesize">{fmtSize(file.size)}</span>
          </div>
        </div>
      )}

      {localError && (
        <div className="up-error">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{localError}</span>
        </div>
      )}
    </div>
  )
}
