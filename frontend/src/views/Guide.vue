<template>
  <div class="container">
    <header class="page-header">
      <h1 class="page-title">作业指导</h1>
      <p class="page-desc">标准操作流程与安全规范 · 共 {{ filteredSteps.length }} 项作业规程 · 员工贡献 {{ employeeGuideCount }} 项</p>
    </header>

    <div class="source-tabs">
      <button
        v-for="t in sourceTabs"
        :key="t.key"
        class="source-tab"
        :class="{ active: currentSource === t.key }"
        @click="currentSource = t.key"
      >
        <span class="st-icon">{{ t.icon }}</span>
        <span class="st-label">{{ t.label }}</span>
        <span class="st-count">{{ t.count }}</span>
      </button>
    </div>

    <div class="guide-toolbar" v-if="currentSource !== 'mine'">
      <div class="search-bar">
        <span class="search-icon">⌕</span>
        <input
          v-model="searchQuery"
          class="input"
          placeholder="搜索作业步骤标题或内容..."
        />
      </div>
      <div class="filter-tabs">
        <button
          v-for="cat in categories"
          :key="cat"
          class="filter-tab"
          :class="{ active: currentCat === cat }"
          @click="currentCat = cat"
        >
          <span class="cat-dot" :class="'cat-' + catClass(cat)"></span>
          {{ cat }}
          <span class="cat-count">{{ categoryCount(cat) }}</span>
        </button>
      </div>
    </div>

    <div class="progress-summary card" v-if="currentCat === '全部' && currentSource !== 'mine' && !loadingGuides">
      <div class="progress-item" v-for="s in summaryStats" :key="s.name">
        <div class="progress-name">{{ s.name }}</div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" :style="{ width: s.percent + '%', background: s.color }"></div>
        </div>
        <div class="progress-count">{{ s.count }} 项</div>
      </div>
    </div>

    <template v-if="currentSource === 'mine'">
      <div v-if="loadingReports" class="skeleton-grid">
        <div v-for="n in 6" :key="n" class="card skeleton-card">
          <div class="skeleton-line skeleton-title"></div>
          <div class="skeleton-line" style="width: 60%"></div>
          <div class="skeleton-line" style="width: 80%"></div>
          <div class="skeleton-line" style="width: 50%"></div>
        </div>
      </div>
      <div v-else class="case-grid">
        <div
          v-for="(r, i) in myReports"
          :key="'report-' + (r.id || i)"
          class="case-card card"
          :class="{ expanded: r._open }"
          @click="r._open = !r._open"
        >
          <div class="case-top">
            <span class="case-tag" :class="catClass(r.device_type)">{{ r.device_type || '通用' }}</span>
            <span class="status-badge" :class="'status-' + (r.status || 'pending')">{{ statusText(r.status) }}</span>
          </div>
          <h3 class="case-title">{{ r.title }}</h3>
          <p class="case-summary">{{ (r.problem || r.solution || '暂无描述').slice(0, 100) }}{{ ((r.problem || r.solution || '').length > 100 ? '...' : '') }}</p>
          <div class="case-meta">
            <span class="meta-item">◈ {{ r.device || '通用设备' }}</span>
            <span class="meta-item">◎ {{ formatDate(r.created_at_ts * 1000) }}</span>
          </div>
          <div class="case-contributor">
            <span class="contrib-icon">⏱</span>
            <span>提交时间：{{ formatDate(r.created_at_ts * 1000) }}</span>
          </div>
          <transition name="expand">
            <div v-show="r._open" class="case-detail">
              <div class="detail-section">
                <div class="detail-label">问题描述</div>
                <p class="detail-text">{{ r.problem || '—' }}</p>
              </div>
              <div class="detail-section">
                <div class="detail-label">解决方案</div>
                <p class="detail-text solution-text">{{ r.solution || '—' }}</p>
              </div>
              <div class="detail-section tips" v-if="r.review_remark">
                <div class="detail-label">审核备注</div>
                <p class="detail-text">{{ r.review_remark }}</p>
              </div>
              <div class="expand-arrow">▲ 收起</div>
            </div>
          </transition>
          <div class="toggle-hint" v-if="!r._open">点击查看详情 ▼</div>
        </div>
      </div>
      <div v-if="!loadingReports && myReports.length === 0" class="empty-state">
        <div class="empty-icon">👤</div>
        <p>您还没有提交过知识贡献</p>
        <p class="empty-sub">通过工单系统提交的解决方案会在这里展示</p>
      </div>
    </template>

    <template v-else>
      <div v-if="loadingGuides || loadingTypes" class="timeline">
        <div v-for="n in 5" :key="'sk-' + n" class="timeline-item">
          <div class="timeline-marker">
            <div class="timeline-dot skeleton-dot"></div>
            <div v-if="n < 5" class="timeline-line line-blue"></div>
          </div>
          <div class="timeline-content card skeleton-card">
            <div class="skeleton-line skeleton-title"></div>
            <div class="skeleton-line" style="width: 40%"></div>
            <div class="skeleton-line" style="width: 90%"></div>
            <div class="skeleton-line" style="width: 70%"></div>
          </div>
        </div>
      </div>

      <div v-else class="timeline">
        <div v-for="(step, i) in filteredSteps" :key="'guide-' + (step.id || i)" class="timeline-item" :class="{ 'from-report': step._fromReport }">
          <div class="timeline-marker">
            <div class="timeline-dot" :class="'cat-' + catClass(step.cat)"></div>
            <div v-if="i < filteredSteps.length - 1" class="timeline-line" :class="'line-' + catClass(step.cat)"></div>
          </div>
          <div class="timeline-content card" @click="step.open = !step.open">
            <div class="step-header">
              <div class="step-header-left">
                <span class="step-num">STEP {{ String(i + 1).padStart(2, '0') }}</span>
                <span class="step-cat-chip" :class="'cat-' + catClass(step.cat)">{{ step.cat }}</span>
                <span v-if="step._fromReport" class="step-badge report-badge" title="来自员工知识贡献">📝 员工贡献</span>
              </div>
              <h3 class="step-title">{{ step.title }}</h3>
              <span class="step-toggle">{{ step.open ? '▲' : '▼' }}</span>
            </div>
            <transition name="expand">
              <div v-show="step.open" class="step-body">
                <p class="step-desc">{{ step.desc }}</p>
                <div class="step-checklist" v-if="step.checklist && step.checklist.length">
                  <div
                    v-for="(chk, ci) in step.checklist"
                    :key="ci"
                    class="check-item"
                    :class="{ checked: step._done && step._done[ci] }"
                    @click.stop="toggleCheck(step, ci)"
                  >
                    <span class="check-box">{{ step._done && step._done[ci] ? '✓' : '' }}</span>
                    <span class="check-text">{{ chk }}</span>
                  </div>
                </div>
                <div class="step-refs" v-if="step.refs && step.refs.length">
                  <span class="refs-label">相关参考：</span>
                  <span class="ref-tag" v-for="(r, ri) in step.refs" :key="ri">{{ r }}</span>
                </div>
                <div v-if="step.warn" class="step-warn">
                  <span class="warn-icon">⚠</span>
                  <span class="warn-text">{{ step.warn }}</span>
                </div>
                <div class="step-footer" v-if="step.estimate || step._userName">
                  <span class="estimate" v-if="step.estimate">⏱ 预计用时：{{ step.estimate }}</span>
                  <span class="step-contributor" v-if="step._userName">🧑 贡献人：<b>{{ step._userName }}</b> · 入库 {{ formatDate(step._syncTime) }}</span>
                </div>
                <div class="step-review" v-if="step._fromReport && step._remark">
                  <span class="review-label">💡 审核备注：</span>
                  <span class="review-text">{{ step._remark }}</span>
                </div>
              </div>
            </transition>
          </div>
        </div>
      </div>

      <div v-if="!loadingGuides && !loadingTypes && filteredSteps.length === 0" class="empty-state">
        <div class="empty-icon">⇢</div>
        <p>未找到匹配的作业步骤</p>
      </div>
    </template>
  </div>
