import { useState } from 'react'

function App() {
  const [backendStatus, setBackendStatus] = useState('Not Checked')
  const [isChecking, setIsChecking] = useState(false)

  const checkBackendHealth = async () => {
    setIsChecking(true)
    try {
      const response = await fetch('http://localhost:8000/api/health')
      if (response.ok) {
        const data = await response.json()
        setBackendStatus(data.status === 'ok' ? 'Connected (status: ok)' : 'Unexpected response')
      } else {
        setBackendStatus(`Error: ${response.status}`)
      }
    } catch (error) {
      setBackendStatus('Backend unreachable (run backend on port 8000)')
    } finally {
      setIsChecking(false)
    }
  }

  const plannedModules = [
    { name: 'Document Extraction', desc: 'OCR field & data parsing' },
    { name: 'MRZ Validation', desc: 'ICAO 9303 checksum verification' },
    { name: 'Document Tamper Screening', desc: 'Digital splicing & artifact detection' },
    { name: 'Face Matching', desc: 'Document photo vs live selfie comparison' },
    { name: 'Duplicate Identity Screening', desc: 'Cross-identity match detection' },
    { name: 'Blacklist Checking', desc: 'Watchlist & sanction screening' },
    { name: 'Explainable Risk Scoring', desc: 'Comprehensive unified risk engine' },
  ]

  return (
    <div className="container">
      <span className="badge">SIH 2026 • Problem Statement: SIH26188</span>
      <h1>AI-Based Fake Identity & Document Screening System</h1>
      <p className="subtitle">
        Initial project skeleton successfully initialized with independent React frontend and FastAPI backend.
      </p>

      <div className="status-card">
        <div className="status-indicator">
          <span
            className={`status-dot ${backendStatus.includes('Connected') ? 'online' : 'offline'}`}
          ></span>
          <span>Backend API Status: <strong>{backendStatus}</strong></span>
        </div>
        <button
          className="status-btn"
          onClick={checkBackendHealth}
          disabled={isChecking}
        >
          {isChecking ? 'Checking...' : 'Check /api/health'}
        </button>
      </div>

      <h2 style={{ fontSize: '1.2rem', color: '#1e293b', marginBottom: '0.5rem' }}>
        Roadmap & Planned Modules
      </h2>
      <div className="modules-grid">
        {plannedModules.map((m, idx) => (
          <div key={idx} className="module-card">
            <div className="module-title">{m.name}</div>
            <div className="module-status">{m.desc}</div>
          </div>
        ))}
      </div>
    </div>
  )
}

export default App
