<template>
  <header class="top-nav">
    <div class="nav-inner">
      <!-- Logo -->
      <div class="logo" @click="goHome">
        <span class="logo-icon">⬡</span>
        <span class="logo-text">EQUIP<span class="highlight">AI</span></span>
      </div>

      <!-- 分组导航 -->
      <nav v-if="menus && menus.length" class="nav-tabs">
        <div
          v-for="group in menus"
          :key="group.key"
          class="nav-group"
          :class="{ hover: hoverGroup === group.key }"
          @mouseenter="group.children.length > 1 && (hoverGroup = group.key)"
          @mouseleave="hoverGroup = null"
        >
          <div
            class="nav-tab"
            :class="{
              'root-active': isGroupActive(group),
              'has-children': group.children.length > 1,
              'accent-purple': group.accent === 'purple'
            }"
            @click="onGroupClick(group)"
          >
            <span class="tab-icon">{{ group.icon }}</span>
            <span class="tab-label">{{ group.label }}</span>
            <span v-if="group.badge" class="tab-badge" :class="'badge-' + (group.accent || 'blue')">{{ group.badge }}</span>
            <span v-if="group.children.length > 1" class="tab-caret">▾</span>
          </div>

          <!-- 子菜单下拉 -->
          <transition name="submenu">
            <div
              v-if="group.children.length > 1 && (hoverGroup === group.key || clickGroup === group.key)"
              class="submenu-panel"
              @click.stop
            >
              <div class="submenu-inner">
                <div
                  v-for="child in group.children"
                  :key="child.path"
                  class="submenu-item"
                  :class="{ active: $route.path === child.path }"
                  @click="go(child.path)"
                >
                  <span class="submenu-label">{{ child.label }}</span>
                </div>
              </div>
            </div>
          </transition>
        </div>
      </nav>

      <!-- 右侧操作 -->
      <div class="nav-actions">
        <div v-if="user" class="user-menu">
          <!-- 消息通知铃铛 -->
          <div class="notif-wrapper" @click.stop>
            <button
              class="notif-bell"
              :class="{ open: notifOpen, 'has-unread': unreadCount > 0 }"
              :title="unreadCount ? `您有 ${unreadCount} 条未读消息` : '消息通知'"
              @click="toggleNotif"
            >
              <span class="bell-icon">🔔</span>
              <span v-if="unreadCount > 0" class="bell-dot">
                {{ unreadCount > 99 ? '99+' : unreadCount }}
              </span>
            </button>

            <transition name="notif-fade">
              <div v-if="notifOpen" class="notif-panel">
                <div class="notif-header">
                  <div class="notif-title">
                    <span>消息通知</span>
                    <span v-if="unreadCount > 0" class="notif-unread-badge">{{ unreadCount }} 条未读</span>
                  </div>
                  <div class="notif-header-actions">
                    <button
                      v-if="unreadCount > 0"
                      class="notif-read-all-btn"
                      @click="markAllRead"
                    >全部标为已读</button>
                    <button
                      v-if="notifications.length > 0"
                      class="notif-delete-all-btn"
                      @click="deleteAll"
                    >清空全部</button>
                  </div>
                </div>
                <div class="notif-divider"></div>
                <div v-if="!notifications.length" class="notif-empty">
                  <div class="empty-icon">📭</div>
                  <div class="empty-text">暂无消息</div>
                </div>
                <div v-else class="notif-list">
                  <div
                    v-for="n in notifications"
                    :key="n.id"
                    class="notif-item"
                    :class="{ unread: !n.is_read }"
                  >
                    <div class="notif-icon" :class="'icon-' + n.type">
                      {{ notifIcon(n.type) }}
                    </div>
                    <div class="notif-body" @click="openNotification(n)">
                      <div class="notif-head">
                        <span class="notif-item-title">{{ n.title }}</span>
                        <span class="notif-time">{{ n._time }}</span>
                      </div>
                      <div class="notif-content">{{ n.content }}</div>
                    </div>
                    <span v-if="!n.is_read" class="notif-point"></span>
                    <button
                      class="notif-delete-btn"
                      @click.stop="deleteSingle(n.id)"
                      :title="`删除这条消息`"
                    >
                      ✕
                    </button>
                  </div>
                </div>
                <div class="notif-divider"></div>
                <div class="notif-footer">
                  <button class="notif-footer-btn" @click="goNotifCenter">
                    查看全部消息 →
                  </button>
                </div>
              </div>
            </transition>
          </div>

          <div class="user-dropdown" @click.stop>
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
                  {{ roleLabel }}
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
                </li>
                <li class="dropdown-item" @click="goNotifCenter">
                  <span class="dd-icon">🔔</span>
                  <span>消息通知</span>
                  <span v-if="unreadCount > 0" class="dd-shortcut notif-inline">{{ unreadCount }}</span>
                </li>
                <li class="dropdown-item" @click="go('/password')">
                  <span class="dd-icon">🔐</span>
                  <span>修改密码</span>
                </li>
                <li v-if="canSeeLogs" class="dropdown-item" @click="go('/logs')">
                  <span class="dd-icon">📋</span>
                  <span>操作日志</span>
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

  <transition name="modal-fade">
    <div v-if="notifDetailOpen" class="notif-detail-mask" @click.self="closeNotifDetail">
      <div class="notif-detail-card card" @click.stop>
        <div class="notif-detail-head">
          <div class="notif-detail-icon" :class="'icon-' + notifDetailData.notification.type">
            {{ notifIcon(notifDetailData.notification.type) }}
          </div>
          <div class="notif-detail-title-wrap">
            <h3 class="notif-detail-title">{{ notifDetailData.notification.title }}</h3>
            <div class="notif-detail-time">{{ _fmtNotifTime(notifDetailData.notification.created_at_ts) }}</div>
          </div>
          <button class="notif-detail-close" @click="closeNotifDetail">✕</button>
        </div>
        <div class="notif-detail-body">
          <div class="notif-detail-content">
            {{ notifDetailData.notification.content }}
          </div>
          <div v-if="notifDetailData.report" class="notif-detail-report">
            <h4 class="notif-detail-subtitle">📋 报告详情</h4>
            <div class="notif-detail-field">
              <span class="field-label">报告编号</span>
              <span class="field-value mono">{{ notifDetailData.report.rid }}</span>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">设备</span>
              <span class="field-value">{{ notifDetailData.report.device || '—' }}</span>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">报告标题</span>
              <span class="field-value">{{ notifDetailData.report.title }}</span>
            </div>
            <div v-if="notifDetailData.report.repair_process" class="notif-detail-field">
              <span class="field-label">维修过程</span>
              <div class="field-value text">{{ notifDetailData.report.repair_process }}</div>
            </div>
            <div v-if="notifDetailData.report.technical_measures" class="notif-detail-field">
              <span class="field-label">技术措施</span>
              <div class="field-value text">{{ notifDetailData.report.technical_measures }}</div>
            </div>
            <div v-if="notifDetailData.report.repair_result" class="notif-detail-field">
              <span class="field-label">维修结果</span>
              <div class="field-value text">{{ notifDetailData.report.repair_result }}</div>
            </div>
            <div v-if="notifDetailData.report.review_remark" class="notif-detail-field">
              <span class="field-label">审核意见</span>
              <div class="field-value text" :class="{ reject: notifDetailData.notification.type === 'report_rejected' }">{{ notifDetailData.report.review_remark }}</div>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">审核结果</span>
              <span class="field-value">
                <span v-if="notifDetailData.notification.type === 'report_approved'" class="status-chip st-approved">✅ 通过</span>
                <span v-else-if="notifDetailData.notification.type === 'report_rejected'" class="status-chip st-rejected">❌ 驳回</span>
                <span v-else-if="notifDetailData.notification.type === 'report_synced'" class="status-chip st-synced">📚 已入库</span>
                <span v-else>{{ notifDetailData.report.status_label || notifDetailData.report.status }}</span>
              </span>
            </div>
            <div v-if="notifDetailData.report.reviewer_name" class="notif-detail-field">
              <span class="field-label">审核人</span>
              <span class="field-value">{{ notifDetailData.report.reviewer_name }}</span>
            </div>
          </div>
          <div v-if="notifDetailData.ticket" class="notif-detail-report">
            <h4 class="notif-detail-subtitle">🎫 工单详情</h4>
            <div class="notif-detail-field">
              <span class="field-label">工单号</span>
              <span class="field-value mono">{{ notifDetailData.ticket.code }}</span>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">设备</span>
              <span class="field-value">{{ notifDetailData.ticket.device_name || '—' }}</span>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">工单标题</span>
              <span class="field-value">{{ notifDetailData.ticket.title }}</span>
            </div>
            <div class="notif-detail-field">
              <span class="field-label">问题描述</span>
              <div class="field-value text">{{ notifDetailData.ticket.problem }}</div>
            </div>
          </div>
        </div>
        <div class="notif-detail-foot">
          <button class="btn btn-outline" @click="closeNotifDetail">关闭</button>
          <button v-if="notifDetailData.notification && notifDetailData.notification.type !== 'ticket_created' && notifDetailData.notification.type !== 'ticket_assigned'" class="btn btn-primary" @click="jumpToRelated">查看完整详情 →</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { authState, logout, resolveAvatarSrc } from '../utils/auth'
