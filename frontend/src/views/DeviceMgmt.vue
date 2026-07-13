<template>
  <div class="container">
    <section class="hero-mini">
      <div>
        <div class="crumb"><router-link to="/home">仪表盘</router-link> · <span>设备管理</span></div>
        <h1 class="page-title">🏗️ 设备管理</h1>
        <p class="page-sub">全厂设备台账 · 健康度 · 维护记录 · 位置分布</p>
      </div>
      <div class="hero-actions">
        <div class="search-box card">
          <span>🔍</span>
          <input v-model="keyword" placeholder="搜索设备编号 / 名称 / 所在区域 / 型号..." />
        </div>
        <button class="btn btn-primary" @click="toast('新增设备请在后端API扩展前端暂未开放弹窗，或在/api/devicesPOST')">+ 新增设备</button>
      </div>
    </section>

    <section class="stats-grid mini">
      <div class="stat-card card">
        <div class="stat-icon blue">🏷️</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.total }}</div>
          <div class="stat-label">注册设备总数</div>
          <div class="stat-trend up">↑ 实时统计</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.ok }}</div>
          <div class="stat-label">正常运行</div>
          <div class="stat-trend up">占比 {{ stats.goodPct }}%</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon orange">⚠</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.repair }}</div>
          <div class="stat-label">维修中</div>
          <div class="stat-trend down">处理中</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon red">🛑</div>
        <div class="stat-info">
          <div class="stat-value">{{ stats.down }}</div>
          <div class="stat-label">故障停机中</div>
          <div class="stat-trend down">请派发工单</div>
        </div>
      </div>
    </section>

    <section class="filters-row card">
      <div class="filters-group">
        <div class="filter-label">设备大类</div>
        <div class="chip-group">
          <span v-for="t in tagChips" :key="t" class="chip" :class="{ active: activeTag === t }" @click="activeTag = t; page = 1">{{ t }}</span>
        </div>
      </div>
      <div class="filters-group">
        <div class="filter-label">设备状态</div>
        <div class="chip-group">
          <span v-for="s in statusChips" :key="s.v" class="chip" :class="['chip-'+s.cls, { active: activeStatus === s.v }]" @click="activeStatus = s.v; page = 1">{{ s.label }}</span>
        </div>
      </div>
    </section>

    <section class="table-section card">
      <table class="data-table">
        <thead>
          <tr>
            <th>设备编号</th>
            <th>设备名称</th>
            <th>所在区域</th>
            <th>型号 / 规格</th>
            <th>启用日期</th>
            <th>健康度</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" style="padding:64px 0">
            <div class="skeleton-wrap">
              <div v-for="i in 6" :key="i" class="skeleton-row"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
            </div>
          </td></tr>
          <tr v-else-if="!pagedItems.length"><td colspan="8" style="text-align:center;padding:64px 0;color:var(--text-muted);" class="muted">暂无符合条件的设备</td></tr>
          <tr v-for="d in pagedItems" :key="d.code" class="row-hover">
            <td class="mono">{{ d.code }}</td>
            <td>
              <div class="device-main">
                <div class="device-icon" :class="'dev-'+tagCls(d.tag)">{{ tagIcon(d.tag) }}</div>
                <div>
                  <div class="device-name">{{ d.name }}</div>
                  <div class="device-sn">{{ d.manufacturer ? '品牌：' + d.manufacturer : ('大类：' + (d.tag || '-')) }}</div>
                </div>
              </div>
            </td>
            <td><span class="area-tag">{{ d.location || '-' }}</span></td>
            <td class="muted">{{ d.spec || '-' }}</td>
            <td class="muted">{{ d.commission_date ? d.commission_date.slice(0,10) : '-' }}</td>
            <td>
              <div class="health-cell">
                <div class="health-bar-sm">
                  <div class="health-fill-sm" :class="healthClass(d.health)" :style="{width: (d.health||0)+'%'}"></div>
                </div>
                <span class="health-val" :class="healthTextClass(d.health)">{{ d.health || 0 }}%</span>
              </div>
            </td>
            <td>
              <span class="status-pill" :class="'st-'+statusCls(d.status)">{{ statusLabel(d.status) }}</span>
            </td>
            <td>
              <button class="btn btn-outline btn-xs" @click="detail(d)">详情</button>
              <button class="btn btn-primary btn-xs" @click="dispatch(d)" :disabled="d.status==='normal'">派维修</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-if="filteredDevices.length > size" class="pagination">
        <div class="muted pagination-info">共 {{ filteredDevices.length }} 台 · 第 {{ page }} / {{ totalPages }} 页</div>
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
import { listDevicesApi, deviceStatsApi } from '../utils/api'

