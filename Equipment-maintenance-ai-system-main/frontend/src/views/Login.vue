<template>
  <div class="login-wrapper">
    <div class="login-container card">
      <!-- 左侧：品牌展示区 -->
      <aside class="login-showcase">
        <div class="showcase-bg" aria-hidden="true"></div>
        <div class="showcase-inner">
          <div class="showcase-tag">1. 登录页</div>
          <div class="showcase-brand">
            <span class="brand-icon big">⬡</span>
            <h1 class="brand-name big">EQUIP<span class="highlight">AI</span></h1>
            <p class="brand-sub big">设备检修智能作业系统</p>
            <p class="brand-slogan">AI 赋能工业运维 · 智能诊断 · 高效管理</p>
          </div>
          <div class="showcase-feats">
            <div class="feat-card">
              <span class="feat-icon">🧠</span>
              <div class="feat-main">
                <div class="feat-title">智能诊断</div>
                <div class="feat-desc">AI 故障分析</div>
              </div>
            </div>
            <div class="feat-card">
              <span class="feat-icon">📚</span>
              <div class="feat-main">
                <div class="feat-title">知识赋能</div>
                <div class="feat-desc">案例经验沉淀</div>
              </div>
            </div>
            <div class="feat-card">
              <span class="feat-icon">👥</span>
              <div class="feat-main">
                <div class="feat-title">高效协同</div>
                <div class="feat-desc">工单流程管理</div>
              </div>
            </div>
          </div>
        </div>
      </aside>

      <!-- 右侧：登录卡（保留原结构 1:1） -->
      <section class="login-panel">
        <div class="login-card card">
          <!-- Logo 区 -->
          <div class="login-brand">
            <span class="brand-icon">⬡</span>
            <h1 class="brand-name">EQUIP<span class="highlight">AI</span></h1>
            <p class="brand-sub">设备检修智能系统 · 登录</p>
          </div>

          <!-- 角色切换 Tab -->
          <div class="role-tabs">
            <button
              v-for="r in roles"
              :key="r.key"
              class="role-tab"
              :class="{ active: role === r.key }"
              @click="role = r.key"
              type="button"
            >
              <span class="rt-icon">{{ r.icon }}</span>
              <span>{{ r.label }}</span>
            </button>
          </div>

          <!-- 登录表单 -->
          <form @submit.prevent="login" class="login-form">
            <div class="form-group">
              <label class="form-label">账号</label>
              <input
                v-model="username"
                class="input"
                :placeholder="role === 'manager' ? '请输入维修管理员姓名/工号' : '请输入一线检修员姓名/工号'"
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
                @keyup.enter="login"
              />
            </div>
            <div class="form-row">
              <label class="remember">
                <input v-model="remember" type="checkbox" />
                <span class="check-icon">{{ remember ? '✔' : '' }}</span>
                <span class="remember-txt">记住账号</span>
              </label>
            </div>
            <button type="submit" class="btn btn-primary btn-block" :disabled="loading">
              <span v-if="loading" class="loading-dots">登 录 中 . . .</span>
              <span v-else>登 录</span>
            </button>
          </form>

          <!-- 提示消息 -->
          <p v-if="msg" class="form-msg" :class="{ error: isError }">{{ msg }}</p>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { login as saveLogin } from '../utils/auth'
import { loginApi } from '../utils/api'
import { getRoleHome } from '../router'

const ROLES = [
  { key: 'manager', label: '维修管理员', role_label: '维修管理员', icon: '☗', home: '/home' },
  { key: 'worker', label: '一线检修员', role_label: '维修工', icon: '🔧', home: '/desk' }
]

const REMEMBER_KEY = 'equipai_remember_account'

