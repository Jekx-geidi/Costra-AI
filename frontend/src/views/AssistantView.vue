<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { PaperclipIcon } from '@solar-icons/vue/outline/paperclip'
import { ArrowUpIcon } from '@solar-icons/vue/outline/arrow-up'
import { FileTextIcon } from '@solar-icons/vue/outline/file-text'
import { DangerTriangleIcon } from '@solar-icons/vue/outline/danger-triangle'
import { TrashBinMinimalisticIcon } from '@solar-icons/vue/outline/trash-bin-minimalistic'
import { CheckCircleIcon } from '@solar-icons/vue/outline/check-circle'
import { RefreshIcon } from '@solar-icons/vue/outline/refresh'
import { assistantApi } from '../api/billing'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const canImport = computed(() => auth.canAccess('billing_admin'))

const MAX_HISTORY = 12
const conversations = ref([])
const activeId = ref(null)
const historyOpen = ref(false)
const historyKey = ref(null)
const historyNotice = ref('')
const historyReady = ref(false)

// Message kinds: 'text' (role user|assistant), 'file' (user attached a file), 'draft' (invoice to confirm), 'error'
const messages = ref([])
const input = ref('')
const busy = ref(false)
const fileInput = ref(null)
const scroller = ref(null)

const suggestions = [
  'Pila ang among total AI spend karong bulana?',
  'Unsa ang bag-o nga nahitabo sa system?',
  'Naa bay records nga pending pa ug review?',
  'Unsa ang status sa OpenAI ug Anthropic integrations?',
]

onMounted(async () => {
  try {
    if (!auth.user) await auth.fetchMe()
    const identity = auth.user?.id || auth.user?.email
    if (!identity) throw new Error('Missing account')
    historyKey.value = `costra-chat-history:${identity}`
    const saved = JSON.parse(localStorage.getItem(historyKey.value) || '[]')
    conversations.value = Array.isArray(saved) ? saved.filter(c => typeof c.id === 'string' && typeof c.title === 'string' && Array.isArray(c.messages)) : []
    if (conversations.value.length) openChat(conversations.value[0])
  } catch {
    historyNotice.value = 'Saved history is unavailable. You can still chat in this session.'
  } finally {
    historyReady.value = true
  }
})

function saveHistory() {
  if (!historyKey.value) return
  try { localStorage.setItem(historyKey.value, JSON.stringify(conversations.value)) }
  catch { historyNotice.value = 'History could not be saved on this browser. Existing saved chats have been kept.' }
}

watch(messages, (value) => {
  if (value.length) {
    if (!activeId.value) activeId.value = crypto.randomUUID()
    const stored = value.map(m => m.kind === 'draft'
      ? { kind: 'text', role: 'assistant', content: `Invoice preview for ${m.draft.filename}. Attach the file again to continue reviewing it.` }
      : { ...m })
    const existing = conversations.value.findIndex(c => c.id === activeId.value)
    const chat = {
      id: activeId.value,
      title: (value.find(m => m.role === 'user')?.content || value.find(m => m.kind === 'file')?.name || 'New conversation').slice(0, 80),
      updatedAt: new Date().toISOString(), messages: stored,
    }
    if (existing >= 0) conversations.value.splice(existing, 1)
    conversations.value.unshift(chat)
    saveHistory()
  }
  nextTick(() => scroller.value?.scrollTo({ top: scroller.value.scrollHeight, behavior: 'smooth' }))
}, { deep: true, flush: 'sync' })

function canLeaveChat() {
  return !busy.value && (!messages.value.some(m => m.kind === 'draft') || window.confirm('Leave this invoice preview? You will need to attach it again to continue.'))
}

function openChat(chat) {
  if (!canLeaveChat()) return
  activeId.value = chat.id
  messages.value = JSON.parse(JSON.stringify(chat.messages))
  input.value = ''
  historyOpen.value = false
}

function deleteChat(chat) {
  if (busy.value || !window.confirm(`Delete "${chat.title}" from this browser?`)) return
  if (activeId.value === chat.id) {
    activeId.value = null
    messages.value = []
  }
  conversations.value = conversations.value.filter(c => c.id !== chat.id)
  saveHistory()
}