import { getRoleHome } from '../router'
import { request, toast } from '../utils/request'

const ROLE_MENUS = {
  sysadmin: [
    { key: 'workbench', label: '仪表盘', icon: '📊',
      children: [{ path: '/home', label: '仪表盘' }] },
    { key: 'ops', label: '设备运维', icon: '🔧', children: [
      { path: '/devices', label: '设备管理' },
      { path: '/admin', label: '维修管理' }
    ]},
    { key: 'ai', label: '智能助手', icon: '🧠', accent: 'purple', badge: 'AI',
      children: [
        { path: '/search', label: '智能检索' },
        { path: '/guide', label: '作业指导' },
        { path: '/case', label: '案例库' },
        { path: '/graph', label: '知识图谱' }
      ]},
    { key: 'sys', label: '用户管理', icon: '⚙',
      children: [{ path: '/users', label: '用户列表' }] }
  ],
  manager: [
    { key: 'workbench', label: '仪表盘', icon: '📊',
      children: [{ path: '/home', label: '仪表盘' }] },
    { key: 'ops', label: '设备运维', icon: '🔧', children: [
      { path: '/devices', label: '设备管理' },
      { path: '/admin', label: '维修管理' }
    ]},
    { key: 'ai', label: '智能助手', icon: '🧠', accent: 'purple', badge: 'AI',
      children: [
        { path: '/search', label: '智能检索' },
        { path: '/guide', label: '作业指导' },
        { path: '/case', label: '案例库' },
        { path: '/graph', label: '知识图谱' }
      ]},
    { key: 'sys', label: '用户管理', icon: '⚙',
      children: [{ path: '/users', label: '用户列表' }] }
  ],
  worker: [
    { key: 'workbench', label: '工作台', icon: '📊',
      children: [{ path: '/desk', label: '我的工作台' }] },
    { key: 'tasks', label: '我的工单', icon: '📋',
      children: [{ path: '/tickets', label: '我的工单' }] },
    { key: 'ai', label: '智能助手', icon: '🧠', accent: 'purple',
      children: [
        { path: '/search', label: '智能检索' },
        { path: '/guide', label: '作业指导' },
        { path: '/graph', label: '知识图谱' },
        { path: '/case', label: '案例库' }
      ]}
  ]
}

