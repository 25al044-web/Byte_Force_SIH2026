import React, { useEffect, useState } from 'react'
import { getAudits, getAudit } from '../services/api'
import { useTranslation } from '../i18n'

export function AuditTrailPage({ backendOnline }) {
  const { t } = useTranslation()
  const [audits, setAudits] = useState([])
  const [blockchainConfigured, setBlockchainConfigured] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [verifyingId, setVerifyingId] = useState(null)
  const [verificationResults, setVerificationResults] = useState({})

  const fetchAudits = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getAudits()
      setAudits(data.audits || [])
      setBlockchainConfigured(Boolean(data.blockchain_configured))
    } catch (err) {
      setError(err.message || 'Failed to load audit records.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAudits()
  }, [])

  const handleVerify = async (screeningId) => {
    setVerifyingId(screeningId)
    try {
      const res = await getAudit(screeningId)
      setVerificationResults((prev) => ({
        ...prev,
        [screeningId]: {
          status: res.integrity_status || 'UNAVAILABLE',
          storedHash: res.stored_hash,
          currentHash: res.current_hash,
          txHash: res.transaction_hash,
          blockNum: res.block_number,
        },
      }))
    } catch (err) {
      setVerificationResults((prev) => ({
        ...prev,
        [screeningId]: {
          status: 'UNAVAILABLE',
          error: err.message,
        },
      }))
    } finally {
      setVerifyingId(null)
    }
  }

  const getVerificationBadge = (screeningId, originalStatus) => {
    const verified = verificationResults[screeningId]
    const status = verified ? verified.status : (originalStatus === 'RECORDED' ? 'RECORDED' : 'UNVERIFIED')

    switch (status) {
      case 'VERIFIED':
        return <span className="badge-verified">VERIFIED</span>
      case 'TAMPERED':
        return <span className="badge-tampered">TAMPERED</span>
      case 'NOT_FOUND':
        return <span className="badge-notfound">NOT_FOUND</span>
      case 'RECORDED':
        return <span className="badge-recorded">RECORDED</span>
      case 'UNAVAILABLE':
        return <span className="badge-unavailable">UNAVAILABLE</span>
      default:
        return <span className="badge-pending">UNVERIFIED</span>
    }
  }

  return (
    <section className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <span className="stage-pill">IMMUTABLE LEDGER</span>
          <h2 className="stage-title">{t('auditTrail')}</h2>
          <p className="stage-sub">
            Cryptographically anchored, tamper-evident screening logs and SHA-256 integrity verification.
          </p>
        </div>
        <button
          type="button"
          className="btn-refresh"
          onClick={fetchAudits}
          disabled={loading || !backendOnline}
          title="Refresh audit records"
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
          <span>Refresh Records</span>
        </button>
      </div>

      {/* Blockchain Status Notice */}
      {!blockchainConfigured && (
        <div className="notice-banner notice-info" role="status">
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <div className="notice-content">
            <strong>Blockchain Audit Temporarily Unavailable</strong>
            <p>
              Local cryptographic hashes and report proofs remain verifiable in SQLite storage. The Ethereum/Hardhat testnet node is currently offline.
            </p>
          </div>
        </div>
      )}

      {error && (
        <div className="toast-offline" role="alert">
          <span>{error}</span>
        </div>
      )}

      {/* Audit Log Table / Empty State */}
      {loading && audits.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-spinner" />
          <p>Loading cryptographic audit ledger…</p>
        </div>
      ) : audits.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75">
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
          </div>
          <h3 className="empty-title">No Audit Records Found</h3>
          <p className="empty-desc">
            Run an identity screening to generate cryptographic hash manifests and immutable audit proofs.
          </p>
        </div>
      ) : (
        <div className="audit-table-card">
          <div className="audit-table-header">
            <span className="table-title">Screening Audit Manifests</span>
            <span className="table-count">{audits.length} Records</span>
          </div>

          <div className="table-responsive">
            <table className="audit-table">
              <thead>
                <tr>
                  <th>Screening ID</th>
                  <th>Timestamp</th>
                  <th>Blockchain Status</th>
                  <th>Report Hash</th>
                  <th>Document Hash</th>
                  <th>Transaction Hash</th>
                  <th>Block</th>
                  <th>Verification</th>
                  <th style={{ textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {audits.map((item) => {
                  const isVerifying = verifyingId === item.screening_id
                  return (
                    <tr key={item.screening_id}>
                      <td>
                        <span className="cell-id">{item.screening_id}</span>
                      </td>
                      <td>
                        <span className="cell-time">{item.timestamp}</span>
                      </td>
                      <td>
                        <span className={`status-pill status-${(item.blockchain_status || 'unavailable').toLowerCase()}`}>
                          {item.blockchain_status || 'UNAVAILABLE'}
                        </span>
                      </td>
                      <td>
                        <span className="cell-hash" title={item.report_hash}>
                          {item.report_hash ? `${item.report_hash.slice(0, 10)}…${item.report_hash.slice(-6)}` : '—'}
                        </span>
                      </td>
                      <td>
                        <span className="cell-hash" title={item.document_hash}>
                          {item.document_hash ? `${item.document_hash.slice(0, 10)}…${item.document_hash.slice(-6)}` : '—'}
                        </span>
                      </td>
                      <td>
                        <span className="cell-hash" title={item.transaction_hash || 'Not mined'}>
                          {item.transaction_hash ? `${item.transaction_hash.slice(0, 8)}…${item.transaction_hash.slice(-4)}` : '—'}
                        </span>
                      </td>
                      <td>
                        <span className="cell-block">
                          {item.block_number != null ? `#${item.block_number}` : '—'}
                        </span>
                      </td>
                      <td>
                        {getVerificationBadge(item.screening_id, item.blockchain_status)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <button
                          type="button"
                          className="btn-verify-audit"
                          onClick={() => handleVerify(item.screening_id)}
                          disabled={isVerifying || !backendOnline}
                        >
                          {isVerifying ? 'VERIFYING…' : 'VERIFY AUDIT RECORD'}
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  )
}
