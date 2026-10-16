<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { SunIcon } from '@solar-icons/vue/outline/sun'
import { MoonIcon } from '@solar-icons/vue/outline/moon'
import { Logout2Icon } from '@solar-icons/vue/outline/logout-2'
import AppNav from '../components/AppNav.vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const router = useRouter()
const mobileMenu = ref(null)
const menuOpen = ref(false)
function closeMenu() {
  mobileMenu.value?.close()
  menuOpen.value = false
  document.body.style.overflow = ''
}
function openMenu() {
  mobileMenu.value?.showModal()
  menuOpen.value = true
  document.body.style.overflow = 'hidden'
}
function onResize() { if (window.innerWidth >= 1024) closeMenu() }
onMounted(() => window.addEventListener('resize', onResize))
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); closeMenu() })
watch(() => router.currentRoute.value.fullPath, closeMenu)
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
    <AppNav class="hidden lg:flex" />
    <dialog ref="mobileMenu" id="mobile-navigation" aria-label="Navigation menu" @close="closeMenu" @cancel="closeMenu" @click="event => { if (event.target === mobileMenu) closeMenu() }" class="fixed inset-y-0 left-0 right-auto m-0 h-dvh max-h-none w-[min(19rem,85vw)] max-w-none border-0 bg-[#f3f4f1] p-3 text-gray-900 shadow-xl backdrop:bg-black/50 dark:bg-[#0d130f] dark:text-white">
      <button type="button" @click="closeMenu" aria-label="Close navigation" class="absolute right-5 top-5 z-10 grid size-11 place-items-center rounded-lg text-gray-700 hover:bg-gray-100 dark:text-white dark:hover:bg-white/10">
        <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="m6 6 12 12M6 18 18 6" /></svg>
      </button>
      <AppNav mobile @navigate="closeMenu" />
    </dialog>
    <div class="flex-1 min-w-0 overflow-y-auto">
      <header class="sticky top-0 z-10 px-4 sm:px-7 py-4 flex items-center justify-between border-b border-[#e5e8e1] bg-[#f3f4f1] dark:border-white/10 dark:bg-[#0d130f]/75">
        <div class="flex min-w-0 items-center gap-2">
        <button type="button" @click="openMenu" aria-label="Open navigation" aria-controls="mobile-navigation" :aria-expanded="menuOpen" class="grid size-11 shrink-0 place-items-center rounded-lg text-gray-700 hover:bg-gray-100 dark:text-white dark:hover:bg-white/10 lg:hidden">
          <svg viewBox="0 0 24 24" class="size-5" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><path d="M4 6h16M4 12h16M4 18h16" stroke-linecap="round" /></svg>
        </button>
        <img src="/costra-ai-logo.png" alt="COSTRA AI" class="h-7 w-28 sm:w-32 object-contain object-left dark:hidden" />
        <img src="/costra-ai-logo-dark.png" alt="COSTRA AI" class="hidden h-7 w-28 sm:w-32 object-contain object-left dark:block" />
        </div>
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