export default {
  name: 'Login',
  data() {
    const remembered = localStorage.getItem(REMEMBER_KEY)
    let defUser = ''
    let defRole = 'manager'
    let checked = false
    if (remembered) {
      try {
        const obj = JSON.parse(remembered)
        defUser = obj.username || ''
        defRole = obj.role || 'manager'
        checked = !!obj.remember
      } catch (_) {}
    }
    return {
      roles: ROLES,
      role: defRole,
      username: defUser,
      password: '',
      remember: checked,
      msg: '',
      isError: false,
      loading: false
    }
  },
  methods: {
    _persistRemember() {
      if (this.remember) {
        localStorage.setItem(REMEMBER_KEY, JSON.stringify({
          username: this.username.trim(),
          role: this.role,
          remember: true
        }))
      } else {
        localStorage.removeItem(REMEMBER_KEY)
      }
    },
    _persistLogin({ token, user }) {
      this._persistRemember()
      const u = user || {}
      const role = u.role || this.role
      const userObj = {
        id: u.id,
        username: u.username || this.username.trim(),
        fullname: u.fullname || u.username || this.username.trim(),
        role,
        role_label: u.role_label || (ROLES.find(r => r.key === role) || {}).role_label || '维修工',
        loginAt: new Date().toISOString()
      }
      saveLogin(userObj, token)
      const redirect = this.$route.query.redirect || getRoleHome(role)
      setTimeout(() => this.$router.replace(redirect), 300)
    },
    async login() {
      const u = this.username.trim()
      if (!u) {
        this.msg = '请输入账号（姓名或工号）'
        this.isError = true
        return
      }
      if (!this.password) {
        this.msg = '请输入密码'
        this.isError = true
        return
      }
      this.loading = true
      this.msg = ''
      this.isError = false

      try {
        const data = await loginApi({ username: u, password: this.password, role: this.role })
        this.msg = '登录成功！'
        this.loading = false
        this._persistLogin(data)
      } catch (err) {
        this.loading = false
        this.msg = (err && err.message) ? err.message : '账号或密码错误'
        this.isError = true
      }
    }
  }
}
</script>

<style scoped>
/* ========== 外层容器 ========== */
.login-wrapper {
  min-height: 100vh;
  display: flex;
  padding: 32px 28px;
  background:
    radial-gradient(ellipse at 10% 0%, rgba(0, 212, 255, 0.18), transparent 50%),
    radial-gradient(ellipse at 100% 100%, rgba(59, 130, 246, 0.14), transparent 55%),
    var(--bg-deep, #050b1f);
  box-sizing: border-box;
}

/* 大圆角容器：左 1.1fr 展示 / 右 0.9fr 登录
   用 margin:auto 实现居中：
   - 内容 < 视口 → 完美水平+垂直居中（等价 flex center）
   - 内容 > 视口 → 自动从顶部开始排，document 滚动条能完整滚到上下所有内容（解决 flex center 截顶部问题） */
.login-container {
  width: 100%;
  max-width: 1180px;
  min-height: 580px;
  margin: auto;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 0;
  overflow: hidden;
  border-radius: 24px;
  padding: 0;
  background: transparent;
  border: 1px solid var(--border-subtle);
  box-shadow:
    0 30px 80px rgba(0, 0, 0, 0.55),
    0 0 0 1px rgba(0, 212, 255, 0.08) inset;
}
.login-container::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: 25px;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.28), transparent 45%, rgba(59, 130, 246, 0.22));
  z-index: -1;
  opacity: 0.8;
  filter: blur(0.2px);
  pointer-events: none;
}

