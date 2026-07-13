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
        <div class="ov-card card">
          <div class="ov-icon total">⬡</div>
          <div class="ov-meta">
            <div class="ov-value">{{ overview.total }}</div>
            <div class="ov-label">设备总数</div>
          </div>
          <div class="ov-foot">全厂在册</div>
        </div>
        <div class="ov-card card">
          <div class="ov-icon ok">✓</div>
          <div class="ov-meta">
            <div class="ov-value ok-val">{{ overview.ok }}</div>
            <div class="ov-label">正常运行</div>
          </div>
          <div class="ov-foot ok-foot">占比 {{ okPercent }}%</div>
        </div>
        <div class="ov-card card">
          <div class="ov-icon ing">⚙</div>
          <div class="ov-meta">
            <div class="ov-value ing-val">{{ overview.repair }}</div>
            <div class="ov-label">维修中</div>
          </div>
          <div class="ov-foot ing-foot">处置中 {{ overview.repair }} 台</div>
        </div>
        <div class="ov-card card">
          <div class="ov-icon bad">✕</div>
          <div class="ov-meta">
            <div class="ov-value bad-val">{{ overview.down }}</div>
            <div class="ov-label">故障停机</div>
          </div>
          <div class="ov-foot bad-foot">需优先处置</div>
        </div>
      </div>
    </section>

    <!-- 图表行：饼图 + 折线并排 -->
    <section class="chart-row">
      <!-- 设备状态分布 饼图 -->
      <div class="panel chart-panel card">
        <div class="panel-header">
          <h2 class="panel-title">设备状态分布</h2>
          <span class="panel-hint">{{ overview.total }} 台设备</span>
        </div>
        <div class="pie-wrap">
          <div class="pie" :style="{ background: pieGradient }">
            <div class="pie-hole">
              <div class="pie-total">{{ overview.total }}</div>
              <div class="pie-sub">设备总数</div>
            </div>
          </div>
          <ul class="pie-legend">
            <li v-for="(l, i) in pieLegends" :key="i">
              <span class="legend-dot" :style="{ background: l.color }"></span>
              <span class="legend-name">{{ l.name }}</span>
              <span class="legend-num">{{ l.value }}</span>
              <span class="legend-pct">{{ l.pct }}%</span>
            </li>
          </ul>
        </div>
      </div>

      <!-- 近期故障趋势 -->
      <div class="panel chart-panel card">
        <div class="panel-header">
          <h2 class="panel-title">设备健康趋势</h2>
          <span class="panel-hint">近 7 天</span>
        </div>
        <div class="line-wrap">
          <svg class="line-svg" viewBox="0 0 600 240" preserveAspectRatio="xMidYMid meet">
            <g class="grid">
              <line x1="40" y1="40"  x2="580" y2="40" />
              <line x1="40" y1="90"  x2="580" y2="90" />
              <line x1="40" y1="140" x2="580" y2="140" />
              <line x1="40" y1="190" x2="580" y2="190" />
            </g>
            <g class="y-axis">
              <text x="30"  y="44"  text-anchor="end">15</text>
              <text x="30"  y="94"  text-anchor="end">10</text>
              <text x="30"  y="144" text-anchor="end">5</text>
              <text x="30"  y="194" text-anchor="end">0</text>
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
            </defs>
            <path :d="areaPath" fill="url(#lineFill)" />
            <polyline :points="linePoints" fill="none" stroke="url(#lineStroke)" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" />
            <g class="data-points">
              <g v-for="(p, i) in dataPoints" :key="i">
                <circle :cx="p.x" :cy="p.y" r="6" fill="var(--bg-deep)" stroke="url(#lineStroke)" stroke-width="2.5" />
                <circle :cx="p.x" :cy="p.y" r="2.5" fill="#2563eb" />
                <text class="p-val" :x="p.x" :y="p.y - 14" text-anchor="middle">{{ p.v }}</text>
              </g>
            </g>
            <g class="x-axis">
              <text v-for="(d, i) in trendData" :key="i" :x="40 + i * 90" y="220" text-anchor="middle">{{ d.label }}</text>
            </g>
          </svg>
        </div>
      </div>
    </section>

    <!-- 更多统计（折叠） -->
    <div class="more-stats-bar">
      <button class="link-btn" @click="showMore = !showMore">
        <span class="link-icon" :class="{ open: showMore }">▸</span>
        {{ showMore ? '收起统计' : '更多统计' }}
      </button>
    </div>

    <transition name="fade">
      <div v-if="showMore" class="more-stats">
        <!-- 维修任务统计 -->
        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">维修任务统计</h2>
            <span class="panel-hint">本月累计</span>
          </div>
          <div class="task-grid">
            <div class="task-card card">
              <div class="task-top">
                <div class="task-dot pending"></div>
                <div class="task-label">待派单</div>
              </div>
              <div class="task-value pending-val">{{ tasks.pending }}</div>
              <div class="task-bar">
                <div class="task-fill pending-fill" :style="{ width: taskPercent(tasks.pending) + '%' }"></div>
              </div>
              <div class="task-foot">等待分配维修工</div>
            </div>
            <div class="task-card card">
              <div class="task-top">
                <div class="task-dot doing"></div>
                <div class="task-label">进行中</div>
              </div>
              <div class="task-value doing-val">{{ tasks.doing }}</div>
              <div class="task-bar">
                <div class="task-fill doing-fill" :style="{ width: taskPercent(tasks.doing) + '%' }"></div>
              </div>
              <div class="task-foot">正在现场处置</div>
            </div>
            <div class="task-card card">
              <div class="task-top">
                <div class="task-dot done"></div>
                <div class="task-label">已完成</div>
              </div>
              <div class="task-value done-val">{{ tasks.done }}</div>
              <div class="task-bar">
                <div class="task-fill done-fill" :style="{ width: taskPercent(tasks.done) + '%' }"></div>
              </div>
              <div class="task-foot">完成率 {{ donePercent }}%</div>
            </div>
            <div class="task-card card">
              <div class="task-top">
                <div class="task-dot over"></div>
                <div class="task-label">超时</div>
              </div>
              <div class="task-value over-val">{{ tasks.over }}</div>
              <div class="task-bar">
                <div class="task-fill over-fill" :style="{ width: taskPercent(tasks.over) + '%' }"></div>
              </div>
              <div class="task-foot">SLA 超期未完成</div>
            </div>
          </div>
        </section>

        <!-- 知识报告审核统计 -->
        <section class="panel">
          <div class="panel-header">
            <h2 class="panel-title">📚 知识报告审核</h2>
            <span class="panel-hint">员工实践方案贡献</span>
          </div>
          <div class="kr-grid">
            <div class="kr-card card kr-pending" @click="goReview('pending')">
              <div class="kr-top">
                <div class="kr-icon kr-pending-icon">⏳</div>
                <div class="kr-hot" v-if="reportStats.pending > 0">{{ reportStats.pending }} 份</div>
              </div>
              <div class="kr-num kr-pending-num">{{ reportStats.pending }}</div>
              <div class="kr-label">待审核报告</div>
              <div class="kr-action">立即处理 →</div>
            </div>
            <div class="kr-card card kr-approved" @click="goReview('approved')">
              <div class="kr-top">
                <div class="kr-icon kr-approved-icon">✓</div>
              </div>
              <div class="kr-num kr-approved-num">{{ reportStats.approved }}</div>
              <div class="kr-label">已通过（本月）</div>
              <div class="kr-action">已入库知识库</div>
            </div>
            <div class="kr-card card kr-total" @click="goReview('all')">
              <div class="kr-top">
                <div class="kr-icon kr-total-icon">📑</div>
              </div>
              <div class="kr-num kr-total-num">{{ reportStats.total }}</div>
              <div class="kr-label">累计提交</div>
              <div class="kr-action">员工累计贡献量</div>
            </div>
            <div class="kr-card card kr-case" @click="goReview('synced')">
              <div class="kr-top">
                <div class="kr-icon kr-case-icon">📂</div>
              </div>
              <div class="kr-num kr-case-num">{{ reportStats.synced }}</div>
              <div class="kr-label">已同步入库</div>
              <div class="kr-action">案例库 / 作业指导</div>
            </div>
          </div>
        </section>
      </div>
    </transition>
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
      showMore: false,
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
    dataPoints() {
      const n = this.trendData.length
      if (n < 2) return []
      const maxV = Math.max(5, ...this.trendData.map(d => Number(d.v) || 0))
      const xStep = (580 - 40) / (n - 1)
      const yMin = 190, yMax = 40
      return this.trendData.map((d, i) => {
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
      return `${poly} L${last.x},190 L${first.x},190 Z`
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
  padding: 20px 24px;
  margin-bottom: 24px;
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
.panel { margin-bottom: 24px; }
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
  gap: 16px;
}
.ov-card {
  padding: 20px;
  display: grid;
  grid-template-columns: 56px 1fr;
  grid-template-rows: auto auto;
  column-gap: 14px;
  row-gap: 12px;
  position: relative;
  overflow: hidden;
}
.ov-card::after {
  content: ''; position: absolute;
  right: -40px; bottom: -40px;
  width: 140px; height: 140px; border-radius: 50%;
  opacity: 0.06;
}
.ov-icon {
  grid-row: 1 / 3;
  width: 56px; height: 56px;
  border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; font-weight: 700;
}
.ov-icon.total { color: var(--primary);       background: var(--primary-subtle); border: 1px solid var(--border-active); }
.ov-icon.ok    { color: var(--accent-green);  background: rgba(16,185,129,0.12); border: 1px solid rgba(16,185,129,0.25); }
.ov-icon.ing   { color: var(--accent-cyan);   background: rgba(6,182,212,0.12); border: 1px solid rgba(6,182,212,0.25); }
.ov-icon.bad   { color: var(--accent-red);    background: rgba(239,68,68,0.1);  border: 1px solid rgba(239,68,68,0.22); }

.ov-card:nth-child(1)::after { background: var(--primary); }
.ov-card:nth-child(2)::after { background: var(--accent-green); }
.ov-card:nth-child(3)::after { background: var(--primary); }
.ov-card:nth-child(4)::after { background: var(--accent-red); }

.ov-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 2.25rem; font-weight: 700; line-height: 1;
  color: var(--text-primary);
}
.ov-value.ok-val  { color: var(--accent-green); text-shadow: 0 0 12px rgba(16,185,129,0.3); }
.ov-value.ing-val { color: var(--accent-cyan);  text-shadow: 0 0 12px rgba(6,182,212,0.3); }
.ov-value.bad-val { color: var(--accent-red);  text-shadow: 0 0 12px rgba(239,68,68,0.35); }

.ov-label {
  font-size: 0.8125rem; color: var(--text-muted);
  margin-top: 6px;
}
.ov-foot {
  grid-column: 2;
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 999px;
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
.task-top {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 12px;
}
.task-dot {
  width: 10px; height: 10px; border-radius: 50%;
  box-shadow: 0 0 10px currentColor;
}
.task-dot.pending { color: var(--accent-orange); background: var(--accent-orange); }
.task-dot.doing   { color: var(--accent-cyan);   background: var(--accent-cyan); }
.task-dot.done    { color: var(--accent-green);  background: var(--accent-green); }
.task-dot.over    { color: var(--accent-red);    background: var(--accent-red); }

.task-label { font-size: 0.8125rem; color: var(--text-muted); }

.task-value {
  font-family: 'Orbitron', sans-serif;
  font-size: 1.75rem; font-weight: 700; line-height: 1;
  margin-bottom: 10px;
}
.task-value.pending-val { color: var(--accent-orange); }
.task-value.doing-val   { color: var(--accent-cyan); }
.task-value.done-val    { color: var(--accent-green); }
.task-value.over-val    { color: var(--accent-red); }

.task-bar {
  height: 6px; border-radius: 999px;
  background: rgba(255,255,255,0.06);
  overflow: hidden; margin-bottom: 10px;
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

/* ====================== 图表通用 ====================== */
.chart-panel { padding: 20px 24px; }
.chart-row {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 16px;
  margin-bottom: 24px;
}

/* 饼图 */
.pie-wrap {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 28px;
  align-items: center;
  min-height: 220px;
}
.pie {
  width: 180px; height: 180px; border-radius: 50%;
  position: relative;
  margin: 0 auto;
  filter: drop-shadow(0 0 12px rgba(37,99,235,0.12));
}
.pie-hole {
  position: absolute; inset: 24px;
  border-radius: 50%;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  box-shadow: inset 0 0 18px rgba(0,0,0,0.3);
}
.pie-total {
  font-family: 'Orbitron', sans-serif;
  font-size: 2rem; font-weight: 700; color: var(--primary);
}
.pie-sub { font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }

.pie-legend {
  list-style: none; padding: 0; margin: 0;
  display: flex; flex-direction: column; gap: 14px;
}
.pie-legend li {
  display: grid;
  grid-template-columns: 14px 1fr auto auto;
  align-items: center;
  gap: 12px;
  font-size: 0.8125rem;
}
.legend-dot {
  width: 12px; height: 12px; border-radius: 4px;
  box-shadow: 0 0 8px currentColor;
}
.legend-name { color: var(--text-secondary); }
.legend-num {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600; color: var(--text-primary);
}
.legend-pct {
  padding: 2px 8px; border-radius: 999px;
  background: rgba(255,255,255,0.04);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6875rem; color: var(--text-muted);
}

/* 折线图 */
.line-wrap { width: 100%; }
.line-svg {
  width: 100%; height: 240px;
}
.grid line { stroke: rgba(255,255,255,0.06); stroke-dasharray: 3 3; }
.y-axis text, .x-axis text {
  fill: var(--text-muted);
  font-size: 11px;
  font-family: 'JetBrains Mono', monospace;
}
.data-points .p-val {
  fill: var(--primary);
  font-size: 12px;
  font-family: 'JetBrains Mono', monospace;
  font-weight: 600;
}

/* === 知识报告卡片 === */
.kr-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}
.kr-card {
  padding: 18px 20px;
  position: relative;
  overflow: hidden;
  cursor: default;
  transition: all 0.25s ease;
}
.kr-card.kr-pending { cursor: pointer; }
.kr-card.kr-pending:hover {
  transform: translateY(-3px);
  border-color: rgba(255,165,2,0.5);
  box-shadow: 0 10px 28px rgba(255,165,2,0.15);
}
.kr-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.kr-icon {
  width: 36px; height: 36px;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.15rem;
}
.kr-pending-icon { background: rgba(245,158,11,0.14); color: var(--accent-orange); }
.kr-approved-icon { background: rgba(16,185,129,0.14); color: var(--accent-green); }
.kr-total-icon { background: var(--primary-subtle); color: var(--primary); }
.kr-case-icon { background: rgba(6,182,212,0.14); color: var(--accent-cyan); }
.kr-hot {
  font-size: 0.6875rem;
  padding: 3px 10px;
  background: var(--accent-amber);
  color: #fff;
  border-radius: 999px;
  font-weight: 600;
  animation: pulse-badge 1.8s ease-in-out infinite;
}
@keyframes pulse-badge {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255,165,2,0.4); }
  50% { box-shadow: 0 0 0 6px rgba(255,165,2,0); }
}
.kr-num {
  font-size: 2.25rem;
  font-weight: 700;
  line-height: 1;
  font-family: 'Orbitron', sans-serif;
}
.kr-pending-num { color: var(--accent-orange); }
.kr-approved-num { color: var(--accent-green); }
.kr-total-num { color: var(--primary); }
.kr-case-num { color: var(--accent-cyan); }
.kr-label {
  margin-top: 10px;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  font-weight: 500;
}
.kr-action {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-subtle);
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.kr-pending .kr-action {
  color: var(--accent-orange);
  font-weight: 600;
}
/* ====================== 折叠面板 ====================== */
.more-stats-bar { margin: 0 0 16px; }
.link-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: var(--radius);
  background: var(--bg-elevated); color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  cursor: pointer; font-size: 0.8125rem;
  transition: all var(--duration) var(--ease);
}
.link-btn:hover {
  color: var(--primary); border-color: var(--border-hover);
  background: var(--primary-subtle);
}
.link-icon {
  display: inline-block; font-size: 0.75rem;
  transition: transform var(--duration) var(--ease);
}
.link-icon.open { transform: rotate(90deg); }

.fade-enter-active, .fade-leave-active { transition: opacity 220ms var(--ease); }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 1080px) {
  .chart-row { grid-template-columns: 1fr; }
  .kr-grid { grid-template-columns: repeat(2, 1fr); }
}
@media (max-width: 560px) {
  .kr-grid { grid-template-columns: 1fr; }
}
</style>
