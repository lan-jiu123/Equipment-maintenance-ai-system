import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './style.css'

const savedTheme = localStorage.getItem('equipai-theme')
if (savedTheme === 'light') {
  document.documentElement.setAttribute('data-theme', 'light')
}

createApp(App).use(router).mount('#app')