import React from 'react'
import { StatusPill } from './StatusPill'

// Forensic sub-signal labels to surface if available
const FORENSIC_LABELS = [
  { key: 'compression_consistency', label: 'Compression Consistency' },
  { key: 'noise_anomaly', label: 'Noise Anomaly' },
  { key: 'edge_irregularity', label: 'Edge Irregularity' },
  { key: 'copy_move_signal', label: 'Copy-Move Signal' },
  { key: 'ela_score', label: 'ELA Analysis' },
]

export function TamperCard({ check }) {
  const status = check?.status || 'NOT_AVAILABLE'
  const risk = check?.risk
  const reason = check?.reason || 'No tamper analysis data available.'

  const hasRisk = typeof risk === 'number'

  const barColor = hasRisk
    ? risk <= 25
      ? '#10b981'
      : risk <= 59
        ? '#f59e0b'
        : '#e05252'
    : '#445066'

  // Surface any forensic sub-signals if present in check data
  const subSignals = FORENSIC_LABELS.filter((s) => check?.[s.key] !== undefined && check?.[s.key] !== null)

  return (
    <div className={`vcard vcard-status-${status.toLowerCase()}`}>
      <div className="vc-header">
        <div className="vc-title-group">
          <span className="vc-category">DIGITAL FORENSICS</span>
          <div className="vc-title-row">
            <div className="vc-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h4 className="vc-name">Tamper Analysis</h4>
          </div>
        </div>
        <StatusPill status={status} />
      </div>

      {hasRisk && (
        <>
          <div className="vc-mini-bar-wrap">
            <div className="vc-mini-bar">
              <div className="vc-mini-fill" style={{ width: `${risk}%`, backgroundColor: barColor }} />
            </div>
            <span className="vc-mini-label" style={{ color: barColor }}>
              Forensic Risk {risk}/100
            </span>
          </div>
        </>
      )}

      <p className="vc-reason">{reason}</p>

      {subSignals.length > 0 && (
        <div className="vc-forensic-chips">
          {subSignals.map((s) => (
            <span key={s.key} className="forensic-chip">{s.label}</span>
          ))}
        </div>
      )}
    </div>
  )
}