/* ========== 左侧：品牌展示区 ========== */
.login-showcase {
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: stretch;
  justify-content: stretch;
}
.showcase-bg {
  position: absolute;
  inset: 0;
  background-color: #0a1530;
  background-image:
    /* 渐变遮罩：让文字更清晰 */
    linear-gradient(180deg, rgba(10, 21, 48, 0.4) 0%, rgba(10, 21, 48, 0.72) 55%, rgba(5, 11, 31, 0.9) 100%),
    linear-gradient(135deg, rgba(0, 180, 255, 0.15), transparent 55%),
    /* 内嵌 SVG 工业塔底图 */
    url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 900 720' preserveAspectRatio='xMidYMid slice'><defs><linearGradient id='skybg' x1='0' y1='0' x2='0' y2='1'><stop offset='0%25' stop-color='%230a1a3e'/><stop offset='100%25' stop-color='%23050d26'/></linearGradient><linearGradient id='gcol' x1='0' y1='0' x2='0' y2='1'><stop offset='0%25' stop-color='%2322d3ee' stop-opacity='0.9'/><stop offset='50%25' stop-color='%230090d4' stop-opacity='0.5'/><stop offset='100%25' stop-color='%23003a6b' stop-opacity='0.3'/></linearGradient><linearGradient id='pipe' x1='0' y1='0' x2='1' y2='0'><stop offset='0%25' stop-color='%2322d3ee'/><stop offset='50%25' stop-color='%233b82f6'/><stop offset='100%25' stop-color='%2360a5fa'/></linearGradient><filter id='glow' x='-50%25' y='-50%25' width='200%25' height='200%25'><feGaussianBlur stdDeviation='3' result='col'/><feMerge><feMergeNode in='col'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs><rect width='900' height='720' fill='url(%23skybg)'/><g opacity='0.85'><!-- 地面平台 --><rect x='20' y='595' width='860' height='22' rx='3' fill='%230b1f48' stroke='%2300d4ff' stroke-opacity='0.35'/><rect x='60' y='617' width='780' height='10' fill='%23050f2c' opacity='0.8'/><!-- 塔 1：大型精馏塔（左） --><rect x='140' y='230' width='76' height='365' rx='14' fill='url(%23gcol)' stroke='%2322d3ee' stroke-width='1.2' stroke-opacity='0.8'/><circle cx='178' cy='245' r='12' fill='%2305132f' stroke='%2322d3ee' stroke-opacity='0.7'/><g stroke='%2322d3ee' stroke-opacity='0.55' stroke-width='1'><line x1='140' y1='300' x2='216' y2='300'/><line x1='140' y1='360' x2='216' y2='360'/><line x1='140' y1='420' x2='216' y2='420'/><line x1='140' y1='480' x2='216' y2='480'/><line x1='140' y1='540' x2='216' y2='540'/></g><!-- 塔顶小罐 + 灯 --><rect x='164' y='185' width='28' height='46' rx='5' fill='%2308234d' stroke='%2322d3ee' stroke-opacity='0.75'/><circle cx='178' cy='175' r='5' fill='%2322d3ee' filter='url(%23glow)'/><!-- 塔 2：中等塔（中右） --><rect x='430' y='310' width='54' height='285' rx='10' fill='url(%23gcol)' stroke='%233b82f6' stroke-width='1.1' stroke-opacity='0.7'/><g stroke='%2360a5fa' stroke-opacity='0.45' stroke-width='1'><line x1='430' y1='355' x2='484' y2='355'/><line x1='430' y1='405' x2='484' y2='405'/><line x1='430' y1='455' x2='484' y2='455'/><line x1='430' y1='505' x2='484' y2='505'/><line x1='430' y1='555' x2='484' y2='555'/></g><circle cx='457' cy='320' r='4' fill='%2334d399' filter='url(%23glow)'/><!-- 塔 3：细长加热炉排管（右） --><g stroke='%233b82f6' stroke-opacity='0.7'><line x1='630' y1='375' x2='630' y2='595' stroke-width='5' stroke-linecap='round'/><line x1='660' y1='350' x2='660' y2='595' stroke-width='5' stroke-linecap='round'/><line x1='690' y1='390' x2='690' y2='595' stroke-width='5' stroke-linecap='round'/><line x1='720' y1='365' x2='720' y2='595' stroke-width='5' stroke-linecap='round'/></g><rect x='618' y='360' width='114' height='20' rx='4' fill='%230a2050' stroke='%233b82f6' stroke-opacity='0.65'/><circle cx='760' cy='355' r='5' fill='%23f59e0b' filter='url(%23glow)'/><!-- 横向连接管道（发光） --><g stroke='url(%23pipe)' stroke-width='4' stroke-linecap='round' filter='url(%23glow)' opacity='0.95'><path d='M216 340 Q310 300 430 340 L430 390 Q540 405 630 390 L630 450 L720 450' fill='none'/></g><g stroke='%2322d3ee' stroke-opacity='0.6' stroke-width='1.2' stroke-dasharray='4 6'><path d='M178 400 Q320 450 457 460 Q560 468 700 480' fill='none'/></g><!-- 远景小建筑群 --><g opacity='0.55'><rect x='770' y='470' width='48' height='125' fill='%230a1f4a' stroke='%2300d4ff' stroke-opacity='0.28'/><rect x='820' y='505' width='40' height='90' fill='%230a1f4a' stroke='%2300d4ff' stroke-opacity='0.28'/><rect x='40' y='460' width='70' height='135' fill='%230a1f4a' stroke='%2300d4ff' stroke-opacity='0.28'/></g><!-- 随机网格点（科技感） --><g fill='%2322d3ee' opacity='0.6'><circle cx='60' cy='60' r='1.2'/><circle cx='150' cy='110' r='1'/><circle cx='250' cy='45' r='1.4'/><circle cx='360' cy='100' r='1'/><circle cx='520' cy='60' r='1.2'/><circle cx='680' cy='140' r='1'/><circle cx='800' cy='80' r='1.3'/><circle cx='840' cy='200' r='1.1'/><circle cx='430' cy='210' r='1'/></g><!-- 底部发光光晕 --><circle cx='450' cy='720' r='320' fill='%2300d4ff' opacity='0.05'/><circle cx='180' cy='600' r='140' fill='%2322d3ee' opacity='0.07'/></g></svg>");
  background-repeat: no-repeat;
  background-position: center;
  background-size: cover;
}
.showcase-bg::after {
  content: '';
  position: absolute;
  right: -2px;
  top: 10%;
  bottom: 10%;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(0, 212, 255, 0.45), transparent);
}

