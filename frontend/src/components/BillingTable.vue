<script setup>
import { ref } from 'vue'
import { CloseCircleIcon } from '@solar-icons/vue/outline/close-circle'
import { AltArrowLeftIcon } from '@solar-icons/vue/outline/alt-arrow-left'
import { AltArrowRightIcon } from '@solar-icons/vue/outline/alt-arrow-right'
import { ArrowRightIcon } from '@solar-icons/vue/outline/arrow-right'
import { useRecordsStore } from '../stores/records'

const records = useRecordsStore()
const selected = ref(null)

const statusColor = {
  pending: 'bg-amber-100 text-amber-700',
  verified: 'bg-green-100 text-green-700',
  disputed: 'bg-red-100 text-red-700',
}
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
    <div v-if="records.loading" class="p-8 text-center text-sm text-gray-400">Loading records…</div>
    <div v-else-if="!records.items.length" class="p-8 text-center text-sm text-gray-400">
      No billing records match the current filters.
    </div>
    <div v-else class="flex">
      <div class="flex-1 overflow-x-auto">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b border-gray-200">
            <tr>
              <th class="th">Provider</th>
              <th class="th">Period</th>
              <th class="th">Category</th>
              <th class="th">Basis</th>
              <th class="th text-right">Amount</th>
              <th class="th">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="row in records.items"
              :key="row.id"
              @click="selected = row"
              class="border-b border-gray-100 hover:bg-gray-50 cursor-pointer"
              :class="{ 'bg-brand-50': selected?.id === row.id }"
            >
              <td class="td font-medium capitalize">{{ row.provider }}</td>
              <td class="td text-gray-500">{{ row.period_start || '—' }}</td>
              <td class="td capitalize">{{ row.expense_category }}</td>
              <td class="td capitalize">{{ row.financial_basis }}</td>
              <td class="td text-right font-mono">{{ parseFloat(row.amount).toFixed(2) }} {{ row.currency }}</td>
              <td class="td">
                <span class="px-2 py-0.5 rounded text-xs font-medium" :class="statusColor[row.validation_status] || 'bg-gray-100 text-gray-600'">
                  {{ row.validation_status }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <aside v-if="selected" class="w-64 border-l border-gray-200 p-4 text-xs text-gray-600 space-y-2 shrink-0">
        <div class="flex justify-between items-center mb-2">
          <span class="font-medium text-gray-800 text-sm">Record detail</span>
          <button @click="selected = null" class="text-gray-400 hover:text-gray-600" aria-label="Close detail">
            <CloseCircleIcon :size="18" />
          </button>
        </div>
        <div><span class="text-gray-400">ID</span><br><span class="font-mono break-all">{{ selected.id }}</span></div>
        <div><span class="text-gray-400">Source</span><br>{{ selected.source_id || '—' }}</div>
        <div><span class="text-gray-400">Description</span><br>{{ selected.description || '—' }}</div>
        <div><span class="text-gray-400">Period</span><br><span class="inline-flex items-center gap-1">{{ selected.period_start }} <ArrowRightIcon :size="12" /> {{ selected.period_end }}</span></div>
        <div><span class="text-gray-400">Amount</span><br>{{ selected.amount }} {{ selected.currency }}</div>
        <div><span class="text-gray-400">Financial basis</span><br>{{ selected.financial_basis }}</div>
        <div><span class="text-gray-400">Validation</span><br>{{ selected.validation_status }}</div>
      </aside>
    </div>

    <div class="flex items-center justify-between px-4 py-3 border-t border-gray-100 text-sm text-gray-500">
      <span>{{ records.total }} total records</span>
      <div class="flex items-center gap-2">
        <button @click="records.prevPage(); records.fetchRecords()" :disabled="records.filters.page <= 1" class="px-2 py-1 rounded border disabled:opacity-40" aria-label="Previous page"><AltArrowLeftIcon :size="16" /></button>
        <span>Page {{ records.filters.page }}</span>
        <button @click="records.nextPage(); records.fetchRecords()" :disabled="records.items.length < records.filters.page_size" class="px-2 py-1 rounded border disabled:opacity-40" aria-label="Next page"><AltArrowRightIcon :size="16" /></button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.th { @apply px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider; }
.td { @apply px-4 py-3 text-gray-700; }
</style>
