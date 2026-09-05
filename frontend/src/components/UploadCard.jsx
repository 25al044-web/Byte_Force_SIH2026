import React, { useRef, useState } from 'react'

export function UploadCard({
  id,
  title,
  subtitle,
  file,
  previewUrl,
  onFileSelect,
  onRemove,
  iconType = 'document',
}) {
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState(null)
  const fileInputRef = useRef(null)

  const allowedMimeTypes = ['image/jpeg', 'image/png']

  const handleFile = (selectedFile) => {
    setError(null)
    if (!selectedFile) return

    if (!allowedMimeTypes.includes(selectedFile.type)) {
      setError('Unsupported format. Please select a JPEG or PNG image.')
      return
    }

    if (selectedFile.size > 15 * 1024 * 1024) {
      setError('File size exceeds 15MB limit.')
      return
    }

    onFileSelect(selectedFile)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  const handleInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFile(e.target.files[0])
    }
  }

  const formatFileSize = (bytes) => {
    if (!bytes) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return `${(bytes / Math.pow(k, i)).toFixed(1)} ${sizes[i]}`
  }

  return (
    <div className={`upload-card ${isDragging ? 'dragging' : ''} ${file ? 'has-file' : ''}`}>
      <div className="card-top-bar">
        <div className="card-icon-tag">
          {iconType === 'document' ? (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          ) : (
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="8" r="5" />
              <path d="M20 21a8 8 0 1 0-16 0" />
            </svg>
          )}
        </div>
        <div className="card-heading-group">
          <h3 className="card-title">{title}</h3>
          <span className="card-subtitle">{subtitle}</span>
        </div>
      </div>

      <input
        ref={fileInputRef}
        id={id}
        type="file"
        accept="image/jpeg,image/png"
        className="hidden-file-input"
        onChange={handleInputChange}
      />

      {!file ? (
        <div
          className="dropzone-area"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === 'Enter' || e.key === ' ') {
              fileInputRef.current?.click()
            }
          }}
        >
          <div className="dropzone-prompt">
            <div className="dropzone-icon-circle">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            </div>
            <p className="dropzone-primary-text">
              <strong>Click to upload</strong> or drag &amp; drop
            </p>
            <p className="dropzone-hint-text">
              Supported: JPEG, PNG • Up to 15MB
            </p>
          </div>
        </div>
      ) : (
        <div className="preview-container">
          <div className="preview-image-wrapper">
            <img
              src={previewUrl}
              alt={`${title} Preview`}
              className="preview-img"
            />
            <div className="preview-overlay-badge">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>IMAGE ATTACHED</span>
            </div>
          </div>

          <div className="preview-metadata-bar">
            <div className="file-info">
              <span className="file-name" title={file.name}>{file.name}</span>
              <span className="file-size">{formatFileSize(file.size)}</span>
            </div>

            <div className="preview-actions">
              <button
                type="button"
                className="btn-action btn-replace"
                onClick={() => fileInputRef.current?.click()}
                title="Replace with another image"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <polyline points="1 4 1 10 7 10" />
                  <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                </svg>
                <span>Replace</span>
              </button>
              <button
                type="button"
                className="btn-action btn-remove"
                onClick={onRemove}
                title="Remove file"
              >
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18" />
                  <line x1="6" y1="6" x2="18" y2="18" />
                </svg>
                <span>Remove</span>
              </button>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="upload-inline-error">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{error}</span>
        </div>
      )}
    </div>
  )
}
