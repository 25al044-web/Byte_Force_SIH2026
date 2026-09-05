import React, { useEffect, useRef } from 'react'

/**
 * RiskGauge — SVG semicircular arc gauge
 * Animates needle from 0 to score on mount.
 */
export function RiskGauge({ score = 0, level = 'REVIEW' }) {
  const normalizedScore = Math.max(0, Math.min(100, Math.round(score)))
  const needleRef = useRef(null)
  const scoreRef = useRef(null)

  // SVG arc parameters
  const cx = 120
  const cy = 115
  const r = 90
  const startAngle = -180  // degrees — left end
  const totalArc = 180     // degrees — full semicircle

  const polarToXY = (angleDeg, radius) => {
    const rad = (angleDeg * Math.PI) / 180
    return {
      x: cx + radius * Math.cos(rad),
      y: cy + radius * Math.sin(rad),
    }
  }

  const describeArc = (startDeg, endDeg, outerR, innerR = 0) => {
    const s = polarToXY(startDeg, outerR)
    const e = polarToXY(endDeg, outerR)
    const largeArc = endDeg - startDeg > 180 ? 1 : 0
    if (innerR === 0) {
      return `M ${cx} ${cy} L ${s.x} ${s.y} A ${outerR} ${outerR} 0 ${largeArc} 1 ${e.x} ${e.y} Z`
    }
    const si = polarToXY(startDeg, innerR)
    const ei = polarToXY(endDeg, innerR)
    return `M ${s.x} ${s.y} A ${outerR} ${outerR} 0 ${largeArc} 1 ${e.x} ${e.y} L ${ei.x} ${ei.y} A ${innerR} ${innerR} 0 ${largeArc} 0 ${si.x} ${si.y} Z`
  }

  // Zone arcs: LOW 0-24, REVIEW 25-59, HIGH 60-100
  const scoreToAngle = (s) => startAngle + (s / 100) * totalArc

  const lowPath = describeArc(scoreToAngle(0), scoreToAngle(24), r, r - 22)
  const reviewPath = describeArc(scoreToAngle(24), scoreToAngle(59), r, r - 22)
  const highPath = describeArc(scoreToAngle(59), scoreToAngle(100), r, r - 22)

  const needleAngle = scoreToAngle(normalizedScore)
  const needleTip = polarToXY(needleAngle, r - 6)
  const needleBase1 = polarToXY(needleAngle - 90, 6)
  const needleBase2 = polarToXY(needleAngle + 90, 6)

  const levelColors = {
    LOW: '#10b981',
    REVIEW: '#f59e0b',
    HIGH: '#e05252',
  }
  const activeColor = levelColors[level.toUpperCase()] || '#f59e0b'

  const levelZoneLabels = {
    LOW: '0 – 24  LOW RISK',
    REVIEW: '25 – 59  REVIEW REQUIRED',
    HIGH: '60 – 100  HIGH RISK',
  }

  useEffect(() => {
    // Animate score counter
    if (!scoreRef.current) return
    let start = null
    const duration = 900
    const target = normalizedScore

    const step = (ts) => {
      if (!start) start = ts
      const progress = Math.min((ts - start) / duration, 1)
      const eased = 1 - Math.pow(1 - progress, 3)
      if (scoreRef.current) {
        scoreRef.current.textContent = Math.round(target * eased)
      }
      if (progress < 1) requestAnimationFrame(step)
    }
    requestAnimationFrame(step)
  }, [normalizedScore])

  return (
    <div className="risk-gauge-card">
      <div className="rg-header">
        <span className="rg-eyebrow">RISK ASSESSMENT</span>
        <span className="rg-zone-label" style={{ color: activeColor }}>
          {levelZoneLabels[level.toUpperCase()] || level}
        </span>
      </div>

      <div className="rg-svg-wrap">
        <svg viewBox="0 0 240 130" className="rg-svg" aria-label={`Risk gauge: ${normalizedScore} out of 100`}>
          {/* Background track */}
          <path d={describeArc(startAngle, startAngle + totalArc, r, r - 22)} fill="#1a2744" />

          {/* Zone segments */}
          <path d={lowPath} fill="#10b98133" />
          <path d={reviewPath} fill="#f59e0b22" />
          <path d={highPath} fill="#e0525222" />

          {/* Active zone highlight */}
          {level.toUpperCase() === 'LOW' && <path d={lowPath} fill="#10b98155" />}
          {level.toUpperCase() === 'REVIEW' && <path d={reviewPath} fill="#f59e0b44" />}
          {level.toUpperCase() === 'HIGH' && <path d={highPath} fill="#e0525244" />}

          {/* Needle */}
          <polygon
            points={`${needleTip.x},${needleTip.y} ${needleBase1.x},${needleBase1.y} ${needleBase2.x},${needleBase2.y}`}
            fill={activeColor}
            style={{ filter: `drop-shadow(0 0 4px ${activeColor}88)` }}
          />
          <circle cx={cx} cy={cy} r="7" fill="#1a2744" stroke={activeColor} strokeWidth="2" />

          {/* Zone tick marks */}
          {[0, 24, 59, 100].map((v) => {
            const a = scoreToAngle(v)
            const outer = polarToXY(a, r + 4)
            const inner = polarToXY(a, r - 26)
            return (
              <line
                key={v}
                x1={inner.x} y1={inner.y}
                x2={outer.x} y2={outer.y}
                stroke="#2d4070"
                strokeWidth="1.5"
              />
            )
          })}

          {/* Score readout in center */}
          <text
            ref={scoreRef}
            x={cx}
            y={cy + 30}
            textAnchor="middle"
            fontSize="32"
            fontFamily="'JetBrains Mono', monospace"
            fontWeight="600"
            fill="#e8edf7"
          >
            {normalizedScore}
          </text>
          <text x={cx} y={cy + 46} textAnchor="middle" fontSize="10" fill="#7d90b0" fontFamily="Inter, sans-serif">
            / 100
          </text>

          {/* Zone labels */}
          <text x={polarToXY(scoreToAngle(12), r + 18).x} y={polarToXY(scoreToAngle(12), r + 18).y}
            textAnchor="middle" fontSize="8" fill="#10b981aa" fontFamily="Inter, sans-serif">LOW</text>
          <text x={cx} y={22}
            textAnchor="middle" fontSize="8" fill="#f59e0baa" fontFamily="Inter, sans-serif">REVIEW</text>
          <text x={polarToXY(scoreToAngle(80), r + 18).x} y={polarToXY(scoreToAngle(80), r + 18).y}
            textAnchor="middle" fontSize="8" fill="#e05252aa" fontFamily="Inter, sans-serif">HIGH</text>
        </svg>
      </div>

      {/* Legend */}
      <div className="rg-legend">
        <div className="rg-legend-item"><span className="rg-swatch rg-sw-low" /><span>0–24 LOW</span></div>
        <div className="rg-legend-item"><span className="rg-swatch rg-sw-review" /><span>25–59 REVIEW</span></div>
        <div className="rg-legend-item"><span className="rg-swatch rg-sw-high" /><span>60–100 HIGH</span></div>
      </div>
    </div>
  )
}