const ROLE_PERMISSION_TEXT = {
  sysadmin: '派单 / 统计 / 管理权限',
  manager: '派单 / 统计 / 管理权限',
  worker: '执行 / 上报权限'
}

export default {
  name: 'TopNav',
  data() {
    return {
      dropdownOpen: false,
      hoverGroup: null,
      clickGroup: null,
      notifOpen: false,
      notifications: [],
      unreadCount: 0,
      _notifTimer: null,
      notifDetailOpen: false,
      notifDetailData: {
        notification: null,
        report: null,
        ticket: null
      },
    }
  },
  computed: {
    user() {
      return authState.user
    },
    menus() {
      const role = (this.user && this.user.role) || 'sysadmin'
      return ROLE_MENUS[role] || ROLE_MENUS.sysadmin
    },
    avatarSrc() {
      return resolveAvatarSrc(authState.avatar)
    },
    userInitial() {
      const name = this.displayName
      if (!name) return 'U'
      return name.charAt(0).toUpperCase()
    },
    displayName() {
      if (!this.user) return ''
      return this.user.fullname || this.user.username
    },
    isWorker() {
      return this.user && this.user.role === 'worker'
    },
    roleLabel() {
      if (!this.user) return ''
      return this.user.role_label || {
        sysadmin: '维修管理员',
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
  mounted() {
    document.addEventListener('click', this.handleOutsideClick)
    if (this.user) {
      this.fetchNotifications()
      this._notifTimer = setInterval(() => this.fetchNotifications(true), 30000)
    }
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleOutsideClick)
    if (this._notifTimer) { clearInterval(this._notifTimer); this._notifTimer = null }
  },
  watch: {
    '$route.path'() {
      this.dropdownOpen = false
      this.clickGroup = null
      this.notifOpen = false
    },
    'authState._version'() {
      // 用户切换后刷新通知
      if (this._notifTimer) { clearInterval(this._notifTimer); this._notifTimer = null }
      if (this.user) {
        this.fetchNotifications()
        this._notifTimer = setInterval(() => this.fetchNotifications(true), 30000)
      } else {
        this.notifications = []
        this.unreadCount = 0
      }
    }
  },
  methods: {
    isGroupActive(group) {
      const path = this.$route.path
      if (group.key === 'workbench') {
        return group.children.some(c => path === c.path)
      }
      if (group.key === 'ops') {
        return path === '/devices' || path === '/admin' || path.startsWith('/devices/') || path.startsWith('/admin/')
      }
      if (group.key === 'ai') {
        return path === '/search' || path === '/guide' || path === '/case' ||
               path.startsWith('/search/') || path.startsWith('/guide/') || path.startsWith('/case/')
      }
      if (group.key === 'sys') {
        return path === '/users' || path.startsWith('/users/')
      }
      if (group.key === 'tasks') {
        return path === '/tickets' || path.startsWith('/tickets/')
      }
      return group.children.some(c => path === c.path)
    },
    onGroupClick(group) {
      this.clickGroup = null
      this.hoverGroup = null
      if (group.children.length === 1) {
        this.go(group.children[0].path)
      } else {
        this.clickGroup = group.key
      }
    },
    toggleDropdown() {
      this.notifOpen = false
      this.dropdownOpen = !this.dropdownOpen
    },
    toggleNotif() {
      this.dropdownOpen = false
      this.notifOpen = !this.notifOpen
    },
    handleOutsideClick() {
      this.dropdownOpen = false
      this.clickGroup = null
      this.hoverGroup = null
      this.notifOpen = false
    },
    go(path) {
      this.dropdownOpen = false
      this.clickGroup = null
      this.hoverGroup = null
      this.notifOpen = false
      this.$router.push(path)
    },
    goHome() {
      this.$router.push(getRoleHome(this.user && this.user.role))
    },
    handleLogout() {
      this.dropdownOpen = false
      this.notifOpen = false
      logout()
      this.$router.replace({ path: '/login' })
    },

    // ---------- 通知相关方法 ----------
    async fetchNotifications(silent = false) {
      try {
        const data = await request('/notifications', {
          params: { size: 8, unread_only: 0 },
          silent
        })
        const items = (data && data.items) || []
        this.unreadCount = (data && typeof data.unread_count === 'number') ? data.unread_count : 0
        this.notifications = items.map(n => ({
          ...n,
          is_read: !!n.is_read,
          _time: this._fmtNotifTime(n.created_at_ts)
        }))
      } catch (e) {
        if (!silent) {
          // 接口不存在时静默降级
        }
      }
    },
    async markRead(ids) {
      if (!ids || !ids.length) return
      try {
        await request('/notifications/read', {
          method: 'POST',
          data: { ids: ids },
          silent: true
        })
        this.notifications.forEach(n => { if (ids.includes(n.id)) n.is_read = true })
        this.unreadCount = Math.max(0, this.unreadCount - ids.length)
      } catch (_) {}
    },
    async markAllRead() {
      try {
        await request('/notifications/read', {
          method: 'POST',
          data: { all: true }
        })
        this.notifications.forEach(n => (n.is_read = true))
        this.unreadCount = 0
        toast('已全部标记为已读', 'success')
      } catch (e) {
        toast('操作失败，请稍后再试')
      }
    },
    async deleteSingle(id) {
      try {
        await request('/notifications', {
          method: 'DELETE',
          data: { ids: [id] },
          silent: true
        })
        const idx = this.notifications.findIndex(n => n.id === id)
        if (idx > -1) {
          const wasUnread = !this.notifications[idx].is_read
          this.notifications.splice(idx, 1)
          if (wasUnread) this.unreadCount = Math.max(0, this.unreadCount - 1)
        }
      } catch (_) {}
    },
    async deleteAll() {
      if (!confirm('确定要删除所有消息吗？')) return
      try {
        await request('/notifications', {
          method: 'DELETE',
          data: {},
          silent: true
        })
        this.notifications = []
        this.unreadCount = 0
        toast('已清空所有消息', 'success')
      } catch (e) {
        toast('操作失败，请稍后再试')
      }
    },
    async openNotification(n) {
      if (!n.is_read) this.markRead([n.id])
      this.notifOpen = false
      this.notifDetailData = { notification: n, report: null, ticket: null }
      const type = (n.type || '').toString()
      const relatedId = n.related_id
      if ((type === 'report_submitted' || type.startsWith('report_')) && relatedId) {
        try {
          const report = await request(`/reports/${relatedId}`, { silent: true })
          if (report) this.notifDetailData.report = report
        } catch (_) {}
      } else if ((type === 'ticket_created' || type === 'ticket_assigned') && relatedId) {
        try {
          const res = await request(`/tickets/${relatedId}`, { silent: true })
          this.notifDetailData.ticket = (res && res.data) || res
        } catch (_) {}
      } else if (type === 'device_fault' && relatedId) {
        // 跳转到设备管理并自动打开该设备的详情弹窗
        this.$router.push({ path: '/devices', query: { did: String(relatedId) } })
        return
      } else if (type === 'device_fault') {
        this.go('/devices')
        return
      }
      this.notifDetailOpen = true
    },
    closeNotifDetail() {
      this.notifDetailOpen = false
      this.notifDetailData = { notification: null, report: null, ticket: null }
    },
    jumpToRelated() {
      const n = this.notifDetailData.notification
      if (!n) return
      const type = (n.type || '').toString()
      const relatedId = n.related_id
      this.closeNotifDetail()
      if ((type === 'report_submitted' || type.startsWith('report_')) &&
          this.user && this.user.role !== 'worker') {
        const q = { tab: 'knowledge', kr: 'pending' }
        if (relatedId) q.rid = String(relatedId)
        this.$router.push({ path: '/admin', query: q })
        return
      }
      if (type === 'report_approved' || type === 'report_rejected' || type === 'report_synced') {
        this.$router.push({ path: '/desk', query: { tab: 'contrib' } })
        return
      }
      if (type === 'ticket_assigned' || type === 'ticket_created') {
        this.go('/tickets')
        return
      }
      if (!relatedId && type.startsWith('ticket_')) {
        this.go('/tickets')
        return
      }
      if (this.user && this.user.role === 'worker') this.go('/desk')
      else this.$router.push({ path: '/admin', query: { tab: 'knowledge', kr: 'pending' } })
    },
    goNotifCenter() {
      this.notifOpen = false
      if (this.user && this.user.role === 'worker') {
        this.$router.push({ path: '/desk', query: { tab: 'contrib' } })
      } else {
        this.$router.push({ path: '/admin', query: { tab: 'knowledge', kr: 'pending' } })
      }
    },
    notifIcon(type) {
      switch (type) {
        case 'report_submitted': return '📨'
        case 'report_approved':  return '✅'
        case 'report_rejected':  return '❌'
        case 'report_synced':    return '📚'
        case 'ticket_assigned':  return '🎫'
        case 'system': default:  return '🔔'
      }
    },
    _fmtNotifTime(ts) {
      if (!ts) return ''
      const now = Date.now()
      const diff = Math.floor((now - ts * 1000) / 1000)
      if (diff < 0) return '刚刚'
      if (diff < 60) return '刚刚'
      if (diff < 3600) return Math.floor(diff / 60) + ' 分钟前'
      if (diff < 86400) return Math.floor(diff / 3600) + ' 小时前'
      if (diff < 7 * 86400) return Math.floor(diff / 86400) + ' 天前'
      const d = new Date(ts * 1000)
      return `${d.getMonth() + 1}/${d.getDate()}`
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
  opacity: 0.4;
}

.nav-inner {
  max-width: var(--max-width);
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  gap: 24px;
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

/* ===== 分组导航 ===== */
.nav-tabs {
  display: flex;
  gap: 2px;
  flex: 1;
  position: relative;
}

.nav-group {
  position: relative;
}

.nav-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--duration) var(--ease);
  border: 1px solid transparent;
  cursor: pointer;
  white-space: nowrap;
}

.nav-tab:hover {
  color: var(--text-primary);
  background: var(--primary-subtle);
  border-color: var(--border-subtle);
}

.nav-tab.root-active {
  color: var(--text-primary);
  background: var(--primary-subtle);
  border-color: var(--border-active);
  font-weight: 600;
}

.nav-tab.root-active.accent-purple {
  border-color: rgba(139, 92, 246, 0.45);
  background: rgba(139, 92, 246, 0.10);
}

.tab-icon {
  font-size: 0.9375rem;
}

.tab-label {
  line-height: 1;
}

.tab-caret {
  font-size: 0.625rem;
  margin-left: 2px;
  opacity: 0.7;
  transition: transform var(--duration) var(--ease);
}

.nav-group.hover .tab-caret,
.nav-group:has(.submenu-panel) .click-open .tab-caret {
  transform: rotate(180deg);
}

.tab-badge {
  font-size: 0.625rem;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 999px;
  letter-spacing: 0.5px;
  line-height: 1.4;
}

.tab-badge.badge-purple {
  background: rgba(139, 92, 246, 0.18);
  color: var(--accent-purple);
  border: 1px solid rgba(139, 92, 246, 0.35);
}

.tab-badge.badge-blue {
  background: var(--primary-subtle);
  color: var(--primary);
  border: 1px solid var(--border-active);
}

/* ===== 子菜单下拉 ===== */
.submenu-panel {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  min-width: 180px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.45);
  overflow: hidden;
  z-index: 900;
  transform-origin: top left;
}

.submenu-inner {
  padding: 6px;
  max-height: 280px;
  overflow-y: auto;
}

.submenu-item {
  display: flex;
  align-items: center;
  padding: 9px 14px;
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  transition: background var(--duration) var(--ease), color var(--duration) var(--ease);
  white-space: nowrap;
}

.submenu-item:hover {
  background: var(--primary-subtle);
  color: var(--text-primary);
}

.submenu-item.active {
  background: var(--primary-subtle);
  color: var(--primary);
  font-weight: 600;
}

.submenu-item.active::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 14px;
  border-radius: 2px;
  background: var(--primary);
  margin-right: 8px;
}

.submenu-enter-active,
.submenu-leave-active {
  transition: opacity 160ms var(--ease), transform 160ms var(--ease);
}
.submenu-enter-from,
.submenu-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.97);
}

