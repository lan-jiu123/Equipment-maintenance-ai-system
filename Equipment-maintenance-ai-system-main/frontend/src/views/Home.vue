<template>
  <div class="container">
    <!-- 顶部欢迎条 -->
    <section class="top-bar card">
      <div class="top-left">
        <h1 class="top-title">设备检修<span class="text-primary">智能系统</span></h1>
        <p class="top-sub">欢迎回来，{{ adminName }} · 今日生产运行平稳，{{ todoTasks }} 项任务待处理</p>
      </div>
      <div class="top-right">
        <div class="status-pill online"><i></i>系统运行中</div>
        <div class="clock">
          <span class="clock-time">{{ currentTime }}</span>
          <span class="clock-date">{{ currentDate }}</span>
        </div>
      </div>
    </section>

    <!-- 设备运行概览 -->
    <section class="panel">
      <div class="panel-header">
        <h2 class="panel-title">设备运行概览</h2>
        <span class="panel-hint">截至 {{ currentTime }}</span>
      </div>
      <div class="overview-grid">
        <div class="ov-card">
          <div class="ov-icon total">⬡</div>
          <div class="ov-data">
            <div class="ov-value">{{ overview.total }}</div>
            <div class="ov-label">设备总数</div>
          </div>
        </div>
        <div class="ov-card" :class="{ 'is-alert': overview.down > 0 }">
          <div class="ov-icon bad">✕</div>
          <div class="ov-data">
            <div class="ov-value bad-val">{{ overview.down }}</div>
            <div class="ov-label">故障停机</div>
          </div>
        </div>
        <div class="ov-card">
          <div class="ov-icon ing">⚙</div>
          <div class="ov-data">
            <div class="ov-value ing-val">{{ overview.repair }}</div>
            <div class="ov-label">维修中</div>
          </div>
        </div>
        <div class="ov-card">
          <div class="ov-icon ok">✓</div>
          <div class="ov-data">
            <div class="ov-value ok-val">{{ overview.ok }}</div>
            <div class="ov-label">正常运行</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 图表行：饼图 + 折线并排（flex 布局确保同行） -->
    <div class="chart-row">
      <!-- 设备状态分布 饼图 -->
      <div class="chart-panel">
        <div class="panel-header">
          <h2 class="panel-title">设备状态分布</h2>
          <span class="panel-hint">{{ overview.total }} 台</span>
        </div>
        <div class="pie-wrap">
          <div class="pie" :style="{ background: pieGradient }">
            <div class="pie-hole">
              <div class="pie-total">{{ overview.total }}</div>
              <div class="pie-sub">总数</div>
            </div>
          </div>
          <ul class="pie-legend">
            <li v-for="(l, i) in pieLegends" :key="i">
              <span class="legend-dot" :style="{ background: l.color }"></span>
              <span class="legend-name">{{ l.name }}</span>
              <span class="legend-num">{{ l.value }}</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- 近期故障趋势 -->
      <div class="chart-panel">
        <div class="panel-header">
          <h2 class="panel-title">设备健康趋势</h2>
          <span class="panel-hint trend-legend">
            <span class="legend-item" v-if="trendRange === 7"><span class="legend-line this-week"></span>本周</span>
            <span class="legend-item" v-if="trendRange === 7"><span class="legend-line prev-week"></span>前7天</span>
            <span class="trend-range">
              <button :class="{ active: trendRange === 7 }" @click="trendRange = 7">7天</button>
              <button :class="{ active: trendRange === 30 }" @click="trendRange = 30">前30天</button>
            </span>
          </span>
        </div>
        <div class="line-wrap">
          <svg class="line-svg" viewBox="0 0 600 240" preserveAspectRatio="xMidYMid meet">
            <g class="grid">
              <line x1="40" y1="35"  x2="580" y2="35" />
              <line x1="40" y1="80"  x2="580" y2="80" />
              <line x1="40" y1="125" x2="580" y2="125" />
              <line x1="40" y1="170" x2="580" y2="170" />
            </g>
            <g class="y-axis">
              <text x="30"  y="39"  text-anchor="end">15</text>
              <text x="30"  y="84"  text-anchor="end">10</text>
              <text x="30"  y="129" text-anchor="end">5</text>
              <text x="30"  y="174" text-anchor="end">0</text>
            </g>
            <defs>
              <linearGradient id="lineFill" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%"   stop-color="#2563eb" stop-opacity="0.25" />
                <stop offset="100%" stop-color="#2563eb" stop-opacity="0" />
              </linearGradient>
              <linearGradient id="lineStroke" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%"   stop-color="#2563eb" />
                <stop offset="100%" stop-color="#06b6d4" />
              </linearGradient>
              <linearGradient id="lineFillPrev" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%"   stop-color="#f59e0b" stop-opacity="0.18" />
                <stop offset="100%" stop-color="#f59e0b" stop-opacity="0" />
              </linearGradient>
              <linearGradient id="lineStrokePrev" x1="0" x2="1" y1="0" y2="0">
                <stop offset="0%"   stop-color="#f59e0b" />
                <stop offset="100%" stop-color="#fb923c" />
              </linearGradient>
            </defs>
            <path :d="areaPath" fill="url(#lineFill)" />
            <polyline :points="linePoints" fill="none" stroke="url(#lineStroke)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
            <path v-if="trendRange === 7" :d="areaPathPrev" fill="url(#lineFillPrev)" />
            <polyline v-if="trendRange === 7" :points="linePointsPrev" fill="none" stroke="url(#lineStrokePrev)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" stroke-dasharray="6 4" />
            <g class="data-points">
              <g v-for="(p, i) in dataPoints" :key="i">
                <circle :cx="p.x" :cy="p.y" r="6" fill="var(--bg-deep)" stroke="url(#lineStroke)" stroke-width="2.5" />
                <circle :cx="p.x" :cy="p.y" r="2.5" fill="#2563eb" />
                <text class="p-val" :x="p.x" :y="p.y - 12" text-anchor="middle">{{ p.v }}</text>
              </g>
            </g>
            <g class="data-points-prev" v-if="trendRange === 7">
              <g v-for="(p, i) in dataPointsPrev" :key="i">
                <circle :cx="p.x" :cy="p.y" r="6" fill="var(--bg-deep)" stroke="url(#lineStrokePrev)" stroke-width="2.5" />
                <circle :cx="p.x" :cy="p.y" r="2.5" fill="#f59e0b" />
                <text class="p-val" :x="p.x" :y="p.y - 12" text-anchor="middle">{{ p.v }}</text>
              </g>
            </g>
            <g class="x-axis">
              <text v-for="(t, i) in xAxisTicks" :key="i" :x="t.x" y="205" text-anchor="middle">{{ t.label }}</text>
            </g>
          </svg>
        </div>
      </div>
    </div>

    <!-- 综合统计（维修任务 + 知识报告合并为一个卡片，上下布局） -->
    <section class="combined-panel">
      <!-- 上：维修任务统计 -->
      <div class="combined-block">
        <div class="panel-header">
          <h2 class="panel-title">维修任务统计</h2>
          <span class="panel-hint">本月累计</span>
        </div>
        <div class="task-grid">
          <div class="task-card">
            <div class="task-top"><div class="task-dot pending"></div><div class="task-label">待派单</div></div>
            <div class="task-value pending-val">{{ tasks.pending }}</div>
            <div class="task-bar"><div class="task-fill pending-fill" :style="{ width: taskPercent(tasks.pending) + '%' }"></div></div>
          </div>
          <div class="task-card">
            <div class="task-top"><div class="task-dot doing"></div><div class="task-label">进行中</div></div>
            <div class="task-value doing-val">{{ tasks.doing }}</div>
            <div class="task-bar"><div class="task-fill doing-fill" :style="{ width: taskPercent(tasks.doing) + '%' }"></div></div>
          </div>
          <div class="task-card">
            <div class="task-top"><div class="task-dot done"></div><div class="task-label">已完成</div></div>
            <div class="task-value done-val">{{ tasks.done }}</div>
            <div class="task-bar"><div class="task-fill done-fill" :style="{ width: taskPercent(tasks.done) + '%' }"></div></div>
          </div>
          <div class="task-card">
            <div class="task-top"><div class="task-dot over"></div><div class="task-label">超时</div></div>
            <div class="task-value over-val">{{ tasks.over }}</div>
            <div class="task-bar"><div class="task-fill over-fill" :style="{ width: taskPercent(tasks.over) + '%' }"></div></div>
          </div>
        </div>
      </div>

      <div class="combined-divider"></div>

      <!-- 下：知识报告审核统计 -->
      <div class="combined-block">
        <div class="panel-header">
          <h2 class="panel-title">📚 知识报告审核</h2>
          <span class="panel-hint">员工实践方案贡献</span>
        </div>
        <div class="kr-grid">
          <div class="kr-card kr-pending" @click="goReview('pending')">
            <div class="kr-top"><span class="kr-icon kr-pending-icon">⏳</span><span class="kr-label">待审核</span></div>
            <div class="kr-num kr-pending-num">{{ reportStats.pending }}</div>
          </div>
          <div class="kr-card kr-approved" @click="goReview('approved')">
            <div class="kr-top"><span class="kr-icon kr-approved-icon">✓</span><span class="kr-label">已通过</span></div>
            <div class="kr-num kr-approved-num">{{ reportStats.approved }}</div>
          </div>
          <div class="kr-card kr-total" @click="goReview('all')">
            <div class="kr-top"><span class="kr-icon kr-total-icon">📑</span><span class="kr-label">累计提交</span></div>
            <div class="kr-num kr-total-num">{{ reportStats.total }}</div>
          </div>
          <div class="kr-card kr-case" @click="goReview('synced')">
            <div class="kr-top"><span class="kr-icon kr-case-icon">📂</span><span class="kr-label">已入库</span></div>
            <div class="kr-num kr-case-num">{{ reportStats.synced }}</div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
