<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { recordsApi } from '../api/billing'

const dialog = ref(null)
const provider = ref('openai')
const period = ref('')
const items = ref([])
const total = ref(0)
const page = ref(1)
const loading = ref(false)
const error = ref('')
const title = computed(() => provider.value === 'anthropic' ? 'Anthropic / Claude invoices' : 'OpenAI invoices')
const pageSize = 20
let requestId = 0
let previousOverflow = ''

async function load() {
  const current = ++requestId
  loading.value = true
  error.value = ''
  items.value = []
  try {
    const { data } = await recordsApi.list({ provider: provider.value, period: period.value,
      ownership_type: 'geidi', financial_basis: 'invoiced', page: page.value, page_size: pageSize })
    if (current !== requestId) return
    items.value = data.items
    total.value = data.total
  } catch (e) {
    if (current !== requestId) return
    error.value = typeof e.response?.data?.detail === 'string' ? e.response.data.detail : 'Unable to load invoices. Please try again.'
  } finally { if (current === requestId) loading.value = false }
}

function open(name, month) {
  provider.value = name
  period.value = month
  page.value = 1
  total.value = 0
  previousOverflow = document.body.style.overflow
  dialog.value.showModal()
  document.body.style.overflow = 'hidden'
  load()
}
function close() {
  ++requestId
  dialog.value?.close()
  document.body.style.overflow = previousOverflow
}
function changePage(direction) {
  if (loading.value) return
  page.value += direction
  load()
}
onBeforeUnmount(() => { if (dialog.value?.open) close(); ++requestId })
defineExpose({ open })
</script>

<template>
  <dialog ref="dialog" aria-labelledby="provider-invoices-title" @cancel="close" @close="close"
    @click="event => { if (event.target === dialog) close() }"
    class="m-auto max-h-[90dvh] w-[calc(100%_-_2rem)] max-w-3xl overflow-y-auto rounded-2xl border border-gray-200 bg-white p-0 text-gray-900 shadow-2xl backdrop:bg-black/60 dark:border-white/15 dark:bg-[#152019] dark:text-white">
    <header class="flex items-start justify-between gap-4 border-b border-gray-200 p-5">
      <div><h2 id="provider-invoices-title" class="text-lg font-semibold">{{ title }}</h2><p class="mt-1 text-xs text-gray-500">{{ period }} · Geidi accounts · Invoiced line items</p></div>
      <button type="button" @click="close" aria-label="Close invoices" class="grid size-10 shrink-0 place-items-center rounded-lg hover:bg-gray-100 dark:hover:bg-white/10">✕</button>
    </header>
    <div class="p-5">
      <p class="mb-4 text-xs text-gray-500">Each row is an invoiced billing entry. One invoice may contain multiple entries. Usage-only records are excluded.</p>
      <p v-if="loading" role="status" class="py-10 text-center text-sm text-gray-500">Loading invoices…</p>
      <div v-else-if="error" role="alert" class="py-6 text-sm text-red-700 dark:text-red-300">{{ error }} <button @click="load" class="ml-2 underline">Retry</button></div>
      <p v-else-if="!items.length" class="py-10 text-center text-sm text-gray-500">No invoiced records for this provider in {{ period }}.</p>
      <div v-else class="overflow-x-auto">
        <table class="w-full min-w-[540px] text-left text-sm">
          <thead class="border-b border-gray-200 bg-gray-50 text-xs text-gray-600"><tr><th class="p-3">Description / reference</th><th class="p-3">Period</th><th class="p-3">Amount</th><th class="p-3">Status</th></tr></thead>
          <tbody><tr v-for="item in items" :key="item.id" class="border-b border-gray-100">
            <td class="max-w-xs break-words p-3"><p>{{ item.description || item.expense_category }}</p><p v-if="item.external_record_id" class="mt-1 text-xs text-gray-500">{{ item.external_record_id }}</p></td>
            <td class="whitespace-nowrap p-3 text-xs">{{ item.period_start || '—' }}<span v-if="item.period_end" class="block text-gray-500">to {{ item.period_end }}</span></td>
            <td class="whitespace-nowrap p-3 font-semibold">{{ item.amount }} {{ item.currency }}</td>
            <td class="p-3"><span class="rounded-md bg-gray-100 px-2 py-1 text-xs capitalize text-gray-700 dark:text-gray-100">{{ item.validation_status }}</span></td>
          </tr></tbody>
        </table>
      </div>
    </div>
    <footer class="flex flex-wrap items-center justify-between gap-3 border-t border-gray-200 px-5 py-4 text-xs text-gray-600">
      <span>{{ total }} invoiced entries</span>
      <div class="flex items-center gap-3"><button @click="changePage(-1)" :disabled="loading || page <= 1" class="rounded-lg border border-gray-300 px-3 py-2 disabled:opacity-40">Previous</button><span>Page {{ page }}</span><button @click="changePage(1)" :disabled="loading || page * pageSize >= total" class="rounded-lg border border-gray-300 px-3 py-2 disabled:opacity-40">Next</button></div>
    </footer>
  </dialog>
</template>
