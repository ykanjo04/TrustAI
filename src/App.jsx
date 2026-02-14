import React, { useState, useCallback, useEffect } from 'react'
import FileUpload from './components/FileUpload'
import DocumentPreview from './components/DocumentPreview'
import ExtractionResults from './components/ExtractionResults'
import TaxBreakdown from './components/TaxBreakdown'
import ValidationReport from './components/ValidationReport'
import ImprovementMetrics from './components/ImprovementMetrics'

export default function App() {
  const [file, setFile] = useState(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [metricsHistory, setMetricsHistory] = useState(null)
  const [health, setHealth] = useState(null)

  // Check backend health on mount
  useEffect(() => {
    fetch('/api/health')
      .then(res => res.json())
      .then(data => setHealth(data))
      .catch(() => setHealth(null))
  }, [])

  // Fetch metrics history after each extraction
  const fetchMetrics = useCallback(async () => {
    try {
      const res = await fetch('/api/metrics')
      if (res.ok) {
        const data = await res.json()
        setMetricsHistory(data)
      }
    } catch {
      // ignore
    }
  }, [])

  const handleFileSelected = useCallback(async (selectedFile) => {
    setFile(selectedFile)
    setResult(null)
    setError(null)
    setIsProcessing(true)

    const formData = new FormData()
    formData.append('file', selectedFile)

    try {
      const res = await fetch('/api/extract', {
        method: 'POST',
        body: formData,
      })

      if (!res.ok) {
        const errData = await res.json().catch(() => ({ detail: 'Unknown error' }))
        throw new Error(errData.detail || `Server error: ${res.status}`)
      }

      const data = await res.json()
      setResult(data)
      await fetchMetrics()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsProcessing(false)
    }
  }, [fetchMetrics])

  const handleDownload = useCallback(() => {
    if (result?.excel_filename) {
      window.open(`/api/download/${result.excel_filename}`, '_blank')
    }
  }, [result])

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-content">
          <div className="logo-area">
            <div className="logo-icon">
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
                <path d="M7 11V7a5 5 0 0 1 10 0v4" />
              </svg>
            </div>
            <div>
              <h1>TrustAI</h1>
              <p className="tagline">Privacy-First Invoice Tax Data Extraction</p>
            </div>
          </div>
          <div className="header-status">
            <span className={`status-dot ${health?.ollama_connected ? 'connected' : 'disconnected'}`}></span>
            <span className="status-text">
              {health?.ollama_connected ? 'Ollama Connected' : 'Ollama Offline'}
            </span>
            <span className="privacy-badge">100% Local</span>
          </div>
        </div>
      </header>

      <main className="app-main">
        <div className="main-grid">
          {/* Left column: Upload and Preview */}
          <div className="left-column">
            <FileUpload onFileSelected={handleFileSelected} isProcessing={isProcessing} />
            <DocumentPreview file={file} ocrText={result?.ocr_text} />
          </div>

          {/* Right column: Results */}
          <div className="right-column">
            {error && (
              <div className="error-banner">
                <span className="error-icon">&#x26A0;</span>
                <span>{error}</span>
              </div>
            )}

            {isProcessing && (
              <div className="processing-banner">
                <div className="spinner"></div>
                <div>
                  <strong>Processing invoice...</strong>
                  <p>Running extraction, validation, and self-improvement agents locally.</p>
                </div>
              </div>
            )}

            {result && (
              <>
                <div className="processing-time">
                  Processed in {result.processing_time_seconds}s | {result.privacy_notice}
                </div>

                <ExtractionResults data={result.extracted_data} />
                <TaxBreakdown data={result.extracted_data} />
                <ValidationReport validation={result.validation} />
                <ImprovementMetrics metrics={result.metrics} metricsHistory={metricsHistory} />

                <div className="download-section">
                  <button className="download-btn" onClick={handleDownload}>
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="7,10 12,15 17,10" />
                      <line x1="12" y1="15" x2="12" y2="3" />
                    </svg>
                    Download Excel Spreadsheet
                  </button>
                </div>
              </>
            )}

            {!result && !isProcessing && !error && (
              <div className="empty-state">
                <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1">
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14,2 14,8 20,8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
                <h3>Upload an invoice to get started</h3>
                <p>Your data stays on this machine. Nothing is sent externally.</p>
              </div>
            )}
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>TrustAI v1.0 | All processing is local | No data leaves your machine | UAE VAT 5% Compliant</p>
      </footer>
    </div>
  )
}
