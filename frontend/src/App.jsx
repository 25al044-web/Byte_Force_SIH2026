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
import { checkBackendHealth, screenIdentity } from './services/api'

function App() {
  const [documentFile, setDocumentFile] = useState(null)
  const [documentPreview, setDocumentPreview] = useState(null)
  const [selfieFile, setSelfieFile] = useState(null)
  const [selfiePreview, setSelfiePreview] = useState(null)

  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)
  const [backendOnline, setBackendOnline] = useState(false)

  // Verify backend connectivity on load
  useEffect(() => {
    let isMounted = true
    const probe = async () => {
      const ok = await checkBackendHealth()
      if (isMounted) setBackendOnline(ok)
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

  const canSubmit = Boolean(documentFile && selfieFile)

  return (
    <div className="screening-app">
      <div className="app-container">
        <Header backendOnline={backendOnline} />

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
              disabled={!canSubmit}
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
        </main>

        <footer className="app-footer">
          <div className="footer-content">
            <span>SIH 2026 • Problem Statement: SIH26188 • Identity Screening Pipeline</span>
            <span className="footer-tag">SECURE BORDER &amp; DOCUMENT SCREENING ARCHITECTURE</span>
          </div>
        </footer>
      </div>
    </div>
  )
}

export default App
