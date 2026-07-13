<template>
  <div class="container">
    <header class="page-header">
      <h1 class="page-title">案例库</h1>
      <p class="page-desc">历史故障案例检索与参考 · 共 {{ totalCaseCount }} 条案例 · 员工知识贡献 {{ employeeCaseCount }} 条</p>
    </header>

    <!-- 来源筛选 Tab -->
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

    <!-- 搜索 + 筛选 -->
    <div class="search-toolbar">
      <div class="search-bar">
        <span class="search-icon">⌕</span>
        <input v-model="searchQuery" class="input" placeholder="搜索案例标题、设备类型、故障类型..." />
      </div>
      <div class="filter-tags">
        <template v-if="tagsLoading">
          <div class="skeleton-wrap inline">
            <span v-for="i in 5" :key="i" class="skeleton-tag"></span>
          </div>
        </template>
        <template v-else>
          <button
            v-for="t in tagList"
            :key="t"
            class="filter-tag"
            :class="{ active: currentTag === t }"
            @click="currentTag = t"
          >{{ t }}</button>
        </template>
      </div>
    </div>

    <!-- 我的贡献：报告列表 -->
    <template v-if="currentSource === 'mine'">
      <div v-if="mineLoading" class="case-grid">
        <div v-for="i in 6" :key="i" class="case-card card skeleton-card">
          <div class="skeleton-block" style="height:14px;width:50%;margin-bottom:14px;"></div>
          <div class="skeleton-block" style="height:18px;width:85%;margin-bottom:12px;"></div>
          <div class="skeleton-block" style="height:12px;width:100%;margin-bottom:8px;"></div>
          <div class="skeleton-block" style="height:12px;width:70%;margin-bottom:16px;"></div>
          <div class="skeleton-block" style="height:12px;width:40%;"></div>
        </div>
      </div>
      <template v-else>
        <div class="case-grid">
          <div
            v-for="(r, i) in filteredMyReports"
            :key="'mine-' + (r.id || i)"
            class="case-card card mine-card"
          >
            <div class="mine-top">
              <span class="mine-type-chip" :class="'type-' + (r.type || 'case')">
                {{ (r.type === 'guide') ? '作业指导' : '故障案例' }}
              </span>
              <span class="mine-status-badge" :class="'status-' + (r.status || 'pending')">
                {{ statusLabel(r.status) }}
              </span>
            </div>
            <h3 class="case-title">{{ r.title || '（未填写标题）' }}</h3>
            <div class="mine-meta">
              <span class="meta-item">◈ {{ r.device || '通用设备' }}</span>
              <span class="meta-item">📅 {{ formatDate((r.submit_time_ts || r.created_at_ts) * 1000) }}</span>
            </div>
            <p class="case-summary mine-summary">{{ (r.problem || r.summary || '暂无描述').slice(0, 120) }}{{ ((r.problem || r.summary || '').length > 120) ? '...' : '' }}</p>
            <div class="mine-review" v-if="r.review_remark">
              <span class="review-label">审核备注：</span>
              <span class="review-text">{{ r.review_remark }}</span>
            </div>
          </div>
        </div>
        <div v-if="filteredMyReports.length === 0 && !_hydrating" class="empty-state">
          <div class="empty-icon">▣</div>
          <p>暂无提交的知识报告</p>
          <p class="empty-sub">在工单完成后可提交知识贡献，积累团队知识库</p>
        </div>
      </template>
    </template>

    <!-- 案例网格 -->
    <template v-else>
      <div v-if="casesLoading" class="case-grid">
        <div v-for="i in 6" :key="i" class="case-card card skeleton-card">
          <div class="case-top">
            <div class="skeleton-block" style="height:18px;width:50px;"></div>
            <div class="skeleton-block" style="height:12px;width:70px;"></div>
          </div>
          <div class="skeleton-block" style="height:18px;width:85%;margin:12px 0 8px;"></div>
          <div class="skeleton-block" style="height:12px;width:100%;margin-bottom:4px;"></div>
          <div class="skeleton-block" style="height:12px;width:100%;margin-bottom:4px;"></div>
          <div class="skeleton-block" style="height:12px;width:70%;margin-bottom:14px;"></div>
          <div class="case-meta">
            <div class="skeleton-block" style="height:12px;width:60px;"></div>
            <div class="skeleton-block" style="height:12px;width:70px;"></div>
            <div class="skeleton-block" style="height:12px;width:50px;"></div>
          </div>
        </div>
      </div>
      <template v-else>
        <div class="case-grid">
          <div
            v-for="(c, i) in filteredCases"
            :key="'case-' + (c.id || i)"
            class="case-card card"
            :class="{ expanded: c._open, 'from-report': c._fromReport }"
            @click="toggleCase(c)"
          >
            <div v-if="c._fromReport" class="case-badge report-badge" title="来自员工知识贡献">
              📝 员工贡献
            </div>
            <div class="case-top">
              <span class="case-tag" :class="c.tagClass">{{ c.tag }}</span>
              <span class="case-date">{{ c.date }}</span>
            </div>
            <h3 class="case-title">{{ c.title }}</h3>
            <p class="case-summary">{{ c.summary }}</p>
            <div class="case-meta">
              <span class="meta-item">◈ {{ c.device }}</span>
              <span class="meta-item">◎ {{ c.fault }}</span>
              <span class="meta-item severity" :class="'sev-' + c.severity">
                ⚠ {{ severityText(c.severity) }}
              </span>
            </div>
            <div v-if="c._fromReport" class="case-contributor">
              <span class="contrib-icon">🧑</span>
              <span>贡献人：<b>{{ c._userName }}</b></span>
              <span class="contrib-time">· 入库 {{ formatDate(c._syncTime) }}</span>
            </div>

            <!-- 展开详情 -->
            <transition name="expand">
              <div v-show="c._open" class="case-detail">
                <div class="detail-section">
                  <div class="detail-label">故障现象</div>
                  <p class="detail-text">{{ c.symptomText || '暂无详细描述' }}</p>
                </div>
                <div class="detail-section" v-if="c.cause">
                  <div class="detail-label">根因分析</div>
                  <p class="detail-text">{{ c.cause }}</p>
                </div>
                <div class="detail-section">
                  <div class="detail-label">处置方案</div>
                  <p class="detail-text solution-text">{{ c.solution || '暂无处置方案描述' }}</p>
                </div>
                <div class="detail-section tips" v-if="c.tipsText">
                  <div class="detail-label">经验与建议</div>
                  <p class="detail-text">{{ c.tipsText }}</p>
                </div>
                <div class="expand-arrow">▲ 收起</div>
              </div>
            </transition>

            <div class="toggle-hint" v-if="!c._open">点击查看详情 ▼</div>
          </div>
        </div>
        <div v-if="filteredCases.length === 0 && !_hydrating" class="empty-state">
          <div class="empty-icon">▣</div>
          <p>未找到匹配的案例</p>
          <p class="empty-sub">尝试更换搜索关键词或选择其他分类</p>
        </div>
      </template>
    </template>
  </div>
