import React from 'react'

function StatusBadge({ status }) {
  const getBadgeClass = (st) => {
    switch (st) {
      case 'PASS':
        return 'badge-pass'
      case 'WARNING':
        return 'badge-warning'
      case 'FAIL':
        return 'badge-fail'
      case 'NOT_AVAILABLE':
      default:
        return 'badge-na'
    }
  }

  const getStatusIcon = (st) => {
    switch (st) {
      case 'PASS':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        )
      case 'WARNING':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        )
      case 'FAIL':
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <line x1="18" y1="6" x2="6" y2="18" />
            <line x1="6" y1="6" x2="18" y2="18" />
          </svg>
        )
      case 'NOT_AVAILABLE':
      default:
        return (
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10" />
            <line x1="8" y1="12" x2="16" y2="12" />
          </svg>
        )
    }
  }

  return (
    <span className={`status-pill ${getBadgeClass(status)}`}>
      {getStatusIcon(status)}
      <span>{status || 'NOT_AVAILABLE'}</span>
    </span>
  )
}

export function VerificationCheck({ checks }) {
  const checkItems = [
    {
      key: 'mrz',
      title: 'MRZ Verification',
      data: checks?.mrz,
      extraMetric:
        checks?.mrz?.score !== null && checks?.mrz?.score !== undefined
          ? `Score: ${checks.mrz.score}`
          : null,
    },
    {
      key: 'expiry',
      title: 'Expiry Verification',
      data: checks?.expiry,
      extraMetric:
        checks?.expiry?.score !== null && checks?.expiry?.score !== undefined
          ? `Score: ${checks.expiry.score}`
          : null,
    },
    {
      key: 'tamper',
      title: 'Document Tamper Screening',
      data: checks?.tamper,
      extraMetric:
        checks?.tamper?.risk !== null && checks?.tamper?.risk !== undefined
          ? `Risk Score: ${checks.tamper.risk} / 100`
          : null,
    },
    {
      key: 'face_match',
      title: 'Face Match',
      data: checks?.face_match,
      extraMetric:
        checks?.face_match?.similarity !== null && checks?.face_match?.similarity !== undefined
          ? `Similarity: ${checks.face_match.similarity}%`
          : null,
    },
    {
      key: 'duplicate_identity',
      title: 'Duplicate Identity',
      data: checks?.duplicate_identity,
      extraMetric: checks?.duplicate_identity?.similar_identity
        ? `Match: ${checks.duplicate_identity.similar_identity}`
        : null,
    },
    {
      key: 'blacklist',
      title: 'Blacklist Screening',
      data: checks?.blacklist,
      extraMetric: null,
    },
  ]

  return (
    <div className="verification-checks-container">
      <div className="section-header">
        <div className="header-label-group">
          <span className="section-eyebrow">AUTOMATED INSPECTIONS</span>
          <h2 className="section-title">Verification Checks</h2>
        </div>
      </div>

      <div className="checks-grid">
        {checkItems.map((item) => {
          const status = item.data?.status || 'NOT_AVAILABLE'
          const reason = item.data?.reason || 'No check details reported.'

          return (
            <div key={item.key} className={`check-card check-status-${status.toLowerCase()}`}>
              <div className="check-card-header">
                <span className="check-title">{item.title}</span>
                <StatusBadge status={status} />
              </div>

              <p className="check-reason">{reason}</p>

              {item.extraMetric && (
                <div className="check-metric-badge">
                  <span className="metric-text">{item.extraMetric}</span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
