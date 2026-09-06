import React, { useState } from 'react'
import { StatusPill } from './StatusPill'

export function TamperCard({ check, documentPreview }) {
  const [selectedRegion, setSelectedRegion] = useState(null)
  const [showHeatmap, setShowHeatmap] = useState(true)

  const status = check?.status || 'NOT_AVAILABLE'
  const risk = check?.risk
  const reason = check?.reason || 'No tamper analysis data available.'
  const recommendation = check?.recommendation || (status === 'FAIL' ? 'SECONDARY_INSPECTION_RECOMMENDED' : status === 'WARNING' ? 'MANUAL_REVIEW_RECOMMENDED' : 'CLEAR')
  const confidence = check?.confidence || 'HIGH'
  const quality = check?.document_quality || {}
  const subChecks = check?.sub_checks || {}
  const fieldAnalysis = check?.field_analysis || []
  const highlightedRegions = check?.highlighted_regions || []
  const reasons = check?.reasons || []

  const hasRisk = typeof risk === 'number'

  const barColor = hasRisk
    ? risk <= 25
      ? '#10b981'
      : risk <= 59
        ? '#f59e0b'
        : '#e05252'
    : '#445066'

  const isQualityDegraded = quality?.status === 'DEGRADED' || quality?.status === 'POOR' || quality?.metrics?.is_heavy_blur || quality?.metrics?.is_heavy_compression

  const getIntegrityBadge = () => {
    if (isQualityDegraded && status !== 'FAIL') {
      return {
        label: 'INCONCLUSIVE (QUALITY DEGRADED)',
        cls: 'badge-inconclusive',
        color: '#f59e0b',
        border: 'rgba(245, 158, 11, 0.3)',
        bg: 'rgba(245, 158, 11, 0.1)',
      }
    }
    if (status === 'FAIL') {
      return {
        label: 'SUSPICIOUS (ANOMALY DETECTED)',
        cls: 'badge-suspicious',
        color: '#ef4444',
        border: 'rgba(239, 68, 68, 0.35)',
        bg: 'rgba(239, 68, 68, 0.12)',
      }
    }
    if (status === 'WARNING') {
      return {
        label: 'REVIEW RECOMMENDED',
        cls: 'badge-warning',
        color: '#f59e0b',
        border: 'rgba(245, 158, 11, 0.3)',
        bg: 'rgba(245, 158, 11, 0.1)',
      }
    }
    return {
      label: 'NO SIGNIFICANT ANOMALY DETECTED',
      cls: 'badge-clean',
      color: '#10b981',
      border: 'rgba(16, 185, 129, 0.3)',
      bg: 'rgba(16, 185, 129, 0.1)',
    }
  }

  const getQualityBadge = () => {
    const qStatus = (quality?.status || 'ACCEPTABLE').toUpperCase()
    if (qStatus === 'POOR') {
      return {
        label: `QUALITY: POOR (${quality.score || 40}%)`,
        cls: 'quality-poor',
        color: '#ef4444',
        border: 'rgba(239, 68, 68, 0.35)',
        bg: 'rgba(239, 68, 68, 0.12)',
      }
    }
    if (qStatus === 'DEGRADED') {
      return {
        label: `QUALITY: DEGRADED (${quality.score || 60}%)`,
        cls: 'quality-degraded',
        color: '#f59e0b',
        border: 'rgba(245, 158, 11, 0.3)',
        bg: 'rgba(245, 158, 11, 0.1)',
      }
    }
    return {
      label: `QUALITY: ACCEPTABLE (${quality?.score || 100}%)`,
      cls: 'quality-acceptable',
      color: '#10b981',
      border: 'rgba(16, 185, 129, 0.3)',
      bg: 'rgba(16, 185, 129, 0.1)',
    }
  }

  const integrityBadge = getIntegrityBadge()
  const qualityBadge = getQualityBadge()

  const getRecommendationBadge = () => {
    switch (recommendation) {
      case 'SECONDARY_INSPECTION_RECOMMENDED':
        return {
          label: 'SECONDARY INSPECTION RECOMMENDED',
          cls: 'rec-badge-secondary',
          icon: (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ),
        }
      case 'MANUAL_REVIEW_RECOMMENDED':
        return {
          label: 'MANUAL REVIEW RECOMMENDED',
          cls: 'rec-badge-review',
          icon: (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          ),
        }
      default:
        return {
          label: 'CLEAR / NO ANOMALY DETECTED',
          cls: 'rec-badge-clear',
          icon: (
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M20 6L9 17l-5-5" />
            </svg>
          ),
        }
    }
  }

  const recBadge = getRecommendationBadge()

  return (
    <div className={`tamper-integrity-card vcard-status-${status.toLowerCase()}`}>
      {/* Header Row */}
      <div className="tic-header">
        <div className="tic-title-group">
          <div className="tic-eyebrow-row">
            <span className="tic-category">LAYERED DIGITAL FORENSICS & DOCUMENT INTEGRITY</span>
            <span className="tic-confidence-chip">Confidence: {confidence}</span>
          </div>

          <div className="tic-title-row">
            <div className="tic-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <path d="M9 12l2 2 4-4" />
              </svg>
            </div>
            <h3 className="tic-name">Document Integrity Analysis</h3>
            <div className={`tic-recommendation-pill ${recBadge.cls}`}>
              {recBadge.icon}
              <span>{recBadge.label}</span>
            </div>
          </div>

          {/* Dual Badge Bar: Clear Quality vs Integrity Separation */}
          <div className="tic-dual-badge-bar">
            <div
              className={`tic-status-chip ${qualityBadge.cls}`}
              style={{ borderColor: qualityBadge.border, backgroundColor: qualityBadge.bg, color: qualityBadge.color }}
            >
              <span className="tic-chip-dot" style={{ backgroundColor: qualityBadge.color }} />
              <span>{qualityBadge.label}</span>
            </div>
            <div
              className={`tic-status-chip ${integrityBadge.cls}`}
              style={{ borderColor: integrityBadge.border, backgroundColor: integrityBadge.bg, color: integrityBadge.color }}
            >
              <span className="tic-chip-dot" style={{ backgroundColor: integrityBadge.color }} />
              <span>DOCUMENT INTEGRITY: {integrityBadge.label}</span>
            </div>
          </div>
        </div>

        <div className="tic-header-right">
          <StatusPill status={status} />
          {hasRisk && (
            <div className="tic-risk-badge" style={{ borderColor: barColor, color: barColor }}>
              <span className="tic-risk-num">{risk}</span>
              <span className="tic-risk-denom">/100 RISK</span>
            </div>
          )}
        </div>
      </div>

      {/* Mini Risk Progress Bar */}
      {hasRisk && (
        <div className="tic-bar-wrap">
          <div className="tic-bar">
            <div className="tic-bar-fill" style={{ width: `${risk}%`, backgroundColor: barColor }} />
          </div>
        </div>
      )}

      {/* Main Body: Forensic Heatmap + Layered Check Signals */}
      <div className="tic-body-grid">
        {/* Left: Document Heatmap & Region Overlay */}
        <div className="tic-heatmap-col">
          <div className="tic-section-title-row">
            <span className="tic-section-label">FORENSIC REGION VISUALIZATION</span>
            {documentPreview && (
              <button
                type="button"
                className="tic-toggle-btn"
                onClick={() => setShowHeatmap(!showHeatmap)}
              >
                {showHeatmap ? 'Hide Heatmap' : 'Show Heatmap'}
              </button>
            )}
          </div>

          {documentPreview ? (
            <div className="tic-preview-container">
              <div className="tic-preview-wrapper">
                <img src={documentPreview} alt="Document Forensic Analysis" className="tic-doc-image" />

                {/* Heatmap bounding box overlays */}
                {showHeatmap &&
                  highlightedRegions.map((region, idx) => {
                    const [ymin, xmin, ymax, xmax] = region.bbox || [0, 0, 0, 0]
                    const top = ymin / 10.0
                    const left = xmin / 10.0
                    const height = (ymax - ymin) / 10.0
                    const width = (xmax - xmin) / 10.0

                    const isSelected = selectedRegion?.field === region.field
                    const sevClass = `region-sev-${region.severity || 'normal'}`

                    return (
                      <div
                        key={idx}
                        className={`tic-bbox-overlay ${sevClass} ${isSelected ? 'region-selected' : ''}`}
                        style={{
                          top: `${top}%`,
                          left: `${left}%`,
                          height: `${height}%`,
                          width: `${width}%`,
                        }}
                        onClick={() => setSelectedRegion(region)}
                        title={`${region.label}: ${region.reason || region.severity}`}
                      >
                        <span className="tic-bbox-label">
                          {region.label}
                          {region.severity === 'suspicious' && ' ⚠'}
                        </span>
                      </div>
                    )
                  })}
              </div>

              {/* Interactive Region Inspection Details */}
              <div className="tic-selected-box-info">
                {selectedRegion ? (
                  <div className="tic-region-detail-active">
                    <div className="tic-rd-header">
                      <span className="tic-rd-name">{selectedRegion.label}</span>
                      <span className={`tic-rd-sev sev-text-${selectedRegion.severity}`}>
                        {selectedRegion.severity.toUpperCase()}
                      </span>
                    </div>
                    <p className="tic-rd-reason">{selectedRegion.reason}</p>
                  </div>
                ) : (
                  <span className="tic-rd-hint">
                    Click or tap any highlighted region on the document to inspect forensic indicators.
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="tic-no-preview">
              <span>Document preview unavailable for optical overlay</span>
            </div>
          )}
        </div>

        {/* Right: Layered Integrity Signals */}
        <div className="tic-signals-col">
          <span className="tic-section-label">MULTI-LAYER INTEGRITY SIGNALS</span>

          <div className="tic-signals-list">
            {/* 1. Text Region Integrity */}
            <div className="tic-signal-item">
              <div className="tic-signal-header">
                <span className="tic-signal-name">Text Region Integrity</span>
                <span className={`tic-signal-badge sig-${subChecks?.text_region_integrity?.status?.toLowerCase() || 'pass'}`}>
                  {subChecks?.text_region_integrity?.status || 'PASS'}
                </span>
              </div>
              <span className="tic-signal-desc">
                Localized ELA compression, background noise uniformity, and gradient boundaries across text fields.
              </span>
            </div>

            {/* 2. Typography Consistency */}
            <div className="tic-signal-item">
              <div className="tic-signal-header">
                <span className="tic-signal-name">Typography Consistency</span>
                <span className={`tic-signal-badge sig-${subChecks?.typography_consistency?.status?.toLowerCase() || 'pass'}`}>
                  {subChecks?.typography_consistency?.status || 'PASS'}
                </span>
              </div>
              <span className="tic-signal-desc">
                Character stroke thickness, kerning regularity, baseline alignment, and ink chromaticity vs baseline.
              </span>
            </div>

            {/* 3. Cross-Field Data Consistency */}
            <div className="tic-signal-item">
              <div className="tic-signal-header">
                <span className="tic-signal-name">Cross-Field Consistency</span>
                <span className={`tic-signal-badge sig-${subChecks?.cross_field_data?.status?.toLowerCase() || 'pass'}`}>
                  {subChecks?.cross_field_data?.has_mismatch ? 'DATA MISMATCH' : subChecks?.cross_field_data?.status || 'PASS'}
                </span>
              </div>
              <span className="tic-signal-desc">
                Cross-verification of Visible Name, DOB, and ID Number against MRZ Lines & 2D Barcode records.
              </span>
            </div>

            {/* 4. Local Image Forensics */}
            <div className="tic-signal-item">
              <div className="tic-signal-header">
                <span className="tic-signal-name">Local Image Forensics</span>
                <span className={`tic-signal-badge sig-${subChecks?.image_forensics?.status?.toLowerCase() || 'pass'}`}>
                  {subChecks?.image_forensics?.status || 'PASS'}
                </span>
              </div>
              <span className="tic-signal-desc">
                Wavelet residual analysis, 2D FFT spectral harmonics, and copy-move SIFT feature clustering.
              </span>
            </div>

            {/* 5. AI Manipulation Indicator */}
            <div className="tic-signal-item">
              <div className="tic-signal-header">
                <span className="tic-signal-name">AI Manipulation Indicator</span>
                <span className={`tic-signal-badge sig-${subChecks?.ai_manipulation?.indicator?.toLowerCase() || 'low'}`}>
                  {subChecks?.ai_manipulation?.indicator || 'LOW'}
                </span>
              </div>
              <span className="tic-signal-desc">
                Neural inpainting texture suppression, boundary blend seams, and editing software metadata signatures.
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Field-by-Field Breakdown Chips */}
      {fieldAnalysis.length > 0 && (
        <div className="tic-fields-breakdown">
          <span className="tic-section-label">SENSITIVE IDENTITY FIELD AUDIT</span>
          <div className="tic-fields-grid">
            {fieldAnalysis.map((field, idx) => {
              const statusCls = `field-status-${field.status || 'normal'}`
              return (
                <div key={idx} className={`tic-field-card ${statusCls}`}>
                  <div className="tic-fc-header">
                    <span className="tic-fc-label">{field.label}</span>
                    <span className={`tic-fc-pill pill-${field.status}`}>
                      {field.status?.toUpperCase()}
                    </span>
                  </div>
                  <span className="tic-fc-value">{field.value || 'Extracted'}</span>
                  <span className="tic-fc-reason">{field.reason}</span>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Explanations and Diagnostic Reasons */}
      <div className="tic-reasons-footer">
        <div className="tic-reasons-header">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
          <span className="tic-reasons-title">Forensic Diagnostic Summary:</span>
        </div>
        <p className="tic-main-reason">{reason}</p>

        {reasons.length > 1 && (
          <ul className="tic-reasons-bullets">
            {reasons.slice(0, 4).map((r, i) => (
              <li key={i}>{r}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}
