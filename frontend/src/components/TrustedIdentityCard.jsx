import React from 'react'
import { StatusPill } from './StatusPill'
import { useTranslation } from '../i18n'

export function TrustedIdentityCard({ check }) {
  const { t } = useTranslation()

  if (!check) return null

  const status = (check.status || 'NOT_FOUND').toUpperCase()
  const isMismatch = status === 'MISMATCH'
  const isMatch = status === 'MATCH'
  const isNotFound = status === 'NOT_FOUND' || status === 'NOT_APPLICABLE'

  const stored = check.stored_record
  const comparisons = check.comparisons || {}
  const triFace = check.tri_face_match
  const mismatches = check.mismatches || []

  return (
    <div className={`vcard vcard-status-${isMismatch ? 'fail' : isMatch ? 'pass' : 'not_available'} trusted-id-card`}>
      <div className="vc-header">
        <div className="vc-title-group">
          <span className="vc-category">DATABASE CROSS-VERIFICATION</span>
          <div className="vc-title-row">
            <div className="vc-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M22 11l-3 3-2-2" />
              </svg>
            </div>
            <h4 className="vc-name">Trusted Identity Registry Verification</h4>
          </div>
        </div>
        <StatusPill status={isMismatch ? 'FAIL' : isMatch ? 'PASS' : 'NOT_AVAILABLE'} />
      </div>

      {/* Critical Mismatch Banner */}
      {isMismatch && (
        <div className="tr-alert-banner tr-alert-danger">
          <div className="tr-alert-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div className="tr-alert-content">
            <h5 className="tr-alert-title">HIGH-RISK IDENTITY INCONSISTENCY</h5>
            <p className="tr-alert-text">{check.reason}</p>
            {mismatches.length > 0 && (
              <ul className="tr-mismatch-list">
                {mismatches.map((m, idx) => (
                  <li key={idx} className="tr-mismatch-item">
                    <span className="tr-mismatch-field">{m.field?.toUpperCase()}:</span>
                    <span className="tr-mismatch-detail">{m.reason}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* Verified Match Banner */}
      {isMatch && (
        <div className="tr-alert-banner tr-alert-success">
          <div className="tr-alert-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
              <polyline points="22 4 12 14.01 9 11.01" />
            </svg>
          </div>
          <div className="tr-alert-content">
            <h5 className="tr-alert-title">TRUSTED RECORD VERIFIED</h5>
            <p className="tr-alert-text">
              Presented document matches registered authoritative record ({check.registry_id}).
            </p>
          </div>
        </div>
      )}

      {/* Not Found Note */}
      {isNotFound && (
        <div className="tr-notfound-box">
          <p className="vc-reason">
            {check.reason || 'No pre-registered identity record found in the local demonstration registry. Standard document inspection rules apply.'}
          </p>
        </div>
      )}

      {/* Detailed Field Cross-Comparison Table */}
      {stored && (
        <div className="tr-details-wrap">
          <div className="tr-table-title">FIELD CROSS-VERIFICATION AUDIT</div>
          <div className="tr-table">
            <div className="tr-thead">
              <div className="tr-th">Identity Field</div>
              <div className="tr-th">Trusted Stored Record</div>
              <div className="tr-th">Presented Document</div>
              <div className="tr-th tr-th-status">Audit Status</div>
            </div>
            <div className="tr-tbody">
              {/* Full Name */}
              <div className={`tr-tr ${comparisons.full_name?.matches ? 'tr-match' : 'tr-mismatch'}`}>
                <div className="tr-td tr-field-label">Full Name</div>
                <div className="tr-td tr-val">{comparisons.full_name?.stored || stored.full_name || '—'}</div>
                <div className="tr-td tr-val">{comparisons.full_name?.presented || '—'}</div>
                <div className="tr-td tr-td-status">
                  {comparisons.full_name?.matches ? (
                    <span className="tr-pill-pass">MATCH</span>
                  ) : (
                    <span className="tr-pill-fail">CONFLICT</span>
                  )}
                </div>
              </div>

              {/* Document Number */}
              <div className="tr-tr tr-match">
                <div className="tr-td tr-field-label">Document Number</div>
                <div className="tr-td tr-val font-mono">{stored.document_number}</div>
                <div className="tr-td tr-val font-mono">{stored.document_number}</div>
                <div className="tr-td tr-td-status">
                  <span className="tr-pill-pass">MATCH</span>
                </div>
              </div>

              {/* Date of Birth */}
              <div className={`tr-tr ${comparisons.date_of_birth?.matches ? 'tr-match' : 'tr-mismatch'}`}>
                <div className="tr-td tr-field-label">Date of Birth</div>
                <div className="tr-td tr-val">{comparisons.date_of_birth?.stored || stored.date_of_birth || '—'}</div>
                <div className="tr-td tr-val">{comparisons.date_of_birth?.presented || '—'}</div>
                <div className="tr-td tr-td-status">
                  {comparisons.date_of_birth?.matches ? (
                    <span className="tr-pill-pass">MATCH</span>
                  ) : (
                    <span className="tr-pill-fail">CONFLICT</span>
                  )}
                </div>
              </div>

              {/* Document Type */}
              <div className={`tr-tr ${comparisons.document_type?.matches ? 'tr-match' : 'tr-mismatch'}`}>
                <div className="tr-td tr-field-label">Document Type</div>
                <div className="tr-td tr-val">{comparisons.document_type?.stored || stored.document_type || '—'}</div>
                <div className="tr-td tr-val">{comparisons.document_type?.presented || '—'}</div>
                <div className="tr-td tr-td-status">
                  {comparisons.document_type?.matches ? (
                    <span className="tr-pill-pass">MATCH</span>
                  ) : (
                    <span className="tr-pill-fail">CONFLICT</span>
                  )}
                </div>
              </div>

              {/* Nationality */}
              {stored.nationality && (
                <div className={`tr-tr ${comparisons.nationality?.matches ? 'tr-match' : 'tr-mismatch'}`}>
                  <div className="tr-td tr-field-label">Nationality</div>
                  <div className="tr-td tr-val">{comparisons.nationality?.stored || stored.nationality}</div>
                  <div className="tr-td tr-val">{comparisons.nationality?.presented || '—'}</div>
                  <div className="tr-td tr-td-status">
                    {comparisons.nationality?.matches ? (
                      <span className="tr-pill-pass">MATCH</span>
                    ) : (
                      <span className="tr-pill-fail">CONFLICT</span>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Tri-Face Biometric Analysis */}
      {triFace && (
        <div className="tr-tri-face-wrap">
          <div className="tr-table-title">TRI-FACE BIOMETRIC CROSS-ANALYSIS</div>
          <div className="tr-face-grid">
            <div className="tr-face-stat">
              <span className="tr-face-label">Trusted Photo vs Document</span>
              <span className="tr-face-val font-mono">
                {triFace.trusted_vs_document != null ? `${triFace.trusted_vs_document.toFixed(1)}%` : 'N/A'}
              </span>
              <span className={`tr-face-sub ${triFace.trusted_vs_document >= 60 ? 'text-emerald' : 'text-red'}`}>
                {triFace.trusted_vs_document >= 60 ? 'MATCH' : 'INCONSISTENT'}
              </span>
            </div>

            <div className="tr-face-stat">
              <span className="tr-face-label">Trusted Photo vs Selfie</span>
              <span className="tr-face-val font-mono">
                {triFace.trusted_vs_selfie != null ? `${triFace.trusted_vs_selfie.toFixed(1)}%` : 'N/A'}
              </span>
              <span className={`tr-face-sub ${triFace.trusted_vs_selfie >= 60 ? 'text-emerald' : 'text-red'}`}>
                {triFace.trusted_vs_selfie >= 60 ? 'MATCH' : 'INCONSISTENT'}
              </span>
            </div>

            <div className="tr-face-stat">
              <span className="tr-face-label">Document vs Selfie</span>
              <span className="tr-face-val font-mono">
                {triFace.document_vs_selfie != null ? `${triFace.document_vs_selfie.toFixed(1)}%` : 'N/A'}
              </span>
              <span className={`tr-face-sub ${triFace.document_vs_selfie >= 60 ? 'text-emerald' : 'text-red'}`}>
                {triFace.document_vs_selfie >= 60 ? 'MATCH' : 'INCONSISTENT'}
              </span>
            </div>
          </div>
        </div>
      )}

      <div className="tr-disclaimer">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="12" cy="12" r="10" />
          <line x1="12" y1="16" x2="12" y2="12" />
          <line x1="12" y1="8" x2="12.01" y2="8" />
        </svg>
        <span>
          Local demonstration trusted registry only. Cross-verification compares presented attributes against pre-registered trusted baseline.
        </span>
      </div>
    </div>
  )
}
