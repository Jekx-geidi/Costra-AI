<script setup>
import { onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { SunIcon } from '@solar-icons/vue/outline/sun'
import { MoonIcon } from '@solar-icons/vue/outline/moon'
import { Logout2Icon } from '@solar-icons/vue/outline/logout-2'
import AppNav from '../components/AppNav.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const darkMode = ref(localStorage.getItem('costra-theme') === 'dark')

function applyTheme() {
  document.documentElement.dataset.theme = darkMode.value ? 'dark' : 'light'
  document.documentElement.classList.remove('dark')
  localStorage.setItem('costra-theme', darkMode.value ? 'dark' : 'light')
}
function signOut() {
  auth.logout()
  router.push({ name: 'Login' })
}
onMounted(applyTheme)
watch(darkMode, applyTheme)
</script>

<template>
  <div class="app-shell flex min-h-screen bg-transparent text-gray-900 dark:text-gray-100">
    <AppNav />
    <div class="flex-1 min-w-0 overflow-y-auto">
      <header class="sticky top-0 z-10 px-4 sm:px-7 py-4 flex items-center justify-between border-b border-[#e5e8e1] bg-[#f3f4f1] dark:border-white/10 dark:bg-[#0d130f]/75">
        <img src="/costra-ai-logo.png" alt="COSTRA AI" class="h-7 w-32 object-contain object-left dark:hidden" />
        <img src="/costra-ai-logo-dark.png" alt="COSTRA AI" class="hidden h-7 w-32 object-contain object-left dark:block" />
        <div class="flex items-center gap-3">
          <button @click="darkMode = !darkMode" class="size-9 grid place-items-center rounded-lg border border-[#dfe4dc] bg-white text-gray-600 dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-300" :aria-label="darkMode ? 'Switch to light mode' : 'Switch to dark mode'"><SunIcon v-if="darkMode" :size="18" /><MoonIcon v-else :size="18" /></button>
          <span class="hidden md:block text-sm text-gray-500 dark:text-gray-400">{{ auth.user?.email }}</span>
          <button
            type="button"
            @click="signOut"
            aria-label="Sign out"
            class="h-9 inline-flex items-center gap-2 rounded-lg border border-[#dfe4dc] bg-white px-2.5 sm:px-3.5 text-sm font-medium text-gray-700 hover:border-red-200 hover:bg-red-50 hover:text-red-700 transition-colors dark:border-white/10 dark:bg-white/[0.06] dark:text-gray-200 dark:hover:border-red-400/30 dark:hover:bg-red-500/10 dark:hover:text-red-300"
          >
            <Logout2Icon :size="18" />
            <span class="hidden sm:inline">Sign out</span>
          </button>
        </div>
      </header>
      <main class="p-4 sm:p-7 max-w-[1560px] mx-auto">
        <RouterView />
      </main>
    </div>
  </div>
</template>
