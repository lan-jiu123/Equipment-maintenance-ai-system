<template>
  <div class="container">
    <header class="page-header">
      <div class="page-header-left">
        <h1 class="page-title">作业指导</h1>
        <p class="page-desc">标准操作流程与安全规范 · 共 {{ filteredSteps.length }} 项作业规程 · 员工贡献 {{ employeeGuideCount }} 项</p>
      </div>
      <div class="header-actions">
        <button class="btn btn-primary" @click="openContributeGuide">
          <span class="btn-icon">+</span> 贡献指导
        </button>
      </div>
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
      <div class="level-filter">
        <select v-model="currentLevel" class="level-select">
          <option v-for="l in maintenanceLevels" :key="l.key" :value="l.key">{{ l.label }}</option>
        </select>
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

    <!-- 贡献表单弹窗（始终渲染，不受 Tab 影响） -->
    <transition name="fade">
      <div v-if="showContributeForm" class="modal-overlay" @click.self="closeContributeGuide">
        <div class="modal-dialog guide-form-dialog">
          <div class="modal-header">
            <h3>贡献作业指导</h3>
            <button class="modal-close" @click="closeContributeGuide">&times;</button>
          </div>
          <div class="modal-body">
            <div class="form-row">
              <label>标题 <span class="required">*</span></label>
              <input v-model="guideForm.title" class="form-input" placeholder="如：滚动轴承更换" />
            </div>
            <div class="form-row form-row-2">
              <div>
                <label>分类 <span class="required">*</span></label>
                <select v-model="guideForm.device_type" class="form-input">
                  <option value="机械">机械</option>
                  <option value="电气">电气</option>
                  <option value="液压">液压</option>
                  <option value="仪表">仪表</option>
                  <option value="安全">安全</option>
                </select>
              </div>
              <div>
                <label>难度</label>
                <div class="star-picker">
                  <span v-for="n in 5" :key="n" class="star" :class="{ active: n <= guideForm.difficulty }" @click="guideForm.difficulty = n">★</span>
                </div>
              </div>
            </div>
            <div class="form-row form-row-2">
              <div>
                <label>预计耗时（分钟）</label>
                <input v-model.number="guideForm.duration_min" type="number" min="5" class="form-input" placeholder="45" />
              </div>
              <div>
                <label>适用设备</label>
                <input v-model="guideForm.applicable_devices" class="form-input" placeholder="如：数控车床、离心泵" />
              </div>
            </div>
            <div class="form-row">
              <label>所需工具</label>
              <div class="tag-input-wrap">
                <span v-for="(t, ti) in guideForm.tools" :key="ti" class="tag tool-tag">
                  {{ t }}<span class="tag-remove" @click="guideForm.tools.splice(ti, 1)">&times;</span>
                </span>
                <input v-model="toolInput" class="tag-input" placeholder="输入工具名按回车添加" @keydown.enter.prevent="addTool" />
              </div>
            </div>
            <div class="form-row">
              <label>操作步骤 <span class="form-hint">建议 5 条以上</span></label>
              <div v-for="(s, si) in guideForm.steps" :key="si" class="step-input-row">
                <span class="step-num">{{ si + 1 }}</span>
                <input v-model="s.content" class="form-input" placeholder="步骤内容" />
                <input v-model="s.tip" class="form-input step-tip" placeholder="提示（可选）" />
                <button class="step-remove" @click="guideForm.steps.splice(si, 1)">&times;</button>
              </div>
              <button class="btn btn-outline btn-sm" @click="guideForm.steps.push({ content: '', tip: '' })">+ 添加步骤</button>
            </div>
            <div class="form-row">
              <label>注意事项</label>
              <textarea v-model="guideForm.risk_note" class="form-input" rows="3" placeholder="安全提示、风险注意事项"></textarea>
            </div>
            <div class="form-error" v-if="guideFormError">{{ guideFormError }}</div>
          </div>
          <div class="modal-footer">
            <button class="btn btn-outline" @click="closeContributeGuide">取消</button>
            <button class="btn btn-primary" @click="submitGuide" :disabled="guideFormSubmitting">
              {{ guideFormSubmitting ? '提交中...' : '提交审核' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

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
      <!-- 工单上下文推荐横幅 -->
      <div v-if="showGuideBanner" class="guide-banner card">
        <div class="banner-head">
          <span class="banner-icon">📋</span>
          <span class="banner-title">来自工单 #{{ ticketId }} 的推荐</span>
          <span v-if="ticketContext" class="banner-context">{{ ticketContext.device_type }} · {{ { low: '1级', mid: '2级', high: '3级' }[ticketContext.level] || '' }}</span>
          <button class="banner-close" @click="showGuideBanner = false" type="button">✕</button>
        </div>
        <div v-if="guideBannerLoading" class="banner-loading">匹配推荐中...</div>
        <div v-else-if="recommendedGuides.length === 0" class="banner-empty">暂未找到匹配的作业指导</div>
        <div v-else class="banner-list">
          <div
            v-for="(rg, ri) in recommendedGuides"
            :key="'rg-' + ri"
            class="banner-item"
            :class="{ 'banner-exact': rg._matchReason && rg._matchReason.includes('精确') }"
            @click="scrollToGuide(rg.id)"
          >
            <span class="banner-rank">{{ ri + 1 }}</span>
            <div class="banner-info">
              <span class="banner-gtitle">{{ rg.title }}</span>
              <span class="banner-greason">{{ rg._matchReason }}</span>
            </div>
            <span class="banner-glevel" :class="rg.maintenanceLevel">{{ { low: '1级', mid: '2级', high: '3级' }[rg.maintenanceLevel] || '' }}</span>
          </div>
        </div>
      </div>

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
        <div v-for="(step, i) in filteredSteps" :key="'guide-' + (step.id || i)" class="timeline-item" :class="{ 'from-report': step._fromReport }" :data-guide-id="step.id">
          <div class="timeline-marker">
            <div class="timeline-dot" :class="'cat-' + catClass(step.cat)"></div>
            <div v-if="i < filteredSteps.length - 1" class="timeline-line" :class="'line-' + catClass(step.cat)"></div>
          </div>
          <div class="timeline-content card" @click="step.open = !step.open">
            <div class="step-header">
              <div class="step-header-left">
                <span class="step-num">STEP {{ String(i + 1).padStart(2, '0') }}</span>
                <span class="step-cat-chip" :class="'cat-' + catClass(step.cat)">{{ step.cat }}</span>
                <span v-if="step.maintenanceLevel" class="level-badge" :style="{ backgroundColor: getLevelColor(step.maintenanceLevel) }">
                  {{ getLevelLabel(step.maintenanceLevel) }}
                </span>
                <span v-if="step._fromReport" class="step-badge report-badge" title="来自员工知识贡献">📝 员工贡献</span>
              </div>
              <h3 class="step-title">{{ step.title }}</h3>
              <span class="step-toggle">{{ step.open ? '▲' : '▼' }}</span>
            </div>
            <transition name="expand">
              <div v-show="step.open" class="step-body">
                <p class="step-desc">{{ step.desc }}</p>

                <!-- 指导概览：难度 / 耗时 / 适用设备 / 工具 -->
                <div class="guide-meta">
                  <span v-if="step.difficulty" class="meta-item meta-difficulty">
                    <span class="meta-label">难度</span>
                    <span class="meta-value difficulty-stars">{{ '★'.repeat(step.difficulty) }}{{ '☆'.repeat(5 - step.difficulty) }}</span>
                  </span>
                  <span v-if="step.estimate && step.estimate !== '—'" class="meta-item">
                    <span class="meta-label">⏱ 预计</span>
                    <span class="meta-value">{{ step.estimate }}</span>
                  </span>
                  <span v-if="step.applicableDevices" class="meta-item">
                    <span class="meta-label">适用</span>
                    <span class="meta-value">{{ step.applicableDevices }}</span>
                  </span>
                </div>

                <!-- 一、适用范围 -->
                <div v-if="step.scope" class="guide-section">
                  <div class="gs-header"><span class="gs-icon">📌</span>适用范围</div>
                  <div class="gs-body"><p class="gs-text">{{ step.scope }}</p></div>
                </div>

                <!-- 二、作业前准备 -->
                <div v-if="step.preparation && step.preparation.length" class="guide-section">
                  <div class="gs-header"><span class="gs-icon">🔧</span>作业前准备</div>
                  <div class="gs-body">
                    <div v-for="(p, pi) in step.preparation" :key="pi" class="prep-item">
                      <span class="prep-label">{{ p.item }}：</span>
                      <span class="prep-detail">{{ p.detail }}</span>
                    </div>
                  </div>
                </div>

                <!-- 三、关键安全/质量控制点 -->
                <div v-if="step.safetyControl && step.safetyControl.length" class="guide-section warn-section">
                  <div class="gs-header warn-header"><span class="gs-icon">⚠️</span>关键安全/质量控制点</div>
                  <div class="gs-body">
                    <div v-for="(sc, si) in step.safetyControl" :key="si" class="safety-item">
                      <span class="safety-dot">•</span>
                      <span class="safety-text">{{ sc }}</span>
                    </div>
                  </div>
                </div>

                <!-- 四、标准操作步骤（展开） -->
                <div class="guide-section" v-if="step.steps_json">
                  <div class="gs-header"><span class="gs-icon">📋</span>标准操作步骤</div>
                  <div class="gs-body step-list">
                    <div v-for="(s, si) in (step.steps || [])" :key="si" class="step-item">
                      <span class="step-num-badge">{{ String(s.step || si + 1).padStart(2, '0') }}</span>
                      <div class="step-item-content">
                        <div class="step-item-text">{{ s.content }}</div>
                        <div v-if="s.tip" class="step-item-tip">💡 {{ s.tip }}</div>
                      </div>
                    </div>
                  </div>
                </div>

                <!-- 工具清单 -->
                <div v-if="step.tools && step.tools.length" class="guide-tools">
                  <span class="tools-label">所需工具：</span>
                  <span class="tool-tag" v-for="(t, ti) in step.tools" :key="ti">{{ t }}</span>
                </div>

                <!-- 五、关键参数/验收标准 -->
                <div v-if="step.acceptanceCriteria && step.acceptanceCriteria.length" class="guide-section">
                  <div class="gs-header"><span class="gs-icon">✅</span>关键参数/验收标准</div>
                  <div class="gs-body">
                    <div v-for="(ac, ai) in step.acceptanceCriteria" :key="ai" class="accept-item">
                      <span class="accept-check">✓</span>
                      <span class="accept-text">{{ ac }}</span>
                    </div>
                  </div>
                </div>

                <!-- 六、异常/停止执行条件 -->
                <div v-if="step.stopConditions && step.stopConditions.length" class="guide-section stop-section">
                  <div class="gs-header stop-header"><span class="gs-icon">🚫</span>异常/停止执行条件</div>
                  <div class="gs-body">
                    <div v-for="(st, sti) in step.stopConditions" :key="sti" class="stop-item">
                      <span class="stop-dot">✕</span>
                      <span class="stop-text">{{ st }}</span>
                    </div>
                    <div class="stop-notice">
                      ⚠ 如现场情况满足以上任一条件，请暂停执行当前指导并重新评估/上报。
                    </div>
                  </div>
                </div>

                <!-- 使用边界声明 -->
                <div class="boundary-notice">
                  本指导用于标准化操作参考，实际检修需结合设备型号、现场状态及专业人员判断执行。
                  如现场出现超出指导范围的异常情况，请暂停执行并重新评估/上报。
                </div>

                <!-- 风险提示 -->
                <div v-if="step.warn" class="step-warn">
                  <span class="warn-icon">⚠</span>
                  <span class="warn-text">{{ step.warn }}</span>
                </div>

                <!-- 合规校验项（与实际操作步骤明确区分） -->
                <div class="step-checklist" v-if="step.checklist && step.checklist.length">
                  <div class="checklist-header">
                    <span class="checklist-title">📋 合规校验项</span>
                    <span v-if="step._execId && !step._completed" class="exec-status-badge">执行中</span>
                    <span v-if="step._completed" class="exec-status-badge done-badge">已完成</span>
                  </div>
                  <div
                    v-for="(chk, ci) in step.checklist"
                    :key="ci"
                    class="check-item"
                    :class="{ checked: step._done && step._done[ci] }"
                    @click.stop="step._execId && !step._completed ? toggleCheck(step, ci) : null"
                  >
                    <span class="check-box">{{ step._done && step._done[ci] ? '✓' : '' }}</span>
                    <span class="check-text">{{ chk }}</span>
                  </div>
                  <div class="checklist-actions" v-if="step.checklist.length">
                    <button v-if="!step._execId" class="btn-exec-start" @click.stop="startExecution(step)">
                      ▶ 开始执行
                    </button>
                    <button v-else-if="!step._completed" class="btn-exec-complete" @click.stop="completeExecution(step)">
                      ✓ 完成校验
                    </button>
                    <div v-else-if="!step._feedbackDone" class="feedback-inline">
                      <span class="feedback-label">这篇指导对你有帮助吗？</span>
                      <button class="fb-btn fb-yes" @click.stop="submitFeedback(step, 'helpful')">👍 有用</button>
                      <button class="fb-btn fb-no" @click.stop="submitFeedback(step, 'unhelpful')">👎 无用</button>
                    </div>
                    <div v-else class="feedback-thanks">✅ 已收到反馈，感谢！</div>
                  </div>
                </div>
                <div class="step-refs" v-if="step.refs && step.refs.length">
                  <span class="refs-label">相关参考：</span>
                  <span class="ref-tag" v-for="(r, ri) in step.refs" :key="ri">{{ r }}</span>
                </div>
                <div class="step-footer" v-if="step._userName">
                  <span class="step-contributor">🧑 贡献人：<b>{{ step._userName }}</b> · 入库 {{ formatDate(step._syncTime) }}</span>
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
import { listGuidesApi, listGuideTypesApi, listReportsApi, submitReportApi,
  recommendGuidesApi, recommendGuidesForTicketApi, createExecutionApi, updateExecutionApi, listExecutionsApi } from '../utils/api'

export default {
  name: 'Guide',
  data() {
    return {
      currentCat: '全部',
      currentSource: 'all',
      currentLevel: 'all',
      searchQuery: '',
      categories: ['全部'],
      maintenanceLevels: [
        { key: 'all', label: '全部等级' },
        { key: 'low', label: '1级（常规检修）' },
        { key: 'mid', label: '2级（重要检修）' },
        { key: 'high', label: '3级（紧急检修）' }
      ],
      allGuides: [],
      myReports: [],
      guideExecutions: [],
      loadingGuides: true,
      loadingTypes: true,
      loadingReports: true,
      ticketId: null,
      ticketContext: null,
      recommendedGuides: [],
      showGuideBanner: false,
      guideBannerLoading: false,
      showContributeForm: false,
      guideFormSubmitting: false,
      guideFormError: '',
      toolInput: '',
      guideForm: {
        title: '',
        device_type: '机械',
        difficulty: 3,
        duration_min: 30,
        maintenance_level: 'mid',
        applicable_devices: '',
        tools: [],
        steps: [{ content: '', tip: '' }, { content: '', tip: '' }, { content: '', tip: '' }, { content: '', tip: '' }, { content: '', tip: '' }],
        risk_note: ''
      }
    }
  },
  async created() {
    try {
      const [guidesRes, typesRes, reportsRes] = await Promise.all([
        listGuidesApi({ page: 1, size: 20000, source: 'all' }).catch(e => ({ data: { list: [] } })),
        listGuideTypesApi().catch(e => ({ data: [] })),
        listReportsApi({ page: 1, size: 20000, scope: 'mine' }).catch(e => ({ data: { list: [] } }))
      ])

      const rawGuides = (guidesRes && guidesRes.items) || []
      const rawTypes = (typesRes && typesRes.types) || []
      const rawReports = (reportsRes && reportsRes.items) || []

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

    // 从 URL 参数读取工单上下文
    this.ticketId = this.$route.query.ticket_id ? Number(this.$route.query.ticket_id) : null
    if (this.ticketId) {
      this.showGuideBanner = true
      this.guideBannerLoading = true
      try {
        const recRes = await recommendGuidesForTicketApi(this.ticketId)
        if (recRes && recRes.recommended) {
          this.recommendedGuides = recRes.recommended.map(r => {
            const g = this._convertGuide(r.guide)
            g._matchReason = r.match_reason
            return g
          })
          this.ticketContext = { device_type: recRes.device_type, level: recRes.level }
        }
      } catch (e) {
        console.warn('加载工单推荐指导失败:', e)
      } finally {
        this.guideBannerLoading = false
      }
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
      if (this.currentLevel !== 'all') {
        list = list.filter(s => s.maintenanceLevel === this.currentLevel)
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
      const checklist = (g.checklist && g.checklist.length) ? g.checklist : []
      return {
        id: g.id,
        cat,
        catClass: this.catClass(cat),
        title: g.title || '未命名作业指导',
        desc,
        checklist,
        warn: g.risk_note || '',
        estimate: g.duration_min ? g.duration_min + ' 分钟' : '—',
        difficulty: g.difficulty || 0,
        maintenanceLevel: g.maintenance_level || '',
        tools: g.tools || [],
        applicableDevices: g.applicable_devices || '',
        scope: g.scope || '',
        preparation: g.preparation || [],
        safetyControl: g.safety_control || [],
        acceptanceCriteria: g.acceptance_criteria || [],
        stopConditions: g.stop_conditions || [],
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
    },
    async loadReports() {
      try {
        const reportsRes = await listReportsApi({ page: 1, size: 20000, scope: 'mine', type: 'guide' })
        const rawReports = (reportsRes && reportsRes.items) || []
        this.myReports = rawReports.map(r => Object.assign({}, r, { _open: false }))
      } catch (e) {
        // ignore
      }
    },
    openContributeGuide() {
      this.guideFormError = ''
      this.showContributeForm = true
    },
    closeContributeGuide() {
      this.showContributeForm = false
    },
    addTool() {
      const v = (this.toolInput || '').trim()
      if (v && !this.guideForm.tools.includes(v)) {
        this.guideForm.tools.push(v)
      }
      this.toolInput = ''
    },
    async submitGuide() {
      this.guideFormError = ''
      if (!this.guideForm.title.trim()) {
        this.guideFormError = '请输入标题'
        return
      }
      const validSteps = this.guideForm.steps.filter(s => (s.content || '').trim())
      if (validSteps.length === 0) {
        this.guideFormError = '请至少填写一个操作步骤'
        return
      }
      this.guideFormSubmitting = true
      try {
        const stepsStr = validSteps.map((s, i) => `步骤${i + 1}：${s.content}${s.tip ? '（提示：' + s.tip + '）' : ''}`).join('\n')
        await submitReportApi({
          type: 'guide',
          title: this.guideForm.title.trim(),
          device: this.guideForm.applicable_devices.trim(),
          tag: this.guideForm.device_type,
          question: this.guideForm.applicable_devices.trim() || this.guideForm.title.trim(),
          solution: stepsStr,
          cause: this.guideForm.risk_note.trim(),
          summary: this.guideForm.title.trim(),
          level: this.guideForm.maintenance_level
        })
        window.dispatchEvent(new CustomEvent('equipai-toast', { detail: { text: '作业指导已提交，等待管理员审核', level: 'success' } }))
        this.closeContributeGuide()
        this.loadReports()
      } catch (e) {
        this.guideFormError = e.msg || e.message || '提交失败，请重试'
      } finally {
        this.guideFormSubmitting = false
      }
    },
    getLevelLabel(level) {
      const map = { low: '1级', mid: '2级', high: '3级' }
      return map[level] || ''
    },
    getLevelColor(level) {
      const map = { low: '#64748b', mid: '#f59e0b', high: '#ef4444' }
      return map[level] || '#64748b'
    },
    async toggleCheck(step, idx) {
      if (!step._done) step._done = {}
      step._done[idx] = !step._done[idx]
      if (step._execId) {
        try {
          const status = {}
          Object.keys(step._done).forEach(k => { status[k] = step._done[k] })
          await updateExecutionApi(step._execId, {
            checklist_status_json: JSON.stringify(status)
          })
        } catch (e) {
          console.error('保存执行状态失败:', e)
        }
      }
    },
    async startExecution(step) {
      try {
        const res = await createExecutionApi(this.ticketId, step.id)
        if (res) {
          step._execId = res.id
          step._done = {}
          window.dispatchEvent(new CustomEvent('equipai-toast', { detail: { text: '已开始执行作业指导', level: 'success' } }))
        }
      } catch (e) {
        window.dispatchEvent(new CustomEvent('equipai-toast', { detail: { text: '启动执行失败: ' + (e.message || ''), level: 'error' } }))
      }
    },
    scrollToGuide(guideId) {
      const el = this.$el?.querySelector(`[data-guide-id="${guideId}"]`)
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' })
    },
    async completeExecution(step) {
      if (!step._execId) return
      try {
        const status = {}
        if (step._done) {
          Object.keys(step._done).forEach(k => { status[k] = step._done[k] })
        }
        await updateExecutionApi(step._execId, {
          checklist_status_json: JSON.stringify(status),
          status: 'completed'
        })
        step._completed = true
        window.dispatchEvent(new CustomEvent('equipai-toast', { detail: { text: '合规校验已完成', level: 'success' } }))
      } catch (e) {
        console.error('完成执行失败:', e)
      }
    },
    async submitFeedback(step, feedback) {
      if (!step._execId || step._feedbackDone) return
      try {
        await updateExecutionApi(step._execId, {
          review_remark: feedback === 'helpful' ? '有用' : '无用'
        })
        step._feedbackDone = true
        window.dispatchEvent(new CustomEvent('equipai-toast', { detail: { text: '感谢反馈！', level: 'success' } }))
      } catch (e) {
        console.error('反馈提交失败:', e)
      }
    }
  }
}
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 20px; margin-bottom: 28px; flex-wrap: wrap; }
.page-header-left { flex: 1; min-width: 0; }
.page-title { font-size: 1.75rem; font-weight: 800; margin: 0; color: var(--text-primary); }
.page-desc { font-size: 0.875rem; color: var(--text-secondary); margin-top: 6px; }
.header-actions { display: flex; gap: 10px; flex-shrink: 0; }
.btn-icon { font-size: 1rem; font-weight: 700; }

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

/* 贡献按钮栏 */
.contribute-bar {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 16px;
}

/* 弹窗 */
.modal-overlay {
  position: fixed; inset: 0; background: var(--modal-mask);
  display: flex; align-items: center; justify-content: center;
  z-index: 2000; padding: 24px;
}
.modal-dialog {
  width: 100%; max-width: 680px; max-height: 90vh;
  display: flex; flex-direction: column; overflow: hidden;
  background: var(--modal-bg); border: 1px solid var(--modal-border);
  border-radius: var(--radius-lg);
}
.modal-header {
  padding: 18px 24px; display: flex; justify-content: space-between; align-items: center;
  border-bottom: 1px solid var(--modal-header-border);
}
.modal-header h3 { margin: 0; font-size: 1.0625rem; color: var(--text-primary); }
.modal-close {
  background: none; border: none; font-size: 1.5rem; color: var(--text-muted);
  cursor: pointer; padding: 0 4px;
}
.modal-close:hover { color: var(--accent-red); }
.modal-body {
  padding: 20px 24px; overflow-y: auto; flex: 1;
  display: flex; flex-direction: column; gap: 14px;
}
.modal-footer {
  padding: 14px 24px; display: flex; justify-content: flex-end; gap: 10px;
  border-top: 1px solid var(--modal-footer-border);
}

/* 表单 */
.form-row { display: flex; flex-direction: column; gap: 6px; }
.form-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-row label { font-size: 0.8125rem; color: var(--text-secondary); font-weight: 500; }
.form-hint { color: var(--text-muted); font-weight: 400; font-size: 0.75rem; }
.required { color: var(--accent-red); }
.form-input {
  width: 100%; background: var(--modal-input-bg);
  border: 1px solid var(--modal-input-border); border-radius: var(--radius);
  color: var(--modal-input-color); padding: 9px 12px; font-family: inherit;
  font-size: 0.875rem; transition: all var(--duration) var(--ease); box-sizing: border-box;
}
.form-input option { background: var(--modal-bg); color: var(--modal-input-color); }
.form-input:focus { outline: none; border-color: var(--primary); background: rgba(37,99,235,0.04); }
textarea.form-input { resize: vertical; }

/* 星级选择 */
.star-picker { display: flex; gap: 4px; }
.star {
  font-size: 1.25rem; color: var(--text-muted); cursor: pointer; transition: color 0.15s;
}
.star.active { color: var(--accent-orange); }
.star:hover { color: var(--accent-orange); }

/* 工具标签输入 */
.tag-input-wrap {
  display: flex; flex-wrap: wrap; gap: 6px; padding: 6px 10px;
  background: var(--bg-deep); border: 1px solid var(--border-subtle);
  border-radius: var(--radius); min-height: 40px; align-items: center;
}
.tag { display: inline-flex; align-items: center; gap: 4px; padding: 2px 8px; border-radius: 3px; font-size: 0.75rem; }
.tool-tag { background: rgba(37,99,235,0.1); color: var(--primary); }
.tag-remove { cursor: pointer; font-size: 0.875rem; opacity: 0.6; }
.tag-remove:hover { opacity: 1; }
.tag-input {
  flex: 1; min-width: 120px; background: none; border: none; outline: none;
  color: var(--text-primary); font-size: 0.875rem; padding: 4px 0;
}

/* 步骤输入 */
.step-input-row { display: flex; gap: 8px; align-items: center; margin-bottom: 8px; }
.step-num {
  width: 24px; height: 24px; border-radius: 50%; background: var(--primary);
  color: #fff; font-size: 0.75rem; display: flex; align-items: center;
  justify-content: center; flex-shrink: 0; font-weight: 600;
}
.step-tip { flex: 0.8; }
.step-remove {
  width: 28px; height: 28px; border-radius: var(--radius); border: 1px solid var(--border-subtle);
  background: transparent; color: var(--text-muted); cursor: pointer; font-size: 1rem;
}
.step-remove:hover { color: var(--accent-red); border-color: var(--accent-red); }
.btn-sm { padding: 6px 14px; font-size: 0.8125rem; }

.form-error { color: var(--accent-red); font-size: 0.8125rem; padding: 8px 0; }

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

/* 作业指导概览：难度 / 耗时 / 适用设备 */
.guide-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 18px;
  margin: 10px 0 8px;
  padding: 10px 14px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  border-left: 3px solid var(--primary);
}
.meta-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.75rem;
}
.meta-label {
  color: var(--text-muted);
  font-weight: 500;
}
.meta-value {
  color: var(--text-primary);
  font-weight: 600;
}
.difficulty-stars {
  color: var(--accent-orange);
  letter-spacing: 2px;
  font-size: 0.8125rem;
}

/* 所需工具 */
.guide-tools {
  margin: 6px 0 12px;
  padding: 8px 14px;
  background: rgba(37, 99, 235, 0.04);
  border-radius: var(--radius);
  border: 1px solid rgba(37, 99, 235, 0.12);
}
.tools-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 500;
  margin-right: 4px;
}
.tool-tag {
  display: inline-block;
  font-size: 0.6875rem;
  padding: 2px 8px;
  margin: 2px 3px 2px 0;
  background: rgba(37, 99, 235, 0.1);
  color: var(--primary);
  border-radius: 3px;
  font-weight: 500;
}

/* 检修等级筛选器 */
.level-filter {
  display: flex;
  align-items: center;
}
.level-select {
  padding: 7px 14px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-secondary);
  font-size: 0.8125rem;
  font-family: inherit;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}