</template>

<script>
import { listCasesApi, listCaseTagsApi, listReportsApi } from '../utils/api'

const TAG_CLASS_MAP = {
  '机械': 'blue',
  '电气': 'green',
  '液压': 'purple',
  '仪表': 'cyan',
  '安全': 'orange'
}

const LEVEL_MAP = {
  'high': 'high',
  'mid': 'medium',
  'low': 'low'
}

const STATUS_LABEL = {
  pending: '待审核',
  approved: '审核通过',
  rejected: '已驳回',
  synced_case: '已入库案例',
  synced_guide: '已入库指南'
}

function _formatDate(ts) {
  if (!ts) return '—'
  const d = new Date(Number(ts))
  if (isNaN(d.getTime())) return '—'
  const y = d.getFullYear()
  const m = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${y}-${m}-${day}`
}

function _firstParagraph(text) {
  if (!text) return ''
  const t = String(text).trim()
  const idx = t.search(/[\n。；;]/)
  if (idx < 0) return t
  return t.slice(0, idx + 1)
}

function _mapCase(raw) {
  if (!raw) return null
  const cause = raw.cause || ''
  const summary = raw.summary || ''
  const problem = cause || _firstParagraph(summary)
  const tag = raw.tag || '机械'
  const level = raw.level || 'mid'
  const createdTs = Number(raw.created_at_ts) || 0
  const symptomParts = []
  if (raw.fault) symptomParts.push(String(raw.fault).trim())
  if (summary) symptomParts.push(String(summary).trim())
  const symptomText = symptomParts.filter(Boolean).join('。')
  return {
    id: raw.id,
    title: raw.title || '（未命名案例）',
    device: raw.device || '通用设备',
    tag: tag,
    tagClass: TAG_CLASS_MAP[tag] || 'blue',
    fault: raw.fault || '现场故障',
    cause: cause,
    solution: raw.solution || '',
    summary: summary,
    level: level,
    severity: LEVEL_MAP[level] || 'medium',
    date: _formatDate(createdTs * 1000),
    contributor_name: raw.contributor_name || '',
    is_employee_contribution: !!raw.is_employee_contribution,
    created_at_ts: createdTs,
    _fromReport: !!raw.is_employee_contribution,
    _userName: raw.contributor_name || '匿名用户',
    _syncTime: createdTs * 1000,
    problem: problem,
    symptomText: symptomText,
    tipsText: raw.tips || '',
    _open: false
  }
}

export default {
  name: 'Case',
  data() {
    return {
      _hydrating: true,
      searchQuery: '',
      currentTag: '全部',
      currentSource: 'all',
      tagList: ['全部'],
      allCases: [],
      myReports: [],
      casesLoading: false,
      tagsLoading: false,
      mineLoading: false
    }
  },
  async created() {
    this._hydrating = true
    try {
      await Promise.all([
        this.loadAllCases(),
        this.loadAllTags(),
        this.loadMyReports()
      ])
    } finally {
      this._hydrating = false
    }
  },
  computed: {
    totalCaseCount() {
      return this.allCases.length
    },
    employeeCaseCount() {
      return this.allCases.filter(c => c._fromReport).length
    },
    officialCases() {
      return this.allCases.filter(c => !c._fromReport)
    },
    employeeCases() {
      return this.allCases.filter(c => c._fromReport)
    },
    sourceTabs() {
      return [
        { key: 'all',      label: '全部案例',   icon: '▣',  count: this.allCases.length },
        { key: 'official', label: '官方知识库', icon: '📚', count: this.officialCases.length },
        { key: 'employee', label: '员工贡献',   icon: '📝', count: this.employeeCases.length },
        { key: 'mine',     label: '我的贡献',   icon: '👤', count: this.myReports.length }
      ]
    },
    sourceCases() {
      switch (this.currentSource) {
        case 'official':
          return this.officialCases
        case 'employee':
          return this.employeeCases
        case 'all':
        default:
          return this.allCases
      }
    },
    filteredCases() {
      let list = this.sourceCases
      if (this.currentTag !== '全部') {
        list = list.filter(c => c.tag === this.currentTag)
      }
      const q = this.searchQuery.trim().toLowerCase()
      if (q) {
        list = list.filter(c =>
          (c.title || '').toLowerCase().includes(q) ||
          (c.device || '').toLowerCase().includes(q) ||
          (c.fault || '').toLowerCase().includes(q) ||
          (c.summary || '').toLowerCase().includes(q) ||
          (c.problem || '').toLowerCase().includes(q) ||
          (c.solution || '').toLowerCase().includes(q) ||
          (c.cause || '').toLowerCase().includes(q)
        )
      }
      return list
    },
    filteredMyReports() {
      let list = this.myReports
      const q = this.searchQuery.trim().toLowerCase()
      if (q) {
        list = list.filter(r =>
          (r.title || '').toLowerCase().includes(q) ||
          (r.device || '').toLowerCase().includes(q) ||
          (r.problem || '').toLowerCase().includes(q) ||
          (r.fault_type || '').toLowerCase().includes(q) ||
          (r.summary || '').toLowerCase().includes(q)
        )
      }
      return list
    }
  },
  methods: {
    async loadAllCases(force = false) {
      this.casesLoading = true
      try {
        const p = await listCasesApi({ page: 1, size: 20000, source: 'all' }) || {}
        const items = p.items || []
        this.allCases = items.map(r => _mapCase(r)).filter(Boolean)
      } catch (e) {
        if (force || this.allCases.length === 0) {
          console.error('案例加载失败:', e)
        }
      } finally {
        this.casesLoading = false
      }
    },
    async loadAllTags(force = false) {
      this.tagsLoading = true
      try {
        const realTags = await listCaseTagsApi() || []
        const arr = Array.isArray(realTags) ? realTags : (realTags.items || [])
        const cleanTags = arr.map(t => (typeof t === 'string' ? t : (t.name || t.label || t.tag || ''))).filter(Boolean)
        this.tagList = ['全部', ...cleanTags]
      } catch (e) {
        if (force || this.tagList.length <= 1) {
          this.tagList = ['全部', '机械', '电气', '液压', '仪表', '安全']
        }
      } finally {
        this.tagsLoading = false
      }
    },
    async loadMyReports(force = false) {
      this.mineLoading = true
      try {
        const p = await listReportsApi({ page: 1, size: 20000, scope: 'mine' }) || {}
        this.myReports = p.items || []
      } catch (e) {
        if (force || this.myReports.length === 0) {
          console.error('我的报告加载失败:', e)
        }
      } finally {
        this.mineLoading = false
      }
    },
    toggleCase(c) {
      this.$set(c, '_open', !c._open)
    },
    severityText(s) {
      return ({ low: '一般', medium: '较重', high: '严重' })[s] || '一般'
    },
    formatDate(ts) {
      return _formatDate(ts)
    },
    statusLabel(s) {
      return STATUS_LABEL[s] || (s || '未知')
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

/* 来源 Tab */
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

/* 工具栏 */
.search-toolbar {
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

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-tag {
  padding: 5px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 0.8125rem;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}

.filter-tag:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

.filter-tag.active {
  background: var(--primary-subtle);
  border-color: var(--border-active);
  color: var(--primary);
}

/* 案例网格 */
.case-grid {
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

.case-card.mine-card {
  cursor: default;
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

.case-date {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

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

.meta-item.severity.sev-high { color: var(--accent-red); }
.meta-item.severity.sev-medium { color: var(--accent-orange); }
.meta-item.severity.sev-low { color: var(--accent-green); }

/* 详情展开 */
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
  white-space: pre-wrap;
}

.detail-list {
  padding-left: 20px;
  font-size: 0.875rem;
  color: var(--text-secondary);
  line-height: 1.8;
}

.detail-list.bullet {
  list-style: none;
  padding-left: 0;
}

.detail-list.bullet li::before {
  content: '›';
  color: var(--primary);
  margin-right: 8px;
  font-weight: 700;
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

.expand-enter-active,
.expand-leave-active {
  transition: all 0.25s var(--ease);
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 80px 0;
  color: var(--text-muted);
}

.empty-icon {
  font-size: 3rem;
  color: var(--primary);
  opacity: 0.4;
  margin-bottom: 12px;
}

.empty-state p {
  font-size: 0.9375rem;
  color: var(--text-secondary);
}

.empty-sub {
  margin-top: 4px;
  font-size: 0.8125rem !important;
  color: var(--text-muted) !important;
}

/* 来自知识报告的卡片样式 */
.case-card {
  position: relative;
  overflow: hidden;
}
.case-card.from-report {
  border-left: 3px solid var(--accent-amber, #ffa502);
  background: linear-gradient(180deg, rgba(255,165,2,0.04), transparent 40%);
}
.case-badge {
  position: absolute;
  top: 0;
  right: 0;
  padding: 4px 12px;
  font-size: 0.6875rem;
  font-weight: 600;
  border-bottom-left-radius: var(--radius);
}
.report-badge {
  background: linear-gradient(135deg, var(--accent-amber), #ff7a00);
  color: #fff;
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
.case-contributor b {
  color: var(--accent-amber);
  font-weight: 600;
}
.contrib-icon { opacity: 0.8; }
.contrib-time { opacity: 0.75; }

.solution-text {
  color: var(--text-primary);
  line-height: 1.7;
}

/* 我的贡献卡片 */
.mine-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
}
.mine-type-chip {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.625rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 999px;
  letter-spacing: 0.5px;
}
.mine-type-chip.type-case {
  color: var(--primary);
  background: var(--primary-subtle);
}
.mine-type-chip.type-guide {
  color: var(--accent-green);
  background: rgba(0, 255, 136, 0.1);
}
.mine-status-badge {
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 4px;
}
.mine-status-badge.status-pending {
  color: #eab308;
  background: rgba(234, 179, 8, 0.12);
}
.mine-status-badge.status-approved {
  color: var(--accent-green);
  background: rgba(0, 255, 136, 0.1);
}
.mine-status-badge.status-rejected {
  color: var(--accent-red);
  background: rgba(239, 68, 68, 0.1);
}
.mine-status-badge.status-synced_case,
.mine-status-badge.status-synced_guide {
  color: var(--primary);
  background: var(--primary-subtle);
}
.mine-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 16px;
  margin-bottom: 10px;
}
.mine-summary {
  margin-bottom: 10px;
}
.mine-review {
  margin-top: 8px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
  font-size: 0.75rem;
  line-height: 1.6;
}
.review-label {
  color: var(--accent-orange);
  font-weight: 600;
}
.review-text {
  color: var(--text-secondary);
}

/* 骨架屏 */
.skeleton-wrap {
  display: flex;
  flex-direction: column;
  gap: 18px;
  width: 100%;
}
.skeleton-wrap.inline {
  flex-direction: row;
  flex-wrap: wrap;
  gap: 8px;
}
.skeleton-tag {
  display: block;
  height: 30px;
  width: 70px;
  border-radius: 999px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(0,212,255,0.10) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
.skeleton-card {
  cursor: default;
  pointer-events: none;
}
.skeleton-block {
  display: block;
  border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(0,212,255,0.10) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
@keyframes skeleton-shine {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
