<script setup>
import { ref, watch } from 'vue'
import { SunIcon } from '@solar-icons/vue/outline/sun'
import { MoonIcon } from '@solar-icons/vue/outline/moon'
import RippleGrid from '../components/RippleGrid.vue'
import { useRouter } from 'vue-router'
import { EyeIcon } from '@solar-icons/vue/outline/eye'
import { EyeClosedIcon } from '@solar-icons/vue/outline/eye-closed'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const darkMode = ref(localStorage.getItem('costra-theme') === 'dark')
watch(darkMode, value => {
  document.documentElement.dataset.theme = value ? 'dark' : 'light'
  localStorage.setItem('costra-theme', value ? 'dark' : 'light')
}, { flush: 'sync' })

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMsg = ref('')

async function submit() {
  errorMsg.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/')
  } catch {
    errorMsg.value = 'Invalid email or password.'
    password.value = ''
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="relative isolate min-h-screen flex items-center justify-center overflow-hidden p-5 bg-[#f3f4f1] dark:bg-[#0d130f]">
    <RippleGrid :key="darkMode ? 'dark' : 'light'" />
    <button type="button" @click="darkMode = !darkMode" :aria-label="darkMode ? 'Switch to light mode' : 'Switch to dark mode'" :title="darkMode ? 'Switch to light mode' : 'Switch to dark mode'" class="absolute right-5 top-5 z-20 grid size-11 place-items-center rounded-xl border border-gray-200 bg-white text-gray-700 shadow-sm hover:bg-gray-50 dark:border-white/15 dark:bg-[#1d2920] dark:text-white dark:hover:bg-[#29372c]">
      <SunIcon v-if="darkMode" :size="20" />
      <MoonIcon v-else :size="20" />
    </button>
    <div class="glass-panel relative z-10 w-full max-w-md rounded-3xl p-7 sm:p-9 backdrop-blur-xl">
      <div class="mb-8">
        <img src="/costra-ai-logo.png" alt="COSTRA AI" class="h-14 w-52 object-contain object-left dark:hidden" />
        <img src="/costra-ai-logo-dark.png" alt="COSTRA AI" class="hidden h-14 w-52 object-contain object-left dark:block" />
        <h1 class="mt-4 text-2xl font-semibold tracking-tight text-gray-900 dark:text-white">Geidi AI Billing Tracker</h1>
        <p class="mt-2 text-sm text-gray-500 dark:text-gray-400">Welcome back. Sign in to review your AI spend.</p>
      </div>

      <form @submit.prevent="submit" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Email</label>
          <input
            v-model="email"
            type="email"
            required
            autocomplete="email"
            class="soft-input w-full"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1.5">Password</label>
          <div class="relative">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              required
              autocomplete="current-password"
              class="soft-input w-full pr-11"
            />
            <button
              type="button"
              @click="showPassword = !showPassword"
              :aria-label="showPassword ? 'Hide password' : 'Show password'"
              :aria-pressed="showPassword"
              class="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-700 dark:hover:text-white transition-colors"
            >
              <EyeClosedIcon v-if="showPassword" :size="20" />
              <EyeIcon v-else :size="20" />
            </button>
          </div>
        </div>
        <p v-if="errorMsg" class="text-sm text-red-600">{{ errorMsg }}</p>
        <button
          type="submit"
          :disabled="loading"
          class="w-full rounded-xl bg-lime-300 py-2.5 text-sm font-semibold text-lime-950 hover:bg-lime-200 disabled:opacity-50 transition-colors"
        >
          {{ loading ? 'Signing in…' : 'Sign in' }}
        </button>
      </form>
    </div>
  </div>
</template>
