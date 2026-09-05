import React from 'react'

/**
 * SectionHeader — reusable eyebrow + title + optional right slot
 */
export function SectionHeader({ eyebrow, title, icon, right }) {
  return (
    <div className="section-header">
      <div className="section-header-left">
        {icon && (
          <div className="section-header-icon">
            {icon}
          </div>
        )}
        <div className="section-header-text">
          {eyebrow && <span className="section-eyebrow">{eyebrow}</span>}
          <h3 className="section-title">{title}</h3>
        </div>
      </div>
      {right && <div className="section-header-right">{right}</div>}
    </div>
  )
}
