<script setup>
import { ref } from 'vue'
import { DangerTriangleIcon } from '@solar-icons/vue/outline/danger-triangle'
import { useAccountsStore } from '../stores/accounts'
import { importsApi } from '../api/billing'

const emit = defineEmits(['uploaded'])
const accounts = useAccountsStore()

const selectedAccount = ref('')
const file = ref(null)
const dragging = ref(false)
const uploading = ref(false)
const preview = ref(null)
const errorMsg = ref('')

const ALLOWED = ['pdf', 'csv']
const MAX_MB = 10

function onDrop(e) {
  dragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) setFile(f)
}

function onFileChange(e) {
  const f = e.target.files[0]
  if (f) setFile(f)
}

function setFile(f) {
  const ext = f.name.split('.').pop().toLowerCase()
  if (!ALLOWED.includes(ext)) {
    errorMsg.value = `File type .${ext} not allowed. Use PDF or CSV.`
    return
  }
  if (f.size > MAX_MB * 1024 * 1024) {
    errorMsg.value = `File is too large (max ${MAX_MB} MB).`
    return
  }
  errorMsg.value = ''
  file.value = f
  preview.value = null
}

async function upload() {
  if (!selectedAccount.value || !file.value) return
  uploading.value = true
  errorMsg.value = ''
  try {
    const fd = new FormData()
    fd.append('account_id', selectedAccount.value)
    fd.append('file', file.value)
    const res = await importsApi.upload(fd)
    preview.value = res.data
    emit('uploaded', res.data)
  } catch (e) {
    const detail = e.response?.data?.detail || ''
    if (e.response?.status === 409) {
      errorMsg.value = `Already imported: ${detail}`
    } else {
      errorMsg.value = detail || 'Upload failed.'
    }
  } finally {
    uploading.value = false
  }
}

function reset() {
  file.value = null
  preview.value = null
  errorMsg.value = ''
}
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 p-5 space-y-4">
    <h3 class="text-sm font-medium text-gray-700">Upload Invoice / Export</h3>

    <div>
      <label class="block text-xs text-gray-500 mb-1">Billing account</label>
      <select v-model="selectedAccount" class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm">
        <option value="">Select account…</option>
        <option v-for="a in accounts.accounts" :key="a.id" :value="a.id">
          {{ a.account_name }} ({{ a.provider }})
        </option>
      </select>
    </div>

    <div
      @dragover.prevent="dragging = true"
      @dragleave="dragging = false"
      @drop.prevent="onDrop"
      class="border-2 border-dashed rounded-lg p-6 text-center transition-colors"
      :class="dragging ? 'border-brand-400 bg-brand-50' : 'border-gray-300'"
    >
      <p class="text-sm text-gray-500 mb-2">Drag & drop a PDF or CSV, or</p>
      <label class="cursor-pointer text-sm text-brand-600 hover:underline">
        browse
        <input type="file" accept=".pdf,.csv" class="hidden" @change="onFileChange" />
      </label>
      <p v-if="file" class="text-xs text-gray-600 mt-2">{{ file.name }} ({{ (file.size / 1024).toFixed(1) }} KB)</p>
    </div>

    <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>

    <div class="flex gap-3">
      <button
        @click="upload"
        :disabled="!selectedAccount || !file || uploading"
        class="px-4 py-2 bg-brand-600 text-white text-sm rounded-md hover:bg-brand-700 disabled:opacity-40"
      >
        {{ uploading ? 'Uploading…' : 'Upload' }}
      </button>
      <button @click="reset" class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800">Clear</button>
    </div>

    <div v-if="preview" class="mt-4 space-y-3">
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium text-gray-700">Parse preview</span>
        <span v-if="preview.requires_review" class="text-xs text-amber-600 bg-amber-50 px-2 py-0.5 rounded">Review required</span>
        <span v-else class="text-xs text-green-600 bg-green-50 px-2 py-0.5 rounded">Auto-posted</span>
      </div>
      <ul v-if="preview.validation_warnings.length" class="text-xs text-amber-700 space-y-0.5">
        <li v-for="w in preview.validation_warnings" :key="w" class="flex items-start gap-1">
          <DangerTriangleIcon :size="14" class="shrink-0 mt-px" />
          <span>{{ w }}</span>
        </li>
      </ul>
      <table class="w-full text-xs border border-gray-200 rounded-md overflow-hidden">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-3 py-2 text-left text-gray-500">Description</th>
            <th class="px-3 py-2 text-left text-gray-500">Category</th>
            <th class="px-3 py-2 text-right text-gray-500">Amount</th>
            <th class="px-3 py-2 text-left text-gray-500">Confidence</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(item, i) in preview.parsed_items" :key="i" class="border-t border-gray-100">
            <td class="px-3 py-2">{{ item.description || '—' }}</td>
            <td class="px-3 py-2 capitalize">{{ item.expense_category }}</td>
            <td class="px-3 py-2 text-right font-mono">{{ parseFloat(item.amount).toFixed(2) }} {{ item.currency }}</td>
            <td class="px-3 py-2" :class="item.confidence === 'high' ? 'text-green-600' : 'text-amber-600'">{{ item.confidence }}</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