import { getUser } from '../utils/auth'
import { dashboardOverviewApi } from '../utils/api'

export default {
  name: 'Home',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      overview: { total: 0, ok: 0, repair: 0, down: 0 },
      tasks:    { pending: 0, doing: 0, done: 0, over: 0 },
      reportStats: { total: 0, pending: 0, approved: 0, synced: 0 },
      pieData: [],
      trendData: [],
      trendPrev: [],
      trendRange: 7,
      loading: false,
      _retryTimer: null
    }
  },
  computed: {
    todoTasks() {
      return this.tasks.pending + this.tasks.doing + this.tasks.over + this.reportStats.pending
    },
    adminName() {
      const u = getUser()
      const base = (u && (u.fullname || u.username)) || ''
      if (!base) return '管理员'
      const surname = base.charAt(0)
      const role = (u && u.role) || 'sysadmin'
      if (role === 'worker') return surname + '师傅'
      return surname + '主任'
    },
    okPercent() {
      return this.overview.total === 0 ? 0 : Math.round(this.overview.ok / this.overview.total * 100)
    },
    donePercent() {
      const total = this.tasks.pending + this.tasks.doing + this.tasks.done + this.tasks.over
      return total === 0 ? 0 : Math.round(this.tasks.done / total * 100)
    },
    tasksTotal() {
      return this.tasks.pending + this.tasks.doing + this.tasks.done + this.tasks.over
    },
    pieGradient() {
      if (!this.pieData || this.pieData.length === 0) return 'conic-gradient(#3b5fae 0 0)'
      const total = this.pieData.reduce((s, x) => s + x.value, 0)
      if (total === 0) return 'conic-gradient(#3b5fae 0 0)'
      let angle = 0
      const segs = []
      for (const p of this.pieData) {
        const start = angle
        const end = angle + (p.value / total) * 360
        segs.push(`${p.color} ${start}deg ${end}deg`)
        angle = end
      }
      return `conic-gradient(${segs.join(', ')})`
    },
    pieLegends() {
      if (!this.pieData || this.pieData.length === 0) return []
      const total = this.pieData.reduce((s, x) => s + x.value, 0)
      return this.pieData.map(p => ({
        ...p,
        pct: total === 0 ? 0 : Math.round(p.value / total * 100)
      }))
    },
    trendSlice() {
      const range = this.trendRange
      return Array.isArray(this.trendData) ? this.trendData.slice(-range) : []
    },
    xAxisTicks() {
      const data = this.trendSlice
      const n = data.length
      if (!n) return []
      // 7 天全标；30 天采 7 个（首尾必含 + 中间均匀 5 个）
      const count = n <= 7 ? n : 7
      const step = (n - 1) / (count - 1)
      const ticks = []
      for (let i = 0; i < count; i++) {
        const idx = Math.round(i * step)
        ticks.push({
          label: data[idx].label,
          x: 40 + idx * (540 / (n - 1))
        })
      }
      return ticks
    },
    trendPrevSlice() {
      const range = this.trendRange
      return Array.isArray(this.trendPrev) ? this.trendPrev.slice(-range) : []
    },
    dataPoints() {
      const data = this.trendSlice
      const n = data.length
      if (n < 2) return []
      const maxV = 15
      const xStep = (580 - 40) / (n - 1)
      const yMin = 170, yMax = 35
      return data.map((d, i) => {
        const v = Number(d.v) || 0
        return {
          x: 40 + i * xStep,
          y: yMin - (v / maxV) * (yMin - yMax),
          v
        }
      })
    },
    linePoints() {
      return this.dataPoints.length ? this.dataPoints.map(p => `${p.x},${p.y}`).join(' ') : '40,190 580,190'
    },
    areaPath() {
      const pts = this.dataPoints
      if (!pts.length) return ''
      const first = pts[0], last = pts[pts.length - 1]
      const poly = pts.map(p => `L${p.x},${p.y}`).join(' ').replace(/^L/, 'M')
      return `${poly} L${last.x},170 L${first.x},170 Z`
    },
    dataPointsPrev() {
      const data = this.trendPrevSlice
      const n = data.length
      if (n < 2) return []
      const maxV = 15
      const xStep = (580 - 40) / (n - 1)
      const yMin = 170, yMax = 35
      return data.map((d, i) => {
        const v = Number(d.v) || 0
        return {
          x: 40 + i * xStep,
          y: yMin - (v / maxV) * (yMin - yMax),
          v
        }
      })
    },
    linePointsPrev() {
      return this.dataPointsPrev.length ? this.dataPointsPrev.map(p => `${p.x},${p.y}`).join(' ') : '40,190 580,190'
    },
    areaPathPrev() {
      const pts = this.dataPointsPrev
      if (!pts.length) return ''
      const first = pts[0], last = pts[pts.length - 1]
      const poly = pts.map(p => `L${p.x},${p.y}`).join(' ').replace(/^L/, 'M')
      return `${poly} L${last.x},170 L${first.x},170 Z`
    }
  },
  created() {
    this.loadDashboardData()
  },
  mounted() {
    this.updateTime()
    this.timer = setInterval(this.updateTime, 1000)
  },
  beforeUnmount() {
    clearInterval(this.timer)
    if (this._retryTimer) clearTimeout(this._retryTimer)
  },
  methods: {
    async loadDashboardData() {
      if (this.loading) return
      this.loading = true
      try {
        const d = await dashboardOverviewApi() || {}
        this.overview = {
          total: Number((d.devices || {}).total || 0),
          ok:    Number((d.devices || {}).ok || 0),
          repair:Number((d.devices || {}).repair || 0),
          down:  Number((d.devices || {}).down || 0)
        }
        this.tasks = {
          pending: Number((d.tickets || {}).pending || 0),
          doing:   Number((d.tickets || {}).doing || 0),
          done:    Number((d.tickets || {}).done || 0),
          over:    Number((d.tickets || {}).over || 0)
        }
        this.reportStats = {
          total:    Number((d.reports || {}).total || 0),
          pending:  Number((d.reports || {}).pending || 0),
          approved: Number((d.reports || {}).approved || 0),
          synced:   Number((d.reports || {}).synced || 0)
        }
        this.pieData = Array.isArray(d.pie) ? d.pie : []
        this.trendData = Array.isArray(d.trend) ? d.trend : []
        this.trendPrev = Array.isArray(d.trend_prev) ? d.trend_prev : []
      } catch (e) {
        if (!this._retryTimer) {
          this._retryTimer = setTimeout(() => {
            this._retryTimer = null
            this.loadDashboardData()
          }, 5000)
        }
      } finally {
        this.loading = false
      }
    },
    goReview(kr) {
      const q = { tab: 'knowledge' }
      if (kr && ['all', 'pending', 'approved', 'synced', 'rejected'].indexOf(kr) >= 0) q.kr = kr
      this.$router.push({ path: '/admin', query: q })
    },
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN', {
        hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit'
      })
      this.currentDate = now.toLocaleDateString('zh-CN', {
        year: 'numeric', month: 'long', day: 'numeric', weekday: 'long'
      })
    },
    taskPercent(n) {
      const total = this.tasksTotal
      if (total === 0) return 0
      return Math.min(100, Math.round(n / total * 100))
    }
  }
}
</script>

