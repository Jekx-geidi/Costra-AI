<script setup>
import { ref, onMounted } from 'vue'
import { reconciliationApi } from '../api/billing'

const items = ref([])
const loading = ref(false)
const activeTab = ref('unmatched')
const actionLoading = ref({})

onMounted(() => fetchItems())

async function fetchItems() {
  loading.value = true
  try {
    const res = await reconciliationApi.list(
      activeTab.value !== 'all' ? { reconciliation_status: activeTab.value } : {}
    )
    items.value = res.data
  } finally {
    loading.value = false
  }
}

async function doAction(billingRecordId, action) {
  actionLoading.value[billingRecordId] = true
  try {
    await reconciliationApi.review(billingRecordId, { action })
    await fetchItems()
  } finally {
    actionLoading.value[billingRecordId] = false
  }
}

const tabColor = {
  matched: 'border-green-500 text-green-700',
  unmatched: 'border-red-400 text-red-600',
  partial: 'border-amber-400 text-amber-600',
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-lg font-semibold text-gray-900">Reconciliation</h1>

    <div class="flex gap-1 border-b border-gray-200">
      <button
        v-for="tab in ['unmatched', 'partial', 'matched', 'all']"
        :key="tab"
        @click="activeTab = tab; fetchItems()"
        class="px-4 py-2 text-sm capitalize border-b-2 -mb-px transition-colors"
        :class="activeTab === tab ? 'border-brand-500 text-brand-700 font-medium' : 'border-transparent text-gray-500 hover:text-gray-700'"
      >
        {{ tab }}
      </button>
    </div>

    <div v-if="loading" class="text-sm text-gray-400 text-center py-8">Loading…</div>
    <div v-else-if="!items.length" class="text-sm text-gray-400 text-center py-8">No items in this category.</div>
    <div v-else class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <table class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="th">Reference</th>
            <th class="th">Expected</th>
            <th class="th">Observed</th>
            <th class="th">Variance</th>
            <th class="th">Status</th>
            <th class="th">Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in items" :key="item.id" class="border-t border-gray-100">
            <td class="td text-xs font-mono">{{ item.financial_reference || '—' }}</td>
            <td class="td font-mono">{{ parseFloat(item.expected_amount).toFixed(2) }}</td>
            <td class="td font-mono">{{ parseFloat(item.observed_amount).toFixed(2) }}</td>
            <td class="td font-mono" :class="parseFloat(item.variance) !== 0 ? 'text-amber-600' : 'text-green-600'">
              {{ parseFloat(item.variance).toFixed(2) }}
            </td>
            <td class="td capitalize text-xs">
              <span
                class="px-2 py-0.5 rounded font-medium"
                :class="{
                  'bg-green-100 text-green-700': item.reconciliation_status === 'matched',
                  'bg-amber-100 text-amber-700': item.reconciliation_status === 'partial',
                  'bg-red-100 text-red-600': item.reconciliation_status === 'unmatched',
                }"
              >{{ item.reconciliation_status }}</span>
            </td>
            <td class="td">
              <span
                v-if="item.reviewed_at"
                class="px-2 py-0.5 rounded text-xs font-medium capitalize"
                :class="item.record_validation_status === 'disputed' ? 'bg-red-100 text-red-600' : 'bg-green-100 text-green-700'"
                :title="`Reviewed ${new Date(item.reviewed_at).toLocaleString()}`"
              >{{ item.record_validation_status === 'disputed' ? 'Disputed' : 'Verified' }}</span>
              <div v-else class="flex gap-2">
                <button
                  @click="doAction(item.billing_record_id, 'approve')"
                  :disabled="actionLoading[item.billing_record_id]"
                  class="text-xs px-2 py-1 bg-green-50 text-green-700 rounded hover:bg-green-100 disabled:opacity-40"
                >Approve</button>
                <button
                  @click="doAction(item.billing_record_id, 'dispute')"
                  :disabled="actionLoading[item.billing_record_id]"
                  class="text-xs px-2 py-1 bg-red-50 text-red-600 rounded hover:bg-red-100 disabled:opacity-40"
                >Dispute</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.th { @apply px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider; }
.td { @apply px-4 py-3 text-gray-700; }
</style>
