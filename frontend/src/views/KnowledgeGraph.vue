<template>
  <div class="container">
    <header class="page-header">
      <div>
        <div class="crumb"><router-link :to="isWorker ? '/desk' : '/home'">{{ isWorker ? '工作台' : '仪表盘' }}</router-link> · <span>知识图谱</span></div>
        <h1 class="page-title">🧠 知识图谱</h1>
        <p class="page-sub">设备 · 故障 · 原因 · 解决方案 的关联关系网络</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-outline" @click="loadGraph(true)" :disabled="loading">
          {{ loading ? '刷新中…' : '刷新图谱' }}
        </button>
        <button v-if="!isWorker" class="btn btn-primary" @click="rebuildGraph" :disabled="loading">重建图谱</button>
      </div>
    </header>

    <div class="tag-tabs">
      <button
        v-for="t in tagTabs" :key="t.key"
        class="tag-tab"
        :class="{ active: activeTag === t.key }"
        @click="switchTag(t.key)"
      >
        <span>{{ t.label }}</span>
        <span class="tag-count">{{ tagCounts[t.key] ?? 0 }}</span>
      </button>
    </div>

    <div class="graph-stats">
      <div class="stat-item">
        <span class="stat-num">{{ nodeCount }}</span>
        <span class="stat-label">知识节点</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ linkCount }}</span>
        <span class="stat-label">关联关系</span>
      </div>
      <div class="stat-item">
        <span class="stat-num">{{ caseCount }}</span>
        <span class="stat-label">沉淀案例</span>
      </div>
    </div>

    <div class="type-legend">
      <div v-for="t in nodeTypes" :key="t.type" class="legend-item">
        <span class="legend-dot" :style="{background: t.color}"></span>
        <span class="legend-label">{{ t.label }}</span>
      </div>
    </div>

    <div class="graph-stage">
      <div class="graph-container" ref="chartRef" :class="{ 'is-refreshing': loading }"></div>
      <transition name="graph-loading">
        <div v-if="loading" class="graph-loading-mask">
          <span class="graph-spinner"></span>
          <span>正在刷新知识图谱…</span>
        </div>
      </transition>
    </div>
    <transition name="graph-notice">
      <div v-if="refreshNotice" class="graph-refresh-notice">{{ refreshNotice }}</div>
    </transition>

    <div class="graph-info" v-if="selectedNode">
      <h3>节点详情</h3>
      <div class="info-row">
        <span class="info-label">名称</span>
        <span class="info-value">{{ selectedNode.name }}</span>
      </div>
      <div class="info-row">
        <span class="info-label">类型</span>
        <span class="info-value">{{ getTypeLabel(selectedNode.type) }}</span>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import * as echarts from 'echarts'
import { request } from '../utils/request'
import { getUser } from '../utils/auth'

const chartRef = ref(null)
let chartInstance = null
let freezeTimer = null
let noticeTimer = null

const loading = ref(false)
const graphData = ref({ nodes: [], links: [] })
const selectedNode = ref(null)
const activeTag = ref("all")
const refreshNotice = ref('')

// tag 切换 tab（全部 + 5 个故障分类）
const tagTabs = [
  { key: "all", label: "全部" },
  { key: "机械", label: "机械" },
  { key: "电气", label: "电气" },
  { key: "液压", label: "液压" },
  { key: "仪表", label: "仪表" },
  { key: "安全", label: "安全" },
  { key: "综合", label: "综合" },
]
const tagCounts = ref({})

const nodeTypes = [
  { type: '设备', label: '设备', color: '#4fd1c5' },
  { type: '故障', label: '故障', color: '#fc8181' },
  { type: '原因', label: '原因', color: '#f6e05e' },
  { type: '解决方案', label: '解决方案', color: '#68d391' },
  { type: '案例', label: '案例', color: '#9f7aea' },
]

const nodeCount = computed(() => graphData.value.nodes.length)
const linkCount = computed(() => graphData.value.links.length)
const caseCount = computed(() => graphData.value.nodes.filter(n => n.type === '案例').length)
const isWorker = computed(() => {
  const user = getUser() || {}
  return user.role === 'worker'
})

function getTypeLabel(type) {
  const t = nodeTypes.find(n => n.type === type)
  return t ? t.label : type
}

function getTypeColor(type) {
  const t = nodeTypes.find(n => n.type === type)
  return t ? t.color : '#718096'
}

async function loadGraph(showFeedback = false) {
  if (loading.value) return
  const startedAt = Date.now()
  loading.value = true
  try {
    const params = activeTag.value === 'all' ? {} : { tag: activeTag.value }
    const data = await request('/knowledge/graph', { params })
    graphData.value = data || { nodes: [], links: [] }
    selectedNode.value = null
    renderChart()
    await refreshTagCounts()
    if (showFeedback) {
      const remaining = Math.max(0, 500 - (Date.now() - startedAt))
      if (remaining) await new Promise(resolve => setTimeout(resolve, remaining))
      refreshNotice.value = `✓ 图谱已刷新：${graphData.value.nodes.length} 个节点，${graphData.value.links.length} 条关系`
      if (noticeTimer) clearTimeout(noticeTimer)
      noticeTimer = setTimeout(() => { refreshNotice.value = '' }, 2200)
    }
  } catch (e) {
    // request 已内置 401 跳登录 + toast 提示，这里无需重复处理
  } finally {
    loading.value = false
  }
}