</template>

<script>
import { listGuidesApi, listGuideTypesApi, listReportsApi } from '../utils/api'

export default {
  name: 'Guide',
  data() {
    return {
      currentCat: '全部',
      currentSource: 'all',
      searchQuery: '',
      categories: ['全部'],
      allGuides: [],
      myReports: [],
      loadingGuides: true,
      loadingTypes: true,
      loadingReports: true
    }
  },
  async created() {
    try {
      const [guidesRes, typesRes, reportsRes] = await Promise.all([
        listGuidesApi({ page: 1, size: 20000, source: 'all' }).catch(e => ({ data: { list: [] } })),
        listGuideTypesApi().catch(e => ({ data: [] })),
        listReportsApi({ page: 1, size: 20000, scope: 'mine' }).catch(e => ({ data: { list: [] } }))
      ])

      const rawGuides = (guidesRes && guidesRes.data && guidesRes.data.list) || []
      const rawTypes = (typesRes && typesRes.data) || []
      const rawReports = (reportsRes && reportsRes.data && reportsRes.data.list) || []

      this.allGuides = rawGuides.map(g => this._convertGuide(g))
      this.myReports = rawReports.map(r => Object.assign({}, r, { _open: false }))
      this.categories = ['全部'].concat(rawTypes.filter(t => t && t.trim()))
    } catch (err) {
      console.error('加载作业指导数据失败:', err)
      this.allGuides = []
      this.myReports = []
    } finally {
      this.loadingGuides = false
      this.loadingTypes = false
      this.loadingReports = false
    }
  },
  computed: {
    employeeGuideCount() {
      return this.allGuides.filter(g => g._fromReport).length
    },
    officialGuides() {
      return this.allGuides.filter(g => !g._fromReport)
    },
    employeeGuides() {
      return this.allGuides.filter(g => g._fromReport)
    },
    sourceTabs() {
      return [
        { key: 'all',      label: '全部规程',    icon: '⇢',  count: this.allGuides.length },
        { key: 'official', label: '官方知识库', icon: '📖', count: this.officialGuides.length },
        { key: 'employee', label: '员工贡献',   icon: '📝', count: this.employeeGuides.length },
        { key: 'mine',     label: '我的贡献',   icon: '👤', count: this.myReports.length }
      ]
    },
    sourceGuides() {
      switch (this.currentSource) {
        case 'official':
          return this.officialGuides
        case 'employee':
          return this.employeeGuides
        case 'all':
        default:
          return this.allGuides
      }
    },
    filteredSteps() {
      let list = this.sourceGuides
      if (this.currentCat !== '全部') {
        list = list.filter(s => s.cat === this.currentCat)
      }
      const q = this.searchQuery.trim().toLowerCase()
      if (q) {
        list = list.filter(s => {
          if ((s.title || '').toLowerCase().includes(q)) return true
          if ((s.desc || '').toLowerCase().includes(q)) return true
          if ((s.warn || '').toLowerCase().includes(q)) return true
          if ((s.checklist || []).some(x => (x || '').toLowerCase().includes(q))) return true
          if ((s.refs || []).some(x => (x || '').toLowerCase().includes(q))) return true
          return false
        })
      }
      return list
    },
    summaryStats() {
      const colorMap = {
        '机械': 'var(--primary)',
        '电气': 'var(--accent-green)',
        '安全': 'var(--accent-orange)',
        '液压': '#a855f7',
        '仪表': '#22d3ee'
      }
      const baseList = this.sourceGuides
      const total = baseList.length || 1
      const realCats = this.categories.filter(c => c !== '全部')
      if (realCats.length === 0) {
        return Object.keys(colorMap).map(name => ({
          name,
          count: baseList.filter(s => s.cat === name).length,
          percent: Math.round(baseList.filter(s => s.cat === name).length / total * 100),
          color: colorMap[name]
        }))
      }
      return realCats.map(name => ({
        name,
        count: this.categoryCountForStats(name, baseList),
        percent: Math.round(this.categoryCountForStats(name, baseList) / total * 100),
        color: colorMap[name] || 'var(--primary)'
      }))
    }
  },
  methods: {
    _convertGuide(g) {
      const cat = g.device_type || '机械'
      const steps = g.steps || []
      const firstTwoSteps = steps.slice(0, 2).map(s => (s.content || '')).filter(x => x).join('；')
      const desc = (g.tag ? g.tag + ' · ' : '') + '适用设备: ' + cat + (firstTwoSteps ? ' · ' + firstTwoSteps : '')
      const checklist = steps.map(s => s.content || '').filter(x => x).slice(0, 8)
      return {
        id: g.id,
        cat,
        catClass: this.catClass(cat),
        title: g.title || '未命名作业指导',
        desc,
        checklist,
        warn: g.risk_note || '',
        estimate: g.duration_min ? g.duration_min + ' 分钟' : '—',
        refs: g.tag ? [g.tag] : [],
        _fromReport: !!g.is_employee_contribution,
        _userName: g.contributor_name || '',
        _syncTime: (g.created_at_ts || 0) * 1000,
        open: false
      }
    },
    catClass(cat) {
      return ({ '机械': 'blue', '电气': 'green', '安全': 'orange', '液压': 'purple', '仪表': 'cyan' })[cat] || 'blue'
    },
    categoryCount(cat) {
      if (cat === '全部') return this.filteredSteps.length
      return this.filteredSteps.filter(s => s.cat === cat).length
    },
    categoryCountForStats(cat, list) {
      return list.filter(s => s.cat === cat).length
    },
    toggleCheck(step, idx) {
      if (!step._done) this.$set(step, '_done', {})
      this.$set(step._done, idx, !step._done[idx])
    },
    formatDate(ts) {
      if (!ts) return '—'
      const d = new Date(ts)
      return d.toLocaleDateString('zh-CN')
    },
    statusText(s) {
      const map = {
        pending: '待审核',
        reviewing: '审核中',
        approved: '已采纳',
        rejected: '已拒绝',
        synced_guide: '已入库指导',
        synced_case: '已入库案例'
      }
      return map[s] || (s || '未知')
    }
  }
}
</script>

