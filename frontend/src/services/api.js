/**
 * API service for SIH26188 Identity Screening System.
 * Connects to the backend at http://127.0.0.1:8000.
 */

const API_BASE_URL = 'http://127.0.0.1:8000'

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
