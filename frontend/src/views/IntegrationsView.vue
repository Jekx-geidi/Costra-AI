<script setup>
import { ref, onMounted } from 'vue'
import { useAccountsStore } from '../stores/accounts'
import { useAuthStore } from '../stores/auth'
import { syncApi } from '../api/billing'

const accounts = useAccountsStore()
const auth = useAuthStore()
const syncResults = ref({})
const syncing = ref({})

onMounted(() => accounts.fetchAccounts())

async function triggerSync(provider) {
  syncing.value[provider] = true
  try {
    const res = await syncApi.trigger(provider, {})
    syncResults.value[provider] = res.data
  } catch (e) {
    syncResults.value[provider] = { error: e.response?.data?.detail || 'Sync failed' }
  } finally {
    syncing.value[provider] = false
  }
}

const capabilityColor = {
  enabled: 'bg-green-100 text-green-700',
  disabled: 'bg-gray-100 text-gray-500',
  blocked: 'bg-red-100 text-red-700',
}

const providers = ['openai', 'anthropic']
</script>

<template>
  <div class="space-y-6">
    <h1 class="text-lg font-semibold text-gray-900">Integrations</h1>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div
        v-for="provider in providers"
        :key="provider"
        class="bg-white rounded-xl border border-gray-200 p-5 space-y-3"
      >
        <div class="flex items-center justify-between">
          <h3 class="font-medium text-gray-800 capitalize">{{ provider }}</h3>
          <span
            v-if="syncResults[provider]"
            class="text-xs px-2 py-0.5 rounded font-medium"
            :class="capabilityColor[syncResults[provider].capability_status] || 'bg-gray-100 text-gray-600'"
          >
            {{ syncResults[provider].capability_status || '—' }}
          </span>
        </div>

        <div class="text-xs text-gray-500 space-y-1">
          <p v-if="syncResults[provider]">
            Last sync: {{ syncResults[provider].started_at ? new Date(syncResults[provider].started_at).toLocaleString() : '—' }}
          </p>
          <p v-if="syncResults[provider]?.records_processed != null">
            Records processed: {{ syncResults[provider].records_processed }}
          </p>
          <p v-if="syncResults[provider]?.error_summary" class="text-red-600">
            {{ syncResults[provider].error_summary }}
          </p>
          <p v-if="syncResults[provider]?.error" class="text-red-600">
            {{ syncResults[provider].error }}
          </p>
        </div>

        <button
          v-if="auth.canAccess('billing_admin')"
          @click="triggerSync(provider)"
          :disabled="syncing[provider]"
          class="text-sm px-3 py-1.5 bg-brand-600 text-white rounded-md hover:bg-brand-700 disabled:opacity-40"
        >
          {{ syncing[provider] ? 'Syncing…' : 'Sync now' }}
        </button>
      </div>
    </div>

    <div class="bg-white rounded-xl border border-gray-200 p-5">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Registered accounts</h3>
      <div v-if="!accounts.accounts.length" class="text-sm text-gray-400">No accounts registered.</div>
      <table v-else class="w-full text-sm">
        <thead class="bg-gray-50">
          <tr>
            <th class="th">Name</th>
            <th class="th">Provider</th>
            <th class="th">Method</th>
            <th class="th">Ownership</th>
            <th class="th">Status</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="a in accounts.accounts" :key="a.id" class="border-t border-gray-100">
            <td class="td">{{ a.account_name }}</td>
            <td class="td capitalize">{{ a.provider }}</td>
            <td class="td capitalize">{{ a.collection_method }}</td>
            <td class="td capitalize">{{ a.ownership_type }}</td>
            <td class="td">
              <span :class="a.is_active ? 'text-green-600' : 'text-gray-400'" class="text-xs">
                {{ a.is_active ? 'Active' : 'Inactive' }}
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
