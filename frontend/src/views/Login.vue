<template>
  <div class="login-wrapper">
    <div class="login-card card">
      <!-- Logo 区 -->
      <div class="login-brand">
        <span class="brand-icon">⬡</span>
        <h1 class="brand-name">EQUIP<span class="highlight">AI</span></h1>
        <p class="brand-sub">设备检修智能系统</p>
      </div>

      <!-- 登录表单 -->
      <form @submit.prevent="login" class="login-form">
        <div class="form-group">
          <label class="form-label">用户名</label>
          <input
            v-model="username"
            class="input"
            placeholder="请输入用户名"
            autocomplete="username"
          />
        </div>
        <div class="form-group">
          <label class="form-label">密码</label>
          <input
            v-model="password"
            type="password"
            class="input"
            placeholder="请输入密码"
            autocomplete="current-password"
          />
        </div>
        <button type="submit" class="btn btn-primary btn-block">登 录</button>
      </form>

      <!-- 提示消息 -->
      <p v-if="msg" class="form-msg" :class="{ error: isError }">{{ msg }}</p>

      <!-- 角色快速切换 -->
      <div class="role-picker">
        <div class="role-title">快速选择演示角色</div>
        <div class="role-list">
          <button
            v-for="r in demoRoles"
            :key="r.username"
            class="role-chip"
            :class="{ active: username === r.username }"
            @click="quickLogin(r)"
            type="button"
          >
            <span class="role-chip-icon">{{ r.icon }}</span>
            <span class="role-chip-name">{{ r.role_label }}</span>
            <span class="role-chip-user">{{ r.username }} / 123456</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { setToken, setUser } from '../utils/auth'

const DEMO_ROLES = {
  admin: { username: 'admin', role: 'sysadmin', role_label: '系统管理员', fullname: '系统管理员', icon: '⚙' },
  manager: { username: 'manager', role: 'manager', role_label: '维修管理员', fullname: '王主任', icon: '☗' },
  worker: { username: 'worker', role: 'worker', role_label: '维修工', fullname: '李师傅', icon: '🔧' }
}

function _roleHome(role) {
  if (role === 'manager') return '/admin'
  if (role === 'worker') return '/worker'
  return '/home'
}

export default {
  name: 'Login',
  data() {
    return {
      username: '',
      password: '',
      msg: '',
      isError: true,
      demoRoles: Object.values(DEMO_ROLES)
    }
  },
  methods: {
    quickLogin(r) {
      this.username = r.username
      this.password = '123456'
      this.$nextTick(() => this.login())
    },
    async login() {
      if (!this.username.trim() || !this.password.trim()) {
        this.msg = '请输入用户名和密码'
        this.isError = true
        return
      }
      try {
        const res = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            username: this.username,
            password: this.password
          })
        })
        const data = await res.json()

        const demo = DEMO_ROLES[this.username]
        if (data.code === 200) {
          this.msg = '登录成功！'
          this.isError = false
          setToken(data.token)
          const user = data.user || { username: this.username }
          setUser({
            username: user.username,
            fullname: user.fullname || user.username,
            role: user.role || 'sysadmin',
            role_label: user.role_label || (user.role === 'manager' ? '维修管理员' : user.role === 'worker' ? '维修工' : '系统管理员'),
            loginAt: new Date().toISOString()
          })
          const redirect = this.$route.query.redirect || _roleHome(user.role || 'sysadmin')
          setTimeout(() => this.$router.replace(redirect), 500)
        } else if (demo && this.password === '123456') {
          this.msg = '登录成功！(演示模式 · 后端未同步)'
          this.isError = false
          setToken('demo-token-' + Date.now())
          setUser({
            username: demo.username,
            fullname: demo.fullname,
            role: demo.role,
            role_label: demo.role_label,
            loginAt: new Date().toISOString(),
            demo: true
          })
          const redirect = this.$route.query.redirect || _roleHome(demo.role)
          setTimeout(() => this.$router.replace(redirect), 500)
        } else {
          this.msg = data.msg || '用户名或密码错误'
          this.isError = true
        }
      } catch (err) {
        const demo = DEMO_ROLES[this.username]
        if (demo && this.password === '123456') {
          this.msg = '登录成功！(演示模式)'
          this.isError = false
          setToken('demo-token-' + Date.now())
          setUser({
            username: demo.username,
            fullname: demo.fullname,
            role: demo.role,
            role_label: demo.role_label,
            loginAt: new Date().toISOString(),
            demo: true
          })
          const redirect = this.$route.query.redirect || _roleHome(demo.role)
          setTimeout(() => this.$router.replace(redirect), 500)
        } else {
          this.msg = '请求失败：后端未启动，请使用下方角色卡片体验演示模式'
          this.isError = true
        }
      }
    }
  }
}
</script>

<style scoped>
.login-wrapper {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  padding: 40px;
}

.login-brand {
  text-align: center;
  margin-bottom: 36px;
}

.brand-icon {
  font-size: 3rem;
  color: var(--primary);
  filter: drop-shadow(0 0 12px var(--primary-glow));
  display: block;
  margin-bottom: 12px;
}

.brand-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 3px;
  margin-bottom: 4px;
}

.brand-name .highlight {
  color: var(--primary);
}

.brand-sub {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 0.9375rem;
  margin-top: 8px;
}

.form-msg {
  text-align: center;
  margin-top: 16px;
  font-size: 0.8125rem;
  color: var(--accent-green);
}

.form-msg.error {
  color: var(--accent-red);
}

.role-picker {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid var(--border-subtle);
}

.role-title {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 12px;
  text-align: center;
}

.role-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.role-chip {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: var(--primary-subtle);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  text-align: left;
  color: inherit;
  font-family: inherit;
}

.role-chip:hover {
  border-color: var(--primary-dim);
  transform: translateY(-1px);
}

.role-chip.active {
  border-color: var(--primary);
  box-shadow: 0 0 0 1px var(--primary), 0 0 12px rgba(0, 212, 255, 0.2);
  background: rgba(0, 212, 255, 0.12);
}

.role-chip-icon {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  color: var(--primary);
  border: 1px solid var(--border-active);
  flex-shrink: 0;
}

.role-chip-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.2;
}

.role-chip-user {
  margin-left: auto;
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}
</style>
