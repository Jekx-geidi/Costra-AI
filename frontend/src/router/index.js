import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/LoginView.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../layouts/AppLayout.vue'),
    children: [
      { path: '', name: 'Overview', component: () => import('../views/OverviewView.vue') },
      { path: 'records', name: 'BillingRecords', component: () => import('../views/BillingRecordsView.vue') },
      { path: 'reports', name: 'Reports', component: () => import('../views/ReportsView.vue') },
      { path: 'imports', name: 'Imports', component: () => import('../views/ImportsView.vue'), meta: { minRole: 'billing_admin' } },
      { path: 'integrations', name: 'Integrations', component: () => import('../views/IntegrationsView.vue'), meta: { minRole: 'billing_admin' } },
      { path: 'assistant', name: 'Assistant', component: () => import('../views/AssistantView.vue') },
      { path: 'reconciliation', name: 'Reconciliation', component: () => import('../views/ReconciliationView.vue'), meta: { minRole: 'finance_reviewer' } },
    ],
  },
  { path: '/403', name: 'NotAuthorized', component: () => import('../views/NotAuthorizedView.vue'), meta: { public: true } },
  { path: '/:pathMatch(.*)*', redirect: '/' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()

  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === 'Login') return { name: 'Overview' }
    return true
  }

  if (!auth.isAuthenticated) return { name: 'Login' }

  if (to.meta.minRole && !auth.canAccess(to.meta.minRole)) return { name: 'NotAuthorized' }

  return true
})

export default router
