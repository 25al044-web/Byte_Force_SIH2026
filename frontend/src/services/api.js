/**
 * API service for SIH26188 Identity Screening System.
 * Connects to the backend at http://127.0.0.1:8000.
 */

const API_BASE_URL = 'http://127.0.0.1:8000'
let registrySession = sessionStorage.getItem('registrySession') || ''
const registryHeaders = () => registrySession ? { 'X-Registry-Session': registrySession } : {}

export async function getRegistryAuthStatus() {
  const res = await fetch(`${API_BASE_URL}/api/registry/auth/status`, { headers: registryHeaders() })
  return res.json()
}
export async function unlockRegistry(pin) {
  const res = await fetch(`${API_BASE_URL}/api/registry/auth/unlock`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ pin }) })
  const data = await res.json().catch(() => ({})); if (!res.ok) throw new Error(data.detail || 'Invalid officer PIN')
  registrySession = data.token; sessionStorage.setItem('registrySession', registrySession); return data
}
export async function lockRegistry() { await fetch(`${API_BASE_URL}/api/registry/auth/lock`, { method: 'POST', headers: registryHeaders() }); registrySession = ''; sessionStorage.removeItem('registrySession') }

/**
 * Sends travel/identity document and selfie image files to the screening endpoint.
 *
 * @param {File} documentFile - Selected travel or identity document image.
 * @param {File} selfieFile - Selected live portrait or selfie photograph.
 * @returns {Promise<Object>} The screening response data adhering to docs/API_CONTRACT.md.
 */
export async function screenIdentity(documentFile, selfieFile) {
  if (!documentFile) {
    throw new Error('Travel/Identity document image is required.')
  }
  if (!selfieFile) {
    throw new Error('Live selfie photograph is required.')
  }

  const formData = new FormData()
  formData.append('document_image', documentFile)
  formData.append('selfie_image', selfieFile)

  let response
  try {
    response = await fetch(`${API_BASE_URL}/api/screen`, {
      method: 'POST',
      body: formData,
    })
  } catch (netErr) {
    throw new Error(
      'Unable to connect to the backend service. Please verify that the FastAPI backend server is running on http://127.0.0.1:8000.'
    )
  }

  let data
  try {
    data = await response.json()
  } catch (jsonErr) {
    throw new Error(
      `Invalid response format from screening server (HTTP ${response.status}). Expected JSON.`
    )
  }

  if (!response.ok) {
    let errorMsg = `Screening request failed with status ${response.status}.`
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        errorMsg = data.detail
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map((err) => `${err.loc ? err.loc.join('.') + ': ' : ''}${err.msg}`).join('; ')
      }
    }
    throw new Error(errorMsg)
  }

  // Basic sanity check against contract
  if (!data.screening_id || !data.checks || !data.risk) {
    throw new Error(
      'Malformed response received from backend: Missing required contract fields (screening_id, checks, risk).'
    )
  }

  return data
}

/**
 * Checks backend health status.
 */
export async function checkBackendHealth() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/health`)
    if (res.ok) {
      const data = await res.json()
      return data.status === 'ok'
    }
    return false
  } catch {
    return false
  }
}

/**
 * Retrieves the current demonstration mode status from backend.
 */
export async function getDemoStatus() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/demo/status`)
    if (res.ok) {
      const data = await res.json()
      return Boolean(data.demo_mode)
    }
    return false
  } catch {
    return false
  }
}

/**
 * Resets demo scan history (clears identity_embeddings only).
 */
export async function resetDemoData() {
  const res = await fetch(`${API_BASE_URL}/api/demo/reset`, {
    method: 'POST',
  })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to reset demo scan data.')
  }
  return res.json()
}

export async function getAudits() {
  const res = await fetch(`${API_BASE_URL}/api/audit`)
  if (!res.ok) throw new Error('Failed to load blockchain audit records.')
  return res.json()
}

export async function getAudit(screeningId) {
  const res = await fetch(`${API_BASE_URL}/api/audit/${encodeURIComponent(screeningId)}`)
  if (!res.ok) throw new Error('Audit verification is unavailable.')
  return res.json()
}

export async function getCases(onlyRequiringReview = true) {
  const res = await fetch(`${API_BASE_URL}/api/cases?all_cases=${!onlyRequiringReview}`)
  if (!res.ok) throw new Error('Failed to load screening cases.')
  return res.json()
}

export async function getCase(screeningId) {
  const res = await fetch(`${API_BASE_URL}/api/cases/${encodeURIComponent(screeningId)}`)
  if (!res.ok) throw new Error('Case not found.')
  return res.json()
}