<style scoped>
/* ====================== 通用 ====================== */
.text-primary { color: var(--primary); }

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  margin-bottom: 16px;
  background:
    linear-gradient(135deg, rgba(37, 99, 235, 0.10), transparent 60%),
    linear-gradient(315deg, rgba(6, 182, 212, 0.06), transparent 60%);
}
.top-title { font-size: 1.5rem; margin: 0 0 6px; }
.top-sub { color: var(--text-secondary); font-size: 0.875rem; margin: 0; }

.top-right {
  display: flex; align-items: center; gap: 20px;
}
.status-pill {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 14px; border-radius: 999px;
  font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px;
  background: var(--primary-subtle); color: var(--primary);
  border: 1px solid var(--border-active);
}
.status-pill i {
  width: 8px; height: 8px; border-radius: 50%;
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
  animation: blink 2s infinite;
}
@keyframes blink { 50% { opacity: 0.4; } }

.clock { text-align: right; line-height: 1.2; }
.clock-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.25rem; font-weight: 700; color: var(--text-primary);
}
.clock-date {
  display: block; font-size: 0.75rem; color: var(--text-secondary);
  margin-top: 4px;
}

/* ====================== Panel 通用 ====================== */
.panel { margin-bottom: 16px; }
.panel-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 12px;
}
.panel-title {
  font-size: 1rem; color: var(--text-primary); margin: 0;
  display: flex; align-items: center; gap: 8px;
  font-weight: 600;
}
.panel-title::before {
  content: ''; width: 3px; height: 16px;
  background: linear-gradient(180deg, var(--primary), var(--accent-cyan));
  border-radius: 2px;
}
.panel-hint {
  font-size: 0.75rem; color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}
