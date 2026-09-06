"""Appends Document Integrity & Heatmap styles to frontend/src/index.css."""

import os
from pathlib import Path

CSS_SNIPPET = """
/* ==========================================================================
   DOCUMENT INTEGRITY & DIGITAL FORENSICS CARD (TamperCard)
   ========================================================================== */
.tamper-integrity-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  transition: box-shadow 0.2s ease;
  position: relative;
  overflow: hidden;
}

.tamper-integrity-card:hover {
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.tamper-integrity-card.vcard-status-pass {
  border-color: rgba(16, 185, 129, 0.2);
}

.tamper-integrity-card.vcard-status-warning {
  border-color: rgba(245, 158, 11, 0.3);
  background: linear-gradient(180deg, rgba(245, 158, 11, 0.02) 0%, var(--bg-surface) 100%);
}

.tamper-integrity-card.vcard-status-fail {
  border-color: rgba(224, 82, 82, 0.35);
  background: linear-gradient(180deg, rgba(224, 82, 82, 0.04) 0%, var(--bg-surface) 100%);
}

/* Header */
.tic-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
  flex-wrap: wrap;
}

.tic-title-group {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.tic-eyebrow-row {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  flex-wrap: wrap;
}

.tic-category {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.tic-quality-chip {
  font-size: 0.62rem;
  font-weight: 600;
  padding: 0.15rem 0.5rem;
  border-radius: 3px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.tic-quality-chip.quality-acceptable {
  background: rgba(16, 185, 129, 0.1);
  color: var(--pass);
  border: 1px solid rgba(16, 185, 129, 0.25);
}

.tic-quality-chip.quality-degraded {
  background: rgba(245, 158, 11, 0.1);
  color: var(--warn);
  border: 1px solid rgba(245, 158, 11, 0.25);
}

.tic-quality-chip.quality-poor {
  background: rgba(224, 82, 82, 0.1);
  color: var(--fail);
  border: 1px solid rgba(224, 82, 82, 0.25);
}

.tic-confidence-chip {
  font-size: 0.6rem;
  font-weight: 600;
  color: var(--text-muted);
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
}

.tic-title-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.tic-icon {
  color: var(--accent-cyan);
  display: flex;
  align-items: center;
}

.tic-name {
  font-size: 1.15rem;
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  letter-spacing: -0.01em;
}

.tic-recommendation-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 0.25rem 0.7rem;
  border-radius: 4px;
}

.rec-badge-clear {
  background: var(--pass-bg);
  color: var(--pass);
  border: 1px solid var(--pass-border);
}

.rec-badge-review {
  background: var(--warn-bg);
  color: var(--warn);
  border: 1px solid var(--warn-border);
}

.rec-badge-secondary {
  background: var(--fail-bg);
  color: var(--fail);
  border: 1px solid var(--fail-border);
  animation: pulse-danger-border 2s infinite;
}

@keyframes pulse-danger-border {
  0%, 100% { box-shadow: 0 0 0 0 rgba(224, 82, 82, 0.4); }
  50% { box-shadow: 0 0 0 4px rgba(224, 82, 82, 0.15); }
}

.tic-header-right {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.tic-risk-badge {
  display: flex;
  align-items: baseline;
  gap: 0.25rem;
  background: var(--bg-card);
  border: 1px solid;
  border-radius: 4px;
  padding: 0.25rem 0.65rem;
}

.tic-risk-num {
  font-family: var(--text-mono);
  font-size: 1.1rem;
  font-weight: 800;
  line-height: 1;
}

.tic-risk-denom {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  opacity: 0.85;
}

/* Progress Bar */
.tic-bar-wrap {
  width: 100%;
}

.tic-bar {
  width: 100%;
  height: 5px;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 3px;
  overflow: hidden;
}

.tic-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Body Grid (Heatmap + Layered Signals) */
.tic-body-grid {
  display: grid;
  grid-template-columns: 1.15fr 1fr;
  gap: 1.5rem;
  align-items: start;
}

@media (max-width: 900px) {
  .tic-body-grid {
    grid-template-columns: 1fr;
  }
}

.tic-section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.6rem;
}

.tic-section-label {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.tic-toggle-btn {
  background: none;
  border: none;
  font-size: 0.68rem;
  font-weight: 600;
  color: var(--accent-cyan);
  cursor: pointer;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  transition: background 0.15s;
}

.tic-toggle-btn:hover {
  background: rgba(56, 189, 248, 0.1);
}

/* Heatmap & Document Overlay */
.tic-preview-container {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}

.tic-preview-wrapper {
  position: relative;
  width: 100%;
  max-height: 380px;
  background: #000;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tic-doc-image {
  width: 100%;
  height: auto;
  max-height: 380px;
  object-fit: contain;
  display: block;
}

/* Bounding Box Overlays */
.tic-bbox-overlay {
  position: absolute;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  pointer-events: auto;
  z-index: 10;
}

.tic-bbox-overlay.region-sev-normal {
  border: 1.5px dashed rgba(16, 185, 129, 0.7);
  background: rgba(16, 185, 129, 0.08);
}

.tic-bbox-overlay.region-sev-normal:hover {
  border-style: solid;
  background: rgba(16, 185, 129, 0.2);
}

.tic-bbox-overlay.region-sev-warning {
  border: 2px solid #f59e0b;
  background: rgba(245, 158, 11, 0.18);
  box-shadow: 0 0 10px rgba(245, 158, 11, 0.35);
}

.tic-bbox-overlay.region-sev-suspicious {
  border: 2px solid #e05252;
  background: rgba(224, 82, 82, 0.28);
  box-shadow: 0 0 14px rgba(224, 82, 82, 0.6);
  animation: pulse-suspicious-box 2s infinite;
}

@keyframes pulse-suspicious-box {
  0%, 100% { box-shadow: 0 0 8px rgba(224, 82, 82, 0.5); }
  50% { box-shadow: 0 0 18px rgba(224, 82, 82, 0.9); }
}

.tic-bbox-overlay.region-selected {
  outline: 2px solid #38bdf8;
  outline-offset: 1px;
  z-index: 20;
}

.tic-bbox-label {
  position: absolute;
  top: -19px;
  left: -1px;
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  padding: 0.1rem 0.35rem;
  border-radius: 2px 2px 0 0;
  white-space: nowrap;
  pointer-events: none;
}

.region-sev-normal .tic-bbox-label {
  background: #10b981;
  color: #042f1a;
}

.region-sev-warning .tic-bbox-label {
  background: #f59e0b;
  color: #3b2203;
}

.region-sev-suspicious .tic-bbox-label {
  background: #e05252;
  color: #ffffff;
}

/* Inspection Tooltip Info */
.tic-selected-box-info {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
  min-height: 48px;
  display: flex;
  align-items: center;
}

.tic-rd-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
  font-style: italic;
}

.tic-region-detail-active {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  width: 100%;
}

.tic-rd-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tic-rd-name {
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--text-primary);
}

.tic-rd-sev {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.sev-text-normal { color: var(--pass); }
.sev-text-warning { color: var(--warn); }
.sev-text-suspicious { color: var(--fail); }

.tic-rd-reason {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.4;
  margin: 0;
}

.tic-no-preview {
  background: var(--bg-card);
  border: 1px dashed var(--border);
  border-radius: var(--radius-sm);
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.75rem;
}

/* Layered Integrity Signals List */
.tic-signals-col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tic-signals-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.tic-signal-item {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.85rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  transition: border-color 0.15s;
}

.tic-signal-item:hover {
  border-color: rgba(56, 189, 248, 0.3);
}

.tic-signal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tic-signal-name {
  font-size: 0.78rem;
  font-weight: 600;
  color: var(--text-primary);
}

.tic-signal-badge {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
  text-transform: uppercase;
}

.tic-signal-badge.sig-pass, .tic-signal-badge.sig-low {
  background: var(--pass-bg);
  color: var(--pass);
  border: 1px solid var(--pass-border);
}

.tic-signal-badge.sig-warning, .tic-signal-badge.sig-medium {
  background: var(--warn-bg);
  color: var(--warn);
  border: 1px solid var(--warn-border);
}

.tic-signal-badge.sig-suspicious, .tic-signal-badge.sig-fail, .tic-signal-badge.sig-high {
  background: var(--fail-bg);
  color: var(--fail);
  border: 1px solid var(--fail-border);
}

.tic-signal-desc {
  font-size: 0.7rem;
  color: var(--text-secondary);
  line-height: 1.4;
}

/* Sensitive Field Audit Grid */
.tic-fields-breakdown {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border-top: 1px solid var(--border);
  padding-top: 1rem;
}

.tic-fields-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.75rem;
}

@media (max-width: 900px) {
  .tic-fields-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

.tic-field-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.65rem 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.tic-field-card.field-status-warning {
  border-color: rgba(245, 158, 11, 0.3);
}

.tic-field-card.field-status-suspicious {
  border-color: rgba(224, 82, 82, 0.4);
  background: rgba(224, 82, 82, 0.04);
}

.tic-fc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tic-fc-label {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.tic-fc-pill {
  font-size: 0.58rem;
  font-weight: 700;
  padding: 0.1rem 0.35rem;
  border-radius: 2px;
}

.tic-fc-pill.pill-normal {
  color: var(--pass);
}

.tic-fc-pill.pill-warning {
  color: var(--warn);
  background: rgba(245, 158, 11, 0.12);
}

.tic-fc-pill.pill-suspicious {
  color: var(--fail);
  background: rgba(224, 82, 82, 0.15);
}

.tic-fc-value {
  font-size: 0.8rem;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tic-fc-reason {
  font-size: 0.65rem;
  color: var(--text-secondary);
  line-height: 1.3;
}

/* Reasons Footer */
.tic-reasons-footer {
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.875rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.tic-reasons-header {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  color: var(--accent-cyan);
}

.tic-reasons-title {
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-primary);
}

.tic-main-reason {
  font-size: 0.8rem;
  color: var(--text-secondary);
  line-height: 1.5;
  margin: 0;
}

.tic-reasons-bullets {
  margin: 0.25rem 0 0 1.25rem;
  padding: 0;
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.tic-reasons-bullets li {
  line-height: 1.4;
}
"""

def main():
    css_path = Path(__file__).resolve().parent.parent / "frontend" / "src" / "index.css"
    with open(css_path, "a", encoding="utf-8") as f:
        f.write("\n" + CSS_SNIPPET)
    print(f"Appended Document Integrity styles ({len(CSS_SNIPPET)} chars) to {css_path}")

if __name__ == "__main__":
    main()
