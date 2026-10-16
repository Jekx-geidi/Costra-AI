<script setup>
import { computed, ref } from 'vue'

const props = defineProps({ summary: { type: Object, default: null }, loading: Boolean })
const hovered = ref(null)
const colors = ['#bef264', '#a78bfa', '#60a5fa', '#fbbf24']
const names = { openai: 'OpenAI', anthropic: 'Claude / Anthropic' }
const providers = computed(() => {
  const values = props.summary?.providers || { openai: null, anthropic: null }
  return Object.entries(values).filter(([key]) => key !== 'currency').map(([key, value], i) => ({
    key, name: names[key] || key, cost: value == null ? null : Number(value), color: colors[i % colors.length],
  }))
})
const total = computed(() => providers.value.reduce((sum, p) => sum + Math.max(0, p.cost || 0), 0))
const segments = computed(() => {
  let offset = 0
  return providers.value.filter(p => p.cost > 0).map(p => {
    const length = p.cost / total.value * 100
    const segment = { ...p, length, offset }
    offset += length
    return segment
  })
})
const active = computed(() => providers.value.find(p => p.key === hovered.value))
const currency = computed(() => props.summary?.currency || 'USD')
const money = value => value == null ? 'Unavailable' : new Intl.NumberFormat('en-US', { style: 'currency', currency: currency.value }).format(value)
</script>

<template>
  <section class="glass-panel rounded-xl p-5" aria-label="AI spend by provider">
    <h2 class="text-sm font-semibold text-gray-900 dark:text-white">Spend by AI provider</h2>
    <p class="mt-1 text-xs text-gray-500">{{ summary?.period || 'Selected period' }} · {{ currency }}</p>
    <div class="relative mx-auto my-5 aspect-square w-full max-w-[240px]">
      <svg viewBox="0 0 120 120" class="h-full w-full overflow-visible" role="group" aria-label="Provider cost distribution">
        <circle cx="60" cy="60" r="46" fill="none" class="stroke-gray-200 dark:stroke-white/10" stroke-width="14" />
        <circle v-for="provider in segments" :key="provider.key" cx="60" cy="60" r="46" fill="none"
          :stroke="provider.color" :stroke-width="hovered === provider.key ? 17 : 14" pathLength="100"
          :stroke-dasharray="`${provider.length} ${100 - provider.length}`" :stroke-dashoffset="-provider.offset"
          transform="rotate(-90 60 60)" tabindex="0" role="img"
          :aria-label="`${provider.name}: ${money(provider.cost)}`" class="cursor-pointer transition-[stroke-width] focus:outline-none"
          @mouseenter="hovered = provider.key" @mouseleave="hovered = null" @focus="hovered = provider.key" @blur="hovered = null">
          <title>{{ provider.name }}: {{ money(provider.cost) }}</title>
        </circle>
      </svg>
      <div class="pointer-events-none absolute inset-0 flex flex-col items-center justify-center px-10 text-center" aria-live="polite">
        <span class="text-xs text-gray-500">{{ active?.name || 'Provider total' }}</span>
        <span class="mt-1 break-all text-lg font-semibold text-gray-900 dark:text-white">{{ loading ? 'Loading…' : active ? money(active.cost) : total > 0 ? money(total) : 'No spend' }}</span>
      </div>
    </div>
    <ul class="space-y-2">
      <li v-for="provider in providers" :key="provider.key">
        <button type="button" class="flex w-full items-center gap-2 rounded-lg px-1 py-1.5 text-left text-xs hover:bg-black/[0.04] dark:hover:bg-white/5"
          @mouseenter="hovered = provider.key" @mouseleave="hovered = null" @focus="hovered = provider.key" @blur="hovered = null" @click="hovered = provider.key">
          <span class="size-2.5 shrink-0 rounded-full" :style="{ backgroundColor: provider.color }" />
          <span class="text-gray-700 dark:text-gray-200">{{ provider.name }}</span>
          <span class="ml-auto font-medium text-gray-900 dark:text-white">{{ money(provider.cost) }}</span>
        </button>
      </li>
    </ul>
    <p v-if="summary?.data_status !== 'complete'" class="mt-3 text-xs text-gray-500">Coverage incomplete. Unavailable providers are excluded from the donut.</p>
  </section>
</template>
