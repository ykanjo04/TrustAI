import React from 'react'

export default function ValidationReport({ validation }) {
  if (!validation) return null

  const { is_valid, confidence_score, errors, warnings, notes } = validation

  const getConfidenceColor = (score) => {
    if (score >= 80) return '#22c55e'
    if (score >= 60) return '#f59e0b'
    return '#ef4444'
  }

  const getConfidenceLabel = (score) => {
    if (score >= 80) return 'High'
    if (score >= 60) return 'Medium'
    return 'Low'
  }

  return (
    <div className="validation-section">
      <h2>Validation Report</h2>

      <div className="confidence-display">
        <div className="confidence-gauge">
          <svg viewBox="0 0 120 120" className="confidence-ring">
            <circle cx="60" cy="60" r="50" fill="none" stroke="#e5e7eb" strokeWidth="10" />
            <circle
              cx="60" cy="60" r="50" fill="none"
              stroke={getConfidenceColor(confidence_score)}
              strokeWidth="10"
              strokeDasharray={`${(confidence_score / 100) * 314} 314`}
              strokeLinecap="round"
              transform="rotate(-90 60 60)"
            />
          </svg>
          <div className="confidence-text">
            <span className="confidence-number">{Math.round(confidence_score)}</span>
            <span className="confidence-percent">%</span>
          </div>
        </div>
        <div className="confidence-info">
          <span
            className="confidence-label"
            style={{ color: getConfidenceColor(confidence_score) }}
          >
            {getConfidenceLabel(confidence_score)} Confidence
          </span>
          <span className={`validity-badge ${is_valid ? 'valid' : 'invalid'}`}>
            {is_valid ? 'VALID' : 'ISSUES FOUND'}
          </span>
        </div>
      </div>

      {errors.length > 0 && (
        <div className="validation-list">
          <h3>Errors</h3>
          {errors.map((err, i) => (
            <div key={i} className="validation-item error">
              <span className="validation-icon">&#x2716;</span>
              <span className="validation-field">{err.field}:</span>
              <span className="validation-msg">{err.message}</span>
            </div>
          ))}
        </div>
      )}

      {warnings.length > 0 && (
        <div className="validation-list">
          <h3>Warnings</h3>
          {warnings.map((warn, i) => (
            <div key={i} className="validation-item warning">
              <span className="validation-icon">&#x26A0;</span>
              <span className="validation-field">{warn.field}:</span>
              <span className="validation-msg">{warn.message}</span>
            </div>
          ))}
        </div>
      )}

      {notes && <p className="validation-notes">{notes}</p>}
    </div>
  )
}
