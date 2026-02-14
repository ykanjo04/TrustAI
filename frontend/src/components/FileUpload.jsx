import React, { useCallback, useRef, useState } from 'react'

export default function FileUpload({ onFileSelected, isProcessing }) {
  const [dragActive, setDragActive] = useState(false)
  const inputRef = useRef(null)

  const handleDrag = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }, [])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      onFileSelected(e.dataTransfer.files[0])
    }
  }, [onFileSelected])

  const handleChange = useCallback((e) => {
    if (e.target.files && e.target.files[0]) {
      onFileSelected(e.target.files[0])
    }
  }, [onFileSelected])

  return (
    <div className="upload-section">
      <h2>Upload Invoice or Receipt</h2>
      <div
        className={`drop-zone ${dragActive ? 'drag-active' : ''} ${isProcessing ? 'disabled' : ''}`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => !isProcessing && inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".jpg,.jpeg,.png,.pdf,.tiff,.bmp"
          onChange={handleChange}
          style={{ display: 'none' }}
          disabled={isProcessing}
        />
        <div className="drop-zone-content">
          <div className="upload-icon">
            {isProcessing ? (
              <div className="spinner"></div>
            ) : (
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
            )}
          </div>
          <p className="drop-zone-text">
            {isProcessing
              ? 'Processing document...'
              : 'Drag & drop your invoice here, or click to browse'}
          </p>
          <p className="drop-zone-hint">
            Supports: JPG, PNG, PDF
          </p>
        </div>
      </div>
    </div>
  )
}