async function refreshTagCounts() {
  try {
    const data = await request('/knowledge/graph/stats')
    tagCounts.value = data || {}
  } catch (e) {
    // ignore
  }
}

function switchTag(tag) {
  if (activeTag.value === tag) return
  activeTag.value = tag
  selectedNode.value = null
  loadGraph()
}

async function rebuildGraph() {
  if (loading.value) return
  loading.value = true
  try {
    const data = await request('/knowledge/graph/rebuild', { method: 'POST' })
    graphData.value = data
    renderChart()
    refreshTagCounts()
  } catch (e) {
    // request 已内置 toast 提示
  } finally {
    loading.value = false
  }
}

function renderChart() {
  if (!chartInstance) return
  if (!graphData.value.nodes.length) {
    chartInstance.clear()
    return
  }

  // 节点大小按类型分层：设备 > 故障 > 原因/解决方案 > 案例
  const NODE_SIZE = { '设备': 40, '故障': 30, '原因': 24, '解决方案': 24, '案例': 18 }

  const nodes = graphData.value.nodes.map(n => ({
    id: n.name,
    name: n.name,
    category: n.type,
    itemStyle: {
      color: getTypeColor(n.type)
    },
    symbolSize: NODE_SIZE[n.type] || 24
  }))

  const links = graphData.value.links.map(l => ({
    source: l.source,
    target: l.target,
    name: l.relation,
    lineStyle: {
      color: '#4a5568',
      width: 2
    },
    label: {
      show: true,
      formatter: '{b}',
      fontSize: 11,
      color: '#a0aec0'
    }
  }))

  const categories = nodeTypes.map(t => ({
    name: t.type,
    itemStyle: { color: t.color }
  }))

  chartInstance.clear()
  chartInstance.setOption({
    tooltip: {
      trigger: 'item',
      formatter: function(params) {
        if (params.dataType === 'node') {
          return `<strong>${params.name}</strong><br/>类型：${getTypeLabel(params.data.category)}`
        } else if (params.dataType === 'edge') {
          return `<strong>${params.data.name}</strong><br/>${params.data.source} → ${params.data.target}`
        }
        return ''
      }
    },
    legend: {
      data: categories.map(c => c.name),
      top: 10,
      textStyle: { color: '#a0aec0' }
    },
    series: [{
      type: 'graph',
      layout: 'force',
      animation: true,
      animationDuration: 2000,
      animationEasingUpdate: 'quinticInOut',
      data: nodes,
      links: links,
      categories: categories,
      roam: true,
      draggable: true,
      force: {
        repulsion: 800,
        edgeLength: [120, 220],
        gravity: 0.05,
        friction: 0.8,
        layoutAnimation: true
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        }
      },
      select: {
        itemStyle: {
          borderColor: '#fff',
          borderWidth: 3
        }
      },
      label: {
        show: true,
        position: 'right',
        fontSize: 12,
        color: '#e2e8f0',
        formatter: '{b}'
      }
    }]
  })
}

function initChart() {
  if (chartRef.value) {
    chartInstance = echarts.init(chartRef.value)
    chartInstance.on('click', function(params) {
      if (params.dataType === 'node') {
        selectedNode.value = {
          name: params.name,
          type: params.data.category
        }
      }
    })

    renderChart()

    // 2秒后固定全部节点（力导向已稳定）
    freezeTimer = setTimeout(function () {
      if (!chartInstance) return
      const opt = chartInstance.getOption()
      const series = opt.series[0]
      if (series && series.data) {
        series.data.forEach(function (n) { n.fixed = true })
        chartInstance.setOption({ series: [{ data: series.data }] })
      }
    }, 2000)

    // 拖动前松开全部节点，让被拖节点可移动
    chartInstance.on('dragstart', function () {
      if (!chartInstance) return
      const opt = chartInstance.getOption()
      const series = opt.series[0]
      if (series && series.data) {
        series.data.forEach(function (n) { n.fixed = false })
        chartInstance.setOption({ series: [{ data: series.data }] })
      }
    })

    // 拖动结束后重新布局并固定
    chartInstance.on('dragend', function () {
      if (!chartInstance) return
      setTimeout(function () {
        if (!chartInstance) return
        const opt = chartInstance.getOption()
        const series = opt.series[0]
        if (series && series.data) {
          series.data.forEach(function (n) { n.fixed = true })
          chartInstance.setOption({ series: [{ data: series.data }] })
        }
      }, 500)
    })
  }
}

