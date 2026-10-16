<script setup>
import { computed, reactive, ref } from 'vue'
import { recordsApi } from '../api/billing'
import { createCsv, createPdf, downloadBlob } from '../utils/reportExport'

const filters = reactive({ period: '', provider: '', expense_category: '', validation_status: '', ownership_type: 'geidi' })
const records = ref([])
const metadata = ref(null)
const loading = ref(false)
const exporting = ref(false)
const progress = ref('')
const error = ref('')
const notice = ref('')
const stale = computed(() => metadata.value && JSON.stringify(metadata.value.filters) !== JSON.stringify(filters))
const ready = computed(() => metadata.value && !stale.value && records.value.length && !loading.value && !exporting.value)

async function generate() {
  loading.value = true
  error.value = ''
  notice.value = ''
  progress.value = ''
  metadata.value = null
  records.value = []
  const applied = { ...filters }
  const params = Object.fromEntries(Object.entries(applied).filter(([, value]) => value))
  try {
    const rows = []
    const ids = new Set()
    let expected = null
    for (let page = 1; ; page++) {
      const { data } = await recordsApi.list({ ...params, page, page_size: 200 })
      if (expected == null) expected = data.total
      if (data.total !== expected) throw new Error('Records changed while loading. Generate the report again.')
      for (const row of data.items) {
        if (ids.has(row.id)) throw new Error('Records changed while loading. Generate the report again.')
        ids.add(row.id)
        rows.push(row)
      }
      progress.value = `${rows.length} of ${expected} records loaded`
      if (rows.length === expected) break
      if (!data.items.length || rows.length > expected) throw new Error('The report could not be loaded completely. Please retry.')
    }
    records.value = rows
    metadata.value = { filters: applied, generatedAt: new Date().toISOString() }
    notice.value = rows.length ? `${rows.length} records ready to download.` : 'No records match these filters.'
  } catch (e) {
    error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : e.message || 'Unable to generate report.'
  } finally { loading.value = false }
}

async function download(format) {
  if (!ready.value) return
  exporting.value = true
  error.value = ''
  const filename = `costra-billing-${metadata.value.filters.period || 'all-periods'}`
  try {
    if (format === 'csv') downloadBlob(createCsv(records.value), 'text/csv;charset=utf-8', `${filename}.csv`)
    else if (format === 'json') downloadBlob(JSON.stringify({ ...metadata.value, records: records.value }, null, 2), 'application/json', `${filename}.json`)
    else (await createPdf(records.value, metadata.value)).save(`${filename}.pdf`)
    notice.value = `${format.toUpperCase()} download started.`
  } catch { error.value = 'Download failed. Please try again.' }
  finally { exporting.value = false }
}
</script>

<template>
  <div class="space-y-5">
    <div><h1 class="text-xl font-semibold text-gray-900 dark:text-white">Reports</h1><p class="mt-1 text-sm text-gray-500">Download billing records for finance reviews and your own analysis.</p></div>
    <form @submit.prevent="generate" class="glass-panel rounded-xl p-5">
      <fieldset :disabled="loading || exporting" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <label class="text-xs font-medium text-gray-700 dark:text-gray-200">Month <input v-model="filters.period" type="month" class="soft-input mt-2 block w-full" /><span class="mt-1 block text-gray-500">Leave blank for all periods.</span></label>
        <label class="text-xs font-medium text-gray-700 dark:text-gray-200">Provider<select v-model="filters.provider" class="soft-input mt-2 block w-full"><option value="">All providers</option><option value="openai">OpenAI</option><option value="anthropic">Claude / Anthropic</option></select></label>
        <label class="text-xs font-medium text-gray-700 dark:text-gray-200">Category<select v-model="filters.expense_category" class="soft-input mt-2 block w-full"><option value="">All categories</option><option v-for="category in ['subscription', 'seat', 'api', 'credit', 'adjustment']" :key="category" :value="category">{{ category }}</option></select></label>
        <label class="text-xs font-medium text-gray-700 dark:text-gray-200">Status<select v-model="filters.validation_status" class="soft-input mt-2 block w-full"><option value="">All statuses</option><option v-for="status in ['pending', 'verified', 'disputed']" :key="status" :value="status">{{ status }}</option></select></label>
        <label class="text-xs font-medium text-gray-700 dark:text-gray-200">Ownership<select v-model="filters.ownership_type" class="soft-input mt-2 block w-full"><option value="geidi">Geidi</option><option value="personal">Personal</option></select></label>
        <div class="flex items-end"><button type="submit" class="w-full rounded-lg bg-lime-300 px-4 py-2.5 text-sm font-semibold text-lime-950 hover:bg-lime-200 disabled:opacity-50">{{ loading ? 'Generating…' : 'Generate report' }}</button></div>
      </fieldset>
    </form>
    <p v-if="loading" role="status" class="text-sm text-gray-500">{{ progress || 'Loading records…' }}</p>
    <p v-if="error" role="alert" class="text-sm text-red-700 dark:text-red-300">{{ error }}</p>
    <p v-if="stale" role="status" class="text-sm text-amber-700 dark:text-amber-300">Filters changed. Generate the report again before downloading.</p>
    <p v-else-if="notice" role="status" class="text-sm text-gray-600">{{ notice }}</p>
    <section class="glass-panel rounded-xl p-5">
      <div class="flex flex-wrap items-center justify-between gap-4">
        <div><h2 class="text-sm font-semibold text-gray-900 dark:text-white">Billing report preview</h2><p class="mt-1 text-xs text-gray-500">{{ metadata ? `${records.length} matching records. Preview shows the first 50; downloads include all records.` : 'Generate a report to preview and download your data.' }}</p></div>
        <div class="flex flex-wrap gap-2"><button v-for="format in ['pdf', 'csv', 'json']" :key="format" type="button" :disabled="!ready" @click="download(format)" class="rounded-lg border border-gray-300 px-3 py-2 text-xs font-semibold uppercase text-gray-800 hover:bg-lime-50 disabled:cursor-not-allowed disabled:opacity-40 dark:text-white dark:hover:bg-white/10">Download {{ format }}</button></div>
      </div>
      <div v-if="records.length" class="mt-5 overflow-x-auto">
        <table class="w-full text-left text-sm"><thead class="border-b border-gray-200 text-xs text-gray-500"><tr><th v-for="heading in ['Provider', 'Period', 'Category', 'Basis', 'Amount', 'Status']" :key="heading" class="px-3 py-3">{{ heading }}</th></tr></thead>
          <tbody class="text-gray-800 dark:text-gray-100"><tr v-for="row in records.slice(0, 50)" :key="row.id" class="border-b border-gray-100"><td class="px-3 py-3">{{ row.provider }}</td><td class="whitespace-nowrap px-3 py-3">{{ row.period_start || '—' }}</td><td class="px-3 py-3">{{ row.expense_category }}</td><td class="px-3 py-3">{{ row.financial_basis }}</td><td class="whitespace-nowrap px-3 py-3 font-mono">{{ row.amount }} {{ row.currency }}</td><td class="px-3 py-3">{{ row.validation_status }}</td></tr></tbody>
        </table>
      </div>
    </section>
  </div>
</template>