function errorText(err, fallback) {
  const detail = err.response?.data?.detail
  return typeof detail === 'string' ? detail : fallback
}

function chatHistory() {
  return messages.value
    .filter(m => m.kind === 'text')
    .slice(-MAX_HISTORY)
    .map(m => ({ role: m.role, content: m.content }))
}

async function send(text = input.value) {
  const content = text.trim()
  if (!content || busy.value || !historyReady.value) return
  input.value = ''
  messages.value.push({ kind: 'text', role: 'user', content })
  busy.value = true
  try {
    const res = await assistantApi.chat(chatHistory())
    messages.value.push({ kind: 'text', role: 'assistant', content: res.data.reply })
  } catch (err) {
    messages.value.push({ kind: 'error', content: errorText(err, 'The assistant could not answer right now. Please try again.') })
  } finally {
    busy.value = false
  }
}

function onKeydown(event) {
  if (event.key === 'Enter' && !event.shiftKey) {
    event.preventDefault()
    send()
  }
}

async function onFilePicked(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file || busy.value || !historyReady.value) return
  messages.value.push({ kind: 'file', role: 'user', name: file.name })
  busy.value = true
  try {
    const form = new FormData()
    form.append('file', file)
    const { data } = await assistantApi.readInvoice(form)
    if (!data.is_invoice) {
      messages.value.push({ kind: 'text', role: 'assistant', content: `Dili invoice ang "${file.name}" sa akong pagbasa, so wala koy gi-import.` })
      return
    }
    messages.value.push({
      kind: 'draft',
      draft: data,
      accountId: data.suggested_account_id || '',
      items: data.items.map(i => ({ ...i, amount: Number(i.amount) === 0 ? '0' : i.amount.replace(/\.?0+$/, '') })),
      saving: false,
      error: '',
    })
  } catch (err) {
    messages.value.push({ kind: 'error', content: errorText(err, 'I could not read that file.') })
  } finally {
    busy.value = false
  }
}

const AMOUNT_PATTERN = /^-?\d+(\.\d{1,6})?$/

function draftTotal(msg) {
  // Sum in integer micro-units so money never goes through floating point.
  let micros = 0n
  for (const item of msg.items) {
    if (!AMOUNT_PATTERN.test(item.amount)) return null
    const [whole, frac = ''] = item.amount.replace('-', '').split('.')
    const value = BigInt(whole) * 1000000n + BigInt((frac + '000000').slice(0, 6))
    micros += item.amount.startsWith('-') ? -value : value
  }
  const sign = micros < 0n ? '-' : ''
  const abs = micros < 0n ? -micros : micros
  return `${sign}${abs / 1000000n}.${String(abs % 1000000n).padStart(6, '0').slice(0, 2)}`
}

function draftInvalid(msg) {
  return !msg.accountId || !msg.items.length || msg.items.some(i => !AMOUNT_PATTERN.test(i.amount))
}

async function confirmDraft(msg) {
  if (draftInvalid(msg) || msg.saving) return
  msg.saving = true
  msg.error = ''
  try {
    const { data } = await assistantApi.confirmInvoice(msg.draft.draft_id, {
      account_id: msg.accountId,
      invoice_number: msg.draft.invoice_number,
      items: msg.items,
    })
    const index = messages.value.indexOf(msg)
    messages.value.splice(index, 1, {
      kind: 'text',
      role: 'assistant',
      content: `Na-import na ang ${msg.draft.filename}: ${data.records_imported} ka linya, total ${Number(data.total).toFixed(2)} ${data.currency}, sa account nga "${data.account_name}". Naa sila sa Billing Records isip "pending" hangtod ma-review.`,
    })
  } catch (err) {
    msg.error = errorText(err, 'The invoice could not be imported.')
  } finally {
    msg.saving = false
  }
}

function discardDraft(msg) {
  const index = messages.value.indexOf(msg)
  messages.value.splice(index, 1, {
    kind: 'text', role: 'assistant', content: `Wala gi-import ang ${msg.draft.filename}.`,
  })
}

function clearChat() {
  if (!canLeaveChat()) return
  activeId.value = null
  messages.value = []
  input.value = ''
}
</script>

