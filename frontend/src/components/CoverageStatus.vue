<script setup>
import { DangerTriangleIcon } from '@solar-icons/vue/outline/danger-triangle'

defineProps({
  missingProviders: { type: Array, default: () => [] },
  dataStatus: { type: String, default: 'complete' },
})
</script>

<template>
  <div
    v-if="dataStatus !== 'complete' && missingProviders.length"
    class="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-start gap-3"
  >
    <DangerTriangleIcon :size="20" class="text-amber-500 shrink-0 mt-0.5" />
    <div>
      <p class="text-sm font-medium text-amber-800">Incomplete coverage this period</p>
      <p class="text-xs text-amber-600 mt-0.5">
        Missing data from: {{ missingProviders.join(', ') }}.
        <RouterLink to="/integrations" class="underline ml-1">Check integrations</RouterLink>
        or
        <RouterLink to="/imports" class="underline ml-1">upload invoices</RouterLink>.
      </p>
    </div>
  </div>
</template>
