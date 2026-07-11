<template>
  <div class="container password">
    <div class="page-header">
      <div>
        <h1 class="page-title">🔐 修改密码</h1>
        <p class="page-sub">请定期更换密码以确保账户安全</p>
      </div>
      <router-link class="btn btn-outline btn-sm" to="/home">← 返回仪表盘</router-link>
    </div>

    <div class="pwd-wrap">
      <div class="card pwd-card">
        <div class="pwd-head">
          <div class="pwd-icon">🔐</div>
          <div>
            <h3>密码修改</h3>
            <p>密码长度 8-32 位，建议包含大小写字母、数字与特殊符号</p>
          </div>
        </div>

        <div class="form-list">
          <div class="form-field">
            <label for="oldPwd">当前密码</label>
            <div class="pwd-input">
              <input
                id="oldPwd"
                :type="oldVisible ? 'text' : 'password'"
                v-model="form.oldPwd"
                class="input"
                placeholder="请输入当前登录密码"
                autocomplete="current-password"
              />
              <button class="eye" type="button" @click="oldVisible = !oldVisible">
                {{ oldVisible ? '🙈' : '👁' }}
              </button>
            </div>
          </div>

          <div class="form-field">
            <label for="newPwd">新密码</label>
            <div class="pwd-input">
              <input
                id="newPwd"
                :type="newVisible ? 'text' : 'password'"
                v-model="form.newPwd"
                class="input"
                placeholder="至少 8 位，混合字母、数字与符号"
                @input="checkStrength"
                autocomplete="new-password"
              />
              <button class="eye" type="button" @click="newVisible = !newVisible">
                {{ newVisible ? '🙈' : '👁' }}
              </button>
            </div>
            <div v-if="form.newPwd" class="strength-row">
              <div class="strength-bar">
                <span class="seg" :class="{ on: strength.score >= 1, s1: strength.score === 1 }"></span>
                <span class="seg" :class="{ on: strength.score >= 2, s2: strength.score === 2 }"></span>
                <span class="seg" :class="{ on: strength.score >= 3, s3: strength.score === 3 }"></span>
                <span class="seg" :class="{ on: strength.score >= 4, s4: strength.score === 4 }"></span>
              </div>
              <span class="strength-label" :class="strength.class">{{ strength.text }}</span>
            </div>
          </div>

          <div class="form-field">
            <label for="confirmPwd">再次输入新密码</label>
            <div class="pwd-input">
              <input
                id="confirmPwd"
                :type="confirmVisible ? 'text' : 'password'"
                v-model="form.confirmPwd"
                class="input"
                placeholder="请再次输入新密码"
                autocomplete="new-password"
              />
              <button class="eye" type="button" @click="confirmVisible = !confirmVisible">
                {{ confirmVisible ? '🙈' : '👁' }}
              </button>
            </div>
          </div>
        </div>

        <ul class="pwd-rules">
          <li :class="{ pass: checks.len }"><span class="tick">{{ checks.len ? '✓' : '○' }}</span>长度 8 - 32 位</li>
          <li :class="{ pass: checks.upper }"><span class="tick">{{ checks.upper ? '✓' : '○' }}</span>包含大写字母 (A-Z)</li>
          <li :class="{ pass: checks.lower }"><span class="tick">{{ checks.lower ? '✓' : '○' }}</span>包含小写字母 (a-z)</li>
          <li :class="{ pass: checks.num }"><span class="tick">{{ checks.num ? '✓' : '○' }}</span>包含数字 (0-9)</li>
          <li :class="{ pass: checks.sym }"><span class="tick">{{ checks.sym ? '✓' : '○' }}</span>包含特殊符号 (!@#$%...)</li>
        </ul>

        <p v-if="errorMsg" class="form-msg error">{{ errorMsg }}</p>
        <p v-if="okMsg" class="form-msg ok">{{ okMsg }}</p>

        <div class="form-actions">
          <button class="btn btn-outline" @click="reset">重 置</button>
          <button class="btn btn-primary" @click="submit">确认修改</button>
        </div>
      </div>

      <div class="card tips-card">
        <h4>💡 安全提示</h4>
        <ul>
          <li>请勿使用与姓名、生日相关的易猜测密码</li>
          <li>密码建议每 90 天更换一次</li>
          <li>不要在其他平台使用相同的账户密码</li>
          <li>如忘记密码，请联系系统管理员重置</li>
          <li>本次修改后所有已登录设备将重新要求登录</li>
        </ul>

        <div class="last-change">
          <span class="label">上次修改</span>
          <span class="value mono">2026-04-22 14:08:31</span>
        </div>
        <div class="pwd-expire">
          <div class="expire-head">
            <span>当前密码有效期</span>
            <span class="mono">{{ remainDays }} 天后过期</span>
          </div>
          <div class="expire-bar">
            <span class="expire-fill" :style="{ width: expirePct + '%' }"></span>
          </div>
          <p class="expire-sub">超过 90 天将强制要求修改后再进入系统</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Password',
  data() {
    return {
      oldVisible: false,
      newVisible: false,
      confirmVisible: false,
      form: {
        oldPwd: '',
        newPwd: '',
        confirmPwd: ''
      },
      errorMsg: '',
      okMsg: '',
      strength: { score: 0, text: '弱', class: 's1' },
      checks: { len: false, upper: false, lower: false, num: false, sym: false },
      remainDays: 61
    }
  },
  computed: {
    expirePct() {
      return Math.max(0, Math.min(100, (this.remainDays / 90) * 100))
    }
  },
  methods: {
    checkStrength() {
      const p = this.form.newPwd || ''
      this.checks.len = p.length >= 8 && p.length <= 32
      this.checks.upper = /[A-Z]/.test(p)
      this.checks.lower = /[a-z]/.test(p)
      this.checks.num = /[0-9]/.test(p)
      this.checks.sym = /[^A-Za-z0-9]/.test(p)

      let score = 0
      if (this.checks.len) score++
      if (this.checks.upper) score++
      if (this.checks.lower) score++
      if (this.checks.num) score++
      if (this.checks.sym && p.length >= 10) score++

      this.strength.score = score
      if (score <= 1) this.strength = { score, text: '弱', class: 's1' }
      else if (score === 2) this.strength = { score, text: '一般', class: 's2' }
      else if (score === 3) this.strength = { score, text: '良好', class: 's3' }
      else this.strength = { score, text: '非常强', class: 's4' }
    },
    reset() {
      this.form = { oldPwd: '', newPwd: '', confirmPwd: '' }
      this.strength = { score: 0, text: '弱', class: 's1' }
      this.checks = { len: false, upper: false, lower: false, num: false, sym: false }
      this.errorMsg = ''
      this.okMsg = ''
    },
    submit() {
      this.errorMsg = ''
      this.okMsg = ''
      if (!this.form.oldPwd) {
        this.errorMsg = '请输入当前密码'
        return
      }
      const { len, upper, lower, num, sym } = this.checks
      if (!(len && upper && lower && num && sym)) {
        this.errorMsg = '新密码强度不足，请满足所有安全规则'
        return
      }
      if (this.form.newPwd !== this.form.confirmPwd) {
        this.errorMsg = '两次输入的新密码不一致'
        return
      }
      if (this.form.oldPwd === this.form.newPwd) {
        this.errorMsg = '新密码不能与当前密码相同'
        return
      }
      this.okMsg = '✓ 密码修改成功！下一次登录请使用新密码'
      setTimeout(() => this.reset(), 1800)
    }
  }
}
</script>

