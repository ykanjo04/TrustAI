import React from 'react'

export default function ExtractionResults({ data }) {
  if (!data) return null

  const fields = [
    { label: 'Invoice Number', value: data.invoice_number },
    { label: 'Vendor Name', value: data.vendor_name },
    { label: 'Date', value: data.invoice_date },
    { label: 'Currency', value: data.currency },
    { label: 'Vendor TRN', value: data.vendor_trn },
  ]

  const items = data.items || []

  return (
    <div className="results-section">
      <h2>Extracted Data</h2>
      <div className="fields-grid">
        {fields.map((f, i) => (
          <div key={i} className="field-card">
            <span className="field-label">{f.label}</span>
            <span className={`field-value ${!f.value ? 'missing' : ''}`}>
              {f.value || 'Not detected'}
            </span>
          </div>
        ))}
      </div>

      {items.length > 0 && (
        <div className="items-table-container">
          <h3>Line Items</h3>
          <table className="items-table">
            <thead>
              <tr>
                <th>Description</th>
                <th>Qty</th>
                <th>Unit Price</th>
                <th>Amount</th>
              </tr>
            </thead>
            <tbody>
              {items.map((item, i) => (
                <tr key={i}>
                  <td>{item.description || '-'}</td>
                  <td>{item.quantity ?? '-'}</td>
                  <td>{item.unit_price != null ? item.unit_price.toFixed(2) : '-'}</td>
                  <td>{item.amount != null ? item.amount.toFixed(2) : '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
