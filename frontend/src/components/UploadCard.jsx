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
      setError('Invalid file format. Only JPEG and PNG images are supported.')
      return
    }

    onFileSelect(selectedFile)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = (e) => {
    e.preventDefault()
    setIsDragging(false)
  }

  const handleDrop = (e) => {
    e.preventDefault()
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
      <div className="upload-header">
        <div className="upload-icon-wrapper">
          {iconType === 'document' ? (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10 9 9 9 8 9" />
            </svg>
          ) : (
            <svg
              width="20"
              height="20"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <circle cx="12" cy="8" r="5" />
              <path d="M20 21a8 8 0 1 0-16 0" />
            </svg>
          )}
        </div>
        <div className="upload-title-block">
          <h2 className="upload-title">{title}</h2>
          <span className="upload-subtitle">{subtitle}</span>
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
          className="drop-zone"
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <div className="drop-zone-content">
            <svg
              className="drop-icon"
              width="36"
              height="36"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.75"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="drop-main-text">
              <strong>Click to browse</strong> or drag &amp; drop image
            </p>
            <span className="drop-sub-text">Supported formats: JPEG, PNG</span>
            <button
              type="button"
              className="browse-btn"
              onClick={(e) => {
                e.stopPropagation()
                fileInputRef.current?.click()
              }}
            >
              Browse Files
            </button>
          </div>
        </div>
      ) : (
        <div className="preview-container">
          <div className="preview-image-wrapper">
            <img src={previewUrl} alt={title} className="preview-image" />
          </div>
          <div className="preview-meta">
            <div className="file-info">
              <span className="file-name" title={file.name}>
                {file.name}
              </span>
              <span className="file-size">{formatFileSize(file.size)}</span>
            </div>
            <div className="preview-actions">
              <button
                type="button"
                className="action-btn replace-btn"
                onClick={() => fileInputRef.current?.click()}
              >
                Replace
              </button>
              <button
                type="button"
                className="action-btn remove-btn"
                onClick={() => {
                  setError(null)
                  onRemove()
                  if (fileInputRef.current) fileInputRef.current.value = ''
                }}
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}

      {error && <div className="card-error-inline">{error}</div>}
    </div>
  )
}