.panel-more {
  font-size: 0.75rem; color: var(--primary);
  text-decoration: none; font-weight: 500;
}
.panel-more:hover { color: var(--primary-dim); }

/* ====================== 设备运行概览 ====================== */
.overview-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
}
.ov-card {
  position: relative; overflow: hidden;
  padding: 12px 14px;
  display: flex; flex-direction: row; align-items: flex-start; gap: 10px;
  border-radius: var(--radius-lg);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
}
.ov-data { display: flex; flex-direction: column; gap: 2px; }
/* 立体装饰图案（双层叠加 + 阴影 = 3D 效果） */
.ov-card::after {
  content: ''; position: absolute;
  right: -28px; bottom: -28px;
  width: 90px; height: 90px; border-radius: 50%;
  opacity: 0.15;
  box-shadow: inset -3px -3px 8px rgba(0,0,0,0.2), inset 3px 3px 8px rgba(255,255,255,0.1);
}
.ov-card::before {
  content: ''; position: absolute;
  right: -8px; top: -8px;
  width: 36px; height: 36px; border-radius: 8px;
  opacity: 0.1;
  transform: rotate(45deg);
}
.ov-card:has(.total)::after  { background: var(--primary); }
.ov-card:has(.total)::before { background: var(--primary); }
.ov-card:has(.bad-val)::after { background: var(--accent-red); opacity: 0.22; }
.ov-card:has(.bad-val)::before { background: var(--accent-red); }
.ov-card:has(.ing-val)::after { background: var(--accent-cyan); }
.ov-card:has(.ing-val)::before { background: var(--accent-cyan); }
.ov-card:has(.ok-val)::after  { background: var(--accent-green); }
.ov-card:has(.ok-val)::before  { background: var(--accent-green); }
/* 故障停机：高风险视觉突出 */
.ov-card:has(.bad-val) {
  border: 1px solid var(--accent-red);
  background: rgba(239, 68, 68, 0.08);
}
.ov-card.is-alert {
  animation: ovAlertBreathe 2s ease-in-out infinite;
}
.ov-card.is-alert .ov-icon {
  animation: ovAlertIcon 2s ease-in-out infinite;
}
@keyframes ovAlertBreathe {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  50%      { box-shadow: 0 0 18px 3px rgba(239, 68, 68, 0.40); }
}
@keyframes ovAlertIcon {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  50%      { box-shadow: 0 0 14px 2px rgba(239, 68, 68, 0.55); }
}
/* icon 底座带立体阴影 */
.ov-icon {
  width: 40px; height: 40px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.2rem; font-weight: 700;
  box-shadow: 0 4px 12px rgba(0,0,0,0.15), inset 0 1px 0 rgba(255,255,255,0.1);
}
.ov-icon.total { color: var(--primary);       background: linear-gradient(135deg, var(--primary-subtle), rgba(37,99,235,0.2)); border: 1px solid var(--border-active); }
.ov-icon.ok    { color: var(--accent-green);  background: linear-gradient(135deg, rgba(16,185,129,0.12), rgba(16,185,129,0.25)); border: 1px solid rgba(16,185,129,0.3); }
.ov-icon.ing   { color: var(--accent-cyan);   background: linear-gradient(135deg, rgba(6,182,212,0.12), rgba(6,182,212,0.25)); border: 1px solid rgba(6,182,212,0.3); }
.ov-icon.bad   { color: var(--accent-red);    background: linear-gradient(135deg, rgba(239,68,68,0.1), rgba(239,68,68,0.25)); border: 1px solid rgba(239,68,68,0.3); }

