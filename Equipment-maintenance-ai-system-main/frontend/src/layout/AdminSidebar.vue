<template>
  <aside class="admin-sidebar">
    <div class="sidebar-inner">
      <div class="sidebar-header">
        <div class="sidebar-title">功能模块</div>
        <div class="sidebar-sub">维修管理员工作台</div>
      </div>

      <ul class="sidebar-menu">
        <li
          v-for="m in menus"
          :key="m.path"
          class="menu-item"
          :class="{
            active: isActive(m.path, m.exact),
            group: !!m.group
          }"
        >
          <router-link :to="m.path" class="menu-link">
            <span class="menu-icon">{{ m.icon }}</span>
            <span class="menu-label">{{ m.label }}</span>
            <span v-if="m.badge" class="menu-badge" :class="m.badgeCls">{{ m.badge }}</span>
            <span class="menu-arrow">›</span>
          </router-link>
        </li>
      </ul>

      <div class="sidebar-footer">
        <div class="footer-quick">
          <div class="footer-title">快捷入口</div>
          <div class="footer-links">
            <router-link to="/logs" class="footer-link">
              <span>📋</span> 操作日志
            </router-link>
            <router-link to="/profile" class="footer-link">
              <span>👤</span> 个人信息
            </router-link>
            <router-link to="/password" class="footer-link">
              <span>🔐</span> 修改密码
            </router-link>
          </div>
        </div>

        <div class="footer-tip">
          <span class="tip-icon">💡</span>
          <span class="tip-text">提示：维修管理模块可派发与复核工单，用户管理仅管理员可操作</span>
        </div>
      </div>
    </div>
  </aside>
</template>

<script>
export default {
  name: 'AdminSidebar',
  data() {
    return {
      menus: [
        { path: '/home', label: '仪表盘', icon: '📊', group: '概览' },
        { path: '/devices', label: '设备管理', icon: '🏗️', badge: 'NEW', badgeCls: 'cyan' },
        { path: '/admin', label: '维修管理', icon: '🛠️', badge: this.$route.path === '/admin' ? '' : '5', badgeCls: 'orange' },
        { path: '/search', label: '智能检索', icon: '🤖', group: '工具' },
        { path: '/guide', label: '作业指导', icon: '📖' },
        { path: '/case', label: '案例库', icon: '📚' },
        { path: '/graph', label: '知识图谱', icon: '🧠' },
        { path: '/users', label: '用户管理', icon: '👥', group: '管理', badge: 'ADMIN', badgeCls: 'red' }
      ]
    }
  },
  methods: {
    isActive(path, exact) {
      const cur = this.$route.path
      if (exact || path === '/home') return cur === path
      return cur === path || cur.startsWith(path + '/')
    }
  }
}
</script>

<style scoped>
.admin-sidebar {
  width: 248px;
  flex-shrink: 0;
  background: linear-gradient(180deg, var(--bg-elevated), var(--bg-deep));
  border-right: 1px solid var(--border-subtle);
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - var(--nav-height));
  position: sticky;
  top: var(--nav-height);
  z-index: 90;
}

.sidebar-inner {
  display: flex;
  flex-direction: column;
  padding: 20px 14px;
  gap: 16px;
  height: 100%;
}

.sidebar-header {
  padding: 0 10px 12px;
  border-bottom: 1px solid var(--border-subtle);
}
.sidebar-title {
  font-size: 0.6875rem;
  font-weight: 700;
  color: var(--text-muted);
  letter-spacing: 2px;
  text-transform: uppercase;
}
.sidebar-sub {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
  margin-top: 4px;
}

.sidebar-menu {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
}

.menu-item {
  position: relative;
}

.menu-link {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 14px;
  border-radius: var(--radius);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.875rem;
  font-weight: 500;
  transition: all var(--duration) var(--ease);
  border: 1px solid transparent;
  position: relative;
}

.menu-link:hover {
  background: var(--primary-subtle);
  color: var(--text-primary);
  border-color: var(--border-subtle);
}

.menu-item.active .menu-link {
  background: linear-gradient(135deg, var(--primary-subtle), rgba(79, 214, 255, 0.04));
  color: var(--primary);
  border-color: var(--border-active);
  box-shadow: inset 2px 0 0 var(--primary);
  font-weight: 600;
}

.menu-icon {
  font-size: 1.125rem;
  width: 22px;
  text-align: center;
  flex-shrink: 0;
}

.menu-label {
  flex: 1;
  min-width: 0;
}

.menu-badge {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  background: var(--primary-subtle);
  color: var(--primary);
  border: 1px solid var(--border-active);
}
.menu-badge.orange {
  background: rgba(255, 156, 86, 0.12);
  color: #ff9c56;
  border-color: rgba(255, 156, 86, 0.3);
}
.menu-badge.cyan {
  background: rgba(34, 211, 238, 0.1);
  color: #22d3ee;
  border-color: rgba(34, 211, 238, 0.3);
}
.menu-badge.red {
  background: rgba(255, 71, 87, 0.12);
  color: var(--accent-red);
  border-color: rgba(255, 71, 87, 0.3);
}

.menu-arrow {
  color: var(--text-muted);
  font-size: 0.75rem;
  opacity: 0.6;
  transform: translateX(-4px);
  transition: all var(--duration) var(--ease);
}
.menu-item.active .menu-arrow {
  opacity: 1;
  transform: translateX(0);
  color: var(--primary);
}

.sidebar-footer {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
}

.footer-title {
  font-size: 0.625rem;
  font-weight: 700;
  letter-spacing: 1.5px;
  color: var(--text-muted);
  margin-bottom: 6px;
  text-transform: uppercase;
}

.footer-links {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.footer-link {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  border-radius: 6px;
  color: var(--text-secondary);
  text-decoration: none;
  font-size: 0.75rem;
  transition: all var(--duration) var(--ease);
}
.footer-link:hover {
  background: var(--primary-subtle);
  color: var(--primary);
}

.footer-tip {
  display: flex;
  gap: 8px;
  padding: 10px;
  background: rgba(255, 204, 51, 0.06);
  border: 1px solid rgba(255, 204, 51, 0.2);
  border-radius: 8px;
}
.tip-icon {
  font-size: 0.875rem;
  flex-shrink: 0;
}
.tip-text {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  line-height: 1.5;
}
</style>
