import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import './style.css'

const savedTheme = localStorage.getItem('costra-theme')
document.documentElement.dataset.theme = savedTheme === 'dark' ? 'dark' : 'light'
document.documentElement.classList.remove('dark')

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.mount('#app')
