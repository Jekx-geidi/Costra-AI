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

    <div class="min-w-0 bg-white rounded-xl border border-gray-200 p-4 sm:p-5">
      <h3 class="text-sm font-medium text-gray-700 mb-3">Registered accounts</h3>
      <div v-if="!accounts.accounts.length" class="text-sm text-gray-400">No accounts registered.</div>
      <template v-else>
      <ul class="space-y-3 md:hidden" aria-label="Registered accounts">
        <li v-for="a in accounts.accounts" :key="a.id" class="rounded-lg border border-gray-200 p-3">
          <div class="flex items-start justify-between gap-3">
            <h4 class="min-w-0 break-words text-sm font-semibold text-gray-900 dark:text-white [overflow-wrap:anywhere]">{{ a.account_name }}</h4>
            <span class="shrink-0 rounded-md px-2 py-1 text-xs font-medium" :class="a.is_active ? 'bg-lime-100 text-lime-950 dark:bg-lime-300/15 dark:text-lime-200' : 'bg-gray-100 text-gray-600'">{{ a.is_active ? 'Active' : 'Inactive' }}</span>
          </div>
          <dl class="mt-3 grid grid-cols-2 gap-3 text-xs">
            <div><dt class="text-gray-500">Provider</dt><dd class="mt-1 break-words capitalize text-gray-900 dark:text-gray-100">{{ a.provider }}</dd></div>
            <div><dt class="text-gray-500">Method</dt><dd class="mt-1 break-words capitalize text-gray-900 dark:text-gray-100">{{ a.collection_method }}</dd></div>
            <div class="col-span-2"><dt class="text-gray-500">Ownership</dt><dd class="mt-1 capitalize text-gray-900 dark:text-gray-100">{{ a.ownership_type }}</dd></div>
          </dl>
        </li>
      </ul>
      <div class="hidden overflow-x-auto md:block">
      <table class="w-full text-sm">
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
      </template>
    </div>
  </div>
</template>

<style scoped>
.th { @apply px-4 py-2.5 text-left text-xs font-medium text-gray-500 uppercase tracking-wider; }
.td { @apply px-4 py-3 text-gray-700; }
</style>
