import React, { useEffect, useState } from 'react'
import {
  deactivateTrustedIdentity,
  getTrustedIdentities,
  registerTrustedIdentity,
  getRegistryAuthStatus,
  unlockRegistry,
  lockRegistry,
  updateTrustedIdentity,
} from '../services/api'
import { useTranslation } from '../i18n'

export function TrustedRegistryPage({ backendOnline }) {
  const { t } = useTranslation()
  const [records, setRecords] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')
  const [showAddModal, setShowAddModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [actionNotice, setActionNotice] = useState(null)
  const [unlocked, setUnlocked] = useState(false)
  const [pin, setPin] = useState('')
  const [lockMessage, setLockMessage] = useState(null)
  const [editing, setEditing] = useState(null)

  // Add Form State
  const [formData, setFormData] = useState({
    full_name: '',
    document_number: '',
    document_type: 'PASSPORT',
    date_of_birth: '',
    nationality: 'IND',
    notes: '',
  })
  const [photoFile, setPhotoFile] = useState(null)
  const [photoPreview, setPhotoPreview] = useState(null)

  const fetchRecords = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await getTrustedIdentities({ search: search.trim() || undefined })
      setRecords(data.records || [])
    } catch (err) {
      setError(err.message || 'Failed to fetch trusted identities.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    getRegistryAuthStatus().then(s => { setUnlocked(Boolean(s.unlocked)); if (s.unlocked) fetchRecords() }).catch(() => {})
  }, [])

  const handleUnlock = async (e) => {
    e.preventDefault(); setLockMessage(null)
    if (!/^\d{6}$/.test(pin)) { setLockMessage('Enter exactly six numeric digits.'); return }
    try { await unlockRegistry(pin); setPin(''); setUnlocked(true); fetchRecords() } catch (err) { setLockMessage(err.message) }
  }
  const handleLock = async () => { await lockRegistry(); setUnlocked(false); setRecords([]); setShowAddModal(false); setEditing(null) }
  const handleEditSave = async (e) => { e.preventDefault(); try { await updateTrustedIdentity(editing.registry_id, editing); setEditing(null); setActionNotice('Identity updated and audit event recorded.'); fetchRecords() } catch (err) { setError(err.message) } }

  if (!unlocked) return (
    <section className="page-container"><div className="empty-panel" style={{ maxWidth: 620, margin: '80px auto' }}>
      <div className="empty-icon">🔒</div><span className="stage-pill">RESTRICTED ACCESS</span><h2 className="stage-title">Trusted Identity Registry</h2>
      <p>This registry contains trusted identity records. Access is restricted to authorized officers.</p>
      <form onSubmit={handleUnlock} className="tr-form" style={{ marginTop: 24 }}><input aria-label="Six digit officer PIN" className="form-input font-mono" type="password" inputMode="numeric" maxLength="6" autoComplete="one-time-code" value={pin} onChange={e => setPin(e.target.value.replace(/\D/g, ''))} placeholder="••••••" />
        {lockMessage && <p className="toast-offline">{lockMessage}</p>}<button className="btn-submit" type="submit">Unlock Registry</button></form>
    </div></section>
  )

  const handleSearchSubmit = (e) => {
    e.preventDefault()
    fetchRecords()
  }

  const handlePhotoSelect = (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
  }

  const handleFormSubmit = async (e) => {
    e.preventDefault()
    if (!formData.full_name || !formData.document_number || !formData.date_of_birth) {
      setError('Please fill in all required fields.')
      return
    }

    setSubmitting(true)
    setError(null)
    setActionNotice(null)

    try {
      let payload
      if (photoFile) {
        payload = new FormData()
        payload.append('full_name', formData.full_name)
        payload.append('document_number', formData.document_number)
        payload.append('document_type', formData.document_type)
        payload.append('date_of_birth', formData.date_of_birth)
        payload.append('nationality', formData.nationality)
        payload.append('notes', formData.notes)
        payload.append('photo', photoFile)
      } else {
        payload = { ...formData }
      }

      const res = await registerTrustedIdentity(payload)
      setActionNotice(`Identity successfully registered (ID: ${res.record?.registry_id || 'TIR'})`)
      setShowAddModal(false)
      setFormData({
        full_name: '',
        document_number: '',
        document_type: 'PASSPORT',
        date_of_birth: '',
        nationality: 'IND',
        notes: '',
      })
      setPhotoFile(null)
      setPhotoPreview(null)
      fetchRecords()
    } catch (err) {
      setError(err.message || 'Registration failed.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeactivate = async (registryId) => {
    if (!window.confirm(`Are you sure you want to deactivate trusted record ${registryId}?`)) {
      return
    }
    try {
      await deactivateTrustedIdentity(registryId)
      setActionNotice(`Record ${registryId} deactivated.`)
      fetchRecords()
    } catch (err) {
      setError(err.message || 'Failed to deactivate record.')
    }
  }

  return (
    <section className="page-container">
      {/* Page Header */}
      <div className="page-header">
        <div className="page-header-left">
          <span className="stage-pill">VERIFIED BASELINE REGISTRY</span>
          <h2 className="stage-title">Trusted Identity Registry</h2>
          <p className="stage-sub">
            Authoritative local demonstration registry of verified identities used for automated border cross-verification.
          </p>
        </div>

        <div className="page-header-actions">
          <button type="button" className="btn-deactivate" onClick={handleLock}>🔓 Lock Registry</button>
          <button
            type="button"
            className="btn-primary-action"
            onClick={() => {
              setShowAddModal(true)
              setError(null)
            }}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            <span>Register New Identity</span>
          </button>
        </div>
      </div>

      {actionNotice && (
        <div className="toast-success" role="status">
          <span>{actionNotice}</span>
          <button type="button" onClick={() => setActionNotice(null)}>×</button>
        </div>
      )}

      {error && (
        <div className="toast-offline" role="alert">
          <span>{error}</span>
          <button type="button" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* Search Bar */}
      <div className="tr-search-bar">
        <form onSubmit={handleSearchSubmit} className="tr-search-form">
          <div className="tr-search-input-wrap">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
            <input
              type="text"
              className="tr-search-input"
              placeholder="Search by name, document number, or registry ID (e.g. ID123456, ARUN KUMAR)..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-search-submit">Search</button>
          {search && (
            <button
              type="button"
              className="btn-search-clear"
              onClick={() => {
                setSearch('')
                setTimeout(fetchRecords, 0)
              }}
            >
              Clear
            </button>
          )}
        </form>
      </div>

      {/* Add Modal */}
      {showAddModal && (
        <div className="modal-backdrop">
          <div className="modal-panel tr-modal">
            <div className="modal-header">
              <h3 className="modal-title">Register Trusted Identity Record</h3>
              <button
                type="button"
                className="btn-modal-close"
                onClick={() => setShowAddModal(false)}
              >
                ×
              </button>
            </div>

            <form onSubmit={handleFormSubmit} className="tr-form">
              <div className="form-grid">
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input
                    type="text"
                    required
                    className="form-input"
                    placeholder="e.g. ARUN KUMAR"
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Document Number / ID *</label>
                  <input
                    type="text"
                    required
                    className="form-input font-mono"
                    placeholder="e.g. ID123456"
                    value={formData.document_number}
                    onChange={(e) => setFormData({ ...formData, document_number: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Document Type *</label>
                  <select
                    className="form-select"
                    value={formData.document_type}
                    onChange={(e) => setFormData({ ...formData, document_type: e.target.value })}
                  >
                    <option value="PASSPORT">Passport</option>
                    <option value="DRIVING_LICENSE">Driving License</option>
                    <option value="NATIONAL_ID">National ID / Citizen Card</option>
                    <option value="AADHAAR">Aadhaar (Synthetic Demo)</option>
                    <option value="VOTER_ID">Voter ID</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Date of Birth (YYYY-MM-DD or DD-MM-YYYY) *</label>
                  <input
                    type="text"
                    required
                    className="form-input font-mono"
                    placeholder="e.g. 1995-05-15 or 15-05-1995"
                    value={formData.date_of_birth}
                    onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Nationality</label>
                  <input
                    type="text"
                    className="form-input font-mono"
                    placeholder="e.g. IND"
                    value={formData.nationality}
                    onChange={(e) => setFormData({ ...formData, nationality: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Reference Biometric Photo (Optional)</label>
                  <input
                    type="file"
                    accept="image/jpeg,image/png"
                    className="form-file-input"
                    onChange={handlePhotoSelect}
                  />
                  {photoPreview && (
                    <div className="photo-preview-wrap">
                      <img src={photoPreview} alt="Reference Preview" className="photo-preview-thumb" />
                      <button
                        type="button"
                        className="btn-remove-photo"
                        onClick={() => {
                          setPhotoFile(null)
                          setPhotoPreview(null)
                        }}
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>

                <div className="form-group form-group-full">
                  <label className="form-label">Verification Notes / Issuing Authority Remarks</label>
                  <textarea
                    rows={2}
                    className="form-textarea"
                    placeholder="Verified government issuance record notes..."
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  />
                </div>
              </div>

              <div className="modal-footer">
                <button
                  type="button"
                  className="btn-cancel"
                  onClick={() => setShowAddModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-submit"
                  disabled={submitting}
                >
                  {submitting ? 'Registering…' : 'Save Trusted Record'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Record Table */}
      {loading ? (
        <div className="empty-panel">
          <div className="empty-spinner" />
          <p>Loading trusted registry records…</p>
        </div>
      ) : records.length === 0 ? (
        <div className="empty-panel">
          <div className="empty-icon empty-icon-check">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
            </svg>
          </div>
          <h3>No Records Found</h3>
          <p>No trusted identities match your search query.</p>
        </div>
      ) : (
        <div className="audit-table-wrap">
          <table className="audit-table">
            <thead>
              <tr>
                <th>Registry ID</th>
                <th>Full Name</th>
                <th>Document No.</th>
                <th>Type</th>
                <th>DOB</th>
                <th>Nationality</th>
                <th>Biometric Photo</th>
                <th>Status</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {records.map((rec) => (
                <tr key={rec.registry_id} className={!rec.is_active ? 'row-inactive' : ''}>
                  <td className="font-mono">{rec.registry_id}</td>
                  <td><strong>{rec.full_name}</strong></td>
                  <td className="font-mono">{rec.document_number}</td>
                  <td><span className="badge-doc-type">{rec.document_type}</span></td>
                  <td className="font-mono">{rec.date_of_birth}</td>
                  <td className="font-mono">{rec.nationality || '—'}</td>
                  <td>
                    {rec.has_reference_photo ? (
                      <span className="pill-photo-attached">Biometric Enrolled</span>
                    ) : (
                      <span className="pill-photo-none">No Photo</span>
                    )}
                  </td>
                  <td>
                    {rec.is_active ? (
                      <span className="status-badge badge-pass">ACTIVE</span>
                    ) : (
                      <span className="status-badge badge-fail">INACTIVE</span>
                    )}
                  </td>
                  <td>
                    {rec.is_active && (
                      <button type="button" className="btn-search-submit" onClick={() => setEditing({ ...rec })}>Edit</button>
                    )}
                    {rec.is_active && (
                      <button
                        type="button"
                        className="btn-deactivate"
                        onClick={() => handleDeactivate(rec.registry_id)}
                        title="Deactivate this record"
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {editing && <div className="modal-backdrop"><div className="modal-panel tr-modal"><div className="modal-header"><h3 className="modal-title">Edit Identity</h3><button className="btn-modal-close" onClick={() => setEditing(null)}>×</button></div><form onSubmit={handleEditSave} className="tr-form"><div className="form-grid">{['full_name','document_number','document_type','date_of_birth','nationality','notes'].map(field => <div className="form-group" key={field}><label className="form-label">{field.replaceAll('_',' ')}</label><input required={['full_name','document_number','document_type','date_of_birth'].includes(field)} className="form-input" value={editing[field] || ''} onChange={e => setEditing({ ...editing, [field]: e.target.value })} /></div>)}</div><div className="modal-footer"><button className="btn-cancel" type="button" onClick={() => setEditing(null)}>Cancel</button><button className="btn-submit" type="submit">Save Changes</button></div></form></div></div>}
    </section>
  )
}