export async function getSystemStatus() {
  const res = await fetch(`${API_BASE_URL}/api/system/status`)
  if (!res.ok) throw new Error('Failed to fetch system status.')
  return res.json()
}

/**
 * Fetches active blacklist records.
 * @param {Object} opts - Optional filters: { severity, search, activeOnly }
 */
export async function getBlacklist({ severity, search, activeOnly = true } = {}) {
  const params = new URLSearchParams()
  params.set('active_only', String(activeOnly))
  if (severity) params.set('severity', severity)
  if (search) params.set('search', search)

  const res = await fetch(`${API_BASE_URL}/api/blacklist?${params.toString()}`)
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to fetch blacklist records.')
  }
  return res.json()
}

/**
 * Adds an entry to the demonstration blacklist.
 * @param {{ document_number, full_name, nationality, date_of_birth, reason, severity }} entry
 */
export async function addBlacklistEntry(entry) {
  const res = await fetch(`${API_BASE_URL}/api/blacklist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entry),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    if (Array.isArray(detail)) {
      throw new Error(detail.map((e) => `${e.loc ? e.loc.join('.') + ': ' : ''}${e.msg}`).join('; '))
    }
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${res.status}).`)
  }
  return data
}

/**
 * Deactivates a blacklist entry by document number.
 * @param {string} documentNumber
 */
export async function deactivateBlacklistEntry(documentNumber) {
  const res = await fetch(
    `${API_BASE_URL}/api/blacklist/${encodeURIComponent(documentNumber)}/deactivate`,
    { method: 'PATCH' }
  )
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    throw new Error(typeof detail === 'string' ? detail : `Deactivate failed (${res.status}).`)
  }
  return data
}

/**
 * Lists trusted identities from the local demo registry.
 */
export async function getTrustedIdentities({ search, activeOnly = false, limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams()
  params.set('active_only', String(activeOnly))
  params.set('limit', String(limit))
  params.set('offset', String(offset))
  if (search) params.set('search', search)

  const res = await fetch(`${API_BASE_URL}/api/trusted-identities?${params.toString()}`, { headers: registryHeaders() })
  if (!res.ok) {
    const data = await res.json().catch(() => ({}))
    throw new Error(data.detail || 'Failed to fetch trusted identities.')
  }
  return res.json()
}

/**
 * Registers a new identity in the trusted registry.
 * Supports FormData (with photo) or plain JS object.
 */
export async function registerTrustedIdentity(payload) {
  const isFormData = payload instanceof FormData
  const options = {
    method: 'POST',
    body: isFormData ? payload : JSON.stringify(payload),
    headers: registryHeaders(),
  }
  if (!isFormData) {
    options.headers = { ...options.headers, 'Content-Type': 'application/json' }
  }

  const res = await fetch(`${API_BASE_URL}/api/trusted-identities`, options)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const detail = data.detail
    if (Array.isArray(detail)) {
      throw new Error(detail.map((e) => `${e.loc ? e.loc.join('.') + ': ' : ''}${e.msg}`).join('; '))
    }
    throw new Error(typeof detail === 'string' ? detail : `Registration failed (${res.status}).`)
  }
  return data
}

/**
 * Look up a trusted identity by document number.
 */
export async function lookupTrustedIdentity(documentNumber) {
  const res = await fetch(`${API_BASE_URL}/api/trusted-identities/lookup/${encodeURIComponent(documentNumber)}`)
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || `Identity lookup failed (${res.status}).`)
  }
  return data
}

/**
 * Soft-deactivates a trusted identity record.
 */
export async function deactivateTrustedIdentity(registryId) {
  const res = await fetch(`${API_BASE_URL}/api/trusted-identities/${encodeURIComponent(registryId)}/deactivate`, {
    method: 'POST', headers: registryHeaders(),
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    throw new Error(data.detail || `Deactivation failed (${res.status}).`)
  }
  return data
}

export async function updateTrustedIdentity(registryId, payload) {
  const isFormData = payload instanceof FormData
  const res = await fetch(`${API_BASE_URL}/api/trusted-identities/${encodeURIComponent(registryId)}`, { method: 'PUT', headers: isFormData ? registryHeaders() : { ...registryHeaders(), 'Content-Type': 'application/json' }, body: isFormData ? payload : JSON.stringify(payload) })
  const data = await res.json().catch(() => ({})); if (!res.ok) throw new Error(data.detail || 'Update failed.')
  return data
}