<style scoped>
.page-header {
  margin-bottom: 28px;
}

.page-title {
  font-size: 1.75rem;
  margin-bottom: 8px;
}

.page-desc {
  color: var(--text-secondary);
}

.source-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}
.source-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-secondary);
  transition: all 0.2s ease;
}
.source-tab:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}
.source-tab.active {
  background: var(--primary-subtle);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: 0 0 0 1px rgba(0,212,255,0.25);
  font-weight: 600;
}
.st-icon { font-size: 1rem; }
.st-count {
  padding: 2px 8px;
  background: rgba(255,255,255,0.06);
  border-radius: 999px;
  font-size: 0.6875rem;
  font-family: 'JetBrains Mono', monospace;
  color: var(--text-muted);
  font-weight: 600;
}
.source-tab.active .st-count {
  background: var(--primary);
  color: #04141f;
}

.guide-toolbar {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 24px;
}

.search-bar {
  position: relative;
}

.search-icon {
  position: absolute;
  left: 14px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--text-muted);
  font-size: 1.125rem;
  pointer-events: none;
}

.search-bar .input {
  padding-left: 40px;
}

.filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tab {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}

.filter-tab:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.filter-tab.active {
  background: var(--primary-subtle);
  border-color: var(--border-active);
  color: var(--primary);
}

