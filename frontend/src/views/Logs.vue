<template>
  <div class="container logs">
    <div class="page-header">
      <div>
        <h1 class="page-title">📋 操作日志</h1>
        <p class="page-sub">记录系统所有关键操作行为，便于审计与追溯</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline btn-sm" @click="exportCsv">⬇ 导出 CSV</button>
        <router-link class="btn btn-outline btn-sm" to="/home">← 返回仪表盘</router-link>
      </div>
    </div>

    <!-- 统计卡 -->
    <div class="stat-row">
      <div class="stat-card card">
        <div class="sc-label">总日志条数</div>
        <div class="sc-num">{{ formatNum(stats.total) }}</div>
        <div class="sc-foot"><span class="up">↑</span> 较昨日 +{{ stats.totalDiff }}</div>
      </div>
      <div class="stat-card card">
        <div class="sc-label">今日操作</div>
        <div class="sc-num today">{{ formatNum(stats.today) }}</div>
        <div class="sc-foot">近 24 小时</div>
      </div>
      <div class="stat-card card">
        <div class="sc-label">⚠ 警告级</div>
        <div class="sc-num warn">{{ formatNum(stats.warn) }}</div>
        <div class="sc-foot">需关注</div>
      </div>
      <div class="stat-card card">
        <div class="sc-label">🔴 错误级</div>
        <div class="sc-num danger">{{ formatNum(stats.error) }}</div>
        <div class="sc-foot">需立即处理</div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="card filter-bar">
      <div class="filter-search">
        <span class="fs-icon">🔍</span>
        <input
          v-model="filters.keyword"
          class="input"
          placeholder="搜索操作内容 / 操作人 / IP"
          @input="onFilterChange"
        />
      </div>

      <div class="filter-group">
        <label>模块</label>
        <select class="input" v-model="filters.module" @change="onFilterChange">
          <option value="">全部</option>
          <option>用户管理</option>
          <option>权限配置</option>
          <option>智能检索</option>
          <option>案例库</option>
          <option>作业指导</option>
          <option>设备管理</option>
          <option>系统设置</option>
        </select>
      </div>

      <div class="filter-group">
        <label>等级</label>
        <select class="input" v-model="filters.level" @change="onFilterChange">
          <option value="">全部</option>
          <option value="info">INFO 信息</option>
          <option value="warn">WARN 警告</option>
          <option value="error">ERROR 错误</option>
        </select>
      </div>

      <div class="filter-group date-group">
        <label>日期</label>
        <input class="input mono" type="date" v-model="filters.from" @change="onFilterChange" />
        <span class="tilde">~</span>
        <input class="input mono" type="date" v-model="filters.to" @change="onFilterChange" />
      </div>

      <button class="btn btn-outline btn-sm" @click="resetFilters">重 置</button>
    </div>

    <!-- 表格 -->
    <div class="card log-table-wrap">
      <table class="log-table">
        <thead>
          <tr>
            <th style="width:160px">时间</th>
            <th style="width:90px">操作人</th>
            <th style="width:110px">模块</th>
            <th>操作内容</th>
            <th style="width:120px">来源 IP</th>
            <th style="width:70px">结果</th>
            <th style="width:70px">等级</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in pagedLogs" :key="row.id" class="log-row">
            <td class="mono muted">{{ row.time }}</td>
            <td>
              <span class="user-chip">{{ row.user }}</span>
            </td>
            <td><span class="mod-tag" :class="'mod-' + slug(row.module)">{{ row.module }}</span></td>
            <td class="op">{{ row.action }}</td>
            <td class="mono muted">{{ row.ip }}</td>
            <td>
              <span class="res" :class="row.ok ? 'ok' : 'fail'">{{ row.ok ? '成功' : '失败' }}</span>
            </td>
            <td>
              <span class="lvl" :class="'lvl-' + row.level">{{ levelLabel(row.level) }}</span>
            </td>
          </tr>
          <tr v-if="pagedLogs.length === 0">
            <td colspan="7" class="empty-row">
              <div class="empty">🔍 暂无符合条件的日志记录</div>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- 分页 -->
      <div class="pagination">
        <div class="pg-info">
          共 <strong>{{ filtered.length }}</strong> 条 · 第
          <strong class="mono">{{ page }}</strong> / {{ totalPages || 1 }} 页
        </div>
        <div class="pg-actions">
          <button class="pg-btn" :disabled="page === 1" @click="go(1)">««</button>
          <button class="pg-btn" :disabled="page === 1" @click="go(page - 1)">‹ 上一页</button>
          <button
            v-for="n in pageWindow"
            :key="n"
            class="pg-btn"
            :class="{ active: n === page }"
            @click="go(n)"
          >{{ n }}</button>
          <button class="pg-btn" :disabled="page === totalPages" @click="go(page + 1)">下一页 ›</button>
          <button class="pg-btn" :disabled="page === totalPages" @click="go(totalPages)">»»</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
