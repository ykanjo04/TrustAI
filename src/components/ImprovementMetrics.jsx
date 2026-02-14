import React from 'react'

export default function ImprovementMetrics({ metrics, metricsHistory }) {
  if (!metrics) return null

  const { confidence_before, confidence_after, improvement_delta, fields_improved, strategy_changes } = metrics
  const improved = improvement_delta > 0

  return (
    <div className="metrics-section">
      <h2>Self-Improvement Metrics</h2>

      <div className="improvement-card">
        <div className="improvement-header">
          <span className={`improvement-badge ${improved ? 'improved' : 'unchanged'}`}>
            {improved ? 'IMPROVED' : 'NO CHANGE NEEDED'}
          </span>
        </div>

        <div className="metrics-grid">
          <div className="metric-box">
            <span className="metric-label">Before Reflection</span>
            <span className="metric-value">{confidence_before.toFixed(1)}%</span>
          </div>
          <div className="metric-box arrow-box">
            <span className={`arrow ${improved ? 'up' : 'neutral'}`}>
              {improved ? '\u2192' : '\u2014'}
            </span>
          </div>
          <div className="metric-box">
            <span className="metric-label">After Reflection</span>
            <span className="metric-value highlight">{confidence_after.toFixed(1)}%</span>
          </div>
          <div className="metric-box">
            <span className="metric-label">Delta</span>
            <span className={`metric-value ${improved ? 'positive' : ''}`}>
              {improved ? '+' : ''}{improvement_delta.toFixed(1)}%
            </span>
          </div>
        </div>

        {fields_improved.length > 0 && (
          <div className="fields-improved">
            <h4>Fields Recovered</h4>
            <div className="field-tags">
              {fields_improved.map((f, i) => (
                <span key={i} className="field-tag">{f}</span>
              ))}
            </div>
          </div>
        )}

        {strategy_changes.length > 0 && (
          <div className="strategy-changes">
            <h4>Strategy Updates</h4>
            <ul>
              {strategy_changes.map((s, i) => (
                <li key={i}>{s}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {metricsHistory && metricsHistory.total_extractions > 0 && (
        <div className="history-summary">
          <h3>Cumulative Performance</h3>
          <div className="history-grid">
            <div className="history-stat">
              <span className="stat-number">{metricsHistory.total_extractions}</span>
              <span className="stat-label">Total Extractions</span>
            </div>
            <div className="history-stat">
              <span className="stat-number">{metricsHistory.average_confidence.toFixed(1)}%</span>
              <span className="stat-label">Avg Confidence</span>
            </div>
            <div className="history-stat">
              <span className="stat-number">+{metricsHistory.average_improvement.toFixed(1)}%</span>
              <span className="stat-label">Avg Improvement</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
