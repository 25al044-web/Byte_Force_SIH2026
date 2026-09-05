/**
 * SelfieCapturePanel
 *
 * Replaces the selfie UploadPanel with two modes:
 *   1. CAPTURE — live webcam feed, then freeze + confirm frame
 *   2. UPLOAD  — drag-drop file upload fallback
 *
 * Produces a standard File object (selfie-capture.jpg or the uploaded file)
 * that is passed to onFileSelect — identical to UploadPanel's interface.
 *
 * The captured File is treated exactly like an uploaded selfie by the
 * existing API, which sends it as the `selfie_image` multipart field.
 *
 * Webcam cleanup: camera is stopped whenever the user:
 *  - captures and accepts a photo
 *  - clicks Cancel
 *  - uploads a file (stops any running stream)
 *  - component unmounts
 */

import React, { useCallback, useEffect, useRef, useState } from 'react'

// ── Mode constants ──────────────────────────────────────────────────────────
const MODE_IDLE     = 'IDLE'      // nothing open
const MODE_CAMERA   = 'CAMERA'    // live viewfinder
const MODE_PREVIEW  = 'PREVIEW'   // frozen captured frame, awaiting confirm
const MODE_UPLOAD   = 'UPLOAD'    // file upload flow (dropzone)

// ── File-size formatter ─────────────────────────────────────────────────────
const fmtSize = (b) => {
  if (!b) return '0 B'
  const k = 1024, s = ['B', 'KB', 'MB']
  const i = Math.floor(Math.log(b) / Math.log(k))
  return `${(b / k ** i).toFixed(1)} ${s[i]}`
}

