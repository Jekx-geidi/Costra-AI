<script setup>
import { LockKeyholeIcon } from '@solar-icons/vue/outline/lock-keyhole'
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50">
    <div class="text-center">
      <LockKeyholeIcon :size="64" class="mx-auto mb-4 text-gray-400" />
      <h1 class="text-xl font-semibold text-gray-900 mb-2">Access Denied</h1>
      <p class="text-sm text-gray-500 mb-4">You do not have permission to view this page.</p>
      <RouterLink to="/" class="text-sm text-brand-600 hover:underline">Back to Overview</RouterLink>
    </div>
  </div>
</template>
