import React from 'react'
import { StatusPill } from './StatusPill'
import { FaceCompareCard } from './FaceCompareCard'
import { TamperCard } from './TamperCard'
import { AlertPanel } from './AlertPanel'
import { SectionHeader } from './SectionHeader'

function VerificationCard({ category, title, icon, status, metric, metricColor, reason }) {
  const hasMetric = metric !== null && metric !== undefined

  return (
    <div className={`vcard vcard-status-${status.toLowerCase()}`}>
      <div className="vc-header">
        <div className="vc-title-group">
          <span className="vc-category">{category}</span>
          <div className="vc-title-row">
            <div className="vc-icon">{icon}</div>
            <h4 className="vc-name">{title}</h4>
          </div>
        </div>
        <StatusPill status={status} />
      </div>

      {hasMetric && (
        <div className="vc-mini-bar-wrap">
          <div className="vc-mini-bar">
            <div
              className="vc-mini-fill"
              style={{
                width: typeof metric === 'number' ? `${Math.min(metric, 100)}%` : '100%',
                backgroundColor: metricColor || '#38bdf8',
              }}
            />
          </div>
          <span className="vc-mini-label" style={{ color: metricColor }}>
            {typeof metric === 'number' ? `${metric}` : metric}
          </span>
        </div>
      )}

      <p className="vc-reason">{reason || 'No diagnostic data recorded.'}</p>
    </div>
  )
}

export function VerificationGrid({ checks, documentPreview, selfiePreview }) {
  const blacklistMatch = checks?.blacklist?.match
  const dupMatch = checks?.duplicate_identity?.similar_identity

  // Build alert metadata
  const blacklistMeta = blacklistMatch
    ? [
        checks?.blacklist?.matched_name && { label: 'Name', value: checks.blacklist.matched_name },
        checks?.blacklist?.matched_doc && { label: 'Document', value: checks.blacklist.matched_doc },
      ].filter(Boolean)
    : []

  const dupMeta = dupMatch
    ? [
        typeof dupMatch === 'object' && dupMatch.document_number
          ? { label: 'Document No.', value: dupMatch.document_number }
          : { label: 'Match', value: String(dupMatch) },
        typeof dupMatch === 'object' && dupMatch.similarity
          ? { label: 'Similarity', value: `${dupMatch.similarity}%` }
          : null,
      ].filter(Boolean)
    : []

  const mrzScore = checks?.mrz?.score
  const expiryScore = checks?.expiry?.score

  const scoreColor = (s) => {
    if (typeof s !== 'number') return '#445066'
    if (s >= 75) return '#10b981'
    if (s >= 40) return '#f59e0b'
    return '#e05252'
  }

  return (
    <div className="verification-grid-section">
      <SectionHeader
        eyebrow="AUTOMATED INSPECTIONS"
        title="Multi-Module Verification Intelligence"
        icon={
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M9 11l3 3L22 4" />
            <path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11" />
          </svg>
        }
        right={<span className="vg-count-badge">6 ACTIVE CHECKS</span>}
      />

      {/* Critical alerts */}
      {blacklistMatch && (
        <AlertPanel
          type="danger"
          title="Watchlist Match Detected"
          detail={checks.blacklist.reason || 'Identity matched against restricted watchlist records.'}
          metadata={blacklistMeta}
        />
      )}
      {dupMatch && (
        <AlertPanel
          type="danger"
          title="Potential Duplicate Identity Detected"
          detail={checks.duplicate_identity.reason || 'Near-identical face embedding matched against a previously screened record under a different document number.'}
          metadata={dupMeta}
        />
      )}

      {/* Face compare — full width special card */}
      <FaceCompareCard
        check={checks?.face_match}
        documentPreview={documentPreview}
        selfiePreview={selfiePreview}
      />

      {/* 2x2 remaining cards */}
      <div className="vg-cards-grid">
        <TamperCard check={checks?.tamper} />

        <VerificationCard
          category="OPTICAL ICAO CHECKS"
          title="MRZ Validation"
          status={checks?.mrz?.status || 'NOT_AVAILABLE'}
          metric={typeof mrzScore === 'number' ? mrzScore : null}
          metricColor={scoreColor(mrzScore)}
          reason={checks?.mrz?.reason}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <rect x="3" y="4" width="18" height="16" rx="2" />
              <line x1="7" y1="13" x2="17" y2="13" />
              <line x1="7" y1="17" x2="17" y2="17" />
            </svg>
          }
        />

        <VerificationCard
          category="TEMPORAL VALIDITY"
          title="Expiry Validation"
          status={checks?.expiry?.status || 'NOT_AVAILABLE'}
          metric={typeof expiryScore === 'number' ? expiryScore : null}
          metricColor={scoreColor(expiryScore)}
          reason={checks?.expiry?.reason}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
          }
        />

        <VerificationCard
          category="WATCHLIST CROSS-REFERENCE"
          title="Blacklist Screening"
          status={checks?.blacklist?.status || 'NOT_AVAILABLE'}
          metric={null}
          reason={checks?.blacklist?.reason}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
            </svg>
          }
        />

        <VerificationCard
          category="FACIAL VECTOR STORE"
          title="Duplicate Identity Check"
          status={checks?.duplicate_identity?.status || 'NOT_AVAILABLE'}
          metric={null}
          reason={checks?.duplicate_identity?.reason}
          icon={
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
              <path d="M16 3.13a4 4 0 0 1 0 7.75" />
            </svg>
          }
        />
      </div>
    </div>
  )
}
