<template>
  <div class="app-wrapper">
    <TopNav v-if="showNav" />
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="page-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    <transition name="toast">
      <div v-if="toast.show" class="global-toast" :class="'toast-' + toast.level">
        <span class="toast-icon">{{ toastIcon }}</span>
        <span class="toast-text">{{ toast.text }}</span>
      </div>
    </transition>
  </div>
</template>

<script>
import TopNav from './layout/TopNav.vue'
import { refreshUserFromMe, logout, isLoggedIn } from './utils/auth'
import { meApi } from './utils/api'
import { getRoleHome } from './router'

export default {
  name: 'App',
  components: { TopNav },
  data() {
    return {
      toast: { show: false, text: '', level: 'info' },
      _toastTimer: null
    }
  },
  computed: {
    showNav() {
      return this.$route.path !== '/login'
    },
    toastIcon() {
      switch (this.toast.level) {
        case 'success': return '✔'
        case 'warn': return '⚠'
        case 'error': return '✕'
        default: return 'ℹ'
      }
    }
  },
  created() {
    window.addEventListener('equipai-toast', this._onToast)
    window.addEventListener('storage', this._onStorageChanged)
    this._refreshMe()
    // 初始页面标题
    const label = this.$route.meta?.label
    document.title = label
      ? label + ' — EQUIPAI · 设备检修智能系统'
      : 'EQUIPAI · 设备检修智能系统'
  },
  beforeUnmount() {
    window.removeEventListener('equipai-toast', this._onToast)
    window.removeEventListener('storage', this._onStorageChanged)
    if (this._toastTimer) clearTimeout(this._toastTimer)
  },
  watch: {
    '$route.path'() {
      this._refreshMe()
    },
    '$route'(to) {
      // 更新浏览器 Tab 标题
      const label = to.meta?.label
      if (label) {
        document.title = label + ' — EQUIPAI · 设备检修智能系统'
      } else if (to.path === '/login') {
        document.title = '登录 — EQUIPAI · 设备检修智能系统'
      } else {
        document.title = 'EQUIPAI · 设备检修智能系统'
      }
    }
  },
  methods: {
    _onToast(e) {
      const d = e.detail || {}
      this.toast = {
        show: true,
        text: d.text || '',
        level: d.level || 'info'
      }
      if (this._toastTimer) clearTimeout(this._toastTimer)
      const dur = (d.level === 'error' || d.level === 'warn') ? 4000 : 2500
      this._toastTimer = setTimeout(() => {
        this.toast.show = false
      }, dur)
    },
    _onStorageChanged(e) {
      if (e.key === 'equipai_token' || e.key === 'equipai_user') {
        if (!isLoggedIn() && this.$route.path !== '/login') {
          this.$router.replace({ path: '/login' })
        }
      }
    },
    async _refreshMe() {
      if (!isLoggedIn()) return
      if (this.$route.path === '/login') return
      try {
        const u = await meApi()
        if (u && u.username) {
          refreshUserFromMe(u)
        }
      } catch (e) {
        if (e && e.code === 401) {
          logout()
          this.$router.replace({ path: '/login', query: { redirect: this.$route.fullPath } })
        } else {
          if (!isLoggedIn()) {
            logout()
            this.$router.replace({ path: '/login' })
          }
        }
      }
    }
  }
}
</script>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 32px 0 64px;
  min-width: 0;
}

.global-toast {
  position: fixed;
  top: 24px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 20px;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
  min-width: 240px;
  max-width: min(520px, 92vw);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(0, 212, 255, 0.15) inset;
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  background: rgba(12, 20, 48, 0.92);
  color: var(--text-primary);
  border: 1px solid var(--border-active);
}
.toast-icon {
  width: 22px; height: 22px;
  display: inline-flex;
  align-items: center; justify-content: center;
  border-radius: 50%;
  font-weight: 900;
  font-family: 'Orbitron', sans-serif;
  font-size: 0.75rem;
  flex-shrink: 0;
}
.global-toast.toast-info    { border-color: var(--primary); }
.global-toast.toast-info    .toast-icon { background: var(--primary); color: var(--bg-deep); }
.global-toast.toast-success { border-color: #2ecc71; color: #2ecc71; box-shadow: 0 8px 32px rgba(46,204,113,0.15), 0 0 0 1px rgba(46,204,113,0.25) inset; }
.global-toast.toast-success .toast-icon { background: #2ecc71; color: #0a1a0a; }
.global-toast.toast-warn    { border-color: #ffcc33; color: #ffcc33; box-shadow: 0 8px 32px rgba(255,204,51,0.18), 0 0 0 1px rgba(255,204,51,0.28) inset; }
.global-toast.toast-warn    .toast-icon { background: #ffcc33; color: #3a2b00; }
.global-toast.toast-error   { border-color: #ff4757; color: #ff838c; box-shadow: 0 8px 32px rgba(255,71,87,0.2), 0 0 0 1px rgba(255,71,87,0.3) inset; }
.global-toast.toast-error   .toast-icon { background: #ff4757; color: #fff; }
.toast-text { line-height: 1.4; min-width: 0; word-break: break-word; }

.toast-enter-active, .toast-leave-active { transition: all 220ms ease; }
.toast-enter-from, .toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -16px);
}

/* 页面切换过渡 */
.page-fade-enter-active {
  transition: opacity 180ms ease, transform 180ms ease;
}
.page-fade-leave-active {
  transition: opacity 120ms ease;
}
.page-fade-enter-from {
  opacity: 0;
  transform: translateY(8px);
}
.page-fade-leave-to {
  opacity: 0;
}
</style>
