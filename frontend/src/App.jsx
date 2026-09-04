import React, { useEffect, useState } from 'react'
import { Header } from './components/Header'
import { UploadCard } from './components/UploadCard'
import { ScreeningButton } from './components/ScreeningButton'
import { LoadingState } from './components/LoadingState'
import { IdentityDetails } from './components/IdentityDetails'
import { VerificationCheck } from './components/VerificationCheck'
import { RiskMeter } from './components/RiskMeter'
import { ExplanationPanel } from './components/ExplanationPanel'
import { ErrorMessage } from './components/ErrorMessage'
import { checkBackendHealth, getDemoStatus, resetDemoData, screenIdentity } from './services/api'

const ACTIVE_MODULES = [
  { name: 'Document Extraction', tech: 'Gemini 2.5 Flash' },
  { name: 'MRZ Validation', tech: 'ICAO Doc 9303 TD3' },
  { name: 'Expiry Validation', tech: 'Temporal Rule Engine' },
  { name: 'Face Verification', tech: 'InsightFace ArcFace' },
  { name: 'Duplicate Identity Detection', tech: 'Cosine Vector Store' },
  { name: 'Blacklist Screening', tech: 'SQLite Exact/Fuzzy' },
  { name: 'Tamper Screening', tech: 'OpenCV Forensic ELA' },
  { name: 'Explainable Risk Scoring', tech: 'Explainable Rules Engine' },
]

