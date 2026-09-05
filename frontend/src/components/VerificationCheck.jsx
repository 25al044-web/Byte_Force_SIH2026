import React from 'react'

function StatusBadge({ status }) {
  const getBadgeMeta = (st) => {
    switch (st) {
      case 'PASS':
        return {
          label: 'PASS',
          className: 'badge-pass',
          icon: (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <polyline points="20 6 9 17 4 12" />
            </svg>
          ),
        }
      case 'WARNING':
        return {
          label: 'WARNING',
          className: 'badge-warning',
          icon: (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ),
        }
      case 'FAIL':
        return {
          label: 'FAIL',
          className: 'badge-fail',
          icon: (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          ),
        }
      case 'NOT_AVAILABLE':
      default:
        return {
          label: 'NOT AVAILABLE',
          className: 'badge-na',
          icon: (
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="8" y1="12" x2="16" y2="12" />
            </svg>
          ),
        }
    }
  }

  const meta = getBadgeMeta(status)

  return (
    <span className={`status-badge ${meta.className}`}>
      {meta.icon}
      <span>{meta.label}</span>
    </span>
  )
}

export function VerificationCheck({ checks }) {
  const checkItems = [
    {
      key: 'face_match',
      title: 'Face Match',
      category: 'BIOMETRIC COMPARISON',
      data: checks?.face_match,
      metric:
        checks?.face_match?.similarity !== null && checks?.face_match?.similarity !== undefined
          ? `Similarity: ${checks.face_match.similarity}%`
          : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="8" r="5" />
          <path d="M20 21a8 8 0 1 0-16 0" />
          <polyline points="16 11 18 13 22 9" />
        </svg>
      ),
    },
    {
      key: 'tamper',
      title: 'Tamper Check',
      category: 'DIGITAL FORENSICS',
      data: checks?.tamper,
      metric:
        checks?.tamper?.risk !== null && checks?.tamper?.risk !== undefined
          ? `Forensic Risk: ${checks.tamper.risk} / 100`
          : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          <line x1="12" y1="8" x2="12" y2="12" />
          <line x1="12" y1="16" x2="12.01" y2="16" />
        </svg>
      ),
    },
    {
      key: 'mrz',
      title: 'MRZ Validation',
      category: 'OPTICAL ICAO CHECKS',
      data: checks?.mrz,
      metric:
        checks?.mrz?.score !== null && checks?.mrz?.score !== undefined
          ? `Checksum Score: ${checks.mrz.score} / 100`
          : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <line x1="7" y1="13" x2="17" y2="13" />
          <line x1="7" y1="17" x2="17" y2="17" />
        </svg>
      ),
    },
    {
      key: 'expiry',
      title: 'Expiry Validation',
      category: 'TEMPORAL VALIDITY',
      data: checks?.expiry,
      metric:
        checks?.expiry?.score !== null && checks?.expiry?.score !== undefined
          ? `Validity Score: ${checks.expiry.score} / 100`
          : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <polyline points="12 6 12 12 16 14" />
        </svg>
      ),
    },
    {
      key: 'blacklist',
      title: 'Blacklist Check',
      category: 'WATCHLIST CROSS-REFERENCE',
      data: checks?.blacklist,
      metric: checks?.blacklist?.match ? 'Watchlist Match Flagged' : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
        </svg>
      ),
    },
    {
      key: 'duplicate_identity',
      title: 'Duplicate Identity Check',
      category: 'FACIAL VECTOR STORE',
      data: checks?.duplicate_identity,
      metric: checks?.duplicate_identity?.similar_identity
        ? typeof checks.duplicate_identity.similar_identity === 'object'
          ? `Match: ${checks.duplicate_identity.similar_identity.document_number || 'Historical Record'}`
          : `Match: ${checks.duplicate_identity.similar_identity}`
        : null,
      icon: (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
          <circle cx="9" cy="7" r="4" />
          <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
          <path d="M16 3.13a4 4 0 0 1 0 7.75" />
        </svg>
      ),
    },
  ]

  return (
    <div className="verification-section">
      <div className="card-header-bar">
        <div className="header-title-box">
          <div className="section-icon-badge">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 11l3 3L22 4" />
              <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
            </svg>
          </div>
          <div>
            <span className="card-eyebrow">AUTOMATED INSPECTIONS</span>
            <h3 className="card-main-title">Multi-Module Verification Checks</h3>
          </div>
        </div>
        <span className="verification-count-pill">6 ACTIVE CHECKS</span>
      </div>

      <div className="checks-grid">
        {checkItems.map((item) => {
          const status = item.data?.status || 'NOT_AVAILABLE'
          const reason = item.data?.reason || 'No specific diagnostic details recorded.'

          return (
            <div key={item.key} className={`check-card card-status-${status.toLowerCase()}`}>
              <div className="check-card-header">
                <div className="check-title-group">
                  <span className="check-category">{item.category}</span>
                  <div className="check-title-row">
                    <div className="check-icon">{item.icon}</div>
                    <h4 className="check-name">{item.title}</h4>
                  </div>
                </div>
                <StatusBadge status={status} />
              </div>

              <p className="check-explanation">{reason}</p>

              {item.metric && (
                <div className="check-metric-tag">
                  <span className="metric-dot" />
                  <span className="metric-text">{item.metric}</span>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
