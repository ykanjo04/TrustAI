import React from 'react'

export default function DocumentPreview({ file, ocrText }) {
  if (!file) return null

  const isImage = file.type.startsWith('image/')
  const isPdf = file.type === 'application/pdf'
  const previewUrl = URL.createObjectURL(file)

  return (
    <div className="preview-section">
      <h2>Document Preview</h2>
      <div className="preview-container">
        {isImage && (
          <img
            src={previewUrl}
            alt="Uploaded invoice"
            className="preview-image"
            onLoad={() => URL.revokeObjectURL(previewUrl)}
          />
        )}
        {isPdf && (
          <div className="pdf-preview">
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14,2 14,8 20,8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
              <polyline points="10,9 9,9 8,9" />
            </svg>
            <p>{file.name}</p>
            <p className="file-size">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
        )}
      </div>

      {ocrText && (
        <div className="ocr-text-section">
          <h3>Raw OCR Text (Transparency)</h3>
          <pre className="ocr-text">{ocrText}</pre>
        </div>
      )}
    </div>
  )
}