<template>
  <div class="flex h-[calc(100vh-8.5rem)] min-h-[480px] flex-col gap-4">
    <div class="flex items-start justify-between gap-4">
      <div>
        <h1 class="text-lg font-semibold text-gray-900 dark:text-white">Assistant</h1>
        <p class="mt-0.5 text-sm text-gray-500">
          Pangutana bahin sa COSTRA. Motubag ra siya base sa data nga naa sa system.
          <span v-if="canImport">I-attach ang invoice ug siya ang mobasa ug mo-input.</span>
        </p>
      </div>
      <div class="flex shrink-0 items-center gap-2">
      <button type="button" @click="historyOpen = !historyOpen" :aria-expanded="historyOpen" aria-controls="chat-history" class="h-9 rounded-lg border border-gray-300 px-3 text-sm text-gray-700 dark:text-white">History ({{ conversations.length }})</button>
      <button
        v-if="messages.length"
        type="button"
        :disabled="busy"
        @click="clearChat"
        class="inline-flex h-9 shrink-0 items-center gap-2 rounded-lg border border-[#dfe4dc] bg-white px-3 text-sm text-gray-600 hover:text-gray-900 dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-300"
      >
        <RefreshIcon :size="16" />
        <span class="hidden sm:inline">New chat</span>
      </button>
      </div>
    </div>

    <p v-if="historyNotice" role="status" class="text-xs text-amber-700 dark:text-amber-300">{{ historyNotice }}</p>
    <section v-if="historyOpen" id="chat-history" class="glass-panel max-h-56 shrink-0 overflow-y-auto rounded-xl p-4" aria-label="Chat history">
      <h2 class="text-sm font-semibold text-gray-900 dark:text-white">Previous conversations</h2>
      <p class="mt-1 text-xs text-gray-500">Saved for your account on this browser.</p>
      <p v-if="!conversations.length" class="mt-3 text-sm text-gray-500">Your conversations will appear here after you send a message.</p>
      <ul class="mt-3 space-y-1">
        <li v-for="chat in conversations" :key="chat.id" class="flex items-center gap-2 rounded-lg" :class="chat.id === activeId ? 'bg-lime-300/10' : ''">
          <button type="button" :disabled="busy" @click="openChat(chat)" class="min-w-0 flex-1 px-3 py-2 text-left hover:bg-black/5 dark:hover:bg-white/5 disabled:opacity-50" :aria-current="chat.id === activeId ? 'true' : undefined">
            <span class="block truncate text-sm font-medium text-gray-800 dark:text-white">{{ chat.title }}</span>
            <span class="text-xs text-gray-500">{{ new Date(chat.updatedAt).toLocaleString() }}</span>
          </button>
          <button type="button" :disabled="busy" @click="deleteChat(chat)" :aria-label="`Delete conversation: ${chat.title}`" class="p-2 text-gray-500 hover:text-red-600 disabled:opacity-50"><TrashBinMinimalisticIcon :size="18" /></button>
        </li>
      </ul>
    </section>

    <div ref="scroller" class="glass-panel flex-1 overflow-y-auto rounded-xl p-4 sm:p-6">
      <div v-if="!messages.length" class="mx-auto flex h-full max-w-xl flex-col items-center justify-center text-center">
        <img src="/favicon.svg" alt="COSTRA assistant" class="size-16 object-contain" />
        <p class="mt-4 text-sm font-medium text-gray-800 dark:text-gray-100">Unsa ang gusto nimong mahibaw-an?</p>
        <p class="mt-1 text-xs text-gray-500">Spend, records, imports, integrations, reconciliation, ug unsay nahitabo sa system.</p>
        <div class="mt-5 flex flex-wrap justify-center gap-2">
          <button
            v-for="s in suggestions"
            :key="s"
            type="button"
            @click="send(s)"
            class="rounded-lg border border-[#dfe4dc] bg-white px-3 py-1.5 text-xs text-gray-700 hover:border-lime-400 hover:bg-lime-50 dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-200"
          >
            {{ s }}
          </button>
        </div>
      </div>

      <ul v-else class="mx-auto max-w-3xl space-y-4">
        <li v-for="(msg, idx) in messages" :key="idx" class="flex items-start gap-2 sm:gap-3" :class="msg.role === 'user' ? 'justify-end' : 'justify-start'">
          <img v-if="msg.role !== 'user'" src="/favicon.svg" alt="COSTRA assistant" class="mt-1 size-8 shrink-0 object-contain sm:size-10" />
          <div
            v-if="msg.kind === 'text'"
            class="max-w-[85%] whitespace-pre-wrap rounded-xl px-4 py-2.5 text-sm leading-relaxed"
            :class="msg.role === 'user'
              ? 'bg-lime-300 text-lime-950'
              : 'border border-[#e5e8e1] bg-white text-gray-800 dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-100'"
          >{{ msg.content }}</div>

          <div v-else-if="msg.kind === 'file'" class="inline-flex items-center gap-2 rounded-xl bg-lime-300 px-4 py-2.5 text-sm text-lime-950">
            <FileTextIcon :size="18" />
            <span class="max-w-[16rem] truncate">{{ msg.name }}</span>
          </div>

          <div v-else-if="msg.kind === 'error'" class="flex max-w-[85%] items-start gap-2 rounded-xl border border-red-200 bg-red-50 px-4 py-2.5 text-sm text-red-700 dark:border-red-400/30 dark:bg-red-500/10 dark:text-red-300">
            <DangerTriangleIcon :size="18" class="mt-0.5 shrink-0" />
            <span>{{ msg.content }}</span>
          </div>

          <div v-else-if="msg.kind === 'draft'" class="min-w-0 flex-1 max-w-2xl rounded-xl border border-[#e5e8e1] bg-white p-4 text-sm dark:border-white/10 dark:bg-white/[0.06]">
            <p class="text-gray-800 dark:text-gray-100">
              Nabasa nako ang <span class="font-medium">{{ msg.draft.filename }}</span>. Susiha una sa dili pa i-import:
            </p>
            <dl class="mt-3 grid grid-cols-2 gap-x-4 gap-y-1 text-xs sm:grid-cols-4">
              <div><dt class="text-gray-400">Vendor</dt><dd class="text-gray-800 dark:text-gray-100">{{ msg.draft.vendor_name || msg.draft.provider }}</dd></div>
              <div><dt class="text-gray-400">Invoice #</dt><dd class="text-gray-800 dark:text-gray-100">{{ msg.draft.invoice_number || '—' }}</dd></div>
              <div><dt class="text-gray-400">Period</dt><dd class="text-gray-800 dark:text-gray-100">{{ msg.draft.period_start || '—' }} – {{ msg.draft.period_end || '—' }}</dd></div>
              <div><dt class="text-gray-400">Invoice total</dt><dd class="text-gray-800 dark:text-gray-100">{{ msg.draft.total ? Number(msg.draft.total).toFixed(2) : '—' }} {{ msg.draft.currency }}</dd></div>
            </dl>

            <label class="mt-4 block text-xs font-medium text-gray-600 dark:text-gray-300">Account</label>
            <select v-model="msg.accountId" class="soft-input mt-1 w-full">
              <option value="" disabled>Pili ug billing account…</option>
              <option v-for="a in msg.draft.accounts" :key="a.id" :value="a.id">{{ a.name }} ({{ a.provider }})</option>
            </select>

            <div class="mt-4 overflow-x-auto">
              <table class="w-full text-xs">
                <thead>
                  <tr class="text-left text-gray-400">
                    <th class="py-1 pr-2 font-medium">Description</th>
                    <th class="py-1 pr-2 font-medium">Category</th>
                    <th class="py-1 pr-2 text-right font-medium">Amount</th>
                    <th class="w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(item, i) in msg.items" :key="i" class="border-t border-[#eef0ec] dark:border-white/10">
                    <td class="py-1.5 pr-2 text-gray-800 dark:text-gray-100">{{ item.description || '—' }}</td>
                    <td class="py-1.5 pr-2 text-gray-500">{{ item.expense_category }}</td>
                    <td class="py-1.5 pr-2 text-right">
                      <input
                        v-model.trim="item.amount"
                        inputmode="decimal"
                        :aria-label="`Amount for ${item.description || 'line ' + (i + 1)}`"
                        class="soft-input w-28 py-1 text-right"
                        :class="{ 'border-red-400': !AMOUNT_PATTERN.test(item.amount) }"
                      />
                    </td>
                    <td class="py-1.5 text-right">
                      <button type="button" @click="msg.items.splice(i, 1)" class="text-gray-400 hover:text-red-600" :aria-label="`Remove ${item.description || 'line'}`">
                        <TrashBinMinimalisticIcon :size="16" />
                      </button>
                    </td>
                  </tr>
                </tbody>
                <tfoot>
                  <tr class="border-t border-[#e5e8e1] font-medium text-gray-800 dark:border-white/10 dark:text-gray-100">
                    <td class="py-1.5" colspan="2">Total to import</td>
                    <td class="py-1.5 pr-2 text-right">{{ draftTotal(msg) ?? '—' }} {{ msg.draft.currency }}</td>
                    <td></td>
                  </tr>
                </tfoot>
              </table>
            </div>

            <ul v-if="msg.draft.warnings.length" class="mt-3 space-y-1 text-xs text-amber-700 dark:text-amber-300">
              <li v-for="w in msg.draft.warnings" :key="w" class="flex items-start gap-1.5">
                <DangerTriangleIcon :size="14" class="mt-px shrink-0" />
                <span>{{ w }}</span>
              </li>
            </ul>
            <p v-if="msg.error" class="mt-3 text-xs text-red-600">{{ msg.error }}</p>

            <div class="mt-4 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                @click="discardDraft(msg)"
                :disabled="msg.saving"
                class="h-9 rounded-lg border border-[#dfe4dc] bg-white px-3.5 text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-200"
              >
                Cancel
              </button>
              <button
                type="button"
                @click="confirmDraft(msg)"
                :disabled="draftInvalid(msg) || msg.saving"
                class="inline-flex h-9 items-center gap-2 rounded-lg bg-lime-300 px-3.5 text-sm font-semibold text-lime-950 hover:bg-lime-200 disabled:opacity-50"
              >
                <CheckCircleIcon :size="18" />
                {{ msg.saving ? 'Nag-import…' : `I-import (${msg.items.length})` }}
              </button>
            </div>
          </div>
        </li>

        <li v-if="busy" class="flex items-start justify-start gap-2 sm:gap-3">
          <img src="/favicon.svg" alt="COSTRA assistant" class="mt-1 size-8 shrink-0 object-contain sm:size-10" />
          <div class="flex items-center gap-1.5 rounded-xl border border-[#e5e8e1] bg-white px-4 py-3 dark:border-white/10 dark:bg-white/[0.06]" aria-label="Assistant is thinking">
            <span v-for="n in 3" :key="n" class="size-1.5 animate-bounce rounded-full bg-gray-400" :style="{ animationDelay: `${n * 120}ms` }"></span>
          </div>
        </li>
      </ul>
    </div>

    <form @submit.prevent="send()" class="glass-panel flex items-end gap-2 rounded-xl p-2">
      <template v-if="canImport">
        <input ref="fileInput" type="file" accept=".pdf,.csv,.png,.jpg,.jpeg,.webp" class="hidden" @change="onFilePicked" />
        <button
          type="button"
          @click="fileInput.click()"
          :disabled="busy"
          class="grid size-10 shrink-0 place-items-center rounded-lg text-gray-500 hover:bg-[#f1f3ef] hover:text-gray-900 disabled:opacity-50 dark:hover:bg-white/[0.07] dark:hover:text-white"
          aria-label="Attach an invoice"
          title="Attach an invoice (PDF, CSV or image)"
        >
          <PaperclipIcon :size="20" />
        </button>
      </template>
      <textarea
        v-model="input"
        @keydown="onKeydown"
        rows="1"
        maxlength="4000"
        placeholder="Pangutana bahin sa imong AI spend…"
        aria-label="Message the assistant"
        class="max-h-40 min-h-10 flex-1 resize-none bg-transparent px-2 py-2.5 text-sm text-gray-800 placeholder:text-gray-400 focus:outline-none dark:text-gray-100"
      ></textarea>
      <button
        type="submit"
        :disabled="busy || !input.trim()"
        class="grid size-10 shrink-0 place-items-center rounded-lg bg-lime-300 text-lime-950 hover:bg-lime-200 disabled:opacity-40"
        aria-label="Send"
      >
        <ArrowUpIcon :size="20" />
      </button>
    </form>
  </div>
</template>
