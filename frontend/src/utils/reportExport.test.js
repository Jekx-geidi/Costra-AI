import { test } from 'node:test'
import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { createCsv, csvCell, createPdf } from './reportExport.js'

test('CSV escapes quotes, commas, multiline descriptions and spreadsheet formulas', () => {
  assert.equal(csvCell('a,"b"\nc'), '"a,""b""\nc"')
  assert.equal(csvCell(' =SUM(A1)'), '"\' =SUM(A1)"')
  const csv = createCsv([{ id: '1', amount: '12.340000', description: '=HYPERLINK("bad")' }])
  assert.ok(csv.startsWith('\ufeff"Record ID"'))
  assert.ok(csv.includes('"12.340000"'))
  assert.ok(csv.includes('"\'=HYPERLINK(""bad"")"'))
})

test('PDF includes all records across multiple pages and returns a valid PDF', async () => {
  const records = Array.from({ length: 220 }, (_, i) => ({ provider: i === 219 ? 'LAST-RECORD' : 'openai', period_start: '2026-10-01', amount: '12.340000', currency: 'USD', expense_category: 'api', financial_basis: 'invoiced', validation_status: 'verified' }))
  const logo = new Uint8Array(await readFile(new URL('../../public/costra-ai-logo.png', import.meta.url)))
  const doc = await createPdf(records, { generatedAt: '2026-10-16T04:00:00.000Z', filters: { provider: '', ownership_type: 'geidi' } }, logo)
  const pdf = doc.output()
  assert.ok(pdf.startsWith('%PDF-'))
  assert.ok(doc.getNumberOfPages() > 1)
  assert.ok(pdf.includes('LAST-RECORD'))
  assert.ok(pdf.includes('12.340000'))
  assert.ok(pdf.includes('/Subtype /Image'))
  assert.equal(pdf.match(/\/I0 Do/g)?.length, doc.getNumberOfPages())
})