.ov-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem; font-weight: 800; line-height: 1.1;
  color: var(--text-primary);
}
.ov-value.ok-val  { color: var(--accent-green); }
.ov-value.ing-val { color: var(--accent-cyan); }
.ov-value.bad-val { color: var(--accent-red); }

.ov-label {
  font-size: 0.7rem; color: var(--text-muted);
}
.ov-foot {
  font-size: 0.65rem;
  color: var(--text-secondary);
  justify-self: start;
  background: rgba(255,255,255,0.04);
  color: var(--text-muted);
}
.ov-foot.ok-foot  { color: var(--accent-green); background: rgba(16,185,129,0.08); }
.ov-foot.ing-foot { color: var(--accent-cyan);  background: rgba(6,182,212,0.08); }
.ov-foot.bad-foot { color: var(--accent-red);  background: rgba(239,68,68,0.08); }

/* ====================== 维修任务统计 ====================== */
.task-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.task-card { padding: 20px; }
.task-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.task-card {
  padding: 8px 10px;
  border-radius: var(--radius);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
}
.task-top {
  display: flex; align-items: center; gap: 5px;
  margin-bottom: 4px;
}
.task-dot {
  width: 6px; height: 6px; border-radius: 50%;
}
.task-dot.pending { background: var(--accent-orange); }
.task-dot.doing   { background: var(--accent-cyan); }
.task-dot.done    { background: var(--accent-green); }
.task-dot.over    { background: var(--accent-red); }

