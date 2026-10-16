<script setup>
import { ref, watch } from 'vue'
import { ChartSquareIcon } from '@solar-icons/vue/outline/chart-square'
import { BillListIcon } from '@solar-icons/vue/outline/bill-list'
import { UploadIcon } from '@solar-icons/vue/outline/upload'
import { PlugCircleIcon } from '@solar-icons/vue/outline/plug-circle'
import { CheckCircleIcon } from '@solar-icons/vue/outline/check-circle'
import { ChatRoundDotsIcon } from '@solar-icons/vue/outline/chat-round-dots'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const collapsed = ref(localStorage.getItem('costra-sidebar-collapsed') === 'true')
watch(collapsed, value => localStorage.setItem('costra-sidebar-collapsed', String(value)))

const navItems = [
  { name: 'Overview', to: '/', icon: ChartSquareIcon, minRole: 'viewer' },
  { name: 'Billing Records', to: '/records', icon: BillListIcon, minRole: 'viewer' },
  { name: 'Reports', to: '/reports', icon: ChartSquareIcon, minRole: 'viewer' },
  { name: 'Imports', to: '/imports', icon: UploadIcon, minRole: 'billing_admin' },
  { name: 'Integrations', to: '/integrations', icon: PlugCircleIcon, minRole: 'billing_admin' },
  { name: 'Reconciliation', to: '/reconciliation', icon: CheckCircleIcon, minRole: 'finance_reviewer' },
  { name: 'Assistant', to: '/assistant', icon: ChatRoundDotsIcon, minRole: 'viewer' },
]
</script>

<template>
  <nav aria-label="Main navigation" class="w-[76px] shrink-0 glass-panel m-3 mr-0 rounded-xl flex flex-col py-5 transition-[width] duration-200 motion-reduce:transition-none" :class="collapsed ? 'lg:w-[76px]' : 'lg:w-60'">
    <div class="px-4 mb-7 flex items-center gap-2 overflow-hidden">
      <button type="button" @click="collapsed = !collapsed" :aria-expanded="!collapsed" aria-controls="sidebar-links" :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'" :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'" class="hidden size-8 shrink-0 items-center justify-center rounded-lg text-gray-600 hover:bg-gray-100 dark:text-white dark:hover:bg-white/10 lg:flex">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" class="size-4 transition-transform" :class="{ 'rotate-180': collapsed }" aria-hidden="true"><path d="m14 7-5 5 5 5" stroke-linecap="round" stroke-linejoin="round" /></svg>
      </button>
      <div class="min-w-0 overflow-hidden" :class="{ 'lg:hidden': collapsed }">
        <img src="/costra-ai-logo.png" alt="COSTRA AI" class="h-9 w-28 max-w-none object-cover object-left dark:hidden" :class="{ 'lg:w-36 lg:object-contain': !collapsed }" />
        <img src="/costra-ai-logo-dark.png" alt="COSTRA AI" class="hidden h-9 w-28 max-w-none object-cover object-left dark:block" :class="{ 'lg:w-36 lg:object-contain': !collapsed }" />
      </div>
    </div>
    <ul id="sidebar-links" class="space-y-1 px-2 flex-1">
      <li v-for="item in navItems" :key="item.to">
        <RouterLink
          v-if="auth.canAccess(item.minRole)"
          :to="item.to"
          :aria-label="item.name"
          :title="item.name"
          exact-active-class="bg-lime-300 text-lime-950 font-semibold dark:!text-lime-950 dark:hover:!text-lime-950"
          :class="{ 'lg:justify-start': !collapsed }"
          class="flex items-center justify-center gap-3 px-3 py-2.5 rounded-lg text-sm text-gray-500 hover:bg-[#f1f3ef] hover:text-gray-900 transition-colors dark:text-white dark:hover:bg-white/[0.07] dark:hover:text-white"
        >
          <component :is="item.icon" :size="20" class="shrink-0" />
          <span v-if="!collapsed" class="hidden lg:inline">{{ item.name }}</span>
        </RouterLink>
      </li>
    </ul>
    <div v-if="!collapsed" class="mx-3 mt-8 hidden rounded-2xl border border-lime-200 bg-lime-50 p-4 lg:block dark:border-lime-300/20 dark:bg-lime-300/[0.06]">
      <svg viewBox="0 0 120 92" class="mx-auto mb-3 h-24 w-28" fill="none" aria-hidden="true">
        <ellipse cx="59" cy="84" rx="25" ry="4" class="fill-lime-500" opacity=".08" />
        <path d="M58 81V33M58 57L39 42M58 46L75 29" class="stroke-lime-600" stroke-width="2" stroke-linecap="round" />
        <path d="M56 37C39 36 35 23 37 13C51 14 60 22 56 37Z" class="fill-lime-700" />
        <path d="M58 36C57 20 65 12 79 10C80 24 71 35 58 36Z" class="fill-lime-400" />
        <path d="M53 57C36 61 24 51 25 39C40 36 51 43 53 57Z" class="fill-lime-200" />
        <path d="M61 68C55 54 63 43 76 41C83 55 76 67 61 68Z" class="fill-lime-500" />
        <path d="M61 67C66 57 69 50 75 43" class="stroke-lime-700" stroke-linecap="round" />
        <path d="M90 35C90 28 95 25 101 26C101 32 97 36 90 35Z" class="fill-lime-300" />
        <path d="M39 16L56 36M77 13L60 34" class="stroke-lime-100" stroke-opacity=".45" stroke-linecap="round" />
      </svg>
      <p class="text-sm font-semibold leading-5 text-lime-950 dark:text-white">Small steps<br />build big wealth.</p>
      <p class="mt-1.5 text-xs text-lime-800 dark:text-gray-300">Track. Save. Grow.</p>
      <RouterLink to="/" class="mt-4 flex items-center justify-between rounded-lg bg-lime-300 px-3 py-2.5 text-xs font-semibold text-lime-950 transition-colors hover:bg-lime-200 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-lime-500">
        Review AI spend <span aria-hidden="true">↗</span>
      </RouterLink>
    </div>
  </nav>
</template>
