import React, { useCallback, useEffect, useRef, useState } from 'react'
import { addBlacklistEntry, deactivateBlacklistEntry, getBlacklist } from '../services/api'
import { StatusPill } from './StatusPill'

// ──────────────────────────────────────────────────────────
// Constants
// ──────────────────────────────────────────────────────────
const SEVERITY_OPTIONS = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']

const SEVERITY_COLOR = {
  LOW:      { color: '#10b981', bg: 'rgba(16,185,129,0.1)',  border: 'rgba(16,185,129,0.25)' },
  MEDIUM:   { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)', border: 'rgba(245,158,11,0.25)' },
  HIGH:     { color: '#e05252', bg: 'rgba(224,82,82,0.1)',   border: 'rgba(224,82,82,0.25)'  },
  CRITICAL: { color: '#dc2626', bg: 'rgba(220,38,38,0.12)',  border: 'rgba(220,38,38,0.35)'  },
}

const EMPTY_FORM = {
  document_number: '',
  full_name: '',
  nationality: '',
  date_of_birth: '',
  reason: '',
  severity: 'HIGH',
}

// ──────────────────────────────────────────────────────────
// Sub-components
// ──────────────────────────────────────────────────────────
function SeverityPill({ severity }) {
  const s = (severity || '').toUpperCase()
  const meta = SEVERITY_COLOR[s] || { color: '#445066', bg: 'rgba(68,80,102,0.15)', border: 'rgba(68,80,102,0.3)' }
  return (
    <span
      style={{
        display: 'inline-block',
        fontSize: '0.62rem',
        fontWeight: 700,
        letterSpacing: '0.07em',
        textTransform: 'uppercase',
        color: meta.color,
        background: meta.bg,
        border: `1px solid ${meta.border}`,
        borderRadius: '3px',
        padding: '0.2rem 0.5rem',
        whiteSpace: 'nowrap',
      }}
    >
      {s}
    </span>
  )
}

function FormField({ label, required, children }) {
  return (
    <div className="bl-form-field">
      <label className="bl-form-label">
        {label}
        {required && <span className="bl-required">*</span>}
      </label>
      {children}
    </div>
  )
}

