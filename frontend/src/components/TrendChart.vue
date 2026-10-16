<script setup>
import { computed, ref } from 'vue'
const props = defineProps({ months: { type: Array, default: () => [] } })
const selected = ref(null)
const valid = m => m.coverage_status !== 'unavailable' && m.actual_expense != null
const available = computed(() => props.months.filter(valid))
const currency = computed(() => props.months[0]?.currency || 'USD')
const total = computed(() => available.value.reduce((sum, m) => sum + Number(m.actual_expense), 0))
const maximum = computed(() => Math.max(1, ...available.value.map(m => Number(m.actual_expense))) * 1.15)
const active = computed(() => selected.value || available.value.reduce((best, m) => !best || Number(m.actual_expense) > Number(best.actual_expense) ? m : best, null)?.period)
const incomplete = computed(() => props.months.some(m => m.coverage_status !== 'complete'))
const money = value => new Intl.NumberFormat('en-US', { style: 'currency', currency: currency.value }).format(Number(value))
function label(period) {
  const [year, month] = period.split('-').map(Number)
  return new Date(year, month - 1, 1).toLocaleDateString('en-US', { month: 'short' })
}
</script>

<template>
  <section class="glass-panel rounded-2xl p-5 sm:p-6" aria-label="Monthly AI spend chart">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-sm font-medium text-gray-700 dark:text-gray-200">Monthly AI spend</h2>
        <p class="mt-1 text-3xl font-semibold tracking-tight text-gray-900 dark:text-white">{{ available.length ? money(total) : 'No spend data' }}</p>
      </div>
      <span class="rounded-lg bg-gray-50 px-3 py-1.5 text-xs text-gray-600">{{ months.length }} months</span>
    </div>
    <p class="mt-3 text-xs text-gray-500">{{ incomplete ? 'Available spend · coverage incomplete' : 'Total spend for the displayed period' }} · {{ currency }}</p>
    <div v-if="months.length" class="mt-5 overflow-x-auto pb-2">
      <div class="flex min-w-[480px] gap-3">
        <div class="flex h-60 w-10 shrink-0 flex-col justify-between pb-6 pt-9 text-[10px] text-gray-500" aria-hidden="true">
          <span v-for="ratio in [1, .75, .5, .25, 0]" :key="ratio">{{ Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 }).format(maximum * ratio) }}</span>
        </div>
        <div class="relative grid h-60 flex-1 gap-2" :style="{ gridTemplateColumns: `repeat(${months.length}, minmax(0, 1fr))` }">
          <div class="pointer-events-none absolute inset-x-0 bottom-6 top-9 flex flex-col justify-between border-l border-gray-300 dark:border-white/25" aria-hidden="true">
            <div v-for="line in 5" :key="line" class="w-full border-t" :class="line === 5 ? 'border-gray-300 dark:border-white/25' : 'border-gray-200 dark:border-white/15'" />
          </div>
          <div class="pointer-events-none absolute inset-x-0 bottom-6 top-9 grid" :style="{ gridTemplateColumns: `repeat(${months.length}, minmax(0, 1fr))` }" aria-hidden="true">
            <div v-for="month in months" :key="month.period" class="border-r border-dashed border-gray-200 dark:border-white/10" />
          </div>
          <button v-for="month in months" :key="month.period" type="button"
            class="group relative flex min-w-0 flex-col rounded-lg"
            :aria-label="`${month.period}: ${valid(month) ? money(month.actual_expense) : 'unavailable'}; ${month.coverage_status} coverage`"
            :aria-pressed="active === month.period" @click="selected = month.period">
            <div class="relative flex w-full flex-1 items-end pt-9">
              <div v-if="valid(month)" class="relative w-full rounded-t-lg transition-all duration-200"
                :class="active === month.period ? 'bg-gradient-to-t from-lime-200 to-lime-400' : 'bg-gray-100 group-hover:bg-lime-100 dark:bg-white/10'"
                :style="{ height: `${Math.max(2, Number(month.actual_expense) / maximum * 100)}%` }">
                <span v-if="active === month.period" class="absolute -top-8 left-1/2 z-10 -translate-x-1/2 whitespace-nowrap rounded-md bg-gray-900 px-2 py-1 text-[10px] font-medium text-white">{{ money(month.actual_expense) }}</span>
                <span v-if="month.coverage_status === 'partial'" class="absolute bottom-1 left-1/2 size-1.5 -translate-x-1/2 rounded-full bg-amber-600" />
              </div>
              <span v-else class="w-full rounded-lg border border-dashed border-gray-200 py-2 text-[10px] text-gray-500 dark:border-white/20">N/A</span>
            </div>
            <span class="mt-2 text-[10px] text-gray-500">{{ label(month.period) }}</span>
          </button>
        </div>
      </div>
    </div>
    <p v-else class="py-16 text-center text-sm text-gray-500">No trend data available.</p>
    <p v-if="incomplete" class="mt-2 text-xs text-gray-500">N/A means unavailable, not zero. Amber dots indicate partial coverage.</p>
  </section>
</template>