function handleResize() {
  chartInstance?.resize()
}

onMounted(() => {
  loadGraph()
  setTimeout(initChart, 100)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (freezeTimer) clearTimeout(freezeTimer)
  if (noticeTimer) clearTimeout(noticeTimer)
  chartInstance?.dispose()
})
</script>

<style scoped>
.container { max-width: var(--max-width); margin: 0 auto; padding: 28px; }

.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 24px; flex-wrap: wrap; }
.page-title { font-size: 1.75rem; font-weight: 800; margin: 0; color: var(--text-primary); }
.page-sub { font-size: 0.875rem; color: var(--text-secondary); margin-top: 6px; }
.crumb { font-size: 0.75rem; color: var(--text-muted); margin-bottom: 6px; }
.crumb a { color: var(--primary); text-decoration: none; }

.header-actions { display: flex; gap: 10px; }

.graph-stats { display: flex; gap: 16px; margin-bottom: 20px; }
.stat-item { flex: 1; background: var(--bg-card); border-radius: var(--radius); padding: 16px; border: 1px solid var(--border-subtle); }
.stat-num { display: block; font-size: 1.75rem; font-weight: 800; color: var(--primary); font-family: 'JetBrains Mono', monospace; }
.stat-label { display: block; font-size: 0.75rem; color: var(--text-muted); margin-top: 4px; }

.type-legend { display: flex; gap: 20px; margin-bottom: 16px; flex-wrap: wrap; }
.legend-item { display: flex; align-items: center; gap: 6px; }
.legend-dot { width: 12px; height: 12px; border-radius: 50%; }
.legend-label { font-size: 0.75rem; color: var(--text-secondary); }

.graph-stage { position: relative; }
.graph-container {
  width: 100%;
  height: 500px;
  background: var(--bg-card);
  border-radius: var(--radius);
  border: 1px solid var(--border-subtle);
  transition: filter .2s ease, opacity .2s ease;
}
.graph-container.is-refreshing { filter: blur(1px); opacity: .58; }
.graph-loading-mask {
  position: absolute; inset: 0; z-index: 3;
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; color: var(--text-primary); font-size: .875rem; font-weight: 600;
  background: rgba(5, 11, 31, .28); backdrop-filter: blur(1px);
  border-radius: var(--radius);
}
.graph-spinner {
  width: 34px; height: 34px; border-radius: 50%;
  border: 3px solid rgba(59,130,246,.2); border-top-color: var(--primary);
  animation: graph-spin .75s linear infinite;
  box-shadow: 0 0 18px rgba(59,130,246,.2);
}
@keyframes graph-spin { to { transform: rotate(360deg); } }
.graph-loading-enter-active, .graph-loading-leave-active { transition: opacity .18s ease; }
.graph-loading-enter-from, .graph-loading-leave-to { opacity: 0; }
.graph-refresh-notice {
  width: max-content; max-width: 100%; margin: 12px auto 0;
  padding: 9px 16px; border: 1px solid rgba(16,185,129,.3);
  border-radius: 999px; background: rgba(16,185,129,.1);
  color: var(--accent-green); font-size: .8rem; font-weight: 600;
}
.graph-notice-enter-active, .graph-notice-leave-active { transition: all .2s ease; }
.graph-notice-enter-from, .graph-notice-leave-to { opacity: 0; transform: translateY(-5px); }

.graph-info {
  margin-top: 16px;
  background: var(--bg-card);
  border-radius: var(--radius);
  padding: 20px;
  border: 1px solid var(--border-subtle);
  display: none;
}
.graph-info h3 { margin: 0 0 12px; font-size: 0.875rem; color: var(--text-primary); }
.info-row { display: flex; gap: 16px; margin-bottom: 8px; }
.info-label { width: 80px; font-size: 0.75rem; color: var(--text-muted); }
.info-value { font-size: 0.875rem; color: var(--text-primary); }

.graph-info:has(.info-row) { display: block; }

.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.tag-tabs { display: flex; gap: 8px; margin-bottom: 18px; flex-wrap: wrap; }
.tag-tab {
  display: flex; align-items: center; gap: 8px;
  padding: 8px 16px; border-radius: var(--radius);
  border: 1px solid var(--border-subtle);
  background: var(--bg-card); color: var(--text-secondary);
  font-size: 0.8125rem; font-family: inherit;
  cursor: pointer; transition: all var(--duration) var(--ease);
}
.tag-tab:hover { border-color: var(--primary); color: var(--primary); }
.tag-tab.active {
  background: var(--primary); color: #fff; border-color: var(--primary);
  font-weight: 600;
}
.tag-tab.active .tag-count { background: rgba(255,255,255,0.25); color: #fff; }
.tag-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 22px; height: 22px; padding: 0 6px; border-radius: 11px;
  background: var(--bg-field); color: var(--text-muted);
  font-size: 0.6875rem; font-weight: 700; font-family: 'JetBrains Mono', monospace;
}
</style>