function App() {
  const [documentFile, setDocumentFile] = useState(null)
  const [documentPreview, setDocumentPreview] = useState(null)
  const [selfieFile, setSelfieFile] = useState(null)
  const [selfiePreview, setSelfiePreview] = useState(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [backendOnline, setBackendOnline] = useState(false)
  const [demoMode, setDemoMode] = useState(true)
  const [resettingDemo, setResettingDemo] = useState(false)
  const [resetSuccessNotice, setResetSuccessNotice] = useState(null)

  // Verify backend connectivity and demo status on load & periodic polling
  useEffect(() => {
    let isMounted = true
    const probe = async () => {
      const ok = await checkBackendHealth()
      if (isMounted) {
        setBackendOnline(ok)
        if (ok) {
          const isDemo = await getDemoStatus()
          if (isMounted) setDemoMode(isDemo)
        }
      }
    }
    probe()
    const interval = setInterval(probe, 8000)
    return () => {
      isMounted = false
      clearInterval(interval)
    }
  }, [])

  const handleDocumentSelect = (file) => {
    if (documentPreview) URL.revokeObjectURL(documentPreview)
    setDocumentFile(file)
    setDocumentPreview(URL.createObjectURL(file))
    setError(null)
  }

  const handleDocumentRemove = () => {
    if (documentPreview) URL.revokeObjectURL(documentPreview)
    setDocumentFile(null)
    setDocumentPreview(null)
  }

  const handleSelfieSelect = (file) => {
    if (selfiePreview) URL.revokeObjectURL(selfiePreview)
    setSelfieFile(file)
    setSelfiePreview(URL.createObjectURL(file))
    setError(null)
  }

  const handleSelfieRemove = () => {
    if (selfiePreview) URL.revokeObjectURL(selfiePreview)
    setSelfieFile(null)
    setSelfiePreview(null)
  }

  const handleRunScreening = async () => {
    if (!documentFile || !selfieFile) {
      setError('Please upload both the travel/identity document and the live selfie.')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const data = await screenIdentity(documentFile, selfieFile)
      setResult(data)
    } catch (err) {
      setError(err.message || 'An unexpected error occurred during screening.')
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    handleDocumentRemove()
    handleSelfieRemove()
    setResult(null)
    setError(null)
  }

  const handleResetDemoData = async () => {
    setResettingDemo(true)
    setError(null)
    try {
      const res = await resetDemoData()
      setResetSuccessNotice(res.message || 'Demo scan history cleared successfully.')
      setTimeout(() => setResetSuccessNotice(null), 4000)
    } catch (err) {
      setError(err.message || 'Failed to reset demo data.')
    } finally {
      setResettingDemo(false)
    }
  }

  const canSubmit = Boolean(documentFile && selfieFile)

  return (
    <div className="screening-app">
      <div className="app-container">
        <Header
          backendOnline={backendOnline}
          demoMode={demoMode}
          onResetDemo={handleResetDemoData}
          resettingDemo={resettingDemo}
        />

        {/* NOTIFICATIONS & ALERTS */}
        {resetSuccessNotice && (
          <div className="demo-notice-banner">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polyline points="20 6 9 17 4 12" />
            </svg>
            <span>{resetSuccessNotice}</span>
          </div>
        )}

        {!backendOnline && (
          <div className="backend-offline-banner">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            <div className="offline-text">
              <strong>Backend Service Disconnected.</strong>
              <span> FastAPI screening server is not reachable on http://127.0.0.1:8000. Launch via START_APP.bat or run uvicorn.</span>
            </div>
          </div>
        )}

        <main className="main-content">
          {/* UPLOAD STAGE */}
          <section className="upload-section">
            <div className="section-intro">
              <span className="section-step-indicator">STAGE 1: BIOMETRIC &amp; DOCUMENT INGESTION</span>
              <p className="section-instruction">
                Submit identity document and live selfie photographs in JPEG or PNG format for automated screening.
              </p>
            </div>

            <div className="upload-grid">
              <UploadCard
                id="document-upload"
                title="Travel / Identity Document"
                subtitle="Accepts JPEG or PNG passport or national ID scan"
                file={documentFile}
                previewUrl={documentPreview}
                onFileSelect={handleDocumentSelect}
                onRemove={handleDocumentRemove}
                iconType="document"
              />

              <UploadCard
                id="selfie-upload"
                title="Live / Selfie Photograph"
                subtitle="Accepts JPEG or PNG frontal portrait of applicant"
                file={selfieFile}
                previewUrl={selfiePreview}
                onFileSelect={handleSelfieSelect}
                onRemove={handleSelfieRemove}
                iconType="selfie"
              />
            </div>

            <ScreeningButton
              disabled={!canSubmit || !backendOnline}
              loading={loading}
              onClick={handleRunScreening}
            />
          </section>

          {/* ERROR DISPLAY */}
          {error && (
            <ErrorMessage
              message={error}
              onDismiss={() => setError(null)}
            />
          )}

          {/* LOADING STATE */}
          {loading && <LoadingState />}

          {/* RESULTS DASHBOARD */}
          {result && !loading && (
            <section className="results-section">
              <div className="results-header-banner">
                <div className="results-title-group">
                  <span className="section-step-indicator">STAGE 2: SCREENING RESULTS &amp; RISK TRIAGE</span>
                  <h2 className="results-main-title">Border Inspection Report</h2>
                </div>
                <button
                  type="button"
                  className="reset-btn"
                  onClick={handleReset}
                >
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                  <span>New Screening</span>
                </button>
              </div>

              {/* High visibility Risk Meter */}
              <RiskMeter risk={result.risk} />

              {/* Extracted Document Information */}
              <IdentityDetails
                screeningId={result.screening_id}
                document={result.document}
              />

              {/* Automated Verification Checks */}
              <VerificationCheck checks={result.checks} />

              {/* Explainability Panel */}
              <ExplanationPanel explanations={result.explanations} />
            </section>
          )}

          {/* ACTIVE REAL-TIME CAPABILITIES */}
          <section className="capabilities-section">
            <div className="section-header">
              <div className="header-label-group">
                <span className="section-eyebrow">PIPELINE ARCHITECTURE</span>
                <h3 className="section-subtitle-sm">Active Real-Time Screening Modules</h3>
              </div>
            </div>
            <div className="modules-grid">
              {ACTIVE_MODULES.map((mod, i) => (
                <div key={i} className="module-chip">
                  <span className="module-status-dot" />
                  <div className="module-info">
                    <span className="module-name">{mod.name}</span>
                    <span className="module-tech">{mod.tech}</span>
                  </div>
                </div>
              ))}
            </div>
            <p className="disclaimer-note">
              <strong>Automated Screening Aid Disclaimer:</strong> This system produces explainable risk triage indicators to assist border control officers. It is not a definitive certification of legal identity.
            </p>
          </section>
        </main>

        <footer className="app-footer">
          <div className="footer-content">
            <span>SIH 2026 • Problem Statement: SIH26188 • AI-Based Fake Identity &amp; Document Screening System</span>
            <span className="footer-tag">SECURE BORDER &amp; DOCUMENT SCREENING ARCHITECTURE</span>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