.level-select:hover {
  border-color: var(--border-hover);
  color: var(--text-primary);
}

/* 检修等级标签 */
.level-badge {
  font-size: 0.625rem;
  padding: 2px 8px;
  border-radius: 999px;
  font-weight: 600;
  color: #fff;
  letter-spacing: 0.5px;
}

/* 合规校验项头部 */
.checklist-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px dashed var(--border-subtle);
}
.checklist-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
}
.exec-status-badge {
  font-size: 0.625rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: rgba(0, 212, 255, 0.15);
  color: var(--primary);
  font-weight: 600;
}

/* 执行操作按钮 */
.checklist-actions {
  display: flex;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border-subtle);
}
.btn-exec-start, .btn-exec-complete {
  padding: 8px 16px;
  border-radius: var(--radius);
  font-size: 0.8125rem;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}
.btn-exec-start {
  background: var(--primary);
  color: #fff;
}
.btn-exec-start:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}
.btn-exec-complete {
  background: var(--accent-green);
  color: #fff;
}
.btn-exec-complete:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

/* 推荐横幅 */
.guide-banner {
  margin-bottom: 20px; padding: 16px 18px;
  border: 1px solid rgba(16,185,129,0.2);
  background: rgba(16,185,129,0.04);
  border-radius: var(--radius-lg);
}
.banner-head { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.banner-icon { font-size: 1rem; }
.banner-title { font-weight: 600; font-size: 0.875rem; color: var(--text-primary); flex: 1; }
.banner-context { font-size: 0.75rem; color: var(--accent-green); background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 999px; }
.banner-close {
  width: 24px; height: 24px; border-radius: 50%;
  background: transparent; border: 1px solid transparent;
  color: var(--text-muted); cursor: pointer; font-family: inherit;
  display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease);
}
.banner-close:hover { background: rgba(255,255,255,0.05); color: var(--text-primary); }
.banner-loading { font-size: 0.8125rem; color: var(--text-secondary); padding: 8px 0; }
.banner-empty { font-size: 0.8125rem; color: var(--text-muted); padding: 8px 0; }
.banner-list { display: flex; flex-direction: column; gap: 6px; }
.banner-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: var(--radius);
  cursor: pointer; transition: all 0.15s;
  border: 1px solid transparent;
}
.banner-item:hover { background: rgba(255,255,255,0.03); border-color: var(--border-subtle); }
.banner-item.banner-exact { background: rgba(16,185,129,0.05); }
.banner-rank {
  width: 22px; height: 22px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-size: 0.6875rem; font-weight: 700; font-family: 'Orbitron', sans-serif;
  background: rgba(16,185,129,0.12); color: var(--accent-green); flex-shrink: 0;
}
.banner-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.banner-gtitle { font-size: 0.8125rem; font-weight: 500; color: var(--text-primary); }
.banner-greason { font-size: 0.625rem; color: var(--accent-green); }
.banner-glevel {
  font-size: 0.625rem; padding: 2px 8px; border-radius: 999px; font-weight: 600; flex-shrink: 0;
}
.banner-glevel.low { background: rgba(16,185,129,0.12); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
.banner-glevel.mid { background: rgba(255,107,53,0.12); color: var(--accent-orange); border: 1px solid rgba(255,107,53,0.2); }
.banner-glevel.high { background: rgba(255,71,87,0.12); color: var(--accent-red); border: 1px solid rgba(255,71,87,0.2); }

/* 执行反馈 */
.feedback-inline { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; padding: 8px 0; }
.feedback-label { font-size: 0.75rem; color: var(--text-secondary); }
.fb-btn {
  padding: 4px 12px; font-size: 0.75rem; border-radius: 999px;
  cursor: pointer; font-family: inherit; border: 1px solid var(--border-subtle);
  background: transparent; color: var(--text-secondary);
  transition: all var(--duration) var(--ease);
}
.fb-btn:hover { transform: translateY(-1px); }
.fb-yes:hover { border-color: var(--accent-green); color: var(--accent-green); background: rgba(16,185,129,0.08); }
.fb-no:hover { border-color: var(--accent-red); color: var(--accent-red); background: rgba(255,71,87,0.08); }
.feedback-thanks { font-size: 0.75rem; color: var(--accent-green); padding: 8px 0; }

/* 指导结构化分区 */
.guide-section { margin-bottom: 16px; }
.gs-header { display: flex; align-items: center; gap: 6px; font-size: 0.8125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; padding-bottom: 4px; border-bottom: 1px solid var(--border-subtle); }
.gs-icon { font-size: 0.875rem; }
.gs-body { padding-left: 4px; }
.gs-text { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.7; white-space: pre-wrap; }

/* 作业前准备 */
.prep-item { display: flex; gap: 6px; padding: 3px 0; font-size: 0.8125rem; }
.prep-label { color: var(--text-primary); font-weight: 500; white-space: nowrap; min-width: 80px; }
.prep-detail { color: var(--text-secondary); }

/* 安全/质量控制点 */
.warn-section { border-left: 3px solid var(--accent-orange); padding-left: 12px; }
.warn-header { color: var(--accent-orange); }
.safety-item { display: flex; gap: 8px; padding: 2px 0; font-size: 0.8125rem; color: var(--text-secondary); }
.safety-dot { color: var(--accent-orange); font-weight: 700; }

/* 标准操作步骤 */
.step-list { display: flex; flex-direction: column; gap: 8px; }
.step-item { display: flex; gap: 10px; padding: 8px 10px; background: rgba(255,255,255,0.02); border-radius: var(--radius); border: 1px solid var(--border-subtle); }
.step-num-badge { width: 28px; height: 28px; border-radius: 6px; background: var(--primary-subtle); color: var(--primary); display: flex; align-items: center; justify-content: center; font-size: 0.6875rem; font-weight: 700; font-family: 'Orbitron', sans-serif; flex-shrink: 0; }
.step-item-content { flex: 1; min-width: 0; }
.step-item-text { font-size: 0.8125rem; color: var(--text-primary); line-height: 1.5; }
.step-item-tip { font-size: 0.75rem; color: var(--text-muted); margin-top: 3px; }

/* 验收标准 */
.accept-item { display: flex; gap: 8px; padding: 3px 0; font-size: 0.8125rem; color: var(--text-secondary); }
.accept-check { color: var(--accent-green); font-weight: 700; }

/* 停止条件 */
.stop-section { border-left: 3px solid var(--accent-red); padding-left: 12px; background: rgba(255,71,87,0.03); border-radius: 0 var(--radius) var(--radius) 0; padding: 8px 12px; }
.stop-header { color: var(--accent-red); }
.stop-item { display: flex; gap: 8px; padding: 3px 0; font-size: 0.8125rem; color: var(--text-secondary); }
.stop-dot { color: var(--accent-red); font-weight: 700; }
.stop-notice { margin-top: 8px; padding: 8px 10px; background: rgba(255,71,87,0.08); border-radius: var(--radius); font-size: 0.75rem; color: var(--accent-red); font-weight: 500; }

/* 边界声明 */
.boundary-notice { margin-top: 12px; margin-bottom: 16px; padding: 10px 14px; background: rgba(37,99,235,0.05); border: 1px dashed var(--primary-dim); border-radius: var(--radius); font-size: 0.75rem; color: var(--text-secondary); line-height: 1.6; }

/* 执行状态标签 */
.exec-status-badge { font-size: 0.625rem; padding: 2px 8px; border-radius: 999px; font-weight: 600; background: var(--accent-green); color: #052e16; }
.exec-status-badge.done-badge { background: rgba(16,185,129,0.12); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
</style>
