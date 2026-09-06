import React, { useEffect, useState } from 'react'
import { getSystemStatus } from '../services/api'
import { useTranslation } from '../i18n'

export function SystemStatusPage({ backendOnline }) {
  const { t } = useTranslation()
  const [statusData, setStatusData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [lastChecked, setLastChecked] = useState(null)
  const [error, setError] = useState(null)

  const fetchStatus = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getSystemStatus()
      setStatusData(data)
      setLastChecked(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err.message || 'Unable to fetch system status.')
      setStatusData({
        backend: backendOnline ? 'ONLINE' : 'OFFLINE',
        database: 'ERROR',
        ai_extraction: 'UNAVAILABLE',
        face_verification: 'UNAVAILABLE',
        blockchain: 'UNAVAILABLE',
        frontend: 'RUNNING',
      })
      setLastChecked(new Date().toLocaleTimeString())
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchStatus()
    const iv = setInterval(fetchStatus, 15000)
    return () => clearInterval(iv)
  }, [])

  const services = [
    {
      id: 'backend',
      title: 'Backend API Service',
      category: 'Core Infrastructure',
      status: statusData?.backend || (backendOnline ? 'ONLINE' : 'OFFLINE'),
      activeText: 'Online',
      inactiveText: 'Offline',
      detail: 'FastAPI Python 3.14 · Asynchronous Non-blocking HTTP Server',
      endpoint: 'http://127.0.0.1:8000/api',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="2" y="2" width="20" height="8" rx="2" ry="2" />
          <rect x="2" y="14" width="20" height="8" rx="2" ry="2" />
          <line x1="6" y1="6" x2="6.01" y2="6" />
          <line x1="6" y1="18" x2="6.01" y2="18" />
        </svg>
      ),
    },
    {
      id: 'database',
      title: 'Database Storage',
      category: 'Data Persistence',
      status: statusData?.database || 'CONNECTED',
      activeText: 'Connected',
      inactiveText: 'Error',
      detail: 'SQLite 3 (WAL mode) · Local Zero-Cloud Blacklist & Case Vault',
      endpoint: 'screening.db (Local filesystem)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <ellipse cx="12" cy="5" rx="9" ry="3" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
        </svg>
      ),
    },
    {
      id: 'ai_extraction',
      title: 'AI Document Extraction',
      category: 'OCR & Parsing Engine',
      status: statusData?.ai_extraction || 'AVAILABLE',
      activeText: 'Available',
      inactiveText: 'Unavailable',
      detail: 'Google Gemini Multimodal Vision API · Structured Document JSON Extraction',
      endpoint: 'gemini-2.5-flash / gemini-2.0-flash',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2zm1 15h-2v-2h2zm0-4h-2V7h2z" />
        </svg>
      ),
    },
    {
      id: 'face_verification',
      title: 'Face Verification',
      category: 'Biometric AI Engine',
      status: statusData?.face_verification || 'AVAILABLE',
      activeText: 'Available',
      inactiveText: 'Unavailable',
      detail: 'InsightFace (RetinaFace Detection + ArcFace 512-D ONNX Embeddings)',
      endpoint: 'Local CPU Execution Provider',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <path d="M8 14s1.5 2 4 2 4-2 4-2" />
          <line x1="9" y1="9" x2="9.01" y2="9" />
          <line x1="15" y1="9" x2="15.01" y2="9" />
        </svg>
      ),
    },
    {
      id: 'blockchain',
      title: 'Blockchain Audit',
      category: 'Immutable Ledger',
      status: statusData?.blockchain || 'UNAVAILABLE',
      activeText: 'Connected',
      inactiveText: 'Unavailable',
      detail: 'Ethereum / Hardhat Node · Smart Contract Tamper Proofing (Port 8545)',
      endpoint: 'Local RPC Provider (Optional)',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
        </svg>
      ),
    },
    {
      id: 'frontend',
      title: 'Frontend Dashboard',
      category: 'User Interface',
      status: 'RUNNING',
      activeText: 'Running',
      inactiveText: 'Stopped',
      detail: 'Vite 5 · React 18 SPA · Modern Border Security Command Center',
      endpoint: 'http://localhost:5173',
      icon: (
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
          <line x1="8" y1="21" x2="16" y2="21" />
          <line x1="12" y1="17" x2="12" y2="21" />
        </svg>
      ),
    },
  ]

  const isHealthy = (status) => ['ONLINE', 'CONNECTED', 'AVAILABLE', 'RUNNING'].includes(status)

  return (
    <section className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <span className="stage-pill">INFRASTRUCTURE HEALTH</span>
          <h2 className="stage-title">{t('systemStatus')}</h2>
          <p className="stage-sub">
            Real-time status monitoring for screening microservices, biometric models, databases, and cryptographic nodes.
          </p>
        </div>
        <button
          type="button"
          className="btn-refresh"
          onClick={fetchStatus}
          disabled={loading}
          title="Refresh service health"
        >
          <svg
            className={loading ? 'spin-icon' : ''}
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.25"
          >
            <polyline points="23 4 23 10 17 10" />
            <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
          </svg>
          <span>Refresh Status</span>
        </button>
      </div>

      {lastChecked && (
        <div className="status-banner-info">
          <span className="status-ping-dot" />
          <span>Last automated health probe: <strong>{lastChecked}</strong> (Polled every 15 seconds)</span>
        </div>
      )}

      {error && (
        <div className="toast-offline" role="alert">
          <span>{error}</span>
        </div>
      )}

      {/* Grid of services */}
      <div className="status-grid">
        {services.map((s) => {
          const healthy = isHealthy(s.status)
          return (
            <div key={s.id} className={`status-card ${healthy ? 'status-card-healthy' : 'status-card-warning'}`}>
              <div className="status-card-header">
                <div className="status-card-icon">{s.icon}</div>
                <span className={`status-badge ${healthy ? 'badge-online' : 'badge-offline'}`}>
                  <span className="badge-dot" />
                  {healthy ? s.activeText : s.inactiveText}
                </span>
              </div>

              <div className="status-card-body">
                <span className="status-card-category">{s.category}</span>
                <h3 className="status-card-title">{s.title}</h3>
                <p className="status-card-detail">{s.detail}</p>
              </div>

              <div className="status-card-footer">
                <span className="status-card-endpoint-label">Target / Host:</span>
                <code className="status-card-endpoint">{s.endpoint}</code>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