/* ===== 右侧操作 ===== */
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
.user-role.role-sysadmin { color: var(--primary); }
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
  background: rgba(239, 68, 68, 0.12);
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

/* ===== 消息通知铃铛 ===== */
.notif-wrapper {
  position: relative;
}

.notif-bell {
  position: relative;
  width: 38px;
  height: 38px;
  border-radius: var(--radius);
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration) var(--ease);
}

.notif-bell:hover,
.notif-bell.open {
  background: var(--primary-subtle);
  color: var(--primary);
  border-color: var(--border-subtle);
}

.notif-bell.open {
  border-color: var(--border-active);
}

.bell-icon {
  font-size: 1.125rem;
  line-height: 1;
}

.notif-bell.has-unread .bell-icon {
  animation: bellShake 3.2s ease-in-out infinite;
}

@keyframes bellShake {
  0%, 88%, 100% { transform: rotate(0); }
  90%  { transform: rotate(-12deg); }
  92%  { transform: rotate(10deg); }
  94%  { transform: rotate(-8deg); }
  96%  { transform: rotate(6deg); }
  98%  { transform: rotate(-3deg); }
}

.bell-dot {
  position: absolute;
  top: 2px;
  right: 2px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--accent-red), #f87171);
  color: #fff;
  font-size: 0.625rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  border: 2px solid var(--bg-glass);
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.55);
  transform: scale(0.85);
}