.cat-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--text-muted);
}
.cat-dot.cat-blue { background: var(--primary); box-shadow: 0 0 6px var(--primary); }
.cat-dot.cat-green { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
.cat-dot.cat-orange { background: var(--accent-orange); box-shadow: 0 0 6px var(--accent-orange); }
.cat-dot.cat-purple { background: #a855f7; box-shadow: 0 0 6px #a855f7; }
.cat-dot.cat-cyan { background: #22d3ee; box-shadow: 0 0 6px #22d3ee; }

.cat-count {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6875rem;
  padding: 1px 6px;
  border-radius: 999px;
  background: rgba(255,255,255,0.05);
}

.progress-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 14px;
  margin-bottom: 28px;
  padding: 18px 20px;
}

.progress-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.progress-name {
  font-size: 0.75rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.progress-bar-wrap {
  width: 100%;
  height: 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 999px;
  overflow: hidden;
}

.progress-bar {
  height: 100%;
  border-radius: 999px;
  transition: width 0.5s var(--ease);
}

.progress-count {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 20px;
}

.timeline-item.from-report .timeline-content {
  border-left: 3px solid #ffa502;
  background: linear-gradient(90deg, rgba(255,165,2,0.05), transparent 60%);
}

.timeline-marker {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 24px;
  flex-shrink: 0;
}

.timeline-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--primary);
  box-shadow: 0 0 8px var(--primary-glow);
  flex-shrink: 0;
  margin-top: 20px;
}
.timeline-dot.cat-blue { background: var(--primary); box-shadow: 0 0 8px var(--primary-glow); }
.timeline-dot.cat-green { background: var(--accent-green); box-shadow: 0 0 8px rgba(0, 255, 136, 0.4); }
.timeline-dot.cat-orange { background: var(--accent-orange); box-shadow: 0 0 8px rgba(255, 107, 53, 0.4); }
.timeline-dot.cat-purple { background: #a855f7; box-shadow: 0 0 8px rgba(168, 85, 247, 0.4); }
.timeline-dot.cat-cyan { background: #22d3ee; box-shadow: 0 0 8px rgba(34, 211, 238, 0.4); }
.skeleton-dot { background: var(--border-subtle); box-shadow: none; animation: pulse 1.5s ease-in-out infinite; }

.timeline-line {
  width: 2px;
  flex: 1;
  background: var(--border-subtle);
  margin: 4px 0;
}
.timeline-line.line-blue { background: rgba(0,212,255,0.25); }
.timeline-line.line-green { background: rgba(0,255,136,0.25); }
.timeline-line.line-orange { background: rgba(255,107,53,0.25); }
.timeline-line.line-purple { background: rgba(168,85,247,0.25); }
.timeline-line.line-cyan { background: rgba(34,211,238,0.25); }

.timeline-content {
  flex: 1;
  margin-bottom: 16px;
  cursor: pointer;
}

.step-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-header-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.step-num {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6875rem;
  font-weight: 600;
  letter-spacing: 1px;
  color: var(--primary);
  background: var(--primary-subtle);
  padding: 2px 8px;
  border-radius: 2px;
  flex-shrink: 0;
}

.step-cat-chip {
  font-size: 0.625rem;
  padding: 2px 8px;
  border-radius: 999px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.step-cat-chip.cat-blue   { color: var(--primary); background: var(--primary-subtle); }
.step-cat-chip.cat-green  { color: var(--accent-green); background: rgba(0, 255, 136, 0.1); }
.step-cat-chip.cat-orange { color: var(--accent-orange); background: rgba(255, 107, 53, 0.1); }
.step-cat-chip.cat-purple { color: #a855f7; background: rgba(168, 85, 247, 0.1); }
.step-cat-chip.cat-cyan   { color: #22d3ee; background: rgba(34, 211, 238, 0.1); }

.step-badge {
  font-size: 0.6875rem;
  padding: 2px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.report-badge {
  background: linear-gradient(135deg, #ffa502, #ff7a00);
  color: #fff;
}

.step-title {
  flex: 1;
  font-size: 1rem;
  font-weight: 600;
}

.step-toggle {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.step-body {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border-subtle);
}

.step-desc {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 14px;
}

.step-checklist {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 14px;
}

.check-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 6px 8px;
  border-radius: var(--radius);
  transition: background var(--duration) var(--ease);
  cursor: pointer;
}

.check-item:hover {
  background: var(--primary-subtle);
}

.check-item.checked .check-box {
  background: var(--primary);
  border-color: var(--primary);
  color: var(--bg-deep);
}

.check-item.checked .check-text {
  color: var(--text-muted);
  text-decoration: line-through;
}

.check-box {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  border-radius: 3px;
  border: 1px solid var(--border-hover);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
  margin-top: 2px;
  color: transparent;
  transition: all var(--duration) var(--ease);
}

.check-text {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

.step-refs {
  margin-bottom: 12px;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}

.refs-label {
  color: var(--text-muted);
}

.ref-tag {
  padding: 2px 8px;
  border-radius: 2px;
  background: rgba(255,255,255,0.04);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.6875rem;
}

.step-warn {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(255, 107, 53, 0.08);
  border: 1px solid rgba(255, 107, 53, 0.2);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  color: var(--accent-orange);
}

.warn-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.warn-text {
  line-height: 1.6;
}

.step-footer {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-subtle);
  display: flex;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  align-items: center;
}

.estimate {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.step-contributor {
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.step-contributor b {
  color: #ffa502;
  font-weight: 600;
}

.step-review {
  margin-top: 10px;
  padding: 10px 14px;
  background: rgba(0,255,136,0.06);
  border: 1px solid rgba(0,255,136,0.25);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  line-height: 1.6;
}
.review-label {
  color: var(--accent-green);
  font-weight: 600;
}
.review-text {
  color: var(--text-primary);
}

.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s var(--ease);
  overflow: hidden;
}
.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-6px);
}

.empty-state {
  text-align: center;
  padding: 80px 0;
}
.empty-icon {
  font-size: 3rem;
  color: var(--primary);
  opacity: 0.4;
  margin-bottom: 12px;
}
.empty-state p {
  font-size: 0.9375rem;
  color: var(--text-muted);
}
.empty-sub {
  margin-top: 4px;
  font-size: 0.8125rem !important;
  opacity: 0.8;
}

/* Skeleton styles */
.skeleton-card {
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, var(--border-subtle) 25%, rgba(255,255,255,0.08) 50%, var(--border-subtle) 75%);
  background-size: 200% 100%;
  border-radius: 4px;
  animation: shimmer 1.4s infinite;
  width: 100%;
}
.skeleton-title {
  height: 20px;
  width: 60%;
  margin-bottom: 4px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
@keyframes pulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* Mine reports grid */
.case-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.skeleton-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}
.case-card {
  display: flex;
  flex-direction: column;
  cursor: pointer;
  position: relative;
  overflow: hidden;
}
.case-card.expanded {
  grid-column: span 3;
  border-color: var(--border-active);
  box-shadow: var(--shadow-glow);
}
.case-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.case-tag {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.625rem;
  font-weight: 600;
  letter-spacing: 1px;
  padding: 2px 8px;
  border-radius: 2px;
  text-transform: uppercase;
}
.case-tag.blue { color: var(--primary); background: var(--primary-subtle); }
.case-tag.green { color: var(--accent-green); background: rgba(0, 255, 136, 0.1); }
.case-tag.orange { color: var(--accent-orange); background: rgba(255, 107, 53, 0.1); }
.case-tag.purple { color: #a855f7; background: rgba(168, 85, 247, 0.1); }
.case-tag.cyan { color: #22d3ee; background: rgba(34, 211, 238, 0.1); }

.status-badge {
  font-size: 0.6875rem;
  padding: 3px 10px;
  border-radius: 999px;
  font-weight: 600;
}
.status-pending { background: rgba(255,193,7,0.12); color: #ffc107; }
.status-reviewing { background: rgba(0,212,255,0.12); color: var(--primary); }
.status-approved, .status-synced_guide, .status-synced_case { background: rgba(0,255,136,0.12); color: var(--accent-green); }
.status-rejected { background: rgba(255,107,107,0.12); color: #ff6b6b; }

.case-title {
  font-size: 0.9375rem;
  font-weight: 600;
  margin-bottom: 8px;
  line-height: 1.4;
}
.case-summary {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.6;
  flex: 1;
  margin-bottom: 14px;
}
.case-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  padding-top: 12px;
  border-top: 1px solid var(--border-subtle);
}
.meta-item {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.case-contributor {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
  font-size: 0.75rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.contrib-icon { opacity: 0.8; }

/* Case detail expand */
.case-detail {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px dashed var(--border-subtle);
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}
.case-detail .detail-section.tips {
  grid-column: span 2;
}
.detail-label {
  font-size: 0.6875rem;
  font-weight: 600;
  color: var(--primary);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 8px;
  font-family: 'JetBrains Mono', monospace;
}
.detail-text {
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.7;
}
.solution-text {
  color: var(--text-primary);
  line-height: 1.7;
}
.expand-arrow {
  grid-column: span 2;
  text-align: center;
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 8px;
}
.toggle-hint {
  position: absolute;
  bottom: 8px;
  right: 12px;
  font-size: 0.6875rem;
  color: var(--text-muted);
  opacity: 0;
  transition: opacity var(--duration) var(--ease);
}
.case-card:hover .toggle-hint {
  opacity: 1;
}

@media (max-width: 1000px) {
  .progress-summary {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  .case-grid, .skeleton-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 600px) {
  .progress-summary {
    grid-template-columns: 1fr;
  }
  .case-grid, .skeleton-grid {
    grid-template-columns: 1fr;
  }
  .case-card.expanded {
    grid-column: span 1;
  }
  .case-detail {
    grid-template-columns: 1fr;
  }
  .case-detail .detail-section.tips {
    grid-column: span 1;
  }
  .expand-arrow {
    grid-column: span 1;
  }
}
</style>
