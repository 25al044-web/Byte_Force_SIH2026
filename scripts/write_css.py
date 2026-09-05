"""
Write the complete index.css for the Sentinel ID premium redesign.
Run from the project root: backend\.venv\Scripts\python.exe scripts/write_css.py
"""
import pathlib

CSS = r"""
/* ==========================================================================
   SENTINEL ID — PREMIUM DESIGN SYSTEM
   SIH26188: AI-Based Fake Identity & Document Screening System
   ========================================================================== */

/* --- CSS Custom Properties (Design Tokens) --- */
:root {
  --bg-root:        #080c14;
  --bg-surface:     #0d1424;
  --bg-card:        #111a2e;
  --bg-card-raised: #16203a;
  --bg-input:       #0f1829;

  --border:         rgba(255, 255, 255, 0.07);
  --border-subtle:  rgba(255, 255, 255, 0.04);
  --border-active:  rgba(56, 189, 248, 0.3);

  --accent-cyan:    #38bdf8;
  --accent-blue:    #1d6eb4;
  --accent-glow:    rgba(56, 189, 248, 0.12);

  --text-primary:   #e8edf7;
  --text-secondary: #7d90b0;
  --text-muted:     #445066;
  --text-mono:      'JetBrains Mono', 'Fira Code', 'Consolas', monospace;

  --pass:           #10b981;
  --pass-bg:        rgba(16, 185, 129, 0.08);
  --pass-border:    rgba(16, 185, 129, 0.2);
  --pass-glow:      rgba(16, 185, 129, 0.15);

  --warn:           #f59e0b;
  --warn-bg:        rgba(245, 158, 11, 0.08);
  --warn-border:    rgba(245, 158, 11, 0.2);

  --fail:           #e05252;
  --fail-bg:        rgba(224, 82, 82, 0.08);
  --fail-border:    rgba(224, 82, 82, 0.2);
  --fail-glow:      rgba(224, 82, 82, 0.15);

  --na:             #445066;
  --na-bg:          rgba(68, 80, 102, 0.15);
  --na-border:      rgba(68, 80, 102, 0.3);

  --sidebar-w:      240px;
  --topbar-h:       60px;
  --radius-sm:      6px;
  --radius-md:      10px;
  --radius-lg:      14px;

  --shadow-card:    0 1px 3px rgba(0,0,0,0.4), 0 4px 16px rgba(0,0,0,0.3);
  --shadow-raised:  0 2px 8px rgba(0,0,0,0.5), 0 8px 24px rgba(0,0,0,0.35);

  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  line-height: 1.5;
  color-scheme: dark;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-rendering: optimizeLegibility;
}

/* --- Reset --- */
*, *::before, *::after { box-sizing: border-box; }
body { margin: 0; background: var(--bg-root); color: var(--text-primary); min-height: 100vh; }
#root { min-height: 100vh; }
h1,h2,h3,h4,h5,h6,p { margin: 0; }
ul { list-style: none; margin: 0; padding: 0; }
button { cursor: pointer; font-family: inherit; }
img { display: block; max-width: 100%; }

/* ==========================================================================
   APP SHELL — Sidebar + Main layout
   ========================================================================== */
.app-shell {
  display: flex;
  min-height: 100vh;
}

/* ==========================================================================
   SIDEBAR
   ========================================================================== */
.sidebar {
  width: var(--sidebar-w);
  min-height: 100vh;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  z-index: 100;
}

/* Brand */
.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.125rem;
}
.brand-mark {
  width: 38px;
  height: 38px;
  background: linear-gradient(135deg, #1a3a6b 0%, #0f2040 100%);
  border: 1px solid var(--border-active);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  flex-shrink: 0;
  box-shadow: 0 0 12px rgba(56,189,248,0.1);
}
.brand-text {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.brand-name {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.brand-sub {
  font-size: 0.68rem;
  color: var(--text-muted);
  font-weight: 400;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.sidebar-divider {
  height: 1px;
  background: var(--border);
  margin: 0 1rem;
}

/* Navigation */
.sidebar-nav {
  padding: 1rem 0.75rem;
}
.nav-section-label {
  display: block;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0 0.5rem 0.6rem;
}
.nav-list {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 0.625rem;
  padding: 0.55rem 0.625rem;
  border-radius: var(--radius-sm);
  font-size: 0.82rem;
  font-weight: 500;
  transition: background 0.15s;
}
.nav-active {
  background: rgba(56, 189, 248, 0.1);
  color: var(--accent-cyan);
  border: 1px solid rgba(56, 189, 248, 0.15);
}
.nav-active .nav-icon { color: var(--accent-cyan); }
.nav-disabled {
  color: var(--text-muted);
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}
.nav-icon { color: inherit; flex-shrink: 0; display: flex; }
.nav-label { flex: 1; }
.nav-active-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent-cyan);
  box-shadow: 0 0 6px rgba(56,189,248,0.6);
  flex-shrink: 0;
}
.nav-lock-badge {
  color: var(--text-muted);
  opacity: 0.6;
  display: flex;
}

.sidebar-spacer { flex: 1; }

/* Bottom */
.sidebar-bottom {
  padding: 1rem 1.125rem 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.sidebar-status-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
}
.sidebar-conn-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.conn-online { background: var(--pass); box-shadow: 0 0 6px rgba(16,185,129,0.5); }
.conn-offline { background: var(--fail); }
.sidebar-conn-label { font-size: 0.72rem; }

.sidebar-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
}
.sidebar-badge {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.15rem 0.45rem;
  border-radius: 3px;
  text-transform: uppercase;
}
.badge-sih   { background: #1a2744; color: #93c5fd; border: 1px solid rgba(147,197,253,0.2); }
.badge-problem { background: #1a2744; color: var(--accent-cyan); border: 1px solid var(--border-active); }
.badge-demo  { background: rgba(245,158,11,0.12); color: var(--warn); border: 1px solid rgba(245,158,11,0.25); }

.sidebar-meta-stack {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.sidebar-version {
  font-size: 0.65rem;
  color: var(--text-muted);
  font-family: var(--text-mono);
}
.sidebar-tech {
  font-size: 0.6rem;
  color: var(--text-muted);
}

/* ==========================================================================
   TOP BAR
   ========================================================================== */
.app-main {
  flex: 1;
  margin-left: var(--sidebar-w);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.topbar {
  height: var(--topbar-h);
  position: sticky;
  top: 0;
  z-index: 90;
  background: rgba(13, 20, 36, 0.9);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border);
  padding: 0 1.75rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.topbar-left {}
.topbar-title-group { display: flex; flex-direction: column; gap: 1px; }
.topbar-page-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.topbar-page-sub {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-weight: 400;
}
.topbar-right {
  display: flex;
  align-items: center;
  gap: 0.875rem;
}
.topbar-clock {
  font-family: var(--text-mono);
  font-size: 0.72rem;
  color: var(--text-secondary);
  letter-spacing: 0.04em;
}
.topbar-divider-v {
  width: 1px;
  height: 20px;
  background: var(--border);
}
.topbar-status-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  font-weight: 500;
  padding: 0.3rem 0.65rem;
  border-radius: 20px;
  border: 1px solid;
}
.status-online {
  color: var(--pass);
  border-color: var(--pass-border);
  background: var(--pass-bg);
}
.status-offline {
  color: var(--fail);
  border-color: var(--fail-border);
  background: var(--fail-bg);
}
.topbar-status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  flex-shrink: 0;
}
.status-online .topbar-status-dot { box-shadow: 0 0 5px rgba(16,185,129,0.6); animation: pulse-green 2s ease-in-out infinite; }

@keyframes pulse-green {
  0%,100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.topbar-mode-pill {
  font-size: 0.67rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.22rem 0.55rem;
  border-radius: 3px;
  background: rgba(245,158,11,0.1);
  color: var(--warn);
  border: 1px solid rgba(245,158,11,0.2);
  text-transform: uppercase;
}
.topbar-reset-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.3rem 0.7rem;
  transition: color 0.15s, border-color 0.15s, background 0.15s;
}
.topbar-reset-btn:hover:not(:disabled) {
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.04);
}
.topbar-reset-btn:disabled { opacity: 0.4; cursor: not-allowed; }

/* ==========================================================================
   MAIN CONTENT
   ========================================================================== */
.app-content {
  flex: 1;
  padding: 2rem 1.75rem 3rem;
  max-width: 1280px;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 0;
}

/* Toasts */
.toast-success, .toast-offline {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.75rem 1rem;
  border-radius: var(--radius-sm);
  font-size: 0.8rem;
  margin-bottom: 1.25rem;
  animation: fadeSlideIn 0.25s ease;
}
.toast-success {
  background: var(--pass-bg);
  border: 1px solid var(--pass-border);
  color: var(--pass);
}
.toast-offline {
  background: rgba(224,82,82,0.06);
  border: 1px solid rgba(224,82,82,0.2);
  color: #fca5a5;
}
.toast-offline strong { color: var(--fail); font-weight: 600; }

/* ==========================================================================
   EMPTY STATE
   ========================================================================== */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 3rem 1.5rem 2.5rem;
  gap: 1.5rem;
}

/* Geometric visual */
.empty-state-visual {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  width: 100%;
  margin-bottom: 0.5rem;
}
.es-outer-ring {
  width: 120px;
  height: 120px;
  border-radius: 50%;
  border: 1px solid rgba(56, 189, 248, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  background: radial-gradient(circle, rgba(56,189,248,0.04) 0%, transparent 70%);
}
.es-inner-ring {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 1px solid rgba(56, 189, 248, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(13, 20, 36, 0.6);
}
.es-shield-icon {
  color: var(--accent-cyan);
  opacity: 0.8;
}
.es-orbit-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-cyan);
  opacity: 0.5;
}
.es-dot-1 { top: 5px; left: 50%; transform: translateX(-50%); animation: orbit1 6s linear infinite; }
.es-dot-2 { top: 50%; right: 5px; transform: translateY(-50%); opacity: 0.3; background: var(--warn); }
.es-dot-3 { bottom: 8px; left: 18px; opacity: 0.25; background: var(--pass); }

@keyframes orbit1 {
  0%   { top: 5px;  left: 50%;   transform: translateX(-50%) scale(1); }
  25%  { top: 50%;  right: 5px;  left: auto; transform: translateY(-50%) scale(0.8); }
  50%  { bottom: 5px; left: 50%; top: auto; transform: translateX(-50%) scale(1); }
  75%  { top: 50%;  left: 5px;   transform: translateY(-50%) scale(0.8); }
  100% { top: 5px;  left: 50%;   transform: translateX(-50%) scale(1); }
}

.es-flanking {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.es-flank-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  color: var(--text-muted);
  font-size: 0.7rem;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
  min-width: 90px;
}
.es-connector-line {
  width: 40px;
  height: 1px;
  background: var(--border);
  position: relative;
}

/* Empty state copy */
.empty-state-copy {}
.es-heading {
  font-size: 1.35rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin-bottom: 0.5rem;
}
.es-body {
  font-size: 0.85rem;
  color: var(--text-secondary);
  max-width: 480px;
  line-height: 1.6;
}

.es-modules-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
}
.es-modules-grid {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.4rem;
  max-width: 560px;
}
.es-module-chip {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0.25rem 0.6rem;
  font-size: 0.72rem;
  color: var(--text-secondary);
}
.es-module-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--pass);
  box-shadow: 0 0 5px rgba(16,185,129,0.5);
  flex-shrink: 0;
}
.es-module-name { font-size: 0.7rem; font-weight: 500; }

.es-disclaimer {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  color: var(--text-muted);
}

/* ==========================================================================
   WORKSPACE SECTION (Upload + CTA + Timeline)
   ========================================================================== */
.workspace-section {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.workspace-below-empty { margin-top: 2rem; }

.stage-header { display: flex; flex-direction: column; gap: 0.3rem; }
.stage-pill {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--accent-cyan);
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.15);
  padding: 0.2rem 0.55rem;
  border-radius: 3px;
  display: inline-block;
  width: fit-content;
}
.stage-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.02em;
  margin-top: 0.35rem;
}
.stage-sub {
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.upload-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.25rem;
}

/* ==========================================================================
   UPLOAD PANEL
   ========================================================================== */
.upload-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.upload-panel.up-dragging {
  border-color: var(--accent-cyan);
  box-shadow: 0 0 0 3px rgba(56,189,248,0.1);
}
.upload-panel.up-filled {
  border-color: rgba(56,189,248,0.2);
}

.up-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-bottom: 1px solid var(--border);
}
.up-icon-badge {
  width: 36px;
  height: 36px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  flex-shrink: 0;
}
.up-title-group { flex: 1; min-width: 0; }
.up-title { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); }
.up-subtitle { font-size: 0.7rem; color: var(--text-muted); }
.up-header-actions { display: flex; gap: 0.35rem; margin-left: auto; }
.up-icon-btn {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border);
  background: transparent;
  color: var(--text-secondary);
  transition: all 0.15s;
}
.up-btn-replace:hover { color: var(--accent-cyan); border-color: rgba(56,189,248,0.3); background: rgba(56,189,248,0.06); }
.up-btn-remove:hover  { color: var(--fail); border-color: var(--fail-border); background: var(--fail-bg); }

.up-hidden-input { display: none; }

.up-dropzone {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem;
  gap: 0.6rem;
  border-top: none;
  cursor: pointer;
  transition: background 0.15s;
  outline: 2px dashed var(--border);
  outline-offset: -8px;
  margin: 0.5rem;
  border-radius: var(--radius-sm);
}
.up-dropzone:hover, .up-dz-active {
  background: rgba(56,189,248,0.04);
  outline-color: rgba(56,189,248,0.4);
}
.up-dz-icon { color: var(--text-muted); }
.up-dz-primary {
  font-size: 0.82rem;
  color: var(--text-secondary);
  text-align: center;
}
.up-dz-primary strong { color: var(--accent-cyan); }
.up-dz-hint { font-size: 0.7rem; color: var(--text-muted); }

.up-preview { display: flex; flex-direction: column; }
.up-preview-img-wrap {
  position: relative;
  width: 100%;
  aspect-ratio: 16/9;
  overflow: hidden;
  background: #0a1020;
}
.up-preview-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.up-preview-overlay {
  position: absolute;
  top: 0.5rem;
  left: 0.5rem;
}
.up-preview-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  background: rgba(16,185,129,0.85);
  color: #fff;
  padding: 0.2rem 0.45rem;
  border-radius: 3px;
  backdrop-filter: blur(4px);
}
.up-file-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--border);
  gap: 0.5rem;
}
.up-filename {
  font-size: 0.72rem;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  font-family: var(--text-mono);
  max-width: 70%;
}
.up-filesize {
  font-size: 0.68rem;
  color: var(--text-muted);
  flex-shrink: 0;
}

.up-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.72rem;
  color: var(--fail);
  padding: 0.5rem 0.75rem;
  border-top: 1px solid var(--fail-border);
  background: var(--fail-bg);
}

/* ==========================================================================
   SCREENING CTA
   ========================================================================== */
.cta-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.625rem;
}
.cta-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.625rem;
  width: 100%;
  max-width: 440px;
  padding: 0.875rem 2rem;
  border-radius: var(--radius-md);
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 0.01em;
  color: #fff;
  background: linear-gradient(135deg, #1565c0 0%, #1e3a6e 100%);
  box-shadow: 0 4px 14px rgba(21, 101, 192, 0.35), inset 0 1px 0 rgba(255,255,255,0.06);
  transition: all 0.2s;
  cursor: pointer;
}
.cta-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(56,189,248,0.2), 0 2px 8px rgba(21,101,192,0.4);
  background: linear-gradient(135deg, #1976d2 0%, #234b8a 100%);
}
.cta-btn:active:not(:disabled) { transform: translateY(0); }
.cta-btn.cta-disabled, .cta-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
  box-shadow: none;
  transform: none;
}
.cta-btn.cta-loading { opacity: 0.7; cursor: wait; }

.cta-spinner {
  width: 17px;
  height: 17px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
  flex-shrink: 0;
}
.cta-text { letter-spacing: 0.01em; }
.cta-hint {
  font-size: 0.72rem;
  color: var(--text-muted);
  text-align: center;
  max-width: 380px;
}

/* ==========================================================================
   LOADING TIMELINE
   ========================================================================== */
.loading-timeline-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.5rem 1.75rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  animation: fadeSlideIn 0.3s ease;
}
.lt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.lt-live-badge {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-cyan);
}
.lt-pulse {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--accent-cyan);
  animation: pulse-green 1.2s ease-in-out infinite;
  flex-shrink: 0;
}
.lt-stage-counter {
  font-size: 0.7rem;
  color: var(--text-muted);
  font-family: var(--text-mono);
}

.lt-progress-bar {
  height: 3px;
  background: var(--bg-surface);
  border-radius: 2px;
  overflow: hidden;
}
.lt-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--accent-blue), var(--accent-cyan));
  border-radius: 2px;
  transition: width 0.8s ease;
}

.lt-stages {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.lt-stage {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
}
.lt-stage-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
  padding-top: 2px;
}
.lt-indicator-done {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--pass-bg);
  border: 1.5px solid var(--pass);
  color: var(--pass);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.lt-indicator-active {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.lt-active-ring {
  position: absolute;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 1.5px solid var(--accent-cyan);
  animation: pulse-ring 1.2s ease-out infinite;
}
.lt-active-core {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--accent-cyan);
  box-shadow: 0 0 8px rgba(56,189,248,0.6);
}
@keyframes pulse-ring {
  0%   { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.6); opacity: 0; }
}

.lt-indicator-pending {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.lt-pending-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--bg-card-raised);
  border: 1.5px solid var(--border);
}
.lt-connector {
  width: 1.5px;
  height: 28px;
  background: var(--border);
  margin: 2px auto;
  border-radius: 1px;
}
.lt-conn-done { background: var(--pass); opacity: 0.5; }

.lt-stage-content {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding-bottom: 14px;
  flex: 1;
}
.lt-stage-icon { color: var(--text-muted); flex-shrink: 0; padding-top: 3px; }
.lt-stage.lt-active .lt-stage-icon { color: var(--accent-cyan); }
.lt-stage.lt-done .lt-stage-icon { color: var(--pass); }
.lt-stage-text { display: flex; flex-direction: column; gap: 3px; }
.lt-stage-label { font-size: 0.8rem; font-weight: 500; color: var(--text-muted); }
.lt-stage.lt-active .lt-stage-label { color: var(--text-primary); font-weight: 600; }
.lt-stage.lt-done .lt-stage-label { color: var(--text-muted); text-decoration: line-through; text-decoration-color: rgba(68,80,102,0.4); }
.lt-stage-detail { font-size: 0.72rem; color: var(--text-secondary); line-height: 1.4; animation: fadeSlideIn 0.3s ease; }

/* ==========================================================================
   RESULTS SECTION
   ========================================================================== */
.results-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  animation: fadeSlideIn 0.4s ease;
}
.results-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}
.results-header-left { display: flex; flex-direction: column; gap: 0.3rem; }
.btn-new-screening {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.77rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.45rem 0.875rem;
  transition: all 0.15s;
  margin-bottom: 0.2rem;
}
.btn-new-screening:hover {
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.15);
  background: var(--bg-card-raised);
}

/* ==========================================================================
   RESULT HERO
   ========================================================================== */
.result-hero {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.hero-low  { border-top: 3px solid var(--pass); background: linear-gradient(180deg, rgba(16,185,129,0.05) 0%, var(--bg-card) 60%); }
.hero-review { border-top: 3px solid var(--warn); background: linear-gradient(180deg, rgba(245,158,11,0.05) 0%, var(--bg-card) 60%); }
.hero-high { border-top: 3px solid var(--fail); background: linear-gradient(180deg, rgba(224,82,82,0.06) 0%, var(--bg-card) 60%); }

.rh-meta-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rh-screening-id { display: flex; flex-direction: column; gap: 2px; }
.rh-id-label { font-size: 0.6rem; text-transform: uppercase; letter-spacing: 0.1em; color: var(--text-muted); }
.rh-id-value { font-family: var(--text-mono); font-size: 0.8rem; color: var(--accent-cyan); }
.rh-protocol-tag {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.68rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.rh-proto-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--pass);
  box-shadow: 0 0 5px rgba(16,185,129,0.5);
  animation: pulse-green 2s ease-in-out infinite;
}

.rh-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  align-items: start;
}
.rh-eyebrow {
  display: block;
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}
.rh-outcome-block { display: flex; flex-direction: column; }
.rh-outcome-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.4rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  margin-bottom: 0.875rem;
}
.rh-outcome-label { line-height: 1; }
.rh-score-row { display: flex; align-items: baseline; gap: 0.3rem; }
.rh-score-num { font-family: var(--text-mono); font-size: 2.5rem; font-weight: 700; color: var(--text-primary); line-height: 1; }
.rh-score-denom { font-size: 1rem; color: var(--text-muted); }
.rh-score-caption { font-size: 0.72rem; color: var(--text-secondary); margin-left: 0.4rem; }

.rh-directive-block { display: flex; flex-direction: column; }
.rh-directive-badge {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-left: 3px solid;
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  padding: 0.875rem;
}
.rh-directive-icon { flex-shrink: 0; padding-top: 1px; }
.rh-directive-title { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); margin-bottom: 0.25rem; }
.rh-directive-detail { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.5; }

/* ==========================================================================
   RESULTS TOP GRID (Hero + Gauge)
   ========================================================================== */
.results-top-grid {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 1.25rem;
  align-items: stretch;
}

/* ==========================================================================
   RISK GAUGE
   ========================================================================== */
.risk-gauge-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
}
.rg-header {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.rg-eyebrow {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.rg-zone-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
}
.rg-svg-wrap { width: 100%; max-width: 240px; }
.rg-svg { width: 100%; height: auto; overflow: visible; }

.rg-legend {
  display: flex;
  gap: 1rem;
  justify-content: center;
}
.rg-legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.65rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.rg-swatch { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.rg-sw-low { background: var(--pass); }
.rg-sw-review { background: var(--warn); }
.rg-sw-high { background: var(--fail); }

/* ==========================================================================
   SECTION HEADER (shared)
   ========================================================================== */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border);
  margin-bottom: 1.25rem;
}
.section-header-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.section-header-icon {
  width: 34px;
  height: 34px;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent-cyan);
  flex-shrink: 0;
}
.section-header-text { display: flex; flex-direction: column; gap: 2px; }
.section-eyebrow {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.section-title { font-size: 0.95rem; font-weight: 700; color: var(--text-primary); }
.section-header-right {}

/* ==========================================================================
   IDENTITY PANEL
   ========================================================================== */
.identity-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
}
.idn-status-pill {
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.2rem 0.55rem;
  border-radius: 3px;
  text-transform: uppercase;
}
.pill-extracted {
  background: rgba(56,189,248,0.08);
  color: var(--accent-cyan);
  border: 1px solid rgba(56,189,248,0.2);
}
.pill-degraded {
  background: var(--warn-bg);
  color: var(--warn);
  border: 1px solid var(--warn-border);
}

.idn-alert {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  background: rgba(245,158,11,0.06);
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: var(--radius-sm);
  padding: 0.75rem;
  font-size: 0.78rem;
  color: #fcd34d;
  margin-bottom: 1.25rem;
}
.idn-alert svg { flex-shrink: 0; margin-top: 1px; }
.idn-alert strong { color: var(--warn); }
.idn-alert span { color: var(--text-secondary); }

.idn-fields-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.idn-field {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.875rem 1rem;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
}
.idn-field:nth-child(3n) { border-right: none; }
.idn-field:nth-last-child(-n+3) { border-bottom: none; }
.idn-label {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.idn-value { font-size: 0.82rem; color: var(--text-primary); font-weight: 500; }
.idn-value-na { color: var(--text-muted); font-style: italic; font-weight: 400; }

.idn-mrz-block {
  margin-top: 1.25rem;
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
}
.idn-mrz-empty { opacity: 0.6; }
.idn-mrz-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0.875rem;
  border-bottom: 1px solid var(--border);
  background: rgba(255,255,255,0.02);
}
.idn-mrz-tag {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.idn-mrz-detected {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--pass);
  letter-spacing: 0.06em;
}
.idn-mrz-absent {
  font-size: 0.62rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 0.06em;
}
.idn-mrz-lines { padding: 0.75rem 0.875rem; }
.idn-mrz-line {
  font-family: var(--text-mono);
  font-size: 0.8rem;
  color: var(--accent-cyan);
  letter-spacing: 0.12em;
  line-height: 1.8;
  white-space: pre;
  overflow-x: auto;
}
.idn-mrz-empty-text {
  padding: 0.75rem 0.875rem;
  font-size: 0.75rem;
  color: var(--text-muted);
  font-style: italic;
}

/* ==========================================================================
   STATUS PILL
   ========================================================================== */
.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  border-radius: 4px;
  border: 1px solid;
  white-space: nowrap;
}
.pill-sm { font-size: 0.62rem; padding: 0.18rem 0.45rem; }
.pill-md { font-size: 0.67rem; padding: 0.22rem 0.55rem; }
.pill-lg { font-size: 0.78rem; padding: 0.3rem 0.7rem; }
.pill-pass  { background: var(--pass-bg); color: var(--pass); border-color: var(--pass-border); }
.pill-warn  { background: var(--warn-bg); color: var(--warn); border-color: var(--warn-border); }
.pill-fail  { background: var(--fail-bg); color: var(--fail); border-color: var(--fail-border); }
.pill-na    { background: var(--na-bg);   color: var(--na);   border-color: var(--na-border);   }

/* ==========================================================================
   VERIFICATION GRID
   ========================================================================== */
.verification-grid-section {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}
.vg-count-badge {
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-cyan);
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.15);
  padding: 0.2rem 0.55rem;
  border-radius: 3px;
}
.vg-cards-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

/* ==========================================================================
   VERIFICATION CARD (base)
   ========================================================================== */
.vcard {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
  transition: box-shadow 0.2s;
}
.vcard:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.3); }

/* Status-specific card styling */
.vcard-status-pass    { border-color: rgba(16,185,129,0.15); }
.vcard-status-warning { border-color: rgba(245,158,11,0.15); }
.vcard-status-fail    { border-color: rgba(224,82,82,0.2); background: rgba(224,82,82,0.03); }
.vcard-status-not_available { opacity: 0.7; }

.vc-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
}
.vc-title-group { display: flex; flex-direction: column; gap: 0.25rem; }
.vc-category {
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.09em;
  text-transform: uppercase;
  color: var(--text-muted);
}
.vc-title-row { display: flex; align-items: center; gap: 0.4rem; }
.vc-icon { color: var(--text-muted); display: flex; }
.vc-name { font-size: 0.8rem; font-weight: 600; color: var(--text-primary); }

.vc-mini-bar-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.vc-mini-bar {
  flex: 1;
  height: 4px;
  background: rgba(255,255,255,0.06);
  border-radius: 2px;
  overflow: hidden;
}
.vc-mini-fill {
  height: 100%;
  border-radius: 2px;
  transition: width 0.8s ease;
}
.vc-mini-label { font-size: 0.65rem; font-family: var(--text-mono); color: var(--text-secondary); flex-shrink: 0; }
.vc-reason { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.45; }

.vc-forensic-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
}
.forensic-chip {
  font-size: 0.62rem;
  color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0.15rem 0.4rem;
}

/* ==========================================================================
   FACE COMPARE CARD
   ========================================================================== */
.face-compare-card {
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.fc-compare-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.fc-face-slot {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}
.fc-slot-label {
  font-size: 0.62rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  color: var(--text-muted);
}
.fc-img-frame {
  width: 100%;
  max-width: 120px;
  aspect-ratio: 3/4;
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid var(--border);
  position: relative;
  background: var(--bg-card);
}
.fc-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.fc-img-badge {
  position: absolute;
  bottom: 0.3rem;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  background: rgba(0,0,0,0.7);
  color: rgba(255,255,255,0.7);
  padding: 0.1rem 0.35rem;
  border-radius: 2px;
  white-space: nowrap;
  backdrop-filter: blur(4px);
}
.fc-img-placeholder {
  width: 100%;
  max-width: 120px;
  aspect-ratio: 3/4;
  border-radius: var(--radius-sm);
  border: 1px dashed var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  color: var(--text-muted);
  font-size: 0.65rem;
}

.fc-connector {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.3rem;
  flex-shrink: 0;
}
.fc-conn-line {
  width: 1px;
  height: 30px;
  background: var(--border);
}
.fc-conn-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}
.fc-sim-num {
  font-family: var(--text-mono);
  font-size: 1.1rem;
  font-weight: 700;
  line-height: 1;
}
.fc-sim-label { font-size: 0.6rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
.fc-sim-na { font-size: 1.1rem; color: var(--text-muted); }

/* ==========================================================================
   ALERT PANEL
   ========================================================================== */
.alert-panel {
  display: flex;
  align-items: flex-start;
  gap: 0.875rem;
  padding: 0.875rem 1rem;
  border-radius: var(--radius-sm);
  border: 1px solid;
  animation: fadeSlideIn 0.25s ease;
}
.alert-danger {
  background: rgba(224, 82, 82, 0.07);
  border-color: rgba(224, 82, 82, 0.3);
  color: #fca5a5;
  box-shadow: 0 0 16px rgba(224,82,82,0.08);
}
.alert-warning {
  background: rgba(245, 158, 11, 0.07);
  border-color: rgba(245, 158, 11, 0.3);
  color: #fcd34d;
}
.alert-icon-col { color: var(--fail); flex-shrink: 0; padding-top: 1px; }
.alert-warning .alert-icon-col { color: var(--warn); }
.alert-body { display: flex; flex-direction: column; gap: 0.35rem; }
.alert-title { font-size: 0.82rem; font-weight: 600; color: var(--text-primary); }
.alert-detail { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4; }
.alert-meta-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.2rem; }
.alert-meta-chip {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.7rem;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 3px;
  padding: 0.15rem 0.5rem;
}
.alert-meta-label { color: var(--text-muted); }
.alert-meta-value { color: var(--text-secondary); font-family: var(--text-mono); }

/* ==========================================================================
   EXPLANATION PANEL
   ========================================================================== */
.explanation-panel {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem 1.5rem;
}
.exp-audit-badge {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.07em;
  text-transform: uppercase;
  color: var(--text-muted);
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border);
  padding: 0.2rem 0.55rem;
  border-radius: 3px;
}
.exp-content { margin: 0 0 1rem; }
.exp-list { display: flex; flex-direction: column; gap: 0; }
.exp-item {
  display: flex;
  align-items: flex-start;
  gap: 0.625rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-subtle);
}
.exp-item:last-child { border-bottom: none; }
.exp-bullet {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 5px;
}
.bullet-penalty { background: var(--fail); box-shadow: 0 0 5px rgba(224,82,82,0.4); }
.bullet-neutral  { background: var(--text-muted); }
.bullet-info     { background: var(--accent-cyan); }
.exp-text { font-size: 0.78rem; color: var(--text-secondary); line-height: 1.45; }
.exp-empty { font-size: 0.78rem; color: var(--text-muted); font-style: italic; padding: 0.5rem 0; }
.exp-footer {
  display: flex;
  align-items: flex-start;
  gap: 0.4rem;
  font-size: 0.68rem;
  color: var(--text-muted);
  border-top: 1px solid var(--border);
  padding-top: 0.875rem;
  line-height: 1.4;
}
.exp-footer svg { flex-shrink: 0; color: var(--pass); margin-top: 1px; }

/* ==========================================================================
   ERROR MESSAGE
   ========================================================================== */
.error-banner {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  background: rgba(224,82,82,0.07);
  border: 1px solid rgba(224,82,82,0.25);
  border-radius: var(--radius-sm);
  padding: 0.875rem 1rem;
  animation: fadeSlideIn 0.2s ease;
}
.error-icon { color: var(--fail); flex-shrink: 0; padding-top: 1px; }
.error-body { display: flex; flex-direction: column; gap: 2px; flex: 1; }
.error-heading { font-size: 0.78rem; font-weight: 600; color: #fca5a5; }
.error-msg { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.4; }
.error-dismiss {
  color: var(--text-muted);
  background: transparent;
  border: none;
  padding: 2px;
  flex-shrink: 0;
  margin-top: 1px;
  display: flex;
  transition: color 0.15s;
}
.error-dismiss:hover { color: var(--text-secondary); }

/* ==========================================================================
   ANIMATIONS & UTILITIES
   ========================================================================== */
@keyframes fadeSlideIn {
  from { opacity: 0; transform: translateY(6px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes spin {
  to { transform: rotate(360deg); }
}
.spin-icon { animation: spin 1s linear infinite; }

/* ==========================================================================
   RESPONSIVE
   ========================================================================== */
@media (max-width: 1100px) {
  .results-top-grid { grid-template-columns: 1fr; }
  .risk-gauge-card { max-width: 340px; align-self: center; }
  .rh-main { grid-template-columns: 1fr; }
}

@media (max-width: 900px) {
  :root { --sidebar-w: 200px; }
  .vg-cards-grid { grid-template-columns: 1fr; }
  .idn-fields-grid { grid-template-columns: repeat(2, 1fr); }
  .upload-grid { grid-template-columns: 1fr; }
}

@media (max-width: 700px) {
  .sidebar { transform: translateX(-100%); }
  .app-main { margin-left: 0; }
  :root { --topbar-h: 56px; }
  .topbar-clock { display: none; }
  .idn-fields-grid { grid-template-columns: 1fr 1fr; }
}

@media (max-width: 480px) {
  .idn-fields-grid { grid-template-columns: 1fr; }
  .idn-field:nth-child(2n) { border-right: none; }
}
"""

target = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "index.css"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text(CSS, encoding="utf-8")
print(f"Written {len(CSS)} chars to {target}")
