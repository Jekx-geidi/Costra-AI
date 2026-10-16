<script setup>
import { useRecordsStore } from '../stores/records'

const records = useRecordsStore()

function update(key, e) {
  records.setFilter(key, e.target.value)
  records.fetchRecords()
}
</script>

<template>
  <div class="flex flex-wrap gap-3">
    <select @change="update('provider', $event)" class="select-sm">
      <option value="">All providers</option>
      <option value="openai">OpenAI</option>
      <option value="anthropic">Anthropic</option>
    </select>
    <input
      type="month"
      :value="records.filters.period"
      @change="update('period', $event)"
      placeholder="Period"
      class="select-sm"
    />
    <select @change="update('expense_category', $event)" class="select-sm">
      <option value="">All categories</option>
      <option value="subscription">Subscription</option>
      <option value="seat">Seat</option>
      <option value="api">API</option>
      <option value="credit">Credit</option>
      <option value="adjustment">Adjustment</option>
    </select>
    <select @change="update('financial_basis', $event)" class="select-sm">
      <option value="">All bases</option>
      <option value="invoiced">Invoiced</option>
      <option value="usage">Usage</option>
      <option value="payment">Payment</option>
      <option value="credit">Credit</option>
    </select>
    <select @change="update('ownership_type', $event)" class="select-sm">
      <option value="geidi">Geidi only</option>
      <option value="personal">Personal</option>
      <option value="">All</option>
    </select>
    <select @change="update('validation_status', $event)" class="select-sm">
      <option value="">All statuses</option>
      <option value="pending">Pending</option>
      <option value="verified">Verified</option>
      <option value="disputed">Disputed</option>
    </select>
  </div>
</template>

<style scoped>
.select-sm {
  @apply border border-gray-300 rounded-md px-2 py-1.5 text-sm text-gray-900 focus:outline-none focus:ring-2 focus:ring-lime-400 bg-white;
}

:global(html[data-theme="dark"]) .select-sm {
  background-color: #1d2920;
  color: #f1f5f1;
  border-color: #48544b;
  color-scheme: dark;
}
</style>