/* ===== 通知下拉面板 ===== */
.notif-panel {
  position: absolute;
  top: calc(100% + 10px);
  right: 0;
  width: 380px;
  max-width: calc(100vw - 40px);
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  box-shadow: 0 10px 36px rgba(0, 0, 0, 0.55), var(--shadow-glow);
  overflow: hidden;
  z-index: 999;
  transform-origin: top right;
}

.notif-fade-enter-active,
.notif-fade-leave-active {
  transition: opacity 160ms var(--ease), transform 160ms var(--ease);
}
.notif-fade-enter-from,
.notif-fade-leave-to {
  opacity: 0;
  transform: translateY(-6px) scale(0.98);
}

.notif-header {
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
}

.notif-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 700;
  font-size: 0.875rem;
  color: var(--text-primary);
}

.notif-unread-badge {
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(239, 68, 68, 0.14);
  color: var(--accent-red);
  font-size: 0.6875rem;
  font-weight: 600;
  border: 1px solid rgba(239, 68, 68, 0.3);
}

.notif-header-actions {
  display: flex;
  gap: 6px;
  align-items: center;
}

.notif-read-all-btn {
  padding: 4px 10px;
  border-radius: var(--radius);
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.notif-read-all-btn:hover {
  background: var(--primary-subtle);
  border-color: var(--border-active);
}

.notif-delete-all-btn {
  padding: 4px 10px;
  border-radius: var(--radius);
  background: transparent;
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--accent-red);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.notif-delete-all-btn:hover {
  background: rgba(239, 68, 68, 0.12);
  border-color: rgba(239, 68, 68, 0.5);
}

.notif-divider {
  height: 1px;
  background: var(--border-subtle);
}

.notif-empty {
  padding: 40px 20px;
  text-align: center;
  color: var(--text-muted);
}
.empty-icon { font-size: 2rem; margin-bottom: 8px; opacity: 0.7; }
.empty-text { font-size: 0.8125rem; }

.notif-list {
  max-height: 360px;
  overflow-y: auto;
}

.notif-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 16px;
  cursor: pointer;
  transition: background var(--duration) var(--ease);
  border-bottom: 1px solid var(--border-subtle);
}