<style scoped>
.password {
  max-width: 1100px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 28px;
}
.page-title {
  font-size: 1.625rem;
  margin-bottom: 4px;
}
.page-sub {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.pwd-wrap {
  display: grid;
  grid-template-columns: 1fr 340px;
  gap: 24px;
  align-items: flex-start;
}

.pwd-head {
  display: flex;
  gap: 14px;
  align-items: center;
  margin-bottom: 26px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--border-subtle);
}
.pwd-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  background: var(--primary-subtle);
  border: 1px solid var(--border-active);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}
.pwd-head h3 {
  font-size: 1.0625rem;
  margin-bottom: 4px;
}
.pwd-head p {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.form-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 22px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-field label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  font-weight: 500;
}

.pwd-input {
  position: relative;
}
.pwd-input .input {
  padding-right: 44px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 1px;
}
.eye {
  position: absolute;
  top: 50%;
  right: 8px;
  transform: translateY(-50%);
  width: 32px;
  height: 32px;
  background: transparent;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  border-radius: var(--radius);
  transition: all var(--duration) var(--ease);
  font-size: 1rem;
}
.eye:hover {
  background: var(--primary-subtle);
  color: var(--primary);
}

.strength-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}
.strength-bar {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
  height: 6px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--bg-deep);
}
.seg {
  background: var(--bg-deep);
  border-radius: 6px;
  transition: all var(--duration) var(--ease);
}
.seg.on.s1 { background: var(--accent-red); }
.seg.on.s2 { background: var(--accent-orange); }
.seg.on.s3 { background: var(--accent-amber); }
.seg.on.s4 { background: var(--accent-green); }
.strength-label {
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  min-width: 52px;
  text-align: right;
}
.strength-label.s1 { color: var(--accent-red); }
.strength-label.s2 { color: var(--accent-orange); }
.strength-label.s3 { color: var(--accent-amber); }
.strength-label.s4 { color: var(--accent-green); }

