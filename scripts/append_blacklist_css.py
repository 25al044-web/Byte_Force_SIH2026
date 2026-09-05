"""
Append BlacklistPanel CSS to the existing index.css.
Run from project root: backend\.venv\Scripts\python.exe scripts\append_blacklist_css.py
"""
import pathlib

BLACKLIST_CSS = r"""
/* ==========================================================================
   BLACKLIST PANEL — Full-screen overlay with slide-in drawer
   ========================================================================== */

/* Overlay backdrop */
.bl-overlay {
  position: fixed;
  inset: 0;
  z-index: 200;
  background: rgba(4, 8, 18, 0.85);
  backdrop-filter: blur(6px);
  display: flex;
  align-items: stretch;
  justify-content: flex-end;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}

/* Drawer panel */
.bl-panel {
  width: 100%;
  max-width: 860px;
  background: var(--bg-surface);
  border-left: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  animation: slideInRight 0.25s ease;
}

@keyframes slideInRight {
  from { transform: translateX(40px); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

/* Panel header */
.bl-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.125rem 1.5rem;
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  background: rgba(255,255,255,0.015);
}
.bl-panel-title-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.bl-panel-icon {
  width: 36px;
  height: 36px;
  background: rgba(224,82,82,0.1);
  border: 1px solid rgba(224,82,82,0.2);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--fail);
  flex-shrink: 0;
}
.bl-eyebrow {
  display: block;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.bl-panel-heading {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: -0.01em;
}
.bl-panel-header-actions {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.bl-demo-badge {
  font-size: 0.6rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  background: rgba(245,158,11,0.1);
  color: var(--warn);
  border: 1px solid rgba(245,158,11,0.2);
}
.bl-close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.bl-close-btn:hover {
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.04);
}

/* Panel body — scrollable */
.bl-panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* Offline notice */
.bl-offline-notice {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  color: #fca5a5;
  background: rgba(224,82,82,0.07);
  border: 1px solid rgba(224,82,82,0.2);
  border-radius: var(--radius-sm);
  padding: 0.75rem 1rem;
}

/* Section */
.bl-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
.bl-section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}
.bl-section-eyebrow {
  display: block;
  font-size: 0.58rem;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 2px;
}
.bl-section-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
}

/* ── FORM ── */
.bl-form {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}
.bl-form-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}
.bl-form-field {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  position: relative;
}
.bl-form-label {
  font-size: 0.68rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-secondary);
}
.bl-required {
  color: var(--fail);
  margin-left: 2px;
}
.bl-input,
.bl-textarea,
.bl-select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 0.82rem;
  font-family: inherit;
  transition: border-color 0.15s, box-shadow 0.15s;
  outline: none;
  width: 100%;
}
.bl-input {
  padding: 0.5rem 0.75rem;
  height: 36px;
}
.bl-textarea {
  padding: 0.5rem 0.75rem;
  resize: vertical;
  min-height: 64px;
}
.bl-input:focus,
.bl-textarea:focus,
.bl-select:focus {
  border-color: var(--border-active);
  box-shadow: 0 0 0 3px var(--accent-glow);
}
.bl-input::placeholder,
.bl-textarea::placeholder { color: var(--text-muted); }
.bl-input:disabled,
.bl-textarea:disabled,
.bl-select:disabled { opacity: 0.4; cursor: not-allowed; }

.bl-select-wrap { position: relative; }
.bl-select {
  padding: 0.5rem 2rem 0.5rem 0.75rem;
  height: 36px;
  appearance: none;
  cursor: pointer;
}
.bl-select-arrow {
  position: absolute;
  right: 0.6rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  pointer-events: none;
}

.bl-char-count {
  font-size: 0.62rem;
  color: var(--text-muted);
  text-align: right;
  margin-top: 2px;
}

.bl-form-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.77rem;
  color: #fca5a5;
  background: rgba(224,82,82,0.07);
  border: 1px solid rgba(224,82,82,0.2);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.75rem;
  animation: fadeSlideIn 0.2s ease;
}
.bl-form-success {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.77rem;
  color: var(--pass);
  background: var(--pass-bg);
  border: 1px solid var(--pass-border);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.75rem;
  animation: fadeSlideIn 0.2s ease;
}

.bl-form-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}
.bl-submit-btn {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1.25rem;
  border-radius: var(--radius-sm);
  border: none;
  font-size: 0.82rem;
  font-weight: 600;
  color: #fff;
  background: linear-gradient(135deg, #8b1111 0%, #c0392b 100%);
  box-shadow: 0 2px 8px rgba(224,82,82,0.25);
  cursor: pointer;
  transition: all 0.15s;
}
.bl-submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 14px rgba(224,82,82,0.35);
}
.bl-submit-btn:disabled { opacity: 0.4; cursor: not-allowed; transform: none; }

.bl-clear-btn {
  font-size: 0.78rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.875rem;
  cursor: pointer;
  transition: all 0.15s;
}
.bl-clear-btn:hover { color: var(--text-primary); border-color: rgba(255,255,255,0.15); }

/* ── SPINNER ── */
.bl-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}
.bl-spinner-sm {
  width: 10px;
  height: 10px;
}

/* ── LIST CONTROLS ── */
.bl-list-controls {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.bl-search-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.bl-search-wrap svg {
  position: absolute;
  left: 0.5rem;
  color: var(--text-muted);
  pointer-events: none;
}
.bl-search-input {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-size: 0.78rem;
  font-family: inherit;
  padding: 0.35rem 0.6rem 0.35rem 1.75rem;
  height: 32px;
  outline: none;
  width: 160px;
  transition: border-color 0.15s;
}
.bl-search-input:focus { border-color: var(--border-active); }
.bl-search-input::placeholder { color: var(--text-muted); }

.bl-filter-select {
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-family: inherit;
  padding: 0.3rem 0.6rem;
  height: 32px;
  outline: none;
  cursor: pointer;
}
.bl-refresh-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}
.bl-refresh-btn:hover:not(:disabled) { color: var(--text-primary); border-color: rgba(255,255,255,0.15); }
.bl-refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.bl-list-error {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  color: #fca5a5;
  background: rgba(224,82,82,0.06);
  border: 1px solid rgba(224,82,82,0.2);
  border-radius: var(--radius-sm);
  padding: 0.5rem 0.75rem;
}

/* ── TABLE ── */
.bl-table-wrap {
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  overflow: hidden;
  overflow-x: auto;
}
.bl-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.78rem;
}
.bl-table thead {
  background: rgba(255,255,255,0.03);
  border-bottom: 1px solid var(--border);
}
.bl-table th {
  padding: 0.5rem 0.875rem;
  text-align: left;
  font-size: 0.62rem;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--text-muted);
  white-space: nowrap;
}
.bl-table td {
  padding: 0.625rem 0.875rem;
  border-bottom: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  vertical-align: middle;
}
.bl-table tbody tr:last-child td { border-bottom: none; }
.bl-table tbody tr:hover td { background: rgba(255,255,255,0.02); }
.bl-row-confirm td { background: rgba(224,82,82,0.04); }

.bl-td-mono { font-family: var(--text-mono); font-size: 0.75rem; color: var(--text-primary); }
.bl-td-name { color: var(--text-secondary); max-width: 120px; }
.bl-td-reason {
  color: var(--text-secondary);
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.bl-td-date { font-size: 0.7rem; color: var(--text-muted); }
.bl-td-action { white-space: nowrap; }
.bl-td-center {
  text-align: center;
  padding: 1.5rem !important;
  display: flex;
  align-items: center;
  justify-content: center;
}
.bl-td-center { display: table-cell; }
.bl-td-empty { color: var(--text-muted); font-style: italic; }
.bl-na { color: var(--text-muted); }

.bl-deactivate-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.68rem;
  font-weight: 500;
  color: var(--text-muted);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0.2rem 0.5rem;
  cursor: pointer;
  transition: all 0.15s;
}
.bl-deactivate-btn:hover:not(:disabled) {
  color: var(--fail);
  border-color: rgba(224,82,82,0.3);
  background: rgba(224,82,82,0.06);
}
.bl-deactivate-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.bl-confirm-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.bl-confirm-text { font-size: 0.7rem; color: var(--fail); }
.bl-btn-danger-sm {
  font-size: 0.68rem;
  font-weight: 600;
  color: #fff;
  background: var(--fail);
  border: none;
  border-radius: 3px;
  padding: 0.2rem 0.45rem;
  cursor: pointer;
  transition: background 0.15s;
}
.bl-btn-danger-sm:hover { background: #c0392b; }
.bl-btn-ghost-sm {
  font-size: 0.68rem;
  font-weight: 500;
  color: var(--text-secondary);
  background: transparent;
  border: 1px solid var(--border);
  border-radius: 3px;
  padding: 0.2rem 0.45rem;
  cursor: pointer;
  transition: all 0.15s;
}
.bl-btn-ghost-sm:hover { color: var(--text-primary); }

.bl-table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 0;
  font-size: 0.68rem;
  color: var(--text-muted);
}
.bl-disclaimer {
  font-size: 0.6rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  opacity: 0.6;
}

/* ── Sidebar LIVE nav button ── */
.nav-live-btn {
  width: 100%;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  cursor: pointer;
  padding: 0;
  color: var(--text-secondary);
  transition: all 0.15s;
}
.nav-live-btn:hover {
  color: var(--fail);
  background: rgba(224,82,82,0.07);
  border-color: rgba(224,82,82,0.15);
  border-radius: var(--radius-sm);
}
.nav-live-badge {
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 0.12rem 0.35rem;
  border-radius: 2px;
  background: rgba(224,82,82,0.12);
  color: #fca5a5;
  border: 1px solid rgba(224,82,82,0.2);
  flex-shrink: 0;
}

@media (max-width: 900px) {
  .bl-form-grid { grid-template-columns: repeat(2, 1fr); }
  .bl-panel { max-width: 100%; }
}
@media (max-width: 600px) {
  .bl-form-grid { grid-template-columns: 1fr; }
  .bl-list-controls { flex-wrap: wrap; }
  .bl-search-input { width: 120px; }
}
"""

target = pathlib.Path(__file__).parent.parent / "frontend" / "src" / "index.css"
with open(target, "a", encoding="utf-8") as f:
    f.write(BLACKLIST_CSS)
print(f"Appended blacklist CSS ({len(BLACKLIST_CSS)} chars) to {target}")