.notif-item:last-child { border-bottom: none; }

.notif-item:hover {
  background: var(--primary-subtle);
}

.notif-item.unread {
  background: linear-gradient(90deg, rgba(59, 130, 246, 0.08), transparent);
}

.notif-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;
  background: var(--primary-subtle);
}
.notif-icon.icon-report_submitted { background: rgba(245, 158, 11, 0.18); }
.notif-icon.icon-report_approved  { background: rgba(16, 185, 129, 0.18); }
.notif-icon.icon-report_rejected  { background: rgba(239, 68, 68, 0.18); }
.notif-icon.icon-report_synced    { background: rgba(59, 130, 246, 0.18); }
.notif-icon.icon-ticket_assigned  { background: rgba(139, 92, 246, 0.18); }
.notif-icon.icon-system           { background: var(--primary-subtle); }

.notif-body {
  flex: 1;
  min-width: 0;
}

.notif-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 4px;
}

.notif-item-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.3;
}

.notif-time {
  font-size: 0.6875rem;
  color: var(--text-muted);
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 1px;
}

.notif-content {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.45;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.notif-point {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  flex-shrink: 0;
  margin-top: 6px;
  box-shadow: 0 0 6px var(--primary-glow);
}

.notif-delete-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.6875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: all var(--duration) var(--ease);
  flex-shrink: 0;
}

