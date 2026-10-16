<script setup>
import { ref, onMounted } from 'vue'
import { useAccountsStore } from '../stores/accounts'
import { importsApi } from '../api/billing'
import UploadPanel from '../components/UploadPanel.vue'

const accounts = useAccountsStore()
const history = ref([])

onMounted(async () => {
  await accounts.fetchAccounts()
  const res = await importsApi.list()
  history.value = res.data
})

function onUploaded(item) {
  history.value.unshift({ ...item, status: item.status })
}

const statusColor = {
  imported: 'bg-gray-100 text-gray-600',
  validated: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
}
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-lg font-semibold text-gray-900">Invoice Imports</h1>
    <UploadPanel @uploaded="onUploaded" />

    <div class="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div class="px-4 py-3 border-b border-gray-100">
        <h3 class="text-sm font-medium text-gray-700">Import history</h3>
      </div>
      <div v-if="!history.length" class="p-6 text-sm text-center text-gray-400">No imports yet.</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="th">File / Source</th>
            <th class="th">Type</th>
            <th class="th">Imported</th>
            <th class="th">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in history" :key="item.id" class="border-t border-gray-100">
            <td class="td font-mono text-xs">{{ item.source_reference || item.id }}</td>
            <td class="td uppercase text-xs">{{ item.source_type }}</td>
            <td class="td text-gray-500">{{ new Date(item.imported_at).toLocaleDateString() }}</td>
            <td class="td">
              <span class="px-2 py-0.5 rounded text-xs font-medium" :class="statusColor[item.status] || 'bg-gray-100 text-gray-600'">
                {{ item.status }}
              </span>
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
