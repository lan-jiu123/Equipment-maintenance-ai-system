<template>
  <div class="container">
    <section class="hero-mini">
      <div>
        <div class="crumb"><router-link to="/home">仪表盘</router-link> · <span>用户管理</span></div>
        <h1 class="page-title">👥 用户管理</h1>
        <p class="page-sub">系统账号 · 角色分配 · 维修任务统计 · 账号禁用</p>
      </div>
      <div class="hero-actions">
        <div class="search-box card">
          <span>🔍</span>
          <input v-model="keyword" placeholder="搜索姓名 / 工号 / 部门..." />
        </div>
        <button class="btn btn-primary" @click="toast('新增用户请扩展API接口，或在/api/users POST')">+ 新增用户</button>
      </div>
    </section>

    <section class="stats-grid mini">
      <div class="stat-card card">
        <div class="stat-icon blue">👥</div>
        <div class="stat-info">
          <div class="stat-value">{{ total }}</div>
          <div class="stat-label">系统总用户</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon purple">☗</div>
        <div class="stat-info">
          <div class="stat-value">{{ managerCount }}</div>
          <div class="stat-label">维修管理员</div>
          <div class="stat-trend up">含调度 / 审核权</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">🔧</div>
        <div class="stat-info">
          <div class="stat-value">{{ workerCount }}</div>
          <div class="stat-label">一线维修工</div>
          <div class="stat-trend up">在岗 {{ onDutyWorker }} 人</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon orange">📡</div>
        <div class="stat-info">
          <div class="stat-value">{{ onlineCount }}</div>
          <div class="stat-label">活跃用户</div>
          <div class="stat-trend up">{{ nowTime }}</div>
        </div>
      </div>
    </section>

    <section class="filters-row card">
      <div class="filters-group">
        <div class="filter-label">角色筛选</div>
        <div class="chip-group">
          <span v-for="r in roles" :key="r.v" class="chip" :class="{ active: activeRole === r.v }" @click="activeRole = r.v; page = 1">{{ r.label }}</span>
        </div>
      </div>
      <div class="filters-group">
        <div class="filter-label">账号状态</div>
        <div class="chip-group">
          <span class="chip" :class="{ active: activeStatus === 'all' }" @click="activeStatus = 'all'; page = 1">全部</span>
          <span class="chip chip-good" :class="{ active: activeStatus === 'active' }" @click="activeStatus = 'active'; page = 1">可用</span>
          <span class="chip chip-bad" :class="{ active: activeStatus === 'disabled' }" @click="activeStatus = 'disabled'; page = 1">🚫 已禁用</span>
        </div>
      </div>
    </section>

    <section class="table-section card">
      <table class="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>工号</th>
            <th>角色</th>
            <th>维修任务统计</th>
            <th>创建时间</th>
            <th>最近登录</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" style="padding:64px 0">
            <div class="skeleton-wrap">
              <div v-for="i in 5" :key="i" class="skeleton-row"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
            </div>
          </td></tr>
          <tr v-else-if="!pagedItems.length"><td colspan="8" style="text-align:center;padding:64px 0;color:var(--text-muted);" class="muted">暂无符合条件的用户</td></tr>
          <tr v-for="u in pagedItems" :key="u.id" class="row-hover">
            <td>
              <div class="user-main">
                <div class="avatar-sm" :class="{ manager: !u.isWorker, worker: u.isWorker }">
                  {{ u.avatar }}
                </div>
                <div>
                  <div class="user-name">{{ u.fullname }}</div>
                  <div class="user-login">@{{ u.username }}</div>
                </div>
                <span v-if="u.online" class="online-dot" title="活跃"></span>
              </div>
            </td>
            <td class="mono">{{ u.empId }}</td>
            <td>
              <span class="role-badge" :class="u.isWorker ? 'worker' : 'manager'">
                <span class="rb-dot"></span>{{ u.role_label }}
              </span>
              <div class="role-tags-sm" v-if="u.extraTags && u.extraTags.length">
                <span v-for="t in u.extraTags" :key="t.text" class="rt-sm" :class="t.cls">{{ t.text }}</span>
              </div>
            </td>
            <td>
              <div class="dept-name">已完成 <b>{{ u.tk_done }}</b> 单</div>
              <div class="pos-name muted">进行中 {{ u.tk_doing }} · 超时 {{ u.tk_over }}</div>
            </td>
            <td class="muted">{{ u.joined }}</td>
            <td>
              <div class="contact-row">{{ u.lastLogin || '从未登录' }}</div>
            </td>
            <td>
              <span class="status-pill" :class="'st-'+u.status">{{ u.statusText }}</span>
              <div class="last-login muted" v-if="u.deleted_at">禁用时间：{{ u.deleted_at.slice(0,10) }}</div>
            </td>
            <td>
              <button class="btn btn-outline btn-xs" @click="edit(u)">编辑</button>
              <button class="btn btn-outline btn-xs" @click="resetPwd(u)">重置密码</button>
              <button class="btn btn-ghost btn-xs" :class="u.status==='disabled' ? 'enable' : 'disable'" @click="toggle(u)" :disabled="u.isSelf">
                {{ u.status==='disabled' ? '启用（暂未提供）' : '禁用' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="filteredItems.length > size" class="pagination">
        <div class="muted pagination-info">共 {{ filteredItems.length }} 人 · 第 {{ page }} / {{ totalPages }} 页</div>
        <div class="pagination-ctrl">
          <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page=1">首页</button>
          <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page--">上一页</button>
          <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page++">下一页</button>
          <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page=totalPages">末页</button>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { toast } from '../utils/request'
import { listUsersApi, resetUserPasswordApi, deleteUserApi } from '../utils/api'
import { getUser } from '../utils/auth'

const ROLE_BADGE_TAGS = {
  sysadmin: [{ text: '系统权限', cls: 'red' }],
  manager:  [{ text: '工单调度', cls: 'amber' }, { text: '报告审核', cls: 'primary' }],
  worker:   [{ text: '维修执行', cls: 'cyan' }]
}

function _fmtAgo(isoStr) {
  if (!isoStr) return '从未登录'
  const t = new Date(isoStr).getTime()
  if (!t) return '从未登录'
  const diff = Date.now() - t
  if (diff < 3600 * 1000) {
    const m = Math.max(1, Math.floor(diff / 60000))
    return m + ' 分钟前 · 活跃'
  }
  if (diff < 86400 * 1000) {
    const h = Math.floor(diff / 3600000)
    return '今天 ' + new Date(t).toTimeString().slice(0, 5) + '（' + h + 'h前）'
  }
  return new Date(t).toLocaleDateString('zh-CN')
}

function _mapUser(u, selfId, now) {
  const isDisabled = !!(u.deleted_at || /^deleted_/i.test(u.username || ''))
  const lastT = u.last_login_at ? new Date(u.last_login_at).getTime() : 0
  const online = !isDisabled && lastT && (now - lastT) < 7 * 86400 * 1000
  const isWorker = u.role === 'worker'
  const done = Number((u.ticket_stats || {}).done || 0)
  const doing = Number((u.ticket_stats || {}).doing || 0)
  const over = Number((u.ticket_stats || {}).over || 0)
  const extra = (ROLE_BADGE_TAGS[u.role] || []).slice()
  if (done > 10 && isWorker) extra.push({ text: '经验值 +' + done, cls: 'green' })
  return {
    id: u.id,
    username: u.username,
    fullname: u.fullname || u.username,
    avatar: (u.fullname || u.username || '?').slice(0, 1),
    empId: 'ID-' + String(100000 + Number(u.id)),
    isWorker,
    role: u.role,
    role_label: u.role_label || (isWorker ? '维修工' : '维修管理员'),
    extraTags: extra,
    tk_done: done,
    tk_doing: doing,
    tk_over: over,
    joined: u.created_at ? String(u.created_at).slice(0, 10) : '-',
    lastLogin: _fmtAgo(u.last_login_at),
    online,
    statusDisabled: isDisabled,
    status: isDisabled ? 'disabled' : (online ? 'online' : 'offline'),
    statusText: isDisabled ? '已禁用' : (online ? '活跃' : '离线'),
    deleted_at: u.deleted_at || null,
    isSelf: selfId && Number(selfId) === Number(u.id)
  }
}

export default {
  name: 'UserMgmt',
  data() {
    return {
      keyword: '',
      activeRole: 'all',
      activeStatus: 'all',
      roles: [
        { v: 'all',     label: '全部' },
        { v: 'admin',   label: '维修管理员' },
        { v: 'worker',  label: '一线检修员' }
      ],
      allUsers: [],
      loading: false,
      _loadingOp: null,
      page: 1, size: 20,
      _selfId: null,
      _now: Date.now(),
      _refreshTick: 0
    }
  },
  computed: {
    mappedAll() {
      const selfId = this._selfId
      const now = this._now
      return this.allUsers.map(u => _mapUser(u, selfId, now))
    },
    total() { return this.mappedAll.length },
    managerCount() { return this.mappedAll.filter(u => !u.isWorker).length },
    workerCount()  { return this.mappedAll.filter(u => u.isWorker).length },
    onlineCount()  { return this.mappedAll.filter(u => u.online && !u.statusDisabled).length },
    onDutyWorker() { return this.mappedAll.filter(u => u.isWorker && u.online).length },
    nowTime() {
      const d = new Date()
      return d.getHours().toString().padStart(2, '0') + ':' + d.getMinutes().toString().padStart(2, '0')
    },
    filteredItems() {
      const kw = this.keyword.trim().toLowerCase()
      const role = this.activeRole
      const st = this.activeStatus
      return this.mappedAll.filter(u => {
        if (role === 'admin' && u.isWorker) return false
        if (role === 'worker' && !u.isWorker) return false
        if (st === 'active' && u.statusDisabled) return false
        if (st === 'disabled' && !u.statusDisabled) return false
        if (kw) {
          const s = String(u.fullname||'').toLowerCase() + ' ' +
                    String(u.username||'').toLowerCase() + ' ' +
                    String(u.empId||'').toLowerCase() + ' ' +
                    String(u.role_label||'').toLowerCase()
          if (!s.includes(kw)) return false
        }
        return true
      })
    },
    totalPages() { return Math.max(1, Math.ceil(this.filteredItems.length / this.size)) },
    pagedItems() {
      const s = (this.page - 1) * this.size
      return this.filteredItems.slice(s, s + this.size)
    }
  },
  watch: {
    keyword()    { this.page = 1 },
    activeRole() { this.page = 1 },
    activeStatus(){ this.page = 1 },
    totalPages(p){ if (this.page > p) this.page = p }
  },
  created() {
    const cur = getUser()
    this._selfId = (cur && cur.id) ? Number(cur.id) : null
    this.loadAll()
  },
  methods: {
    toast,
    _touchNow() {
      this._now = Date.now()
      this._refreshTick++
    },
    async loadAll() {
      this.loading = true
      try {
        const p = await listUsersApi({ page: 1, size: 5000 }) || {}
        this.allUsers = p.items || []
        this._touchNow()
      } finally {
        this.loading = false
      }
    },
    _optimisticUpdate(id, patch) {
      const idx = this.allUsers.findIndex(u => Number(u.id) === Number(id))
      if (idx >= 0) {
        this.allUsers.splice(idx, 1, { ...this.allUsers[idx], ...patch })
        this._touchNow()
      }
    },
    edit(u) {
      const info = [
        'ID: ' + u.id,
        '姓名: ' + u.fullname,
        '工号: ' + u.username,
        '角色: ' + u.role_label,
        '创建时间: ' + u.joined,
        '最近登录: ' + u.lastLogin,
        '已完成: ' + u.tk_done + ' 单',
        '进行中: ' + u.tk_doing + '，超时: ' + u.tk_over
      ]
      alert(info.join('\n'))
    },
    async resetPwd(u) {
      if (!confirm('确定重置 ' + u.fullname + ' 的登录密码?')) return
      const prev = this._loadingOp
      this._loadingOp = 'pwd:' + u.id
      try {
        await resetUserPasswordApi(u.id)
        toast('密码已重置，请通知用户首次登录后修改密码', 'success')
        setTimeout(() => this.loadAll(), 200)
      } catch (e) {
        toast('重置失败：' + (e.message || '未知错误'), 'error')
      } finally {
        this._loadingOp = prev
      }
    },
    async toggle(u) {
      if (u.isSelf) {
        toast('不能禁用当前登录的账号', 'warn')
        return
      }
      if (u.statusDisabled) {
        toast('启用账号请扩展 /api/users/{id}/enable 接口（或直接重设 deleted_ 前缀并重建密码）', 'warn')
        return
      }
      if (!confirm('确定禁用账号：' + u.fullname + '？\n禁用后该用户无法登录，其关联工单和报告数据会保留。')) return
      const prev = this._loadingOp
      this._loadingOp = 'toggle:' + u.id
      const orig = this.allUsers.find(x => Number(x.id) === Number(u.id))
      const origCopy = orig ? { ...orig } : null
      try {
        this._optimisticUpdate(u.id, {
          deleted_at: new Date().toISOString(),
          username: 'deleted_' + (orig ? orig.username : u.username)
        })
        await deleteUserApi(u.id)
        toast('账号已禁用', 'success')
        setTimeout(() => this.loadAll(), 300)
      } catch (e) {
        if (origCopy) {
          const idx = this.allUsers.findIndex(x => Number(x.id) === Number(u.id))
          if (idx >= 0) this.allUsers.splice(idx, 1, origCopy)
          this._touchNow()
        }
        toast('禁用失败：' + (e.message || '未知错误'), 'error')
      } finally {
        this._loadingOp = prev
      }
    }
  }
}
</script>

<style scoped>
.container { max-width: var(--max-width); margin: 0 auto; padding: 28px 28px 64px; }
.hero-mini { display: flex; justify-content: space-between; align-items: flex-end; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.crumb { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px; }
.crumb a { color: var(--primary); text-decoration: none; }
.page-title { font-size: 1.625rem; font-weight: 800; color: var(--text-primary); letter-spacing: 0.5px; margin: 0; }
.page-sub { font-size: 0.875rem; color: var(--text-secondary); margin-top: 6px; }
.hero-actions { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; }
.search-box { display: flex; align-items: center; gap: 8px; padding: 8px 14px; border-radius: var(--radius); min-width: 320px; }
.search-box input { flex: 1; background: transparent; border: none; outline: none; color: var(--text-primary); font-size: 0.875rem; }

.stats-grid.mini { grid-template-columns: repeat(4, 1fr); gap: 16px; display: grid; margin-bottom: 24px; }

.filters-row { padding: 14px 18px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 14px; }
.filters-group { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.filter-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; min-width: 72px; }
.chip-group { display: flex; gap: 6px; flex-wrap: wrap; }
.chip { padding: 5px 14px; border-radius: 999px; font-size: 0.75rem; cursor: pointer; background: var(--bg-deep); color: var(--text-secondary); border: 1px solid var(--border-subtle); transition: all var(--duration) var(--ease); }
.chip:hover { border-color: var(--border-active); color: var(--text-primary); }
.chip.active { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); font-weight: 600; }
.chip-good.active { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); border-color: rgba(0, 255, 136, 0.35); }
.chip-warn.active { background: var(--primary-subtle); color: var(--text-secondary); border-color: var(--border-subtle); }
.chip-bad.active { background: rgba(255, 71, 87, 0.1); color: var(--accent-red); border-color: rgba(255, 71, 87, 0.35); }

.table-section { padding: 0; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.data-table thead th { text-align: left; padding: 12px 18px; background: var(--bg-deep); color: var(--text-muted); font-weight: 600; font-size: 0.75rem; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-subtle); }
.data-table tbody td { padding: 14px 18px; border-bottom: 1px solid var(--border-subtle); color: var(--text-primary); vertical-align: middle; }
.row-hover:hover td { background: var(--primary-subtle); }

.mono { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--primary); }
.mono-sm { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-secondary); }
.muted { color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

.user-main { display: flex; align-items: center; gap: 12px; position: relative; }
.avatar-sm {
  width: 40px; height: 40px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.9375rem; font-family: 'Orbitron', sans-serif;
  border: 2px solid; flex-shrink: 0;
}
.avatar-sm.manager { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); }
.avatar-sm.worker { background: rgba(0, 255, 136, 0.08); color: var(--accent-green); border-color: rgba(0, 255, 136, 0.3); }
.user-name { font-weight: 600; color: var(--text-primary); font-size: 0.875rem; }
.user-login { font-size: 0.6875rem; color: var(--text-muted); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }
.online-dot {
  position: absolute; left: 38px; top: 4px; width: 10px; height: 10px;
  border-radius: 50%; background: var(--accent-green);
  box-shadow: 0 0 0 2px var(--bg-elevated), 0 0 6px var(--accent-green);
}

