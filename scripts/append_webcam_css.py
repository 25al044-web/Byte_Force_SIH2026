"""
Append SelfieCapturePanel (webcam) CSS to the existing index.css.
Run from project root: backend\.venv\Scripts\python.exe scripts\append_webcam_css.py
"""
import pathlib

WEBCAM_CSS = r"""
/* ==========================================================================
   SELFIE CAPTURE PANEL — Live webcam capture + upload fallback
   ========================================================================== */

/* Shared panel state */
.sc-panel { transition: border-color 0.2s; }
.sc-camera-open { border-color: rgba(56,189,248,0.3) !important; }

/* Slightly taller icon badge for camera icon */
.sc-icon svg { color: var(--accent-cyan); }

/* LIVE badge */
.sc-live-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--fail);
  background: rgba(224,82,82,0.08);
  border: 1px solid rgba(224,82,82,0.2);
  border-radius: 3px;
  padding: 0.18rem 0.45rem;
  flex-shrink: 0;
}
.sc-live-dot {
  width: 6px;
  height: 6px;
  background: var(--fail);
  border-radius: 50%;
  animation: pulse-live 1.1s ease-in-out infinite;
}
@keyframes pulse-live {
  0%, 100% { opacity: 1; transform: scale(1); }
  50%       { opacity: 0.5; transform: scale(0.75); }
}

/* ── IDLE ZONE ── */
.sc-idle-zone {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  padding: 0.25rem 0 0;
}
.sc-action-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.625rem;
}

/* Primary: Open Camera */
.sc-primary-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid rgba(56,189,248,0.25);
  background: rgba(56,189,248,0.05);
  color: var(--accent-cyan);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  width: 100%;
}
.sc-primary-btn:hover {
  border-color: rgba(56,189,248,0.45);
  background: rgba(56,189,248,0.09);
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(56,189,248,0.1);
}
.sc-primary-btn svg { flex-shrink: 0; }

/* Secondary: Upload */
.sc-secondary-btn {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  transition: all 0.15s;
  width: 100%;
}
.sc-secondary-btn:hover {
  border-color: rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.03);
  color: var(--text-primary);
}
.sc-secondary-btn svg { flex-shrink: 0; }

.sc-btn-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.sc-btn-label {
  font-size: 0.82rem;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}
.sc-btn-sub {
  font-size: 0.68rem;
  opacity: 0.65;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.sc-error {
  font-size: 0.75rem;
}

/* ── UPLOAD MODE ── */
.sc-upload-mode {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}
.sc-back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.7rem;
  color: var(--text-muted);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem 0;
  transition: color 0.15s;
}
.sc-back-btn:hover { color: var(--text-secondary); }

/* ── VIEWFINDER ── */
.sc-viewfinder-wrap {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  align-items: center;
}
.sc-viewfinder {
  position: relative;
  width: 100%;
  max-width: 340px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid rgba(56,189,248,0.25);
  background: #000;
  aspect-ratio: 4 / 3;
}
.sc-video {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transform: scaleX(-1); /* mirror for natural feel */
}

/* Face oval guide */
.sc-face-guide {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
  z-index: 1;
}
.sc-face-oval {
  width: 44%;
  aspect-ratio: 3 / 4;
  border: 1.5px dashed rgba(56,189,248,0.45);
  border-radius: 50%;
}

/* Corner brackets */
.sc-bracket {
  position: absolute;
  width: 18px;
  height: 18px;
  border-color: rgba(56,189,248,0.6);
  border-style: solid;
  z-index: 2;
}
.sc-br-tl { top: 8px;    left: 8px;    border-width: 2px 0 0 2px; border-radius: 3px 0 0 0; }
.sc-br-tr { top: 8px;    right: 8px;   border-width: 2px 2px 0 0; border-radius: 0 3px 0 0; }
.sc-br-bl { bottom: 8px; left: 8px;    border-width: 0 0 2px 2px; border-radius: 0 0 0 3px; }
.sc-br-br { bottom: 8px; right: 8px;   border-width: 0 2px 2px 0; border-radius: 0 0 3px 0; }

.sc-viewfinder-hint {
  font-size: 0.68rem;
  color: var(--text-muted);
  text-align: center;
  margin: 0;
  padding: 0 0.5rem;
}

/* Capture controls row */
.sc-capture-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1.25rem;
  padding: 0.25rem 0;
}
.sc-cancel-btn,
.sc-upload-alt-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.4rem 0.75rem;
  cursor: pointer;
  transition: all 0.15s;
  min-width: 72px;
  justify-content: center;
}
.sc-cancel-btn:hover  { color: var(--fail);        border-color: rgba(224,82,82,0.3); background: rgba(224,82,82,0.05); }
.sc-upload-alt-btn:hover { color: var(--text-primary); border-color: rgba(255,255,255,0.15); }

/* Shutter button */
.sc-capture-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: transform 0.1s;
}
.sc-capture-btn:hover  { transform: scale(1.07); }
.sc-capture-btn:active { transform: scale(0.94); }
.sc-shutter-ring {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  border: 3px solid rgba(255,255,255,0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255,255,255,0.06);
  box-shadow: 0 0 0 4px rgba(255,255,255,0.08), 0 2px 12px rgba(0,0,0,0.4);
}
.sc-shutter-core {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  transition: background 0.12s;
}
.sc-capture-btn:hover .sc-shutter-core { background: #e2e8f0; }

/* ── PREVIEW ZONE ── */
.sc-preview-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.sc-preview-img-wrap {
  position: relative;
  width: 100%;
  max-width: 260px;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
}
.sc-preview-img {
  width: 100%;
  aspect-ratio: 4 / 3;
  object-fit: cover;
  display: block;
}
.sc-preview-chip {
  position: absolute;
  bottom: 8px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--pass);
  background: rgba(16,185,129,0.12);
  border: 1px solid rgba(16,185,129,0.25);
  border-radius: 3px;
  padding: 0.18rem 0.45rem;
  white-space: nowrap;
}

.sc-preview-actions {
  display: flex;
  gap: 0.625rem;
}
.sc-retake-btn {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.875rem;
  cursor: pointer;
  transition: all 0.15s;
}
.sc-retake-btn:hover { color: var(--text-primary); border-color: rgba(255,255,255,0.15); }

.sc-accept-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.78rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, var(--pass) 0%, #059669 100%);
  border: none;
  border-radius: var(--radius-sm);
  padding: 0.45rem 1rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(16,185,129,0.25);
  transition: all 0.15s;
}
.sc-accept-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(16,185,129,0.35);
}

/* LIVE CAPTURE badge variant for confirmed preview */
.badge-capture {
  background: rgba(56,189,248,0.1) !important;
  border-color: rgba(56,189,248,0.25) !important;
  color: var(--accent-cyan) !important;
}

/* Responsive: stack buttons vertically on narrow cards */
@media (max-width: 480px) {
  .sc-action-grid { grid-template-columns: 1fr; }
  .sc-capture-controls { gap: 0.75rem; }
}
"""

target = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "index.css"
with open(target, "a", encoding="utf-8") as f:
    f.write(WEBCAM_CSS)
print(f"Appended webcam CSS ({len(WEBCAM_CSS)} chars) to {target}")