.notif-item:hover .notif-delete-btn {
  opacity: 1;
}

.notif-delete-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  color: var(--accent-red);
}

.notif-footer {
  padding: 8px 12px;
  background: linear-gradient(90deg, transparent, var(--primary-subtle), transparent);
}

.notif-footer-btn {
  width: 100%;
  padding: 8px 12px;
  background: transparent;
  border: 1px dashed var(--border-active);
  border-radius: var(--radius);
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}

.notif-footer-btn:hover {
  background: var(--primary-subtle);
  border-style: solid;
}

.notif-inline {
  background: linear-gradient(135deg, var(--accent-red), #f87171);
  color: #fff;
  border-radius: 999px;
  padding: 1px 7px;
  letter-spacing: 0;
  font-weight: 700;
  min-width: 20px;
  text-align: center;
}

/* ===== 消息详情弹窗 ===== */
.notif-detail-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  backdrop-filter: blur(6px);
}

.notif-detail-card {
  width: 90%;
  max-width: 520px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.notif-detail-head {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.notif-detail-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;
}

.notif-detail-title-wrap {
  flex: 1;
  min-width: 0;
}

.notif-detail-title {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
}

.notif-detail-time {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 2px;
}

.notif-detail-close {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  color: var(--text-muted);
  font-size: 0.875rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration) var(--ease);
  flex-shrink: 0;
}

