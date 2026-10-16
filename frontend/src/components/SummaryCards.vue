<script setup>
defineProps({
  summary: { type: Object, default: null },
  loading: { type: Boolean, default: false },
})

function fmt(val, currency = 'USD') {
  if (val == null) return '—'
  return `${parseFloat(val).toFixed(2)} ${currency}`
}
</script>

<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
    <template v-if="loading">
      <div v-for="i in 6" :key="i" class="metric-card animate-pulse h-28" />
    </template>
    <template v-else-if="summary">
      <div class="metric-card spend-highlight sm:col-span-2 lg:col-span-1">
        <p class="text-xs text-lime-100 mb-2">Total AI Spend</p>
        <p class="text-2xl font-semibold tracking-tight text-white">{{ fmt(summary.actual_expense, summary.currency) }}</p>
        <p class="inline-flex rounded-md border px-2 py-0.5 text-xs mt-2" :class="summary.data_status === 'complete' ? 'border-lime-200/30 bg-black/20 text-lime-200' : 'border-amber-200/30 bg-black/30 text-amber-200'">
          {{ summary.data_status }}
        </p>
      </div>
      <div class="metric-card"><p class="text-xs text-gray-500 dark:text-gray-400 mb-2">OpenAI</p><p class="text-xl font-semibold tracking-tight text-gray-900 dark:text-white">{{ fmt(summary.providers?.openai, summary.currency) }}</p>
      </div>
      <div class="metric-card"><p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Anthropic</p><p class="text-xl font-semibold tracking-tight text-gray-900 dark:text-white">{{ fmt(summary.providers?.anthropic, summary.currency) }}</p>
      </div>
      <div class="metric-card"><p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Subscriptions</p><p class="text-xl font-semibold text-gray-900 dark:text-white">{{ fmt(summary.subscription_cost, summary.currency) }}</p>
      </div>
      <div class="metric-card"><p class="text-xs text-gray-500 dark:text-gray-400 mb-2">API Consumption</p><p class="text-xl font-semibold text-gray-900 dark:text-white">{{ fmt(summary.api_consumption_cost, summary.currency) }}</p>
      </div>
      <div class="metric-card"><p class="text-xs text-gray-500 dark:text-gray-400 mb-2">Unreconciled</p><p class="text-xl font-semibold" :class="summary.unreconciled_records > 0 ? 'text-amber-600' : 'text-gray-900 dark:text-white'">
          {{ summary.unreconciled_records }} records
        </p>
      </div>
    </template>
  </div>
</template>

<style scoped>
.metric-card.spend-highlight {
  background: linear-gradient(130deg, #4d7c0f 0%, #2b4614 48%, #101c10 100%);
  border-color: rgb(190 242 100 / 40%);
  box-shadow: 0 8px 24px rgb(34 55 14 / 18%);
}
.metric-card.spend-highlight:hover {
  border-color: #bef264;
}
</style>
