import React from 'react'

export default function TaxBreakdown({ data }) {
  if (!data) return null

  const currency = data.currency || 'AED'
  const fmt = (val) => {
    if (val == null) return 'N/A'
    return `${currency} ${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  }

  const vatRate = data.subtotal && data.vat_amount
    ? ((data.vat_amount / data.subtotal) * 100).toFixed(1)
    : '5.0'

  return (
    <div className="tax-breakdown-section">
      <h2>Tax Breakdown</h2>
      <div className="tax-card">
        <div className="tax-row">
          <span className="tax-label">Subtotal (before VAT)</span>
          <span className="tax-value">{fmt(data.subtotal)}</span>
        </div>
        <div className="tax-row vat-row">
          <span className="tax-label">
            VAT ({vatRate}%)
            <span className="uae-badge">UAE VAT</span>
          </span>
          <span className="tax-value vat-amount">{fmt(data.vat_amount)}</span>
        </div>
        <div className="tax-divider"></div>
        <div className="tax-row total-row">
          <span className="tax-label">Total (incl. VAT)</span>
          <span className="tax-value total-value">{fmt(data.total)}</span>
        </div>
      </div>
    </div>
  )
}
