<template>
  <header class="top-nav">
    <div class="nav-inner">
      <!-- Logo -->
      <div class="logo" @click="goHome">
        <span class="logo-icon">⬡</span>
        <span class="logo-text">EQUIP<span class="highlight">AI</span></span>
      </div>

      <!-- Tab 导航：按角色动态渲染 -->
      <nav class="nav-tabs">
        <router-link
          v-for="tab in tabs"
          :key="tab.path"
          :to="tab.path"
          class="nav-tab"
          :class="{ active: isTabActive(tab.path) }"
        >
          <span class="tab-icon">{{ tab.icon }}</span>
          {{ tab.label }}
        </router-link>
      </nav>

      <!-- 右侧操作 -->
      <div class="nav-actions">
        <div v-if="user" class="user-menu">
          <div
            class="user-dropdown"
            @click.stop
          >
            <div
              class="user-info dropdown-trigger"
              :class="{ open: dropdownOpen }"
              @click="toggleDropdown"
            >
              <div class="avatar" :class="{ 'has-img': avatarSrc }">
                <img v-if="avatarSrc" :src="avatarSrc" alt="avatar" />
                <template v-else>{{ userInitial }}</template>
              </div>
              <div class="user-meta">
                <div class="user-name">{{ displayName }}</div>
                <div class="user-role" :class="'role-' + (user.role || 'sysadmin')">
                  {{ user.demo ? '演示模式 · ' : '' }}{{ roleLabel }}
                </div>
              </div>
              <span class="caret">▾</span>
            </div>

            <div v-if="dropdownOpen" class="dropdown-panel">
              <div class="dropdown-header">
                <div class="dropdown-avatar" :class="{ 'has-img': avatarSrc }">
                  <img v-if="avatarSrc" :src="avatarSrc" alt="avatar" />
                  <template v-else>{{ userInitial }}</template>
                </div>
                <div class="dropdown-user">
                  <div class="dropdown-username">{{ displayName }}</div>
                  <div class="dropdown-sub">{{ roleLabel }} · {{ rolePermissionText }}</div>
                </div>
              </div>
              <div class="dropdown-divider"></div>
              <ul class="dropdown-list">
                <li class="dropdown-item" @click="go('/profile')">
                  <span class="dd-icon">👤</span>
                  <span>个人信息</span>
                  <span class="dd-shortcut">⌘P</span>
                </li>
                <li class="dropdown-item" @click="go('/password')">
                  <span class="dd-icon">🔐</span>
                  <span>修改密码</span>
                  <span class="dd-shortcut">⌘K</span>
                </li>
                <li v-if="canSeeLogs" class="dropdown-item" @click="go('/logs')">
                  <span class="dd-icon">📋</span>
                  <span>操作日志</span>
                  <span class="dd-shortcut">⌘L</span>
                </li>
              </ul>
              <div class="dropdown-divider"></div>
              <ul class="dropdown-list">
                <li class="dropdown-item danger" @click="handleLogout">
                  <span class="dd-icon">🚪</span>
                  <span>退出登录</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
        <router-link v-else to="/login" class="btn btn-outline btn-sm">登录</router-link>
      </div>
    </div>
  </header>
</template>

<script>
import { getUser, logout, getAvatar, resolveAvatarSrc } from '../utils/auth'
import { getRoleHome } from '../router'

const ROLE_TABS = {
  sysadmin: [
    { path: '/home', label: '仪表盘', icon: '◈' },
    { path: '/admin', label: '维修管理', icon: '☗' },
    { path: '/search', label: '智能检索', icon: '◎' },
    { path: '/guide', label: '作业指导', icon: '⇢' },
    { path: '/case', label: '案例库', icon: '▣' }
  ],
  manager: [
    { path: '/admin', label: '工作台', icon: '☗' },
    { path: '/search', label: '智能检索', icon: '◎' },
    { path: '/guide', label: '作业指导', icon: '⇢' },
    { path: '/case', label: '案例库', icon: '▣' }
  ],
  worker: [
    { path: '/worker', label: '我的工单', icon: '🔧' },
    { path: '/search', label: '智能检索', icon: '◎' },
    { path: '/guide', label: '作业指导', icon: '⇢' },
    { path: '/case', label: '案例库', icon: '▣' }
  ]
}

const ROLE_PERMISSION_TEXT = {
  sysadmin: '超级权限',
  manager: '派单 / 统计 / 管理权限',
  worker: '执行 / 上报权限'
}