.role-badge {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 4px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 600;
  border: 1px solid;
}
.role-badge.manager { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); }
.role-badge.manager .rb-dot { background: var(--primary); }
.role-badge.worker { background: rgba(0, 255, 136, 0.08); color: var(--accent-green); border-color: rgba(0, 255, 136, 0.3); }
.role-badge.worker .rb-dot { background: var(--accent-green); box-shadow: 0 0 5px var(--accent-green); }
.rb-dot { width: 6px; height: 6px; border-radius: 50%; }
.role-tags-sm { display: flex; gap: 5px; margin-top: 5px; flex-wrap: wrap; }
.rt-sm { padding: 1px 8px; font-size: 0.625rem; border-radius: 999px; font-weight: 600; border: 1px solid; }
.rt-sm.amber { background: rgba(255, 156, 86, 0.1); color: #ff9c56; border-color: rgba(255, 156, 86, 0.3); }
.rt-sm.red { background: rgba(255, 71, 87, 0.1); color: var(--accent-red); border-color: rgba(255, 71, 87, 0.3); }
.rt-sm.cyan { background: rgba(34, 211, 238, 0.1); color: #22d3ee; border-color: rgba(34, 211, 238, 0.3); }
.rt-sm.green { background: rgba(0, 255, 136, 0.08); color: var(--accent-green); border-color: rgba(0, 255, 136, 0.3); }
.rt-sm.primary { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); }

.dept-name { font-weight: 600; font-size: 0.8125rem; }
.pos-name { margin-top: 3px; font-size: 0.6875rem; }

.contact-row { display: flex; align-items: center; gap: 7px; font-size: 0.8125rem; line-height: 1.8; }

.status-pill { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
.st-online { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); }
.st-offline { background: rgba(148, 163, 184, 0.1); color: #94a3b8; }
.st-disabled { background: rgba(255, 71, 87, 0.1); color: var(--accent-red); }
.last-login { margin-top: 4px; font-size: 0.625rem; }

.btn-xs { padding: 4px 10px; font-size: 0.6875rem; margin-right: 4px; }
.btn-xs:last-child { margin-right: 0; }
.btn-ghost { background: transparent; border: 1px dashed var(--border-subtle); color: var(--text-secondary); }
.btn-ghost.disable:hover { border-color: rgba(255, 71, 87, 0.35); color: var(--accent-red); }
.btn-ghost.enable:hover { border-color: rgba(0, 255, 136, 0.35); color: var(--accent-green); }

.skeleton-wrap { padding: 0 18px; display: flex; flex-direction: column; gap: 18px; }
.skeleton-row { display: grid; grid-template-columns: repeat(8, 1fr); gap: 16px; }
.skeleton-row span {
  display: block; height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(0,212,255,0.10) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
.skeleton-row span:nth-child(1) { width: 70%; }
.skeleton-row span:nth-child(2) { width: 75%; }
.skeleton-row span:nth-child(5) { width: 60%; }
.skeleton-row span:nth-child(6) { width: 75%; }
.skeleton-row span:nth-child(7) { width: 65%; }
.skeleton-row span:nth-child(8) { width: 92%; }
@keyframes skeleton-shine {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.pagination {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 18px; border-top: 1px solid var(--border-subtle); background: var(--bg-deep);
}
.pagination-info { font-size: 0.75rem; }
.pagination-ctrl { display: flex; gap: 6px; }
</style>