const MODULES = ['用户管理', '权限配置', '智能检索', '案例库', '作业指导', '设备管理', '系统设置']
const USERS = ['admin', 'zhangwei', 'liuting', 'chenbo', 'wangli', 'sunjie', 'zhouyang']
const ACTIONS = {
  '用户管理': [
    '创建新用户 zhouyang',
    '重置用户 zhangwei 的密码',
    '禁用用户 account_guest',
    '修改用户 liuting 的所属部门',
    '删除过期测试账号 test_01'
  ],
  '权限配置': [
    '为角色「检修工程师」新增设备写入权限',
    '移除角色「访客」的案例导出权限',
    '修改角色权限范围为仅华东厂区',
    '新增自定义角色「设备巡视员」'
  ],
  '智能检索': [
    '发起 AI 检索：离心泵轴承温度异常分析',
    '发起 AI 检索：PLC 通信中断诊断',
    '导出 AI 分析报告 PDF',
    '保存 AI 推荐处置方案到草稿'
  ],
  '案例库': [
    '新建案例【减速箱齿轮磨损修复 #1088】',
    '编辑案例 #1057 更新处置记录',
    '删除无效测试案例 #1003',
    '将案例 #1076 标记为"已归档"'
  ],
  '作业指导': [
    '发布新版《液压系统换油作业规程 v3.2》',
    '停用旧版本作业指导 v2.8',
    '添加「压力表现场校准」步骤 6 条',
    '调整作业指导章节排序'
  ],
  '设备管理': [
    '新增设备档案：CNC-850-032',
    '修改设备 #EQ-1028 的维保周期为 45 天',
    '批量导入设备台账 128 条',
    '标记设备 PUMP-07 为"停机待修"'
  ],
  '系统设置': [
    '修改全局故障预警阈值 70% → 65%',
    '开启邮件提醒：每日 08:30 运维摘要',
    '更新系统 Logo 与站点标题',
    '关闭「运维模式」开放普通用户登录'
  ]
}

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)] }

