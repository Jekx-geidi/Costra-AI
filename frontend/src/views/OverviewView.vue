<script setup>
import { onMounted, watch } from 'vue'
import { useReportingStore } from '../stores/reporting'
import SummaryCards from '../components/SummaryCards.vue'
import TrendChart from '../components/TrendChart.vue'
import CoverageStatus from '../components/CoverageStatus.vue'
import ProviderSpend from '../components/ProviderSpend.vue'

const reporting = useReportingStore()

onMounted(async () => {
  await Promise.all([reporting.fetchSummary(), reporting.fetchTrends(12)])
})

async function onPeriodChange(e) {
  await reporting.fetchSummary(e.target.value)
}
</script>

<template>
  <div class="space-y-5">
    <div class="flex flex-wrap items-end justify-between gap-3">
      <div><p class="text-xs font-medium uppercase tracking-[0.14em] text-lime-700 dark:text-lime-300">Spend overview</p><h1 class="mt-1 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Good day, {{ reporting.selectedPeriod || 'team' }}</h1><p class="mt-1 text-sm text-gray-500 dark:text-gray-400">Keep an eye on your AI costs and coverage.</p></div>
      <input
        type="month"
        :value="reporting.selectedPeriod"
        @change="onPeriodChange"
        class="soft-input"
      />
    </div>

    <CoverageStatus
      :data-status="reporting.summary?.data_status"
      :missing-providers="reporting.summary?.missing_providers || []"
    />

    <div class="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_280px] gap-5">
      <div class="space-y-5 min-w-0">
        <SummaryCards :summary="reporting.summary" :loading="reporting.loadingSummary" />
        <TrendChart :months="reporting.trends" />
      </div>
      <aside class="space-y-5 self-start">
        <div class="glass-panel rounded-xl p-5">
        <p class="text-xs font-semibold uppercase tracking-[0.15em] text-gray-400">Quick actions</p>
        <p class="mt-2 text-sm text-gray-600 dark:text-gray-300">Manage the sources behind this month’s spend.</p>
        <div class="mt-5 grid grid-cols-2 gap-2">
          <RouterLink to="/imports" class="rounded-lg bg-lime-300 px-3 py-3 text-center text-xs font-semibold text-lime-950 hover:bg-lime-200">Import invoice</RouterLink>
          <RouterLink to="/integrations" class="rounded-lg border border-[#e1e5df] bg-white px-3 py-3 text-center text-xs font-semibold text-gray-700 hover:bg-[#f6f7f4] dark:border-white/10 dark:bg-white/[0.08] dark:text-gray-100">Connections</RouterLink>
        </div>
        <div class="mt-6 border-t border-black/[0.06] pt-5 dark:border-white/10"><p class="text-xs font-semibold uppercase tracking-[0.15em] text-gray-400">Coverage</p><p class="mt-2 text-2xl font-semibold text-gray-900 dark:text-white">{{ reporting.summary?.data_status || 'Loading' }}</p><p class="mt-1 text-xs text-gray-500 dark:text-gray-400">Data availability for the selected period.</p></div>
        </div>
        <ProviderSpend :summary="reporting.summary" :loading="reporting.loadingSummary" />
      </aside>
    </div>

    <p v-if="reporting.error" class="text-sm text-red-600">{{ reporting.error }}</p>
  </div>
</template>