const STATUS_LABEL = {
  normal:    '正常运行',
  repairing: '维修中',
  down:      '故障停机'
}

const TAG_ICON = {
  '机械': '⚙️',
  '电气': '🔌',
  '液压': '💧',
  '仪表': '📊',
  '安全': '🛡️'
}
const TAG_CLS = {
  '机械': 'cnc',
  '电气': 'plc',
  '液压': 'conv',
  '仪表': 'robot',
  '安全': 'air'
}

export default {
  name: 'DeviceMgmt',
  data() {
    return {
      keyword: '',
      activeTag: '全部',
      activeStatus: 'all',
      statusChips: [
        { v: 'all',         label: '全部',     cls: 'good' },
        { v: 'normal',      label: '正常运行', cls: 'good' },
        { v: 'repairing',   label: '维修中',   cls: 'warn' },
        { v: 'down',        label: '故障停机', cls: 'bad'  }
      ],
      allDevices: [],
      loading: false,
      stats: { total: 0, ok: 0, repair: 0, down: 0, goodPct: 0 },
      page: 1, size: 20
    }
  },
  computed: {
    tagChips() {
      const s = new Set(['全部'])
      for (const d of this.allDevices) {
        if (d && d.tag) s.add(d.tag)
      }
      return Array.from(s)
    },
    filteredDevices() {
      const kw = this.keyword.trim().toLowerCase()
      const tag = this.activeTag
      const st = this.activeStatus
      return this.allDevices.filter(d => {
        if (tag !== '全部' && d.tag !== tag) return false
        if (st !== 'all' && d.status !== st) return false
        if (kw) {
          const s = String(d.code||'').toLowerCase() + ' ' +
                    String(d.name||'').toLowerCase() + ' ' +
                    String(d.location||'').toLowerCase() + ' ' +
                    String(d.spec||'').toLowerCase() + ' ' +
                    String(d.manufacturer||'').toLowerCase()
          if (!s.includes(kw)) return false
        }
        return true
      })
    },
    totalPages() {
      return Math.max(1, Math.ceil(this.filteredDevices.length / this.size))
    },
    pagedItems() {
      const start = (this.page - 1) * this.size
      return this.filteredDevices.slice(start, start + this.size)
    }
  },
  watch: {
    keyword() { this.page = 1 },
    activeTag() { this.page = 1 },
    activeStatus() { this.page = 1 },
    totalPages(p) { if (this.page > p) this.page = p }
  },
  created() {
    this.reloadStats()
    this.loadAll()
  },
  methods: {
    toast,
    async reloadStats() {
      try {
        const s = await deviceStatsApi() || {}
        const by = s.by_status || {}
        this.stats = {
          total:  Number(s.total || 0),
          ok:     Number(by['正常运行'] || by.normal || 0),
          repair: Number(by['维修中']   || by.repairing  || 0),
          down:   Number(by['故障停机'] || by.down   || 0)
        }
        this.stats.goodPct = this.stats.total === 0 ? 0
          : Math.round(this.stats.ok / this.stats.total * 100)
      } catch (_) {}
    },
    async loadAll() {
      this.loading = true
      try {
        const p = await listDevicesApi({ page: 1, size: 20000 }) || {}
        this.allDevices = p.items || []
      } finally {
        this.loading = false
      }
    },
    tagIcon(t) { return TAG_ICON[t] || '📦' },
    tagCls(t)  { return TAG_CLS[t]  || 'cnc' },
    statusCls(s) {
      if (s === 'normal') return 'good'
      if (s === 'down')   return 'bad'
      if (s === 'repairing') return 'warn'
      return 'warn'
    },
    statusLabel(s) { return STATUS_LABEL[s] || s || '未知' },
    healthClass(h) { return h >= 90 ? 'good' : h >= 70 ? 'warn' : 'bad' },
    healthTextClass(h) { return this.healthClass(h) },
    detail(d) {
      const s = [
        '设备编号：' + d.code,
        '设备名称：' + d.name,
        '大类：' + (d.tag || '-'),
        '位置：' + (d.location || '-'),
        '规格：' + (d.spec || '-'),
        '健康度：' + (d.health||0) + '%',
        '状态：' + this.statusLabel(d.status)
      ]
      if (d.last_repair_at) s.push('最近维修：' + String(d.last_repair_at).slice(0,16).replace('T',' '))
      if (d.remark) s.push('备注：' + d.remark)
      alert(s.join('\n'))
    },
    dispatch(d) {
      this.$router.push('/admin?tab=repair&device=' + encodeURIComponent(d.code || ''))
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

.filters-row { padding: 14px 18px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 12px; }
.filters-group { display: flex; align-items: center; gap: 14px; flex-wrap: wrap; }
.filter-label { font-size: 0.75rem; color: var(--text-muted); font-weight: 600; letter-spacing: 0.5px; min-width: 72px; }
.chip-group { display: flex; gap: 6px; flex-wrap: wrap; }
.chip {
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 0.75rem;
  cursor: pointer;
  background: var(--bg-deep);
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  transition: all var(--duration) var(--ease);
}
.chip:hover { border-color: var(--border-active); color: var(--text-primary); }
.chip.active { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); font-weight: 600; }
.chip-good.active { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); border-color: rgba(0, 255, 136, 0.35); }
.chip-warn.active { background: rgba(255, 204, 51, 0.1); color: #ffcc33; border-color: rgba(255, 204, 51, 0.35); }
.chip-bad.active { background: rgba(255, 71, 87, 0.1); color: var(--accent-red); border-color: rgba(255, 71, 87, 0.35); }

.table-section { padding: 0; overflow: hidden; }
.data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.data-table thead th { text-align: left; padding: 12px 18px; background: var(--bg-deep); color: var(--text-muted); font-weight: 600; font-size: 0.75rem; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-subtle); }
.data-table tbody td { padding: 14px 18px; border-bottom: 1px solid var(--border-subtle); color: var(--text-primary); vertical-align: middle; }
.row-hover:hover td { background: var(--primary-subtle); }

.mono { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--primary); }
.muted { color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

.device-main { display: flex; align-items: center; gap: 12px; }
.device-icon {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center; font-size: 1.25rem;
  background: var(--primary-subtle); border: 1px solid var(--border-active);
}
.dev-cnc { background: rgba(79, 214, 255, 0.08); border-color: rgba(79, 214, 255, 0.25); }
.dev-robot { background: rgba(255, 156, 86, 0.08); border-color: rgba(255, 156, 86, 0.25); }
.dev-plc { background: rgba(168, 85, 247, 0.08); border-color: rgba(168, 85, 247, 0.25); }
.dev-conv { background: rgba(34, 211, 238, 0.08); border-color: rgba(34, 211, 238, 0.25); }
.device-name { font-weight: 600; }
.device-sn { font-size: 0.6875rem; color: var(--text-muted); margin-top: 2px; font-family: 'JetBrains Mono', monospace; }

.area-tag {
  display: inline-block; padding: 3px 10px; font-size: 0.75rem;
  background: var(--bg-deep); border: 1px solid var(--border-subtle);
  border-radius: 6px; color: var(--text-secondary);
}

.health-cell { min-width: 140px; display: flex; align-items: center; gap: 10px; }
.health-bar-sm { flex: 1; height: 6px; background: var(--bg-deep); border-radius: 3px; overflow: hidden; }
.health-fill-sm { height: 100%; border-radius: 3px; transition: width 0.4s ease; }
.health-fill-sm.good { background: var(--accent-green); }
.health-fill-sm.warn { background: linear-gradient(90deg, #ffcc33, #ff9c56); }
.health-fill-sm.bad { background: linear-gradient(90deg, #ff4757, #ff9c56); }
.health-val { font-size: 0.75rem; font-weight: 700; font-family: 'JetBrains Mono', monospace; min-width: 42px; text-align: right; }
.health-val.good { color: var(--accent-green); }
.health-val.warn { color: #ffcc33; }
.health-val.bad { color: var(--accent-red); }

.status-pill { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
.st-running { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); }
.st-warning { background: rgba(255, 204, 51, 0.12); color: #ffcc33; }
.st-fault { background: rgba(255, 71, 87, 0.12); color: var(--accent-red); }

.status-pill { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
.st-running, .st-good  { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); }
.st-warning, .st-warn  { background: rgba(255, 204, 51, 0.12); color: #ffcc33; }
.st-fault,   .st-bad   { background: rgba(255, 71, 87, 0.12); color: var(--accent-red); }

.btn-xs { padding: 4px 12px; font-size: 0.6875rem; margin-right: 6px; }
.btn-xs:last-child { margin-right: 0; }

.skeleton-wrap { padding: 0 18px; display: flex; flex-direction: column; gap: 18px; }
.skeleton-row { display: grid; grid-template-columns: repeat(8, 1fr); gap: 16px; }
.skeleton-row span {
  display: block; height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(0,212,255,0.10) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
.skeleton-row span:nth-child(1) { width: 70%; }
.skeleton-row span:nth-child(2) { width: 85%; }
.skeleton-row span:nth-child(5) { width: 60%; }
.skeleton-row span:nth-child(6) { width: 55%; }
.skeleton-row span:nth-child(7) { width: 75%; }
.skeleton-row span:nth-child(8) { width: 90%; }
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