export default {
  name: 'TopNav',
  data() {
    return {
      tabs: [],
      user: null,
      dropdownOpen: false,
      avatarSrc: ''
    }
  },
  computed: {
    userInitial() {
      const name = this.displayName
      if (!name) return 'U'
      return name.charAt(0).toUpperCase()
    },
    displayName() {
      if (!this.user) return ''
      return this.user.fullname || this.user.username
    },
    roleLabel() {
      if (!this.user) return ''
      return this.user.role_label || {
        sysadmin: '系统管理员',
        manager: '维修管理员',
        worker: '维修工'
      }[this.user.role] || '访客'
    },
    rolePermissionText() {
      return ROLE_PERMISSION_TEXT[(this.user && this.user.role) || 'sysadmin']
    },
    canSeeLogs() {
      return !this.user || this.user.role !== 'worker'
    }
  },
  created() {
    this.refreshUser()
    this.refreshAvatar()
    window.addEventListener('storage', this.refreshUser)
    window.addEventListener('equipai-avatar-changed', this.refreshAvatar)
  },
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
    this.refreshAvatar()
  },
  beforeUnmount() {
    window.removeEventListener('storage', this.refreshUser)
    window.removeEventListener('equipai-avatar-changed', this.refreshAvatar)
    document.removeEventListener('click', this.handleOutsideClick)
  },
  watch: {
    '$route.path'() {
      this.refreshUser()
      this.dropdownOpen = false
    }
  },
  methods: {
    refreshUser() {
      this.user = getUser()
      const role = (this.user && this.user.role) || 'sysadmin'
      this.tabs = ROLE_TABS[role] || ROLE_TABS.sysadmin
    },
    refreshAvatar() {
      this.avatarSrc = resolveAvatarSrc(getAvatar())
    },
    isTabActive(path) {
      if (path === '/home') return this.$route.path === '/home'
      if (path === '/admin') return this.$route.path === '/admin'
      if (path === '/worker') return this.$route.path === '/worker'
      return this.$route.path === path
    },
    toggleDropdown() {
      this.dropdownOpen = !this.dropdownOpen
    },
    handleOutsideClick() {
      this.dropdownOpen = false
    },
    go(path) {
      this.dropdownOpen = false
      this.$router.push(path)
    },
    goHome() {
      this.$router.push(getRoleHome(this.user && this.user.role))
    },
    handleLogout() {
      this.dropdownOpen = false
      logout()
      this.user = null
      this.$router.replace({ path: '/login' })
    }
  }
}
</script>

<style scoped>
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  height: var(--nav-height);
  background: var(--bg-glass);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--border-subtle);
}

.top-nav::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, var(--primary-dim), transparent);
  opacity: 0.6;
}

.nav-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 32px;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  cursor: pointer;
  user-select: none;
}

.logo-icon {
  font-size: 1.5rem;
  color: var(--primary);
  filter: drop-shadow(0 0 6px var(--primary-glow));
}

.logo-text {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.125rem;
  font-weight: 700;
  letter-spacing: 2px;
  color: var(--text-primary);
}

.logo-text .highlight {
  color: var(--primary);
}

.nav-tabs {
  display: flex;
  gap: 4px;
  flex: 1;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--duration) var(--ease);
  border: 1px solid transparent;
}

.nav-tab:hover {
  color: var(--text-primary);
  background: var(--primary-subtle);
  border-color: var(--border-subtle);
}

.nav-tab.active {
  color: var(--primary);
  background: var(--primary-subtle);
  border-color: var(--border-active);
}

.tab-icon {
  font-size: 0.9375rem;
}

.nav-actions {
  flex-shrink: 0;
}

.user-menu {
  display: flex;
  align-items: center;
  gap: 14px;
}

.user-dropdown {
  position: relative;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dropdown-trigger {
  padding: 4px 8px 4px 4px;
  border-radius: var(--radius);
  cursor: pointer;
  border: 1px solid transparent;
  transition: all var(--duration) var(--ease);
}

.dropdown-trigger:hover,
.dropdown-trigger.open {
  background: var(--primary-subtle);
  border-color: var(--border-subtle);
}

.dropdown-trigger.open {
  border-color: var(--border-active);
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--primary-subtle);
  border: 1px solid var(--border-active);
  color: var(--primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.8125rem;
  font-family: 'Orbitron', sans-serif;
  overflow: hidden;
  flex-shrink: 0;
}
.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.avatar.has-img {
  background: #000;
  color: transparent;
}

.user-meta {
  line-height: 1.2;
}

.user-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}

.user-role {
  font-size: 0.625rem;
  letter-spacing: 0.5px;
  margin-top: 2px;
  font-weight: 600;
}
.user-role.role-sysadmin { color: #a855f7; }
.user-role.role-manager { color: var(--primary); }
.user-role.role-worker { color: var(--accent-green); }

.caret {
  color: var(--text-secondary);
  font-size: 0.625rem;
  margin-left: 4px;
  transition: transform var(--duration) var(--ease);
}

.dropdown-trigger.open .caret {
  transform: rotate(180deg);
  color: var(--primary);
}

/* ===== Dropdown Panel ===== */
.dropdown-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  min-width: 280px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5), var(--shadow-glow);
  overflow: hidden;
  z-index: 999;
  animation: dropdownIn 180ms var(--ease);
}

@keyframes dropdownIn {
  from {
    opacity: 0;
    transform: translateY(-6px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dropdown-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
  border-bottom: 1px solid var(--border-subtle);
}

.dropdown-avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary);
  color: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
  font-size: 1rem;
  flex-shrink: 0;
  box-shadow: 0 0 0 2px var(--primary-glow);
  overflow: hidden;
}
.dropdown-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.dropdown-avatar.has-img {
  background: #000;
  color: transparent;
}

.dropdown-user {
  flex: 1;
  min-width: 0;
}

.dropdown-username {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.2;
}

.dropdown-sub {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  margin-top: 4px;
  letter-spacing: 0.3px;
}

.dropdown-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 0;
}

.dropdown-list {
  list-style: none;
  padding: 6px;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 12px;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-primary);
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease);
  user-select: none;
}

.dropdown-item:hover {
  background: var(--primary-subtle);
  color: var(--primary);
}

.dropdown-item.danger:hover {
  background: rgba(255, 71, 87, 0.12);
  color: var(--accent-red);
}

.dd-icon {
  font-size: 0.875rem;
  width: 20px;
  text-align: center;
  flex-shrink: 0;
}

.dd-shortcut {
  margin-left: auto;
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

.btn-sm {
  padding: 6px 16px;
  font-size: 0.8125rem;
}
</style>
