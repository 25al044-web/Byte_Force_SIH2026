import React, { useEffect, useState } from 'react'
import { Sidebar } from './components/Sidebar'
import { TopBar } from './components/TopBar'
import { EmptyState } from './components/EmptyState'
import { UploadPanel } from './components/UploadPanel'
import { SelfieCapturePanel } from './components/SelfieCapturePanel'
import { ScreeningCTA } from './components/ScreeningCTA'
import { LoadingTimeline } from './components/LoadingTimeline'
import { ResultHero } from './components/ResultHero'
import { RiskGauge } from './components/RiskGauge'
import { IdentityPanel } from './components/IdentityPanel'
import { VerificationGrid } from './components/VerificationGrid'
import { ExplanationList } from './components/ExplanationList'
import { ErrorMessage } from './components/ErrorMessage'
import { BlacklistPanel } from './components/BlacklistPanel'
import { BlockchainAuditCard } from './components/BlockchainAuditCard'
import { checkBackendHealth, getDemoStatus, resetDemoData, screenIdentity } from './services/api'
import { useTranslation } from './i18n'

function App() {
  const { t } = useTranslation()
  // Upload state
  const [documentFile, setDocumentFile] = useState(null)
  const [documentPreview, setDocumentPreview] = useState(null)
  const [selfieFile, setSelfieFile] = useState(null)
  const [selfiePreview, setSelfiePreview] = useState(null)

  // Process state
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  // System state
  const [backendOnline, setBackendOnline] = useState(false)
  const [demoMode, setDemoMode] = useState(true)
  const [resettingDemo, setResettingDemo] = useState(false)
  const [resetNotice, setResetNotice] = useState(null)
  const [showBlacklist, setShowBlacklist] = useState(false)

  // Backend health polling
  useEffect(() => {
    let mounted = true
    const probe = async () => {
      const ok = await checkBackendHealth()
      if (!mounted) return
      setBackendOnline(ok)
      if (ok) {
        const demo = await getDemoStatus()
        if (mounted) setDemoMode(demo)
      }
    }
    probe()
    const iv = setInterval(probe, 8000)
    return () => { mounted = false; clearInterval(iv) }
  }, [])

  // File handlers
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

  // Screening
  const handleRunScreening = async () => {
    if (!documentFile || !selfieFile) {
      setError(`${t('uploadIdentityDocument')} · ${t('applicantSelfie')}`)
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

  // New screening
  const handleNewScreening = () => {
    handleDocumentRemove()
    handleSelfieRemove()
    setResult(null)
    setError(null)
  }

  // Reset demo
  const handleResetDemo = async () => {
    setResettingDemo(true)
    setError(null)
    try {
      const res = await resetDemoData()
      setResetNotice(res.message || t('clear'))
      setTimeout(() => setResetNotice(null), 4000)
    } catch (err) {
      setError(err.message || t('analysisFailed'))
    } finally {
      setResettingDemo(false)
    }
  }

  const canSubmit = Boolean(documentFile && selfieFile)
  const showEmpty = !loading && !result && !documentFile && !selfieFile
  const showWorkspace = !result || loading

  return (
    <div className="app-shell">
      <Sidebar backendOnline={backendOnline} demoMode={demoMode} onOpenBlacklist={() => setShowBlacklist(true)} />

      {showBlacklist && (
        <BlacklistPanel
          onClose={() => setShowBlacklist(false)}
          backendOnline={backendOnline}
        />
      )}

      <div className="app-main">
        <TopBar
          backendOnline={backendOnline}
          demoMode={demoMode}
          onResetDemo={handleResetDemo}
          resettingDemo={resettingDemo}
        />

        <div className="app-content">
          {/* Toast notifications */}
          {resetNotice && (
            <div className="toast-success" role="status">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polyline points="20 6 9 17 4 12" />
              </svg>
              <span>{resetNotice}</span>
            </div>
          )}

          {!backendOnline && (
            <div className="toast-offline" role="alert">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span>
                <strong>{t('serviceUnavailable')}.</strong> {t('pleaseTryAgain')}
              </span>
            </div>
          )}

          {/* ── EMPTY STATE ── */}
          {showEmpty && <EmptyState />}

          {/* ── WORKSPACE: Upload + Screening ── */}
          {!result && (
            <section className={`workspace-section ${showEmpty ? 'workspace-below-empty' : ''}`}>
              {/* Stage header */}
              {!showEmpty && (
                <div className="stage-header">
                  <span className="stage-pill">{t('startAnalysis')}</span>
                  <h2 className="stage-title">{t('identityScreening')}</h2>
                  <p className="stage-sub">{t('uploadIdentityDocument')} · {t('applicantSelfie')}</p>
                </div>
              )}

              <div className="upload-grid">
                <UploadPanel
                  id="doc-upload"
                  title={t('identityDocument')}
                  subtitle={t('documentSubtitle')}
                  file={documentFile}
                  previewUrl={documentPreview}
                  onFileSelect={handleDocumentSelect}
                  onRemove={handleDocumentRemove}
                  iconType="document"
                />
                <SelfieCapturePanel
                  id="selfie-upload"
                  title={t('applicantSelfie')}
                  subtitle={t('selfieSubtitle')}
                  file={selfieFile}
                  previewUrl={selfiePreview}
                  onFileSelect={handleSelfieSelect}
                  onRemove={handleSelfieRemove}
                />
              </div>

              <ErrorMessage message={error} onDismiss={() => setError(null)} />

              <ScreeningCTA
                disabled={!canSubmit || !backendOnline}
                loading={loading}
                onClick={handleRunScreening}
              />

              {loading && <LoadingTimeline />}
            </section>
          )}

          {/* ── RESULTS ── */}
          {result && !loading && (
            <section className="results-section">
              {/* Results header */}
              <div className="results-header">
                <div className="results-header-left">
                  <span className="stage-pill">{t('report')}</span>
                  <h2 className="stage-title">{t('verificationResult')}</h2>
                </div>
                <button
                  type="button"
                  className="btn-new-screening"
                  onClick={handleNewScreening}
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                  {t('newScreening')}
                </button>
              </div>

              <ErrorMessage message={error} onDismiss={() => setError(null)} />

              {/* Hero + Gauge two-col */}
              <div className="results-top-grid">
                <ResultHero
                  risk={result.risk}
                  screeningId={result.screening_id}
                />
                <RiskGauge
                  score={result.risk?.score}
                  level={result.risk?.level}
                />
              </div>

              {/* Identity information */}
              <IdentityPanel
                screeningId={result.screening_id}
                document={result.document}
                mrzLine1={result.document?.mrz_line_1}
                mrzLine2={result.document?.mrz_line_2}
              />

              {/* Verification intelligence */}
              <VerificationGrid
                checks={result.checks}
                documentPreview={documentPreview}
                selfiePreview={selfiePreview}
              />

              {/* Explainability */}
              <ExplanationList explanations={result.explanations} />
              <BlockchainAuditCard audit={result.blockchain_audit} />
            </section>
          )}
        </div>
      </div>
    </div>
  )
}

export default App