// ──────────────────────────────────────────────────────────
// Main Panel
// ──────────────────────────────────────────────────────────
export function BlacklistPanel({ onClose, backendOnline }) {
  const [form, setForm] = useState(EMPTY_FORM)
  const [submitting, setSubmitting] = useState(false)
  const [formError, setFormError] = useState(null)
  const [formSuccess, setFormSuccess] = useState(null)

  const [records, setRecords] = useState([])
  const [listLoading, setListLoading] = useState(true)
  const [listError, setListError] = useState(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [severityFilter, setSeverityFilter] = useState('')
  const [deactivatingDoc, setDeactivatingDoc] = useState(null)
  const [deactivateConfirm, setDeactivateConfirm] = useState(null) // doc_number awaiting confirm

  const firstInputRef = useRef(null)

  const fetchRecords = useCallback(async () => {
    setListLoading(true)
    setListError(null)
    try {
      const data = await getBlacklist({
        search: searchQuery || undefined,
        severity: severityFilter || undefined,
      })
      setRecords(data.records || [])
    } catch (err) {
      setListError(err.message)
    } finally {
      setListLoading(false)
    }
  }, [searchQuery, severityFilter])

  useEffect(() => {
    if (backendOnline) fetchRecords()
    else setListLoading(false)
  }, [fetchRecords, backendOnline])

  // Focus first input on mount
  useEffect(() => {
    firstInputRef.current?.focus()
  }, [])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm((prev) => ({ ...prev, [name]: value }))
    setFormError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setFormError(null)
    setFormSuccess(null)

    if (!form.document_number.trim()) {
      setFormError('Document Number is required.')
      return
    }
    if (!form.reason.trim()) {
      setFormError('Reason is required.')
      return
    }

    setSubmitting(true)
    try {
      const payload = {
        document_number: form.document_number.trim(),
        reason: form.reason.trim(),
        severity: form.severity,
        ...(form.full_name.trim()    && { full_name:    form.full_name.trim() }),
        ...(form.nationality.trim()  && { nationality:  form.nationality.trim().toUpperCase() }),
        ...(form.date_of_birth.trim() && { date_of_birth: form.date_of_birth.trim() }),
      }
      const res = await addBlacklistEntry(payload)
      setFormSuccess(res.message || 'Document successfully added to blacklist.')
      setForm(EMPTY_FORM)
      fetchRecords()
    } catch (err) {
      setFormError(err.message || 'Failed to add blacklist entry.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeactivate = async (docNumber) => {
    if (deactivateConfirm !== docNumber) {
      setDeactivateConfirm(docNumber)
      return
    }
    setDeactivateConfirm(null)
    setDeactivatingDoc(docNumber)
    try {
      await deactivateBlacklistEntry(docNumber)
      fetchRecords()
    } catch (err) {
      setListError(err.message)
    } finally {
      setDeactivatingDoc(null)
    }
  }

  const handleCancelConfirm = () => setDeactivateConfirm(null)

  const fmtDate = (iso) => {
    if (!iso) return '—'
    try { return new Date(iso.replace(' ', 'T') + 'Z').toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', hour12: false }) }
    catch { return iso }
  }

  return (
    <div className="bl-overlay" role="dialog" aria-modal="true" aria-label="Blacklist Management">
      <div className="bl-panel">
        {/* ── PANEL HEADER ── */}
        <div className="bl-panel-header">
          <div className="bl-panel-title-group">
            <div className="bl-panel-icon">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="4.93" y1="4.93" x2="19.07" y2="19.07" />
              </svg>
            </div>
            <div>
              <span className="bl-eyebrow">WATCHLIST MANAGEMENT</span>
              <h2 className="bl-panel-heading">Blacklist Records</h2>
            </div>
          </div>
          <div className="bl-panel-header-actions">
            <span className="bl-demo-badge">DEMO DATABASE</span>
            <button type="button" className="bl-close-btn" onClick={onClose} aria-label="Close">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          </div>
        </div>

        <div className="bl-panel-body">
          {!backendOnline && (
            <div className="bl-offline-notice">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              Backend service is offline. Connect the FastAPI server to manage blacklist records.
            </div>
          )}

          {/* ════════════════════════════════════════
              ADD ENTRY FORM
          ════════════════════════════════════════ */}
          <section className="bl-section">
            <div className="bl-section-header">
              <span className="bl-section-eyebrow">ACTION</span>
              <h3 className="bl-section-title">Add New Blacklist Entry</h3>
            </div>

            <form onSubmit={handleSubmit} className="bl-form" noValidate>
              <div className="bl-form-grid">
                <FormField label="Document Number" required>
                  <input
                    ref={firstInputRef}
                    className="bl-input"
                    name="document_number"
                    value={form.document_number}
                    onChange={handleChange}
                    placeholder="e.g. TEST-JURY-001"
                    maxLength={50}
                    autoComplete="off"
                    disabled={!backendOnline || submitting}
                  />
                </FormField>

                <FormField label="Full Name">
                  <input
                    className="bl-input"
                    name="full_name"
                    value={form.full_name}
                    onChange={handleChange}
                    placeholder="e.g. DEMO PERSON"
                    maxLength={100}
                    disabled={!backendOnline || submitting}
                  />
                </FormField>

                <FormField label="Nationality (ISO)">
                  <input
                    className="bl-input"
                    name="nationality"
                    value={form.nationality}
                    onChange={handleChange}
                    placeholder="e.g. IND"
                    maxLength={10}
                    disabled={!backendOnline || submitting}
                  />
                </FormField>

                <FormField label="Date of Birth">
                  <input
                    className="bl-input"
                    name="date_of_birth"
                    type="date"
                    value={form.date_of_birth}
                    onChange={handleChange}
                    disabled={!backendOnline || submitting}
                  />
                </FormField>

                <FormField label="Severity" required>
                  <div className="bl-select-wrap">
                    <select
                      className="bl-select"
                      name="severity"
                      value={form.severity}
                      onChange={handleChange}
                      disabled={!backendOnline || submitting}
                    >
                      {SEVERITY_OPTIONS.map((s) => (
                        <option key={s} value={s}>{s}</option>
                      ))}
                    </select>
                    <svg className="bl-select-arrow" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                      <polyline points="6 9 12 15 18 9" />
                    </svg>
                  </div>
                </FormField>
              </div>

              <FormField label="Reason for Blacklisting" required>
                <textarea
                  className="bl-textarea"
                  name="reason"
                  value={form.reason}
                  onChange={handleChange}
                  placeholder="e.g. Reported stolen document — submitted for jury demonstration"
                  rows={2}
                  maxLength={300}
                  disabled={!backendOnline || submitting}
                />
                <span className="bl-char-count">{form.reason.length}/300</span>
              </FormField>

              {formError && (
                <div className="bl-form-error" role="alert">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="12" cy="12" r="10" />
                    <line x1="12" y1="8" x2="12" y2="12" />
                    <line x1="12" y1="16" x2="12.01" y2="16" />
                  </svg>
                  <span>{formError}</span>
                </div>
              )}
              {formSuccess && (
                <div className="bl-form-success" role="status">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  <span>{formSuccess}</span>
                </div>
              )}

              <div className="bl-form-actions">
                <button
                  type="submit"
                  className="bl-submit-btn"
                  disabled={!backendOnline || submitting}
                >
                  {submitting ? (
                    <>
                      <span className="bl-spinner" />
                      Adding to Blacklist…
                    </>
                  ) : (
                    <>
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                        <line x1="12" y1="5" x2="12" y2="19" />
                        <line x1="5" y1="12" x2="19" y2="12" />
                      </svg>
                      Add to Blacklist
                    </>
                  )}
                </button>
                <button
                  type="button"
                  className="bl-clear-btn"
                  onClick={() => { setForm(EMPTY_FORM); setFormError(null); setFormSuccess(null) }}
                  disabled={submitting}
                >
                  Clear Form
                </button>
              </div>
            </form>
          </section>

          {/* ════════════════════════════════════════
              RECORDS TABLE
          ════════════════════════════════════════ */}
          <section className="bl-section">
            <div className="bl-section-header">
              <div>
                <span className="bl-section-eyebrow">DATABASE</span>
                <h3 className="bl-section-title">Active Blacklist Records</h3>
              </div>
              <div className="bl-list-controls">
                <div className="bl-search-wrap">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8" />
                    <line x1="21" y1="21" x2="16.65" y2="16.65" />
                  </svg>
                  <input
                    className="bl-search-input"
                    placeholder="Search…"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                  />
                </div>
                <select
                  className="bl-filter-select"
                  value={severityFilter}
                  onChange={(e) => setSeverityFilter(e.target.value)}
                >
                  <option value="">All Severity</option>
                  {SEVERITY_OPTIONS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
                <button
                  type="button"
                  className="bl-refresh-btn"
                  onClick={fetchRecords}
                  disabled={listLoading || !backendOnline}
                  title="Refresh"
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.25">
                    <polyline points="1 4 1 10 7 10" />
                    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
                  </svg>
                </button>
              </div>
            </div>

            {listError && (
              <div className="bl-list-error">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {listError}
              </div>
            )}

            <div className="bl-table-wrap">
              <table className="bl-table">
                <thead>
                  <tr>
                    <th>Document No.</th>
                    <th>Name</th>
                    <th>Severity</th>
                    <th>Reason</th>
                    <th>Created At (IST)</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {listLoading ? (
                    <tr>
                      <td colSpan={6} className="bl-td-center">
                        <span className="bl-spinner" />
                        <span style={{ marginLeft: '0.5rem', color: 'var(--text-muted)' }}>Loading…</span>
                      </td>
                    </tr>
                  ) : records.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="bl-td-center bl-td-empty">
                        {backendOnline ? 'No active blacklist records match your filters.' : 'Backend offline.'}
                      </td>
                    </tr>
                  ) : (
                    records.map((rec) => {
                      const isDeactivating = deactivatingDoc === rec.document_number
                      const awaitingConfirm = deactivateConfirm === rec.document_number
                      return (
                        <tr key={rec.document_number} className={awaitingConfirm ? 'bl-row-confirm' : ''}>
                          <td className="bl-td-mono">{rec.document_number}</td>
                          <td className="bl-td-name">{rec.full_name || <span className="bl-na">—</span>}</td>
                          <td><SeverityPill severity={rec.severity} /></td>
                          <td className="bl-td-reason" title={rec.reason}>{rec.reason}</td>
                          <td className="bl-td-mono bl-td-date">{fmtDate(rec.created_at)}</td>
                          <td className="bl-td-action">
                            {awaitingConfirm ? (
                              <div className="bl-confirm-row">
                                <span className="bl-confirm-text">Deactivate?</span>
                                <button
                                  className="bl-btn-danger-sm"
                                  onClick={() => handleDeactivate(rec.document_number)}
                                  disabled={isDeactivating}
                                >Yes</button>
                                <button
                                  className="bl-btn-ghost-sm"
                                  onClick={handleCancelConfirm}
                                >No</button>
                              </div>
                            ) : (
                              <button
                                className="bl-deactivate-btn"
                                onClick={() => handleDeactivate(rec.document_number)}
                                disabled={isDeactivating}
                                title="Deactivate this record"
                              >
                                {isDeactivating ? <span className="bl-spinner bl-spinner-sm" /> : (
                                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                                    <line x1="18" y1="6" x2="6" y2="18" />
                                    <line x1="6" y1="6" x2="18" y2="18" />
                                  </svg>
                                )}
                                Deactivate
                              </button>
                            )}
                          </td>
                        </tr>
                      )
                    })
                  )}
                </tbody>
              </table>
            </div>

            <div className="bl-table-footer">
              <span>{records.length} active record{records.length !== 1 ? 's' : ''}</span>
              <span className="bl-disclaimer">SYNTHETIC DEMONSTRATION DATA ONLY — NOT REAL PERSONAL INFORMATION</span>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