// ──────────────────────────────────────────────────────────────────────────────
// Component
// ──────────────────────────────────────────────────────────────────────────────
export function SelfieCapturePanel({
  id = 'selfie-upload',
  title = 'Applicant Selfie',
  subtitle = 'Live frontal portrait — clear, unobstructed',
  file,
  previewUrl,
  onFileSelect,
  onRemove,
}) {
  const [mode, setMode]           = useState(MODE_IDLE)
  const [cameraError, setCameraError] = useState(null)
  const [isDragging, setIsDragging]   = useState(false)
  const [uploadError, setUploadError] = useState(null)
  const [capturePreview, setCapturePreview] = useState(null) // blob URL of frozen frame
  const [capturedFile, setCapturedFile]     = useState(null) // File object ready to confirm

  const videoRef    = useRef(null)
  const canvasRef   = useRef(null)
  const streamRef   = useRef(null)
  const inputRef    = useRef(null)

  // ── Webcam teardown ─────────────────────────────────────────────────────────
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null
    }
  }, [])

  // Cleanup on unmount
  useEffect(() => () => {
    stopCamera()
    if (capturePreview) URL.revokeObjectURL(capturePreview)
  }, [stopCamera]) // eslint-disable-line react-hooks/exhaustive-deps

  // ── Open camera ─────────────────────────────────────────────────────────────
  const openCamera = useCallback(async () => {
    setCameraError(null)
    setCapturePreview(null)
    setCapturedFile(null)
    setMode(MODE_CAMERA)

    if (!navigator.mediaDevices?.getUserMedia) {
      setCameraError('Your browser does not support camera access. Please upload a selfie instead.')
      setMode(MODE_IDLE)
      return
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 720 } },
        audio: false,
      })
      streamRef.current = stream
      if (videoRef.current) {
        videoRef.current.srcObject = stream
        // Play after metadata loaded to avoid race condition
        videoRef.current.onloadedmetadata = () => videoRef.current?.play().catch(() => {})
      }
    } catch (err) {
      stopCamera()
      setMode(MODE_IDLE)
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setCameraError('Camera access was denied. You can upload a selfie instead.')
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setCameraError('No camera was found on this device. Please upload a selfie instead.')
      } else if (err.name === 'NotReadableError' || err.name === 'TrackStartError') {
        setCameraError('Camera is already in use by another application.')
      } else {
        setCameraError('Unable to access the camera. Please upload a selfie instead.')
      }
    }
  }, [stopCamera])

  // ── Capture frame ───────────────────────────────────────────────────────────
  const captureFrame = useCallback(() => {
    const video  = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return

    canvas.width  = video.videoWidth  || 1280
    canvas.height = video.videoHeight || 720
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

    canvas.toBlob(
      (blob) => {
        if (!blob) return
        const file = new File([blob], 'selfie-capture.jpg', { type: 'image/jpeg' })
        const url  = URL.createObjectURL(blob)
        setCapturePreview(url)
        setCapturedFile(file)
        stopCamera()
        setMode(MODE_PREVIEW)
      },
      'image/jpeg',
      0.92,
    )
  }, [stopCamera])

  // ── Accept captured photo ───────────────────────────────────────────────────
  const acceptCapture = useCallback(() => {
    if (capturedFile) {
      onFileSelect(capturedFile)
    }
    setMode(MODE_IDLE)
  }, [capturedFile, onFileSelect])

  // ── Retake ──────────────────────────────────────────────────────────────────
  const retake = useCallback(() => {
    if (capturePreview) URL.revokeObjectURL(capturePreview)
    setCapturePreview(null)
    setCapturedFile(null)
    openCamera()
  }, [capturePreview, openCamera])

  // ── Cancel camera ───────────────────────────────────────────────────────────
  const cancelCamera = useCallback(() => {
    stopCamera()
    if (capturePreview) URL.revokeObjectURL(capturePreview)
    setCapturePreview(null)
    setCapturedFile(null)
    setMode(MODE_IDLE)
  }, [stopCamera, capturePreview])

  // ── Upload file handler ──────────────────────────────────────────────────────
  const ALLOWED   = ['image/jpeg', 'image/png']
  const MAX_BYTES = 15 * 1024 * 1024

  const handleUploadFile = useCallback((f) => {
    setUploadError(null)
    if (!f) return
    if (!ALLOWED.includes(f.type)) {
      setUploadError('Unsupported format. Use JPEG or PNG.')
      return
    }
    if (f.size > MAX_BYTES) {
      setUploadError('File exceeds 15 MB limit.')
      return
    }
    // If webcam was open, stop it
    stopCamera()
    setMode(MODE_IDLE)
    onFileSelect(f)
  }, [onFileSelect, stopCamera]) // eslint-disable-line react-hooks/exhaustive-deps

  const onDragOver  = (e) => { e.preventDefault(); setIsDragging(true)  }
  const onDragLeave = (e) => { e.preventDefault(); setIsDragging(false) }
  const onDrop      = (e) => {
    e.preventDefault(); setIsDragging(false)
    if (e.dataTransfer.files?.[0]) handleUploadFile(e.dataTransfer.files[0])
  }
  const onFileInput = (e) => { if (e.target.files?.[0]) handleUploadFile(e.target.files[0]) }

  const openUpload = () => {
    stopCamera()
    setMode(MODE_UPLOAD)
    setCameraError(null)
  }

  // ── Remove / reset ───────────────────────────────────────────────────────────
  const handleRemove = () => {
    stopCamera()
    setMode(MODE_IDLE)
    setCameraError(null)
    setUploadError(null)
    if (capturePreview) URL.revokeObjectURL(capturePreview)
    setCapturePreview(null)
    setCapturedFile(null)
    onRemove()
  }

  // ── Derived booleans ────────────────────────────────────────────────────────
  const isCameraOpen  = mode === MODE_CAMERA
  const isPreviewMode = mode === MODE_PREVIEW
  const isUploadMode  = mode === MODE_UPLOAD
  const hasFile       = Boolean(file)

  // ────────────────────────────────────────────────────────────────────────────
  // Render
  // ────────────────────────────────────────────────────────────────────────────
  return (
    <div className={`upload-panel sc-panel ${isCameraOpen ? 'sc-camera-open' : ''} ${hasFile ? 'up-filled' : ''}`}>
      {/* Hidden canvas for frame capture */}
      <canvas ref={canvasRef} style={{ display: 'none' }} aria-hidden="true" />
      {/* Hidden file input */}
      <input
        ref={inputRef}
        id={id}
        type="file"
        accept="image/jpeg,image/png"
        className="up-hidden-input"
        onChange={onFileInput}
      />

      {/* ── PANEL HEADER ── */}
      <div className="up-header">
        <div className="up-icon-badge sc-icon">
          {isCameraOpen ? (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M23 7l-7 5 7 5V7z" />
              <rect x="1" y="5" width="15" height="14" rx="2" ry="2" />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 0 2-2l2-3h10l2 3a2 2 0 0 0 2 2v11z" />
              <circle cx="12" cy="13" r="4" />
            </svg>
          )}
        </div>
        <div className="up-title-group">
          <h3 className="up-title">{title}</h3>
          <span className="up-subtitle">
            {isCameraOpen
              ? 'Capture a current applicant selfie for biometric comparison.'
              : hasFile && file?.name === 'selfie-capture.jpg'
                ? 'Live capture ready for verification.'
                : subtitle}
          </span>
        </div>

        {/* Header right: LIVE badge OR file actions */}
        {isCameraOpen && (
          <div className="sc-live-badge">
            <span className="sc-live-dot" />
            LIVE
          </div>
        )}
        {hasFile && !isCameraOpen && (
          <div className="up-header-actions">
            <button
              type="button"
              className="up-icon-btn up-btn-replace"
              onClick={() => { onRemove(); openCamera() }}
              title="Retake with camera"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 0 2-2l2-3h10l2 3a2 2 0 0 0 2 2v11z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
            </button>
            <button
              type="button"
              className="up-icon-btn up-btn-replace"
              onClick={() => { onRemove(); setMode(MODE_UPLOAD) }}
              title="Replace with file upload"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
            </button>
            <button
              type="button"
              className="up-icon-btn up-btn-remove"
              onClick={handleRemove}
              title="Remove selfie"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        )}
      </div>

      {/* ── CAMERA ERROR ── */}
      {cameraError && !isCameraOpen && !hasFile && (
        <div className="up-error sc-error">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <span>{cameraError}</span>
        </div>
      )}

      {/* ════════════════════════════════════════
          STATE: File already selected → preview
      ════════════════════════════════════════ */}
      {hasFile && !isCameraOpen && !isPreviewMode && (
        <div className="up-preview">
          <div className="up-preview-img-wrap">
            <img src={previewUrl} alt="Selfie preview" className="up-preview-img" />
            <div className="up-preview-overlay">
              <span className={`up-preview-badge ${file?.name === 'selfie-capture.jpg' ? 'badge-capture' : ''}`}>
                {file?.name === 'selfie-capture.jpg' ? (
                  <>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 0 2-2l2-3h10l2 3a2 2 0 0 0 2 2v11z" />
                      <circle cx="12" cy="13" r="3" />
                    </svg>
                    LIVE CAPTURE
                  </>
                ) : (
                  <>
                    <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    UPLOADED
                  </>
                )}
              </span>
            </div>
          </div>
          <div className="up-file-meta">
            <span className="up-filename">{file.name}</span>
            <span className="up-filesize">{fmtSize(file.size)}</span>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════
          STATE: IDLE — Show action buttons
      ════════════════════════════════════════ */}
      {!hasFile && !isCameraOpen && !isPreviewMode && !isUploadMode && (
        <div className="sc-idle-zone">
          <div className="sc-action-grid">
            <button
              type="button"
              className="sc-primary-btn"
              onClick={openCamera}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 0 2-2l2-3h10l2 3a2 2 0 0 0 2 2v11z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
              <div className="sc-btn-text">
                <span className="sc-btn-label">Open Camera</span>
                <span className="sc-btn-sub">Capture live applicant selfie</span>
              </div>
            </button>

            <button
              type="button"
              className="sc-secondary-btn"
              onClick={openUpload}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              <div className="sc-btn-text">
                <span className="sc-btn-label">Upload Photo</span>
                <span className="sc-btn-sub">JPEG or PNG · up to 15 MB</span>
              </div>
            </button>
          </div>

          {cameraError && (
            <div className="up-error sc-error">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{cameraError}</span>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════
          STATE: UPLOAD MODE — drag-drop zone
      ════════════════════════════════════════ */}
      {isUploadMode && !hasFile && (
        <div className="sc-upload-mode">
          <div
            className={`up-dropzone ${isDragging ? 'up-dz-active' : ''}`}
            onDragOver={onDragOver}
            onDragLeave={onDragLeave}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && inputRef.current?.click()}
            aria-label="Upload selfie photo"
          >
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text-muted)' }}>
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="17 8 12 3 7 8" />
              <line x1="12" y1="3" x2="12" y2="15" />
            </svg>
            <p className="up-dz-primary"><strong>Click to upload</strong> or drag &amp; drop</p>
            <p className="up-dz-hint">JPEG, PNG &bull; Up to 15 MB</p>
          </div>
          <button type="button" className="sc-back-btn" onClick={() => setMode(MODE_IDLE)}>
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="15 18 9 12 15 6" />
            </svg>
            Back to camera option
          </button>
          {uploadError && (
            <div className="up-error sc-error">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>{uploadError}</span>
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════
          STATE: CAMERA — live viewfinder
      ════════════════════════════════════════ */}
      {isCameraOpen && (
        <div className="sc-viewfinder-wrap">
          <div className="sc-viewfinder">
            {/* Face oval guide */}
            <div className="sc-face-guide" aria-hidden="true">
              <div className="sc-face-oval" />
            </div>

            <video
              ref={videoRef}
              className="sc-video"
              autoPlay
              playsInline
              muted
              aria-label="Live camera feed"
            />

            {/* Corner brackets */}
            <div className="sc-bracket sc-br-tl" aria-hidden="true" />
            <div className="sc-bracket sc-br-tr" aria-hidden="true" />
            <div className="sc-bracket sc-br-bl" aria-hidden="true" />
            <div className="sc-bracket sc-br-br" aria-hidden="true" />
          </div>

          <p className="sc-viewfinder-hint">
            Position applicant face within the oval guide. Ensure even lighting.
          </p>

          <div className="sc-capture-controls">
            <button
              type="button"
              className="sc-cancel-btn"
              onClick={cancelCamera}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              Cancel
            </button>

            <button
              type="button"
              className="sc-capture-btn"
              onClick={captureFrame}
              aria-label="Capture photo"
            >
              <div className="sc-shutter-ring">
                <div className="sc-shutter-core" />
              </div>
            </button>

            <button
              type="button"
              className="sc-upload-alt-btn"
              onClick={() => { cancelCamera(); setTimeout(() => openUpload(), 50) }}
              title="Upload file instead"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17 8 12 3 7 8" />
              </svg>
              Upload
            </button>
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════
          STATE: PREVIEW — frozen captured frame
      ════════════════════════════════════════ */}
      {isPreviewMode && capturePreview && (
        <div className="sc-preview-zone">
          <div className="sc-preview-img-wrap">
            <img src={capturePreview} alt="Captured selfie preview" className="sc-preview-img" />
            <div className="sc-preview-chip">
              <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 0 2-2l2-3h10l2 3a2 2 0 0 0 2 2v11z" />
                <circle cx="12" cy="13" r="3" />
              </svg>
              LIVE APPLICANT CAPTURE
            </div>
          </div>

          <div className="sc-preview-actions">
            <button type="button" className="sc-retake-btn" onClick={retake}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="1 4 1 10 7 10" />
                <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
              </svg>
              Retake
            </button>
            <button type="button" className="sc-accept-btn" onClick={acceptCapture}>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Use This Photo
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
