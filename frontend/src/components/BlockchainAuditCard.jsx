import React, { useState } from 'react'
import { getAudit } from '../services/api'

const shortHash = (value) => value ? `${value.slice(0, 10)}…${value.slice(-6)}` : '—'

export function BlockchainAuditCard({ audit }) {
  const [verification, setVerification] = useState(null)
  const [checking, setChecking] = useState(false)
  if (!audit) return null
  const verify = async () => {
    setChecking(true)
    try { setVerification(await getAudit(audit.screening_id)) } catch { setVerification({ integrity_status: 'UNAVAILABLE' }) } finally { setChecking(false) }
  }
  const verified = verification?.integrity_status === 'VERIFIED' || audit.verified
  return <section className="blockchain-audit-card" aria-label="Blockchain audit">
    <div><span className="audit-eyebrow">BLOCKCHAIN AUDIT</span><h3>Immutable screening record</h3></div>
    <span className={`audit-status status-${audit.status.toLowerCase()}`}>{verified ? 'VERIFIED' : audit.status}</span>
    <dl><div><dt>Screening ID</dt><dd>{audit.screening_id}</dd></div><div><dt>Report Hash</dt><dd title={audit.report_hash}>{shortHash(audit.report_hash)}</dd></div><div><dt>Transaction</dt><dd title={audit.transaction_hash}>{shortHash(audit.transaction_hash)}</dd></div><div><dt>Block</dt><dd>{audit.block_number ?? '—'}</dd></div></dl>
    <p>{verification?.integrity_status === 'TAMPERED' ? 'Audit integrity failure: the current report no longer matches the immutable record.' : audit.status === 'UNAVAILABLE' ? 'Temporarily unavailable. Screening was completed normally.' : 'AI detects suspicious identity evidence; blockchain ensures the screening record cannot be silently altered afterward.'}</p>
    <button type="button" onClick={verify} disabled={checking || audit.status === 'UNAVAILABLE'}>{checking ? 'Verifying…' : 'Verify Audit Record'}</button>
  </section>
}