.task-label { font-size: 0.68rem; color: var(--text-muted); }

.task-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem; font-weight: 700; line-height: 1;
  margin-bottom: 4px;
}
.task-value.pending-val { color: var(--accent-orange); }
.task-value.doing-val   { color: var(--accent-cyan); }
.task-value.done-val    { color: var(--accent-green); }
.task-value.over-val    { color: var(--accent-red); }

.task-bar {
  height: 4px; border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden; margin-bottom: 6px;
}
.task-fill {
  height: 100%; border-radius: 999px;
  transition: width 0.6s var(--ease);
}
.task-fill.pending-fill { background: linear-gradient(90deg, var(--accent-orange), #fbbf24); }
.task-fill.doing-fill   { background: linear-gradient(90deg, var(--accent-cyan), #67e8f9); }
.task-fill.done-fill    { background: linear-gradient(90deg, var(--accent-green), #34d399); }
.task-fill.over-fill    { background: linear-gradient(90deg, var(--accent-red), #f87171); }

.task-foot { font-size: 0.75rem; color: var(--text-secondary); }

/* ====================== 图表行（flex 同行，不走全局 .panel/.card 样式） ====================== */
.chart-row {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 12px;
  margin-bottom: 12px;
}
.chart-panel {
  flex: 1;
  min-width: 0;
  padding: 10px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
}

/* 饼图（左右布局：饼 + 图例，尽可能放大） */
.pie-wrap {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 10px;
  flex: 1;
  min-height: 120px;
}
.pie {
  width: 130px; height: 130px; border-radius: 50%;
  position: relative; flex-shrink: 0;
  filter: drop-shadow(0 0 12px rgba(37,99,235,0.12));
}
.pie-hole {
  position: absolute; inset: 16px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
}
.pie-total {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.6rem; font-weight: 700; color: var(--primary);
}
.pie-sub { font-size: 0.7rem; color: var(--text-muted); }

.pie-legend {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 5px;
}
.pie-legend li {
  display: flex; align-items: center; gap: 6px;
  font-size: 0.75rem;
}
.legend-dot {
  width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0;
}
.legend-name { color: var(--text-secondary); }
.legend-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600; color: var(--text-primary);
  margin-left: auto;
}

/* 折线图（尽可能放大，overflow 防止溢出卡片） */
.line-wrap { width: 100%; flex: 1; overflow: hidden; }
.line-svg {
  width: 100%; height: 200px;
}
.grid line { stroke: rgba(255,255,255,0.06); stroke-dasharray: 3 3; }
.y-axis text, .x-axis text {
  fill: var(--text-secondary);
  font-size: 13px;
  font-family: 'JetBrains Mono', monospace;
}
.data-points .p-val {
  fill: var(--text-primary);
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
}
.data-points-prev .p-val {
  fill: #f59e0b;
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

/* 折线图图例（本周 / 上周）*/
.trend-legend {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-weight: 600;
}
.legend-line {
  display: inline-block;
  width: 18px;
  height: 0;
  border-top-width: 3px;
  border-top-style: solid;
}
.legend-line.this-week {
  border-top-color: #2563eb;
}
.legend-line.prev-week {
  border-top-color: #f59e0b;
  border-top-style: dashed;
}

/* 折线图时间范围切换 */
.trend-range {
  display: inline-flex;
  gap: 0;
  margin-left: 4px;
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
  overflow: hidden;
}
.trend-range button {
  background: transparent;
  border: none;
  color: var(--text-muted);
  font-size: 0.6875rem;
  font-family: 'JetBrains Mono', monospace;
  padding: 2px 8px;
  cursor: pointer;
  transition: all 0.15s ease;
}
.trend-range button + button {
  border-left: 1px solid var(--border-subtle);
}
.trend-range button.active {
  background: var(--primary-subtle);
  color: var(--primary);
  font-weight: 600;
}
.trend-range button:hover:not(.active) {
  color: var(--text-primary);
  background: rgba(255,255,255,0.04);
}

/* === 综合统计卡片（维修任务 + 知识报告 上下布局） === */
.combined-panel {
  padding: 12px 16px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: 16px;
}
.combined-block .panel-header { margin-bottom: 8px; }
.combined-divider {
  height: 1px;
  background: var(--border-subtle);
  margin: 8px 0;
}

/* === 知识报告卡片 === */
/* 知识报告卡片 —— 与维修任务 task-card 同布局 */
.kr-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.kr-card {
  padding: 8px 10px;
  border-radius: var(--radius);
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  cursor: pointer;
  transition: all 0.2s ease;
}
.kr-card:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
}
.kr-icon {
  font-size: 0.85rem;
  display: inline-block;
  margin-right: 4px;
}
.kr-pending-icon { color: var(--accent-orange); }
.kr-approved-icon { color: var(--accent-green); }
.kr-total-icon { color: var(--primary); }
.kr-case-icon { color: var(--accent-cyan); }
.kr-num {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.1rem; font-weight: 700; line-height: 1;
  margin: 4px 0;
}
.kr-pending-num { color: var(--accent-orange); }
.kr-approved-num { color: var(--accent-green); }
.kr-total-num { color: var(--primary); }
.kr-case-num { color: var(--accent-cyan); }
.kr-label {
  font-size: 0.68rem;
  color: var(--text-muted);
}

@media (max-width: 1080px) {
  .chart-row { grid-template-columns: 1fr; }
}
@media (max-width: 560px) {
  .task-grid { grid-template-columns: repeat(2, 1fr); }
  .kr-grid { grid-template-columns: repeat(2, 1fr); }
}
</style>