.showcase-inner {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
  padding: 44px 44px 36px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 24px;
  box-sizing: border-box;
  min-height: 0;
  overflow-y: auto;
  /* 细滚动条（藏在左栏里不突兀） */
  scrollbar-width: thin;
  scrollbar-color: rgba(34, 211, 238, 0.3) transparent;
}
.showcase-inner::-webkit-scrollbar { width: 6px; }
.showcase-inner::-webkit-scrollbar-track { background: transparent; }
.showcase-inner::-webkit-scrollbar-thumb { background: rgba(34, 211, 238, 0.28); border-radius: 999px; }
.showcase-inner::-webkit-scrollbar-thumb:hover { background: rgba(34, 211, 238, 0.5); }
.showcase-tag {
  align-self: flex-start;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  color: #22d3ee;
  background: rgba(34, 211, 238, 0.12);
  border: 1px solid rgba(34, 211, 238, 0.28);
}

/* 左侧品牌文字（放大版） */
.showcase-brand {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.brand-icon.big {
  font-size: 3.4rem;
  color: var(--primary);
  filter: drop-shadow(0 0 22px var(--primary-glow));
  display: inline-block;
  margin-bottom: 4px;
}
.brand-name.big {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.5rem;
  font-weight: 700;
  letter-spacing: 6px;
  margin: 0;
  color: #f0f9ff;
}
.brand-name.big .highlight {
  color: var(--primary);
  text-shadow: 0 0 18px var(--primary-glow);
}
.brand-sub.big {
  font-size: 1.25rem;
  color: #dbeafe;
  letter-spacing: 2px;
  font-weight: 500;
  margin: 0;
}
.brand-slogan {
  margin: 14px 0 0 0;
  padding: 10px 14px;
  display: inline-block;
  align-self: flex-start;
  font-size: 0.9375rem;
  color: var(--primary);
  letter-spacing: 0.8px;
  background: rgba(0, 212, 255, 0.08);
  border-left: 3px solid var(--primary);
  border-radius: 4px;
}

/* 3 个能力卡片 */
.showcase-feats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.feat-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 14px;
  border-radius: 14px;
  background: rgba(10, 25, 60, 0.55);
  border: 1px solid rgba(0, 212, 255, 0.22);
  backdrop-filter: blur(6px);
  transition: transform 220ms ease, border-color 220ms ease, box-shadow 220ms ease;
}
.feat-card:hover {
  transform: translateY(-3px);
  border-color: rgba(0, 212, 255, 0.5);
  box-shadow: 0 10px 28px rgba(0, 212, 255, 0.14);
}
.feat-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 1.125rem;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.2), rgba(59, 130, 246, 0.2));
  border: 1px solid rgba(0, 212, 255, 0.35);
}
.feat-main {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.feat-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: #f0f9ff;
}
.feat-desc {
  font-size: 0.75rem;
  color: rgba(191, 219, 254, 0.8);
  letter-spacing: 0.3px;
}