.notif-detail-close:hover {
  background: rgba(239, 68, 68, 0.1);
  color: var(--accent-red);
  border-color: rgba(239, 68, 68, 0.3);
}

.notif-detail-body {
  padding: 16px 20px;
  flex: 1;
  overflow-y: auto;
}

.notif-detail-content {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.6;
  margin-bottom: 16px;
  padding: 12px;
  background: var(--primary-subtle);
  border-radius: var(--radius);
}

.notif-detail-report {
  background: var(--bg-panel);
  border-radius: var(--radius);
  padding: 12px;
}

.notif-detail-subtitle {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin: 0 0 12px 0;
}

.notif-detail-field {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
}

.notif-detail-field:last-child {
  margin-bottom: 0;
}

.notif-detail-field .field-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  min-width: 70px;
  flex-shrink: 0;
  padding-top: 3px;
}

.notif-detail-field .field-value {
  font-size: 0.8125rem;
  color: var(--text-primary);
  flex: 1;
  padding-top: 3px;
}

.notif-detail-field .field-value.text {
  padding-top: 0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.notif-detail-field .field-value.mono {
  font-family: 'SF Mono', 'Monaco', monospace;
}

.notif-detail-field .field-value.reject {
  color: var(--accent-red);
}

.notif-detail-foot {
  padding: 12px 20px;
  border-top: 1px solid var(--border-subtle);
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
.ticket-review-actions { display: flex; gap: 10px; margin-top: 12px; }
.btn-success { background: var(--accent-green); color: #052e16; border: none; padding: 6px 16px; border-radius: var(--radius); cursor: pointer; font-weight: 600; font-size: 0.875rem; }
.btn-success:hover { filter: brightness(1.1); }
.btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-danger { background: var(--accent-red); color: #fff; border: none; padding: 6px 16px; border-radius: var(--radius); cursor: pointer; font-weight: 600; font-size: 0.875rem; }
.btn-danger:hover { filter: brightness(1.1); }
.btn-danger:disabled { opacity: 0.5; cursor: not-allowed; }
.attach-list { display: flex; flex-direction: column; gap: 6px; margin-top: 4px; }
.attach-item { display: flex; justify-content: space-between; align-items: center; padding: 4px 8px; background: rgba(255,255,255,0.03); border-radius: 4px; }
.attach-name { font-size: 0.75rem; color: var(--text-secondary); }
.attach-view { font-size: 0.75rem; color: var(--primary); text-decoration: none; }

.status-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.status-chip.st-approved {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.status-chip.st-rejected {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.status-chip.st-synced {
  background: rgba(59, 130, 246, 0.15);
  color: #3b82f6;
}

.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: opacity 200ms var(--ease);
}

.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}

.modal-fade-enter-active .notif-detail-card,
.modal-fade-leave-active .notif-detail-card {
  transition: transform 200ms var(--ease), opacity 200ms var(--ease);
}

.modal-fade-enter-from .notif-detail-card,
.modal-fade-leave-to .notif-detail-card {
  opacity: 0;
  transform: scale(0.95) translateY(8px);
}
</style>