.pwd-rules {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px 14px;
  margin: 0 0 20px;
  padding: 14px 16px;
  background: var(--bg-deep);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius);
}
.pwd-rules li {
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
}
.pwd-rules li.pass {
  color: var(--accent-green);
}
.tick {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
}

.form-msg {
  font-size: 0.8125rem;
  padding: 10px 14px;
  border-radius: var(--radius);
  margin-bottom: 14px;
  border: 1px solid;
}
.form-msg.error {
  color: var(--accent-red);
  background: rgba(255, 71, 87, 0.06);
  border-color: rgba(255, 71, 87, 0.3);
}
.form-msg.ok {
  color: var(--accent-green);
  background: rgba(0, 255, 136, 0.06);
  border-color: rgba(0, 255, 136, 0.3);
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-sm {
  padding: 6px 16px;
  font-size: 0.8125rem;
}

/* === Tips Card === */
.tips-card h4 {
  font-size: 0.9375rem;
  margin-bottom: 12px;
  color: var(--text-primary);
}
.tips-card ul {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  margin-bottom: 20px;
}
.tips-card ul li {
  font-size: 0.75rem;
  color: var(--text-secondary);
  line-height: 1.5;
  padding-left: 14px;
  position: relative;
}
.tips-card ul li::before {
  content: '';
  position: absolute;
  left: 0;
  top: 7px;
  width: 6px;
  height: 6px;
  background: var(--primary);
  border-radius: 50%;
  box-shadow: 0 0 4px var(--primary-glow);
}

.last-change {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px dashed var(--border-subtle);
  font-size: 0.75rem;
  margin-bottom: 16px;
}
.last-change .label {
  color: var(--text-secondary);
}
.last-change .value {
  color: var(--text-primary);
  font-size: 0.75rem;
}
.mono {
  font-family: 'JetBrains Mono', monospace;
}

.pwd-expire {
  padding: 14px;
  background: var(--primary-subtle);
  border: 1px solid var(--border-active);
  border-radius: var(--radius);
}
.expire-head {
  display: flex;
  justify-content: space-between;
  font-size: 0.75rem;
  color: var(--text-primary);
  font-weight: 600;
  margin-bottom: 10px;
}
.expire-bar {
  height: 8px;
  background: var(--bg-deep);
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
}
.expire-fill {
  display: block;
  height: 100%;
  background: linear-gradient(90deg, var(--primary), var(--accent-green));
  border-radius: 8px;
  transition: width 400ms var(--ease);
}
.expire-sub {
  font-size: 0.6875rem;
  color: var(--text-secondary);
}

@media (max-width: 880px) {
  .pwd-wrap {
    grid-template-columns: 1fr;
  }
  .pwd-rules {
    grid-template-columns: 1fr;
  }
}
</style>