function genLogs(n) {
  const list = []
  const now = new Date()
  for (let i = 0; i < n; i++) {
    const d = new Date(now.getTime() - i * 1000 * (Math.floor(Math.random() * 480) + 30))
    const mod = pick(MODULES)
    const act = pick(ACTIONS[mod])
    const user = pick(USERS)
    const ok = Math.random() > 0.08
    let level = 'info'
    const r = Math.random()
    if (/密码|权限|删除|禁用|阈值|停用/.test(act)) level = r > 0.65 ? 'warn' : 'info'
    if (!ok) level = 'error'
    if (r > 0.93) level = 'warn'
    const ip = `10.128.${Math.floor(Math.random() * 40) + 10}.${Math.floor(Math.random() * 240) + 2}`
    list.push({
      id: i + 1,
      time: fmt(d),
      user, module: mod, action: act, ip, ok, level
    })
  }
  return list
}
function pad(n) { return n < 10 ? '0' + n : '' + n }
function fmt(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

export default {
  name: 'Logs',
  data() {
    const today = new Date()
    const from = new Date(today.getTime() - 14 * 86400000)
    return {
      logs: genLogs(268),
      filters: {
        keyword: '',
        module: '',
        level: '',
        from: `${from.getFullYear()}-${pad(from.getMonth() + 1)}-${pad(from.getDate())}`,
        to: `${today.getFullYear()}-${pad(today.getMonth() + 1)}-${pad(today.getDate())}`
      },
      page: 1,
      pageSize: 12
    }
  },
  computed: {
    stats() {
      const all = this.logs
      const dayAgo = Date.now() - 86400000
      const today = all.filter(l => new Date(l.time.replace(' ', 'T')).getTime() > dayAgo)
      return {
        total: all.length,
        totalDiff: 47,
        today: today.length,
        warn: all.filter(l => l.level === 'warn').length,
        error: all.filter(l => l.level === 'error').length
      }
    },
    filtered() {
      const kw = this.filters.keyword.trim().toLowerCase()
      const mod = this.filters.module
      const lv = this.filters.level
      const from = this.filters.from ? new Date(this.filters.from + ' 00:00:00').getTime() : -Infinity
      const to = this.filters.to ? new Date(this.filters.to + ' 23:59:59').getTime() : Infinity
      return this.logs.filter(l => {
        const t = new Date(l.time.replace(' ', 'T')).getTime()
        if (t < from || t > to) return false
        if (mod && l.module !== mod) return false
        if (lv && l.level !== lv) return false
        if (kw) {
          const hay = `${l.user} ${l.action} ${l.ip}`.toLowerCase()
          if (!hay.includes(kw)) return false
        }
        return true
      })
    },
    totalPages() {
      return Math.ceil(this.filtered.length / this.pageSize)
    },
    pagedLogs() {
      const start = (this.page - 1) * this.pageSize
      return this.filtered.slice(start, start + this.pageSize)
    },
    pageWindow() {
      const total = this.totalPages || 1
      const cur = this.page
      const from = Math.max(1, cur - 2)
      const to = Math.min(total, from + 4)
      const arr = []
      for (let i = from; i <= to; i++) arr.push(i)
      return arr
    }
  },
  methods: {
    formatNum(n) {
      return n.toLocaleString('en-US')
    },
    levelLabel(lv) {
      return { info: 'INFO', warn: 'WARN', error: 'ERROR' }[lv] || lv
    },
    slug(s) {
      return String(s).replace(/[^a-zA-Z0-9\u4e00-\u9fa5]+/g, '').toLowerCase()
    },
    onFilterChange() {
      this.page = 1
    },
    resetFilters() {
      this.filters = { keyword: '', module: '', level: '', from: this.filters.from, to: this.filters.to }
      this.page = 1
    },
    go(n) {
      if (n < 1 || n > this.totalPages) return
      this.page = n
    },
    exportCsv() {
      const header = ['时间', '操作人', '模块', '操作内容', '来源IP', '结果', '等级']
      const rows = this.filtered.map(l => [
        l.time, l.user, l.module, `"${l.action.replace(/"/g, '""')}"`, l.ip,
        l.ok ? '成功' : '失败', this.levelLabel(l.level)
      ])
      const csv = [header, ...rows].map(r => r.join(',')).join('\r\n')
      const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `operation-logs-${Date.now()}.csv`
      a.click()
      URL.revokeObjectURL(url)
    }
  }
}
</script>

<style scoped>
.logs {
  max-width: 1280px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 24px;
}
.page-title {
  font-size: 1.625rem;
  margin-bottom: 4px;
}
.page-sub {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}
.header-actions {
  display: flex;
  gap: 10px;
}
.btn-sm {
  padding: 6px 16px;
  font-size: 0.8125rem;
}

/* Stats */
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}
.stat-card {
  padding: 18px 20px;
}
.sc-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  margin-bottom: 10px;
}
.sc-num {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 1.75rem;
  color: var(--primary);
  line-height: 1.1;
  margin-bottom: 8px;
}
.sc-num.today { color: var(--text-primary); }
.sc-num.warn  { color: var(--accent-amber); }
.sc-num.danger{ color: var(--accent-red); }
.sc-foot {
  font-size: 0.6875rem;
  color: var(--text-muted);
}
.sc-foot .up { color: var(--accent-green); font-weight: 700; margin-right: 4px; }

/* Filter Bar */
.filter-bar {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr auto auto;
  gap: 14px;
  align-items: end;
  margin-bottom: 20px;
}
.filter-search {
  position: relative;
}
.filter-search .input {
  padding-left: 38px;
}
.fs-icon {
  position: absolute;
  left: 12px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 0.875rem;
  color: var(--text-muted);
}
.filter-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.filter-group label {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
  font-weight: 500;
}
.date-group {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  grid-template-rows: auto 1fr;
  grid-template-areas:
    "label label label"
    "from tilde to";
  gap: 6px;
  align-items: center;
}
.date-group label { grid-area: label; }
.date-group input:nth-of-type(1) { grid-area: from; }
.date-group .tilde { grid-area: tilde; color: var(--text-muted); font-size: 0.8125rem; text-align: center; }
.date-group input:nth-of-type(2) { grid-area: to; }
.mono { font-family: 'JetBrains Mono', monospace; }

