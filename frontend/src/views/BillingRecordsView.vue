<script setup>
import { onMounted } from 'vue'
import { useRecordsStore } from '../stores/records'
import FilterBar from '../components/FilterBar.vue'
import BillingTable from '../components/BillingTable.vue'

const records = useRecordsStore()
onMounted(() => records.fetchRecords())
</script>

<template>
  <div class="space-y-4">
    <h1 class="text-lg font-semibold text-gray-900">Billing Records</h1>
    <FilterBar />
    <BillingTable />
  </div>
</template>
