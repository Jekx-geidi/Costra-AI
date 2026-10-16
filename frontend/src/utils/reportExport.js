export const columns = [
  ['id', 'Record ID'], ['provider', 'Provider'], ['period_start', 'Period start'],
  ['period_end', 'Period end'], ['expense_category', 'Category'], ['financial_basis', 'Basis'],
  ['amount', 'Amount'], ['currency', 'Currency'], ['validation_status', 'Status'], ['description', 'Description'],
]

export function csvCell(value) {
  let text = String(value ?? '')
  // Spreadsheet applications can execute formulas even inside quoted CSV cells.
  if (/^[\s]*[=+@-]/.test(text) || /^[\t\r\n]/.test(text)) text = "'" + text
  return '"' + text.replaceAll('"', '""') + '"'
}

export function createCsv(records) {
  return '\ufeff' + [columns.map(([, title]) => csvCell(title)).join(','),
    ...records.map(row => columns.map(([key]) => csvCell(row[key])).join(',')),
  ].join('\r\n')
}

export async function createPdf(records, metadata, logoBytes) {
  const [{ jsPDF }, { autoTable }] = await Promise.all([import('jspdf'), import('jspdf-autotable')])
  if (!logoBytes) {
    const response = await fetch('/costra-ai-logo.png')
    if (!response.ok) throw new Error('Unable to load the report logo. Please retry.')
    logoBytes = new Uint8Array(await response.arrayBuffer())
  }
  const doc = new jsPDF({ orientation: 'landscape' })
  doc.setFontSize(10)
  doc.text(`Billing report | ${records.length} records | Generated ${metadata.generatedAt}`, 14, 36)
  const filters = Object.entries(metadata.filters).map(([key, value]) => `${key}: ${value || 'All'}`).join(' | ')
  doc.text(doc.splitTextToSize(filters, 265), 14, 43)
  const fields = ['provider', 'period_start', 'expense_category', 'financial_basis', 'amount', 'currency', 'validation_status']
  autoTable(doc, {
    startY: 60, head: [['Provider', 'Period', 'Category', 'Basis', 'Amount', 'Currency', 'Status']],
    body: records.map(row => fields.map(key => String(row[key] ?? '—'))),
    styles: { fontSize: 9, cellPadding: 3 }, headStyles: { fillColor: [32, 50, 12] },
    alternateRowStyles: { fillColor: [246, 249, 240] }, columnStyles: { 4: { halign: 'right' } },
    margin: { top: 34, bottom: 16 },
    willDrawPage: () => {
      doc.addImage(logoBytes, 'PNG', 14, 10, 44, 44 * 748 / 2103, 'costra-logo')
      doc.setFontSize(18)
      doc.setTextColor(23, 33, 27)
      doc.text('Geidi AI Billing Tracker', 66, 21)
    },
    didDrawPage: () => {
      doc.setFontSize(8)
      doc.text(`COSTRA AI | Page ${doc.getNumberOfPages()}`, 14, doc.internal.pageSize.getHeight() - 8)
    },
  })
  return doc
}

export function downloadBlob(content, type, filename) {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.append(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}