/* Table */
.log-table-wrap {
  padding: 0;
  overflow: hidden;
}
.log-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.8125rem;
}
.log-table thead th {
  padding: 14px 18px;
  text-align: left;
  background: var(--bg-deep);
  color: var(--text-secondary);
  font-weight: 600;
  font-size: 0.75rem;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  border-bottom: 1px solid var(--border-subtle);
  position: sticky;
  top: 56px;
  z-index: 1;
}
.log-table tbody td {
  padding: 13px 18px;
  border-bottom: 1px solid var(--border-subtle);
  vertical-align: middle;
  color: var(--text-primary);
}
.log-row:hover td {
  background: var(--primary-subtle);
}
.log-row:last-child td {
  border-bottom: none;
}
.muted { color: var(--text-secondary); }
.op { line-height: 1.5; }

.user-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 60px;
  padding: 3px 10px;
  background: var(--primary-subtle);
  border: 1px solid var(--border-subtle);
  color: var(--primary);
  border-radius: 16px;
  font-size: 0.6875rem;
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
}

.mod-tag {
  display: inline-block;
  padding: 3px 10px;
  font-size: 0.6875rem;
  font-weight: 500;
  border-radius: 4px;
  border: 1px solid;
}
.mod-用户管理 { color: var(--primary); border-color: var(--border-active); background: var(--primary-subtle); }
.mod-权限配置 { color: var(--accent-amber); border-color: rgba(255,165,2,.3); background: rgba(255,165,2,.08); }
.mod-智能检索 { color: var(--accent-green); border-color: rgba(0,255,136,.3); background: rgba(0,255,136,.08); }
.mod-案例库 { color: #b088ff; border-color: rgba(176,136,255,.3); background: rgba(176,136,255,.08); }
.mod-作业指导 { color: #ff7ac6; border-color: rgba(255,122,198,.3); background: rgba(255,122,198,.08); }
.mod-设备管理 { color: var(--accent-orange); border-color: rgba(255,107,53,.3); background: rgba(255,107,53,.08); }
.mod-系统设置 { color: var(--text-secondary); border-color: var(--border-subtle); background: var(--bg-deep); }

.res {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 4px;
}
.res::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.res.ok { color: var(--accent-green); background: rgba(0,255,136,.08); border: 1px solid rgba(0,255,136,.25); }
.res.ok::before { background: var(--accent-green); box-shadow: 0 0 5px var(--accent-green); }
.res.fail { color: var(--accent-red); background: rgba(255,71,87,.08); border: 1px solid rgba(255,71,87,.25); }
.res.fail::before { background: var(--accent-red); box-shadow: 0 0 5px var(--accent-red); }

.lvl {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  font-size: 0.6875rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  font-family: 'JetBrains Mono', monospace;
  border-radius: 4px;
}
.lvl-info  { color: var(--primary);        background: var(--primary-subtle);    border: 1px solid var(--border-active); }
.lvl-warn  { color: var(--accent-amber);    background: rgba(255,165,2,.1);      border: 1px solid rgba(255,165,2,.35); }
.lvl-error { color: var(--accent-red);      background: rgba(255,71,87,.1);      border: 1px solid rgba(255,71,87,.35); }

.empty-row {
  padding: 40px 0 !important;
  text-align: center;
}
.empty {
  font-size: 0.875rem;
  color: var(--text-muted);
}

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-deep);
}
.pg-info {
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.pg-info strong { color: var(--text-primary); }
.pg-actions {
  display: flex;
  gap: 6px;
}
.pg-btn {
  min-width: 32px;
  height: 32px;
  padding: 0 10px;
  background: var(--bg-surface);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  font-size: 0.75rem;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}
.pg-btn:hover:not(:disabled) {
  background: var(--primary-subtle);
  color: var(--primary);
  border-color: var(--border-active);
}
.pg-btn.active {
  background: var(--primary);
  color: var(--bg-deep);
  border-color: var(--primary);
  font-weight: 700;
}
.pg-btn:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 1100px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
  .filter-bar {
    grid-template-columns: 1fr 1fr;
  }
  .filter-search { grid-column: 1 / -1; }
  .date-group { grid-column: 1 / -1; }
}
</style>