/* ========== 右侧：登录面板（居中放原 login-card） ========== */
.login-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 20px;
  background:
    radial-gradient(ellipse at 50% 0%, rgba(59, 130, 246, 0.08), transparent 60%),
    var(--bg-panel, #0b1533);
}

/* ========== 原登录卡（保持图一完全一致） ========== */
.login-card {
  width: 100%;
  max-width: 440px;
  padding: 36px 36px 32px;
  position: relative;
}
.login-card::before {
  content: '';
  position: absolute;
  inset: -1px;
  border-radius: calc(var(--radius-lg, 16px) + 1px);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.35), transparent 40%, transparent 60%, rgba(168, 85, 247, 0.25));
  z-index: -1;
  filter: blur(0.3px);
  opacity: 0.6;
}
.login-brand {
  text-align: center;
  margin-bottom: 24px;
}
.brand-icon {
  font-size: 2.6rem;
  color: var(--primary);
  filter: drop-shadow(0 0 16px var(--primary-glow));
  display: block;
  margin-bottom: 10px;
}
.brand-name {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.375rem;
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
  letter-spacing: 0.5px;
}

/* 角色 tabs */
.role-tabs {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin-bottom: 14px;
  padding: 4px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
}
.role-tab {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 12px;
  background: transparent;
  border: 1px solid transparent;
  color: var(--text-secondary);
  border-radius: calc(var(--radius) - 2px);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  font-family: inherit;
  transition: all var(--duration, 200ms) var(--ease, ease);
}
.role-tab:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.03);
}
.role-tab.active {
  background: var(--primary-subtle);
  color: var(--primary);
  border-color: var(--border-active);
  box-shadow: 0 0 0 1px rgba(0, 212, 255, 0.15) inset;
}
.rt-icon {
  font-size: 0.9375rem;
  filter: drop-shadow(0 0 3px currentColor);
}

/* 表单 */
.login-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
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
.form-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -2px;
}
.remember {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
  font-size: 0.8125rem;
  color: var(--text-secondary);
}
.remember input[type="checkbox"] {
  position: absolute;
  opacity: 0;
  width: 0;
  height: 0;
  pointer-events: none;
}
.check-icon {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1px solid var(--border-subtle);
  background: rgba(255, 255, 255, 0.02);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  color: var(--primary);
  font-weight: 800;
  transition: all var(--duration) var(--ease);
  line-height: 1;
}
.remember input[type="checkbox"]:checked + .check-icon {
  background: var(--primary);
  color: var(--bg-deep);
  border-color: var(--primary);
  box-shadow: 0 0 6px var(--primary-glow);
}
.remember-txt { line-height: 1; }

.btn-block {
  width: 100%;
  padding: 12px;
  font-size: 0.9375rem;
  margin-top: 4px;
  letter-spacing: 2px;
  font-weight: 700;
  box-shadow: 0 6px 20px -6px var(--primary-glow);
}
.btn-block:disabled {
  opacity: 0.75;
  cursor: not-allowed;
}
.loading-dots {
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
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

/* ========== 响应式：小屏切回单列居中 ========== */
@media (max-width: 860px) {
  .login-container {
    grid-template-columns: 1fr;
    min-height: auto;
  }
  .login-showcase {
    min-height: 320px;
  }
  .showcase-bg::after {
    right: 8%;
    left: 8%;
    top: auto;
    bottom: -1px;
    width: auto;
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(0, 212, 255, 0.45), transparent);
  }
  .showcase-inner {
    padding: 40px 32px 36px;
  }
  .brand-name.big {
    font-size: 2rem;
    letter-spacing: 4px;
  }
  .login-panel {
    padding: 36px 20px 40px;
  }
}
@media (max-width: 520px) {
  .login-wrapper {
    padding: 16px 12px;
  }
  .showcase-inner {
    padding: 28px 20px 24px;
    gap: 18px;
  }
  .showcase-feats {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  .brand-name.big {
    font-size: 1.625rem;
    letter-spacing: 3px;
  }
  .brand-sub.big {
    font-size: 1.05rem;
  }
  .login-card {
    padding: 28px 20px 24px;
  }
  .brand-name {
    font-size: 1.125rem;
    letter-spacing: 2px;
  }
}
</style>
