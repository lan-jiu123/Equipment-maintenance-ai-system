<template>
  <div class="container">
    <!-- 顶部统计条 -->
    <section class="stats-grid mini">
      <div class="stat-card card" :class="{ 'is-alert': urgentCount > 0 }" data-cat="urgent">
        <div class="stat-icon">🚨</div>
        <div class="stat-info">
          <div class="stat-value">{{ urgentCount }}</div>
          <div class="stat-label">加急待处理</div>
        </div>
      </div>
      <div class="stat-card card" data-cat="pending">
        <div class="stat-icon">📌</div>
        <div class="stat-info">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待处理</div>
        </div>
      </div>
      <div class="stat-card card" data-cat="ongoing">
        <div class="stat-icon">🔄</div>
        <div class="stat-info">
          <div class="stat-value">{{ ongoingCount }}</div>
          <div class="stat-label">处理中</div>
        </div>
      </div>
      <div class="stat-card card" data-cat="done">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ doneCount }}</div>
          <div class="stat-label">本月已完成</div>
        </div>
      </div>
    </section>

    <!-- 紧凑筛选条 -->
    <section class="filter-bar card">
      <div class="filter-bar-row">
        <div class="seg-control">
          <button
            v-for="tab in statusTabs"
            :key="tab.k"
            class="seg"
            :class="{ active: activeStatus === tab.k }"
            @click="activeStatus = tab.k; page = 1"
          >{{ tab.label }} <span class="seg-count">{{ countByStatus(tab.k) }}</span></button>
        </div>
        <div class="filter-spacer"></div>
        <select v-model="statusFilter" class="input mini-select">
          <option value="">全部状态</option>
          <option value="pending">待处理</option>
          <option value="ongoing">处理中</option>
          <option value="done">已完成</option>
        </select>
        <select v-model="levelFilter" class="input mini-select">
          <option value="">全部等级</option>
          <option value="high">高</option>
          <option value="mid">中</option>
          <option value="low">低</option>
        </select>
        <select v-model="sortBy" class="input mini-select">
          <option value="sla">按 SLA 剩余</option>
          <option value="level">按故障等级</option>
          <option value="created">按创建时间</option>
        </select>
        <div class="search-box">
          <span>🔍</span>
          <input v-model="keyword" placeholder="搜索工单号 / 设备 / 故障..." />
        </div>
      </div>
    </section>

    <section class="table-section card">

      <table class="data-table compact">
        <thead>
          <tr>
            <th style="width:90px">工单号</th>
            <th style="width:100px">设备</th>
            <th>故障描述</th>
            <th style="width:60px">等级</th>
            <th style="width:110px">SLA</th>
            <th style="width:140px">创建时间</th>
            <th style="width:90px">状态</th>
            <th style="width:220px">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading"><td colspan="8" style="padding:64px 0">
            <div class="skeleton-wrap">
              <div v-for="i in 6" :key="i" class="skeleton-row"><span></span><span></span><span></span><span></span><span></span><span></span><span></span><span></span></div>
            </div>
          </td></tr>
          <tr v-else-if="!pagedItems.length"><td colspan="8" style="text-align:center;padding:64px 0;color:var(--text-muted);">暂无符合条件的工单</td></tr>
          <tr v-for="t in pagedItems" :key="t.id" class="ticket-row">
            <td class="mono">{{ t.code || ('WO-' + t.id) }}</td>
            <td>
              <div class="device-cell">
                <span class="device-code">{{ t.device_name || '未关联' }}</span>
                <span class="device-loc">{{ t.location || '—' }}</span>
              </div>
            </td>
            <td class="desc-cell">{{ t.problem || t.title || '—' }}</td>
            <td>
              <span class="level-tag" :class="'lv-' + t.level">{{ t.level_label }}</span>
            </td>
            <td>
              <div class="sla-cell">
                <div class="sla-bar">
                  <div class="sla-fill" :class="slaClass(t.slaPct)" :style="{ width: t.slaPct + '%' }"></div>
                </div>
                <div class="sla-text" :class="slaTextClass(t.slaPct)">{{ t.slaText }}</div>
              </div>
            </td>
            <td class="muted">{{ t.createdText }}</td>
            <td>
              <span class="status-pill" :class="'st-' + t.status">{{ t.status_label }}</span>
            </td>
            <td>
              <div class="row-actions">
              <button class="btn btn-primary btn-xs" v-if="(t.status === 'assigned' || t.status === 'pending') && Number(t.assignee_id) === Number(meId)" :disabled="t._op" @click="handle(t)">
                {{ t._op === 'accept' ? '接单中…' : '开始处理' }}
              </button>
              <button class="btn btn-success btn-xs" v-else-if="t.status === 'ongoing' || t.status === 'processing'" :disabled="t._op" @click="finish(t)">
                {{ t._op === 'complete' ? '提交中…' : '完成 / 上报' }}
              </button>
              <button class="btn btn-outline btn-xs" @click="view(t)">详情</button>
              <button class="btn btn-outline btn-xs guide-btn" :disabled="t._gop" @click="showGuideRecommend(t)" style="margin-left:4px;">📋 指导</button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="filteredTickets.length > size" class="table-footer card">
        <div class="pagination-info">共 <b>{{ filteredTickets.length }}</b> 条 · 第 {{ page }} / {{ totalPages }} 页</div>
        <div class="pagination">
          <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page=1">首页</button>
          <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page--">‹ 上一页</button>
          <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page++">下一页 ›</button>
          <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page=totalPages">末页</button>
        </div>
      </div>
    </section>

    <transition name="fade">
      <div v-if="detailVisible && detailTicket" class="finish-mask" @click.self="closeDetail">
        <div class="finish-dialog detail-dialog card">
          <div class="finish-header detail-header">
            <div class="fh-title">
              <span class="fh-icon">📋</span>
              <div>
                <div class="fh-big">工单详情 · {{ detailTicket.code }}</div>
                <div class="fh-small">{{ detailTicket.title }}</div>
              </div>
            </div>
            <button class="kr-close" @click="closeDetail" type="button">✕</button>
          </div>
          <div class="finish-body detail-body">
            <div class="detail-field detail-full">
              <div class="detail-label">工单标题</div>
              <div class="detail-value strong">{{ detailTicket.title || '—' }}</div>
            </div>
            <div class="detail-field">
              <div class="detail-label">关联设备</div>
              <div class="detail-value">{{ detailTicket.device_name || '—' }}</div>
            </div>
            <div class="detail-field">
              <div class="detail-label">类别</div>
              <div class="detail-value">{{ detailTicket.category || '—' }}</div>
            </div>
            <div class="detail-field">
              <div class="detail-label">优先级</div>
              <div class="detail-value">
                <span class="level-tag" :class="'lv-' + detailTicket.level">{{ detailTicket.level_label }}</span>
              </div>
            </div>
            <div class="detail-field">
              <div class="detail-label">状态</div>
              <div class="detail-value">
                <span class="status-pill" :class="'st-' + detailTicket.status">{{ detailTicket.status_label }}</span>
              </div>
            </div>
            <div class="detail-field">
              <div class="detail-label">处理人</div>
              <div class="detail-value">{{ detailTicket.assignee_name || '待分配' }}</div>
            </div>
            <div class="detail-field">
              <div class="detail-label">创建人</div>
              <div class="detail-value">{{ detailTicket.submitter_name || '系统' }}</div>
            </div>
            <div class="detail-field detail-full">
              <div class="detail-label">创建时间</div>
              <div class="detail-value mono">{{ detailTicket.createdText }}</div>
            </div>
            <div class="detail-field detail-full">
              <div class="detail-label">问题描述</div>
              <div class="detail-value detail-text">{{ detailTicket.problem || '—' }}</div>
            </div>
            <div v-if="detailTicket.solution" class="detail-field detail-full">
              <div class="detail-label">解决方案</div>
              <div class="detail-value detail-text solution">{{ detailTicket.solution }}</div>
            </div>
            <div class="detail-field detail-full">
              <div class="detail-label">备注</div>
              <div class="detail-value detail-text remark">{{ detailTicket.remark || '—' }}</div>
            </div>
          </div>
          <div class="detail-footer">
            <button class="btn btn-outline" @click="closeDetail" type="button">关闭</button>
          </div>
        </div>
      </div>
    </transition>

    <transition name="fade">
      <div v-if="finishVisible" class="finish-mask" @click.self="closeFinish">
        <div class="finish-dialog card">
          <div class="finish-header">
            <div class="fh-title">
              <span class="fh-icon">✅</span>
              <div>
                <div class="fh-big">完成工单</div>
                <div class="fh-small">工单号：<b class="mono">{{ finishTicket && (finishTicket.code || finishTicket.id) }}</b> · 设备：{{ finishTicket && finishTicket.device_name }}</div>
              </div>
            </div>
            <button class="kr-close" @click="closeFinish" type="button">✕</button>
          </div>
          <div class="finish-body">
            <div class="kr-row">
              <label class="kr-label required">现场处置步骤及解决方案</label>
              <textarea
                v-model="finishForm.solution"
                class="input"
                rows="5"
                placeholder="分步骤描述您在现场的操作流程、故障根因判定、更换部件、验证结果（温度/噪音/电流等数据）"
              ></textarea>
            </div>
            <div class="kr-row kr-double">
              <div>
                <label class="kr-label">更换部件</label>
                <input v-model="finishForm.parts" class="input" placeholder="如：303型高温轴承 ×1；美孚XHP222高温锂基脂" type="text" />
              </div>
              <div>
                <label class="kr-label">工时（小时）</label>
                <input v-model="finishForm.hours" class="input" placeholder="如：2.5" type="text" />
              </div>
            </div>
            <label class="contrib-check card" :class="{ checked: finishForm.contrib }" @click="finishForm.contrib = !finishForm.contrib">
              <span class="cc-box">
                <span v-if="finishForm.contrib" class="cc-check">✓</span>
              </span>
              <span class="cc-text">
                <b>🧪 AI 未能解决，我通过现场实践完成了该工单</b>
                <em>勾选后生成知识实践报告并通知管理员审核；不勾选仅保存完成方案</em>
              </span>
            </label>
          </div>
          <div class="kr-footer">
            <div class="kr-err" v-if="finishErr">{{ finishErr }}</div>
            <div class="kr-actions">
              <button class="btn btn-outline" @click="closeFinish" type="button">取消</button>
              <button class="btn btn-success" @click="submitFinish" type="button" :disabled="finishSubmitting">
                {{ finishSubmitting ? '提交中…' : (finishForm.contrib ? '完成并提交知识报告' : '确认完成工单') }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </transition>

    <!-- 推荐作业指导弹窗 -->
    <div v-if="guideModalOpen" class="modal-mask" @click="guideModalOpen = false">
      <div class="modal-card card" @click.stop style="max-width: 640px;">
        <div class="modal-head">
          <h3>📋 推荐作业指导 — {{ guideModalTicket?.title }}</h3>
          <div class="modal-head-actions">
            <button class="modal-refresh-btn" @click="refreshGuideRecommend" :disabled="guideModalLoading" title="重新匹配">🔄</button>
            <button class="modal-close" @click="guideModalOpen = false" type="button">✕</button>
          </div>
        </div>
        <div class="modal-body">
          <div v-if="guideModalLoading" class="guide-loading">正在匹配最合适的作业指导...</div>
          <div v-else-if="guideModalError" class="guide-error">{{ guideModalError }}</div>
          <div v-else-if="guideModalItems.length === 0 && !guideModalDynamic" class="guide-empty">
            <div class="guide-empty-icon">📭</div>
            <div class="guide-empty-text">暂未找到匹配的作业指导</div>
            <div class="guide-empty-desc">可前往<a href="/guide" class="guide-link">作业指导库</a>浏览全部规程</div>
          </div>
          <div v-else class="guide-list">
            <div
              v-for="(item, gi) in guideModalItems"
              :key="gi"
              class="guide-rec-card card"
              :class="{ 'guide-exact': item.match_reason && item.match_reason.includes('精确') }"
            >
              <div class="guide-rec-header">
                <span class="guide-rec-title">{{ item.guide.title }}</span>
                <span class="guide-rec-badge" :class="item.guide.maintenance_level">
                  {{ { low: '1级', mid: '2级', high: '3级' }[item.guide.maintenance_level] || '' }}
                </span>
              </div>
              <div class="guide-rec-meta">
                <span>🔧 {{ item.guide.device_type }}</span>
                <span>⏱ {{ item.guide.duration_min || '—' }} 分钟</span>
                <span>📊 {{ '★'.repeat(item.guide.difficulty || 0) }}{{ '☆'.repeat(5 - (item.guide.difficulty || 0)) }}</span>
              </div>
              <div class="guide-rec-reason">{{ item.match_reason }}</div>

              <!-- 适用范围 -->
              <div v-if="item.guide.scope" class="rec-section">
                <div class="rec-section-title">📌 适用范围</div>
                <div class="rec-section-body">{{ item.guide.scope.split('\n')[0] }}</div>
              </div>

              <!-- 作业前准备 -->
              <div v-if="item.guide.preparation && item.guide.preparation.length" class="rec-section">
                <div class="rec-section-title">🔧 作业前准备</div>
                <div class="rec-prep-list">
                  <span v-for="(p, pi) in item.guide.preparation" :key="pi" class="rec-prep-chip">{{ p.item }}: {{ p.detail }}</span>
                </div>
              </div>

              <!-- 安全控制点 -->
              <div v-if="item.guide.safety_control && item.guide.safety_control.length" class="rec-section">
                <div class="rec-section-title warn-title">⚠️ 安全控制点</div>
                <div class="rec-tag-list">
                  <span v-for="(sc, si) in item.guide.safety_control.slice(0, 3)" :key="si" class="rec-tag rec-tag-warn">{{ sc }}</span>
                  <span v-if="item.guide.safety_control.length > 3" class="rec-tag rec-tag-more">+{{ item.guide.safety_control.length - 3 }}</span>
                </div>
              </div>

              <!-- 验收标准 -->
              <div v-if="item.guide.acceptance_criteria && item.guide.acceptance_criteria.length" class="rec-section">
                <div class="rec-section-title">✅ 验收标准</div>
                <div class="rec-tag-list">
                  <span v-for="(ac, ai) in item.guide.acceptance_criteria.slice(0, 3)" :key="ai" class="rec-tag rec-tag-ok">{{ ac }}</span>
                  <span v-if="item.guide.acceptance_criteria.length > 3" class="rec-tag rec-tag-more">+{{ item.guide.acceptance_criteria.length - 3 }}</span>
                </div>
              </div>

              <!-- 合规校验项 -->
              <div v-if="item.guide.checklist && item.guide.checklist.length" class="rec-section">
                <div class="rec-section-title">📋 合规校验项（{{ item.guide.checklist.length }}项）</div>
                <div v-for="(chk, ci) in item.guide.checklist.slice(0, 3)" :key="ci" class="rec-cl-item">✓ {{ chk }}</div>
                <div v-if="item.guide.checklist.length > 3" class="rec-cl-more">+{{ item.guide.checklist.length - 3 }} 项</div>
              </div>

              <!-- 停止条件 -->
              <div v-if="item.guide.stop_conditions && item.guide.stop_conditions.length" class="rec-stop-warn">
                🚫 如现场存在：{{ item.guide.stop_conditions.slice(0, 2).join('、') }} 等，请暂停执行并评估
              </div>

              <button class="rec-view-btn" @click="goGuideDetail(item.guide.id)">📄 查看完整指导详情 →</button>
            </div>
          </div>

          <!-- AI 动态生成流程（无匹配时的自适应方案） -->
          <div v-if="guideModalDynamic" class="dynamic-guide-card card">
            <div class="dynamic-guide-header">
              <span class="dynamic-guide-icon">✨</span>
              <div>
                <div class="dynamic-guide-title">AI 动态生成检修流程</div>
                <div class="dynamic-guide-note">{{ guideModalDynamicNote }}</div>
              </div>
            </div>
            <div class="dynamic-guide-body">
              <div class="dg-title">{{ guideModalDynamic.title }}</div>
              <div v-if="guideModalDynamic.risk_note" class="dg-risk">⚠️ {{ guideModalDynamic.risk_note }}</div>
              <div v-if="guideModalDynamic.required_tools && guideModalDynamic.required_tools.length" class="dg-tools">
                <span class="dg-label">🔧 所需工具：</span>
                <span v-for="(tool, ti) in guideModalDynamic.required_tools" :key="ti" class="dg-tool-chip">{{ tool }}</span>
              </div>
              <div v-if="guideModalDynamic.estimated_duration_min" class="dg-duration">
                ⏱ 预计耗时：{{ guideModalDynamic.estimated_duration_min }} 分钟
              </div>
              <div class="dg-steps">
                <div v-for="(step, si) in guideModalDynamic.steps" :key="si" class="dg-step">
                  <span class="dg-step-num">{{ step.step }}</span>
                  <div class="dg-step-body">
                    <div class="dg-step-content">{{ step.content }}</div>
                    <div v-if="step.tip" class="dg-step-tip">💡 {{ step.tip }}</div>
                  </div>
                </div>
              </div>
              <div class="dg-footer">⚠️ 本流程由 AI 根据故障描述自动生成，执行前请现场核实安全条件</div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<script>
import { getUser } from '../utils/auth'
import {
  listTicketsApi, acceptTicketApi, completeTicketApi, submitReportApi,
  recommendGuidesForTicketApi
} from '../utils/api'
import { toast as _toast } from '../utils/request'

const LEVEL_ORDER = { critical: 0, high: 0, mid: 1, low: 2 }
const LEVEL_LABEL = { critical: '高（加急）', high: '高（加急）', mid: '中', low: '低' }
const LEVEL_CLS = { critical: 'high', high: 'high', mid: 'medium', low: 'low' }
const STATUS_DISPLAY = {
  pending:    { label: '待处理', cls: 'pending' },
  assigned:   { label: '待处理', cls: 'pending' },
  processing: { label: '处理中', cls: 'ongoing' },
  ongoing:    { label: '处理中', cls: 'ongoing' },
  completed:  { label: '已完成', cls: 'done' },
  done:       { label: '已完成', cls: 'done' },
  overdue:    { label: '超时',   cls: 'overdue' },
  cancelled:  { label: '已取消', cls: 'overdue' }
}
const LEVEL_SLA_HOURS = { critical: 6, high: 6, mid: 24, low: 48 }

function _fmtTime(ts) {
  if (!ts) return '-'
  const d = new Date(Number(ts) * 1000)
  const y = d.getFullYear()
  const m = (d.getMonth() + 1).toString().padStart(2, '0')
  const day = d.getDate().toString().padStart(2, '0')
  const hh = d.getHours().toString().padStart(2, '0')
  const mm = d.getMinutes().toString().padStart(2, '0')
  return y + '-' + m + '-' + day + ' ' + hh + ':' + mm
}

function _calcSla(ts, level, finishTs) {
  if (finishTs) {
    return { pct: 100, text: '已完成' }
  }
  if (!ts) return { pct: 50, text: '未设置' }
  const hours = LEVEL_SLA_HOURS[level] || 24
  const startMs = Number(ts) * 1000
  const totalMs = hours * 3600 * 1000
  const elapsedMs = Date.now() - startMs
  const remainMs = totalMs - elapsedMs
  let pct = Math.max(0, Math.min(100, Math.round((remainMs / totalMs) * 100)))
  if (remainMs <= 0) return { pct: 0, text: '待处理' }
  const h = Math.floor(remainMs / 3600000)
  const m = Math.floor((remainMs % 3600000) / 60000)
  let text
  if (h > 0) text = '剩余 ' + h + ' 小时 ' + (m > 0 ? m + ' 分' : '')
  else text = '剩余 ' + Math.max(1, m) + ' 分'
  return { pct, text }
}

function _mapTicket(t) {
  let level = (t.level || 'mid').toLowerCase()
  if (level === 'critical') level = 'high'
  const statusKey = (t.status || 'pending').toLowerCase()
  const display = STATUS_DISPLAY[statusKey] || STATUS_DISPLAY.pending
  const sla = _calcSla(t.submit_time_ts, level, t.finish_time_ts)
  let mappedStatus = statusKey
  if (statusKey === 'processing' || statusKey === 'doing') mappedStatus = 'ongoing'
  if (statusKey === 'completed') mappedStatus = 'done'
  if (statusKey === 'over') mappedStatus = 'ongoing'
  let slaText, slaPct
  if (mappedStatus === 'done') {
    slaText = '已完成'
    slaPct = 100
  } else if (mappedStatus === 'pending' || mappedStatus === 'assigned') {
    slaText = '待处理'
    slaPct = 0
  } else {
    slaText = '处理中'
    slaPct = 50
  }
  return {
    id: t.id,
    code: t.code || ('WO-' + String(t.id).padStart(6, '0')),
    title: t.title,
    device_name: t.device_name,
    category: t.category || '—',
    location: '',
    problem: t.problem || t.title,
    level: LEVEL_CLS[level] || level,
    level_label: t.level_label || LEVEL_LABEL[level] || '中',
    _levelKey: level,
    _submitTs: t.submit_time_ts || 0,
    _finishTs: t.finish_time_ts || 0,
    slaPct: slaPct,
    slaText: slaText,
    createdText: _fmtTime(t.submit_time_ts),
    status: mappedStatus,
    status_label: t.status_label || display.label,
    status_cls: display.cls,
    assignee_id: t.assignee_id,
    assignee_name: t.assignee_name,
    submitter_name: t.submitter_name,
    solution: t.solution || '',
    remark: t.remark || '',
    _op: null
  }
}

export default {
  name: 'Tickets',
  data() {
    return {
      keyword: '',
      onlyUrgent: false,
      activeStatus: 'all',
      statusFilter: '',
      levelFilter: '',
      sortBy: 'sla',
      statusTabs: [
        { k: 'all',     label: '全部' },
        { k: 'pending', label: '待处理' },
        { k: 'ongoing', label: '处理中' },
        { k: 'done',    label: '已完成' }
      ],
      allTickets: [],
      loading: false,
      page: 1,
      size: 10,
      meId: null,
      _hydrating: true,
      _refreshTick: 0,
      finishVisible: false,
      finishTicket: null,
      detailVisible: false,
      detailTicket: null,
      finishForm: { solution: '', parts: '', hours: '', contrib: true },
      finishSubmitting: false,
      finishErr: '',
      toast: '',
      guideModalOpen: false,
      guideModalLoading: false,
      guideModalError: '',
      guideModalTicket: null,
      guideModalItems: [],
      guideModalDynamic: null,
      guideModalDynamicNote: '',
    }
  },
  computed: {
    filteredTickets() {
      this._refreshTick
      let arr = this.allTickets.slice()
      const st = this.activeStatus
      if (st === 'pending') arr = arr.filter(t => t.status === 'assigned' || t.status === 'pending')
      else if (st === 'ongoing') arr = arr.filter(t => t.status === 'ongoing')
      else if (st === 'done') arr = arr.filter(t => t.status === 'done')
      if (this.statusFilter) arr = arr.filter(t => t.status === this.statusFilter || (this.statusFilter === 'over' && t.status === 'overdue'))
      if (this.levelFilter) arr = arr.filter(t => t._levelKey === this.levelFilter)
      if (this.onlyUrgent) arr = arr.filter(t => t._levelKey === 'high')
      if (this.keyword) {
        const k = this.keyword.trim().toLowerCase()
        if (k) {
          arr = arr.filter(t => {
            const s = String(t.code || '').toLowerCase() + ' ' +
                      String(t.device_name || '').toLowerCase() + ' ' +
                      String(t.problem || '').toLowerCase() + ' ' +
                      String(t.title || '').toLowerCase()
            return s.includes(k)
          })
        }
      }
      if (this.sortBy === 'sla') arr.sort((a, b) => a.slaPct - b.slaPct)
      else if (this.sortBy === 'level') arr.sort((a, b) => (LEVEL_ORDER[a._levelKey] ?? 5) - (LEVEL_ORDER[b._levelKey] ?? 5))
      else if (this.sortBy === 'created') arr.sort((a, b) => (b._submitTs || 0) - (a._submitTs || 0))
      return arr
    },
    totalPages() { return Math.max(1, Math.ceil(this.filteredTickets.length / this.size)) },
    pagedItems() {
      const s = (this.page - 1) * this.size
      return this.filteredTickets.slice(s, s + this.size)
    },
    urgentCount() {
      return this.allTickets.filter(t =>
        (t.status === 'pending' || t.status === 'assigned') &&
        (t._levelKey === 'high')
      ).length
    },
    pendingCount() { return this.countByStatus('pending') },
    ongoingCount() { return this.countByStatus('ongoing') },
    doneCount()    { return this.countByStatus('done') }
  },
  watch: {
    keyword()       { this.page = 1 },
    onlyUrgent()    { this.page = 1 },
    activeStatus()  { this.page = 1 },
    sortBy()        { this.page = 1 },
    statusFilter()  { this.page = 1 },
    levelFilter()  { this.page = 1 },
    totalPages(p)   { if (this.page > p) this.page = p }
  },
  async created() {
    this._hydrating = true
    const cur = getUser()
    this.meId = (cur && cur.id) ? Number(cur.id) : null
    try {
      await this.loadAll()
    } finally {
      this._hydrating = false
    }
  },
  methods: {
    countByStatus(k) {
      if (k === 'all') return this.allTickets.length
      if (k === 'pending') return this.allTickets.filter(t => t.status === 'pending' || t.status === 'assigned').length
      if (k === 'ongoing') return this.allTickets.filter(t => t.status === 'ongoing').length
      if (k === 'done')    return this.allTickets.filter(t => t.status === 'done').length
      return 0
    },
    slaClass(p)      { return p <= 15 ? 'danger' : p <= 40 ? 'warn' : 'ok' },
    slaTextClass(p)  { return p <= 15 ? 'danger' : p <= 40 ? 'warn' : '' },
    async loadAll() {
      this.loading = true
      try {
        const p = await listTicketsApi({ page: 1, size: 20000, scope: 'mine' }) || {}
        const items = p.items || []
        this.allTickets = items.map(t => _mapTicket(t))
        this._refreshTick++
      } catch (e) {
        _toast('工单加载失败：' + (e.message || '网络异常'), 'error')
      } finally {
        this.loading = false
      }
    },
    _optimisticPatch(id, patch) {
      const idx = this.allTickets.findIndex(t => Number(t.id) === Number(id))
      if (idx >= 0) {
        const merged = { ...this.allTickets[idx], ...patch }
        this.allTickets.splice(idx, 1, merged)
        this._refreshTick++
        return merged
      }
      return null
    },
    async handle(t) {
      const id = t.id
      const saved = this._optimisticPatch(id, { _op: 'accept' })
      try {
        await acceptTicketApi(id)
        this._optimisticPatch(id, {
          status: 'ongoing',
          status_label: '处理中',
          status_cls: 'ongoing',
          _op: null
        })
        _toast('已开始处理：' + (t.code || t.id), 'success')
        setTimeout(() => this.loadAll(), 300)
      } catch (e) {
        if (saved) this._optimisticPatch(id, {
          status: saved.status,
          status_label: saved.status_label,
          status_cls: saved.status_cls,
          _op: null
        })
        _toast('处理失败：' + (e.message || '请重试'), 'error')
      }
    },
    finish(t) {
      this.finishTicket = t
      this.finishForm = { solution: '', parts: '', hours: '', contrib: false }
      this.finishErr = ''
      this.finishVisible = true
    },
    view(t) {
      this.detailTicket = t
      this.detailVisible = true
    },
    closeDetail() {
      this.detailVisible = false
      this.detailTicket = null
    },
    closeFinish() {
      this.finishVisible = false
      this.finishTicket = null
    },
    async submitFinish() {
      const t = this.finishTicket
      if (!t) return
      this.finishErr = ''
      if (!this.finishForm.solution.trim()) {
        this.finishErr = '请填写现场处置步骤及解决方案'
        return
      }
      const id = t.id
      const saved = this._optimisticPatch(id, { _op: 'complete' })
      this.finishSubmitting = true
      try {
        await completeTicketApi(id, this.finishForm.solution.trim())
        const nowTs = Math.floor(Date.now() / 1000)
        this._optimisticPatch(id, {
          status: 'done',
          status_label: '已完成',
          status_cls: 'done',
          slaPct: 100,
          slaText: '已完成',
          solution: this.finishForm.solution.trim(),
          _finishTs: nowTs,
          _op: null
        })
        let contrib = ''
        if (this.finishForm.contrib) {
          try {
            const parts = this.finishForm.parts ? ('更换部件：' + this.finishForm.parts + '\n') : ''
            const hours = this.finishForm.hours ? ('工时：' + this.finishForm.hours + '小时\n') : ''
            const resp = await submitReportApi({
              type: 'case',
              title: (t.device_name ? '【' + t.device_name + '】' : '') + (t.title || '现场处置实践'),
              device: t.device_name || '',
              level: t._levelKey || 'mid',
              question: '原工单问题描述：\n' + (t.problem || t.title || '') +
                '\n\n工单系统派单后，现场按常规思路处理，实际处置方案如下：',
              solution: parts + hours + this.finishForm.solution.trim(),
              ticket_id: String(t.id)
            })
            if (resp && resp.rid) contrib = '（知识报告 ' + resp.rid + ' 已提交审核）'
          } catch (e2) { contrib = '（知识报告提交失败，可稍后手动上报）' }
        }
        this.toast = this.finishForm.contrib
          ? '✅ 工单已完成，知识实践报告已提交审核 ' + contrib
          : '✅ 工单已完成，完成方案已保存'
        setTimeout(() => (this.toast = ''), 4000)
        this.finishVisible = false
        setTimeout(() => this.loadAll(), 400)
      } catch (e) {
        if (saved) this._optimisticPatch(id, {
          status: saved.status,
          status_label: saved.status_label,
          status_cls: saved.status_cls,
          slaPct: saved.slaPct,
          slaText: saved.slaText,
          solution: saved.solution,
          _finishTs: saved._finishTs,
          _op: null
        })
        this.finishErr = '提交失败：' + (e.message || '请重试')
      } finally {
        this.finishSubmitting = false
      }
    },
    async showGuideRecommend(t) {
      this.guideModalTicket = t
      this.guideModalOpen = true
      await this.refreshGuideRecommend()
    },
    async refreshGuideRecommend() {
      if (!this.guideModalTicket) return
      this.guideModalLoading = true
      this.guideModalError = ''
      this.guideModalItems = []
      this.guideModalDynamic = null
      this.guideModalDynamicNote = ''
      try {
        const res = await recommendGuidesForTicketApi(this.guideModalTicket.id)
        this.guideModalItems = (res && res.recommended) || []
        if (res && res.dynamic_guide) {
          this.guideModalDynamic = res.dynamic_guide
          this.guideModalDynamicNote = res.dynamic_guide_note || ''
        }
      } catch (e) {
        this.guideModalError = '推荐加载失败: ' + (e.message || '请重试')
      } finally {
        this.guideModalLoading = false
      }
    },
    goGuideDetail(guideId) {
      const ticketId = this.guideModalTicket?.id
      const path = ticketId ? '/guide?ticket_id=' + ticketId : '/guide'
      this.$router.push(path)
      this.guideModalOpen = false
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
.filter-chip {
  padding: 9px 14px; cursor: pointer; border-radius: var(--radius);
  display: flex; align-items: center; gap: 6px;
  font-size: 0.8125rem; color: var(--text-secondary);
  transition: all var(--duration) var(--ease);
}
.filter-chip:hover { color: var(--accent-red); border-color: var(--border-active); }
.filter-chip.active { background: rgba(239, 68, 68, 0.1); color: var(--accent-red); border-color: rgba(239, 68, 68, 0.35); }

.stats-grid.mini { grid-template-columns: repeat(4, 1fr); gap: 12px; display: grid; margin-bottom: 16px; }

/* 统计卡片：左竖条 + 背景晕染 + data-cat 主题色 */
.stat-card {
  display: flex; align-items: center; gap: 14px;
  position: relative; overflow: hidden;
  padding: 18px 20px;
}
.stat-card::before {
  content: ''; position: absolute; left: 0; top: 0; bottom: 0;
  width: 4px; border-radius: 0 4px 4px 0;
}
.stat-card::after {
  content: ''; position: absolute; right: -30px; bottom: -30px;
  width: 100px; height: 100px; border-radius: 50%;
  opacity: 0.08; pointer-events: none;
}
.stat-card[data-cat="urgent"]::before,
.stat-card[data-cat="urgent"]::after   { background: var(--accent-red); }
.stat-card[data-cat="pending"]::before,
.stat-card[data-cat="pending"]::after { background: var(--accent-orange); }
.stat-card[data-cat="ongoing"]::before,
.stat-card[data-cat="ongoing"]::after { background: var(--primary); }
.stat-card[data-cat="done"]::before,
.stat-card[data-cat="done"]::after    { background: var(--accent-green); }

/* 图标色块 */
.stat-icon {
  width: 52px; height: 52px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.375rem; flex-shrink: 0; position: relative; z-index: 1;
}
.stat-card[data-cat="urgent"] .stat-icon   { color: var(--accent-red);    background: rgba(239,68,68,0.10);  border: 1px solid rgba(239,68,68,0.18); }
.stat-card[data-cat="pending"] .stat-icon  { color: var(--accent-orange); background: rgba(245,158,11,0.10); border: 1px solid rgba(245,158,11,0.18); }
.stat-card[data-cat="ongoing"] .stat-icon  { color: var(--primary);       background: var(--primary-subtle);               border: 1px solid var(--border-active); }
.stat-card[data-cat="done"] .stat-icon     { color: var(--accent-green);  background: rgba(16,185,129,0.10);               border: 1px solid rgba(16,185,129,0.18); }

/* 文案 */
.stat-info { flex: 1; min-width: 0; }
.stat-value { font-size: 1.625rem; font-weight: 700; font-family: 'Orbitron', sans-serif; line-height: 1.1; color: var(--text-primary); }
.stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }
.stat-trend {
  font-size: 0.6875rem; font-family: 'JetBrains Mono', monospace;
  margin-top: 6px; font-weight: 600;
}

/* 加急卡片呼吸红光（仅 urgentCount > 0 时渲染 .is-alert）*/
.stat-card.is-alert {
  animation: alertBreathe 2s ease-in-out infinite;
}
.stat-card.is-alert::before {
  animation: alertBar 2s ease-in-out infinite;
}
.stat-card.is-alert .stat-icon {
  animation: alertIcon 2s ease-in-out infinite;
}
@keyframes alertBreathe {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  50%      { box-shadow: 0 0 22px 4px rgba(239, 68, 68, 0.45); }
}
@keyframes alertBar {
  0%, 100% { opacity: 0.6; }
  50%      { opacity: 1; }
}
@keyframes alertIcon {
  0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
  50%      { box-shadow: 0 0 16px 3px rgba(239, 68, 68, 0.6); }
}

.table-section { padding: 20px; }
.table-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; flex-wrap: wrap; gap: 12px; }
.table-tabs { display: flex; gap: 4px; flex-wrap: wrap; }
.table-tab {
  padding: 7px 16px; border-radius: var(--radius); font-size: 0.8125rem; cursor: pointer;
  color: var(--text-secondary); transition: all var(--duration) var(--ease);
  border: 1px solid transparent;
}
.table-tab:hover { background: var(--primary-subtle); color: var(--text-primary); }
.table-tab.active { background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active); font-weight: 600; }
.tab-count {
  display: inline-block; min-width: 20px; text-align: center; margin-left: 6px;
  padding: 1px 7px; background: var(--bg-deep); border-radius: 999px;
  font-size: 0.6875rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace;
}
.table-tab.active .tab-count { background: var(--primary); color: var(--bg-deep); }

.mini-select { padding: 7px 10px; font-size: 0.75rem; border-radius: var(--radius); background: var(--bg-deep); color: var(--text-primary); border: 1px solid var(--border-subtle); outline: none; }

.data-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.data-table thead th { text-align: left; padding: 10px 12px; background: var(--bg-deep); color: var(--text-muted); font-weight: 600; font-size: 0.75rem; letter-spacing: 0.5px; border-bottom: 1px solid var(--border-subtle); }
.data-table tbody td { padding: 13px 12px; border-bottom: 1px solid var(--border-subtle); color: var(--text-primary); vertical-align: middle; }
.ticket-row:hover td { background: var(--primary-subtle); }
.mono { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--primary); }

.device-cell { display: flex; flex-direction: column; gap: 2px; }
.device-code { font-weight: 600; font-family: 'JetBrains Mono', monospace; }
.device-loc { font-size: 0.6875rem; color: var(--text-muted); }

.desc-cell { max-width: 360px; line-height: 1.5; }
.muted { color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

.level-tag { display: inline-block; padding: 3px 10px; border-radius: 6px; font-size: 0.6875rem; font-weight: 700; letter-spacing: 0.5px; }
.lv-high     { background: rgba(245, 158, 11, 0.14); color: var(--accent-orange); border: 1px solid rgba(245, 158, 11, 0.35); }
.lv-medium   { background: rgba(6, 182, 212, 0.12); color: var(--accent-cyan); border: 1px solid rgba(6, 182, 212, 0.35); }
.lv-low      { background: var(--primary-subtle); color: var(--primary); border: 1px solid var(--border-active); }

.sla-cell { min-width: 140px; }
.sla-bar { height: 5px; background: var(--bg-deep); border-radius: 3px; overflow: hidden; }
.sla-fill { height: 100%; transition: width 0.4s ease; border-radius: 3px; }
.sla-fill.ok { background: var(--accent-green); }
.sla-fill.warn { background: linear-gradient(90deg, var(--accent-orange), #fbbf24); }
.sla-fill.danger { background: linear-gradient(90deg, var(--accent-red), var(--accent-orange)); animation: pulseDanger 1.5s ease-in-out infinite; }
@keyframes pulseDanger { 0%,100% { opacity: 1; } 50% { opacity: 0.65; } }
.sla-text { font-size: 0.6875rem; margin-top: 5px; font-family: 'JetBrains Mono', monospace; color: var(--text-muted); }
.sla-text.warn { color: var(--accent-orange); }
.sla-text.danger { color: var(--accent-red); font-weight: 700; }

.status-pill { display: inline-block; padding: 3px 11px; border-radius: 999px; font-size: 0.6875rem; font-weight: 600; }
.st-pending { background: rgba(245, 158, 11, 0.12); color: var(--accent-orange); }
.st-assigned { background: rgba(139,92,246,0.12); color: var(--accent-purple); }
.st-ongoing { background: rgba(79, 214, 255, 0.12); color: var(--primary); }
.st-done    { background: rgba(0, 255, 136, 0.1); color: var(--accent-green); }
.st-overdue { background: rgba(255,71,87,0.12); color: var(--accent-red); }

.btn-xs { padding: 4px 12px; font-size: 0.6875rem; margin-right: 4px; }
.btn-xs:last-child { margin-right: 0; }
.row-actions { display: flex; align-items: center; gap: 6px; white-space: nowrap; }
.row-actions .btn-xs { margin-right: 0; }
.btn-primary {
  background: var(--primary); color: var(--bg-deep);
  border: 1px solid var(--primary); border-radius: var(--radius);
  font-weight: 600; cursor: pointer; font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.btn-primary:hover { background: var(--primary-dim); border-color: var(--primary-dim); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-success {
  background: linear-gradient(135deg, #34d399, #10b981); color: #052e16;
  border: 1px solid rgba(16,185,129,0.4); border-radius: var(--radius);
  font-weight: 600; cursor: pointer; font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.btn-success:hover { filter: brightness(1.08); box-shadow: 0 4px 14px rgba(16,185,129,0.25); }
.btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-outline {
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  cursor: pointer; font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.btn-outline:hover { border-color: var(--primary-dim); color: var(--text-primary); }

.table-footer {
  margin-top: 14px; display: flex; justify-content: space-between; align-items: center;
  padding: 12px 4px 0; background: transparent; border: none; box-shadow: none;
}
.pagination-info { font-size: 0.75rem; color: var(--text-muted); }
.pagination { display: flex; gap: 6px; }

.skeleton-wrap { padding: 0 12px; display: flex; flex-direction: column; gap: 18px; }
.skeleton-row { display: grid; grid-template-columns: repeat(8, 1fr); gap: 16px; }
.skeleton-row span {
  display: block; height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
.skeleton-row span:nth-child(1) { width: 70%; }
.skeleton-row span:nth-child(2) { width: 85%; }
.skeleton-row span:nth-child(5) { width: 60%; }
.skeleton-row span:nth-child(6) { width: 55%; }
.skeleton-row span:nth-child(7) { width: 75%; }
.skeleton-row span:nth-child(8) { width: 90%; }
@keyframes skeleton-shine { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.finish-mask {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.65); backdrop-filter: blur(6px);
  z-index: 2000; display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.finish-dialog {
  width: 100%; max-width: 600px; max-height: 90vh; min-height: 0;
  display: flex; flex-direction: column; overflow: hidden;
  border: 1px solid var(--border-active); border-radius: var(--radius-lg);
}
.finish-header {
  padding: 18px 24px; display: flex; justify-content: space-between; align-items: flex-start;
  background: linear-gradient(135deg, rgba(16,185,129,0.08), transparent 60%);
  border-bottom: 1px solid var(--border-subtle);
}
.detail-dialog { max-width: 640px; }
.detail-header {
  background: linear-gradient(135deg, rgba(37,99,235,0.12), transparent 60%);
}
.finish-body.detail-body {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.detail-field {
  min-width: 0;
  padding: 11px 12px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.025);
  border: 1px solid var(--border-subtle);
}
.detail-full { grid-column: 1 / -1; }
.detail-label {
  margin-bottom: 6px;
  color: var(--text-muted);
  font-size: 0.75rem;
}
.detail-value {
  color: var(--text-primary);
  font-size: 0.875rem;
  line-height: 1.55;
  word-break: break-word;
}
.detail-value.strong { font-weight: 600; }
.detail-text {
  padding: 10px 12px;
  border-radius: 6px;
  background: rgba(37,99,235,0.05);
  white-space: pre-wrap;
}
.detail-text.solution { background: rgba(16,185,129,0.06); }
.detail-text.remark { background: rgba(245,158,11,0.06); }
.detail-footer {
  display: flex;
  justify-content: flex-end;
  padding: 14px 24px;
  border-top: 1px solid var(--border-subtle);
}
.fh-title { display: flex; align-items: center; gap: 12px; }
.fh-icon { font-size: 1.75rem; }
.fh-big { font-size: 1.0625rem; font-weight: 600; color: var(--text-primary); }
.fh-small { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; }

.kr-close {
  width: 32px; height: 32px; background: transparent; color: var(--text-muted);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  cursor: pointer; font-family: inherit; transition: all var(--duration) var(--ease);
}
.kr-close:hover { color: var(--accent-red); border-color: var(--accent-red); background: rgba(239,68,68,0.1); }

.finish-body { padding: 20px 24px; overflow-y: auto; flex: 1; min-height: 0; display: flex; flex-direction: column; gap: 14px; }
.ticket-detail-dialog { background: var(--bg-surface); }
.ticket-detail-header {
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.12), transparent 60%);
}
.ticket-detail-body { gap: 18px; }
.ticket-detail-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 10px;
}
.ticket-detail-item {
  display: flex; flex-direction: column; gap: 5px; padding: 12px 14px;
  background: rgba(255,255,255,0.025); border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
}
.ticket-detail-item span,
.ticket-detail-label { font-size: 0.75rem; color: var(--text-muted); }
.ticket-detail-item b { font-size: 0.875rem; color: var(--text-primary); font-weight: 600; }
.ticket-detail-section {
  padding: 14px 16px; background: rgba(255,255,255,0.025);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
}
.ticket-detail-section.solution {
  background: rgba(16,185,129,0.06); border-color: rgba(16,185,129,0.22);
}
.ticket-detail-label { margin-bottom: 7px; }
.ticket-detail-content {
  color: var(--text-primary); font-size: 0.875rem; line-height: 1.7;
  white-space: pre-wrap; overflow-wrap: anywhere;
}
.kr-row .kr-label { display: block; font-size: 0.8125rem; color: var(--text-secondary); margin-bottom: 6px; font-weight: 500; }
.kr-label.required::before { content: '*'; color: var(--accent-red); margin-right: 4px; }
.kr-row.kr-double { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.input {
  width: 100%; background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  color: var(--text-primary); padding: 10px 12px; font-family: inherit;
  font-size: 0.875rem; transition: all var(--duration) var(--ease);
  resize: vertical; line-height: 1.6; box-sizing: border-box;
}
.input:focus {
  outline: none; border-color: var(--primary); background: rgba(37,99,235,0.04);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.1);
}
.input::placeholder { color: var(--text-muted); }

.contrib-check {
  display: flex; gap: 14px; padding: 14px 16px; cursor: pointer;
  margin-top: 4px; background: rgba(37,99,235,0.04);
  border: 1px dashed var(--border-active);
  transition: all var(--duration) var(--ease); user-select: none;
  align-items: flex-start;
}
.contrib-check.checked { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.35); }
.cc-box {
  width: 20px; height: 20px; flex-shrink: 0; border-radius: 6px;
  background: var(--bg-deep); border: 1px solid var(--border-subtle);
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px; transition: all var(--duration) var(--ease);
}
.contrib-check.checked .cc-box {
  background: var(--accent-green); border-color: var(--accent-green);
  box-shadow: 0 0 10px rgba(16,185,129,0.4);
}
.cc-check { color: #f0fdf4; font-weight: 900; font-size: 0.8125rem; }
.cc-text { display: flex; flex-direction: column; gap: 3px; }
.cc-text b { font-size: 0.875rem; color: var(--text-primary); }
.cc-text em { font-size: 0.75rem; color: var(--text-secondary); font-style: normal; }

.kr-footer {
  padding: 14px 24px; border-top: 1px solid var(--border-subtle);
  display: flex; justify-content: space-between; align-items: center;
}
.kr-err { font-size: 0.75rem; color: var(--accent-red); font-weight: 500; }
.kr-actions { display: flex; gap: 10px; }

.toast {
  position: fixed; left: 50%; bottom: 40px;
  transform: translateX(-50%); padding: 12px 26px;
  background: var(--accent-green); color: #052e16;

  font-weight: 600; font-size: 0.875rem; border-radius: 999px;
  box-shadow: 0 8px 24px rgba(16,185,129,0.3); z-index: 9999;
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }

/* ====================== 紧凑筛选条 ====================== */
.filter-bar { padding: 10px 14px; margin-bottom: 14px; }
.filter-bar-row { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.filter-spacer { flex: 1; }
.search-box {
  display: flex; align-items: center; gap: 6px;
  background: var(--bg-deep); border: 1px solid var(--border-subtle);
  border-radius: var(--radius); padding: 0 10px;
  color: var(--text-muted); transition: all var(--duration) var(--ease);
  flex: 1; min-width: 180px; max-width: 320px;
}
.search-box:focus-within { border-color: var(--primary); color: var(--primary); }
.search-box input {
  background: transparent; border: none; outline: none; color: var(--text-primary);
  font-size: 0.8125rem; padding: 7px 0; width: 100%; font-family: inherit;
}
.search-box input::placeholder { color: var(--text-muted); }

.seg-control {
  display: inline-flex; background: var(--bg-deep);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  overflow: hidden;
}
.seg-control .seg {
  padding: 6px 14px; background: transparent; border: none;
  color: var(--text-secondary); font-size: 0.8125rem; cursor: pointer;
  font-family: inherit; transition: all var(--duration) var(--ease);
  border-right: 1px solid var(--border-subtle);
  display: inline-flex; align-items: center; gap: 5px;
}
.seg-control .seg:last-child { border-right: none; }
.seg-control .seg:hover { color: var(--text-primary); background: rgba(148,163,184,0.08); }
.seg-control .seg.active { background: var(--primary); color: #fff; font-weight: 600; }
.seg-count {
  min-width: 18px; text-align: center;
  padding: 1px 6px; background: rgba(255,255,255,0.15); border-radius: 999px;
  font-size: 0.625rem; font-family: 'JetBrains Mono', monospace;
}
.seg.active .seg-count { background: rgba(255,255,255,0.25); color: #fff; }

.mini-select { padding: 6px 8px; font-size: 0.75rem; border-radius: var(--radius); background: var(--bg-deep); color: var(--text-primary); border: 1px solid var(--border-subtle); outline: none; }

/* ====================== 紧凑表格 ====================== */
.data-table.compact { font-size: 0.8125rem; }
.data-table.compact thead th { padding: 8px 10px; font-size: 0.75rem; }
.data-table.compact tbody td { padding: 9px 10px; }

/* 作业指导弹窗 */
.guide-btn { border-color: rgba(16,185,129,0.3); color: var(--accent-green); }
.guide-btn:hover { background: rgba(16,185,129,0.08); border-color: var(--accent-green); }
.guide-loading { text-align: center; padding: 40px 16px; color: var(--text-secondary); font-size: 0.875rem; }
.guide-error { text-align: center; padding: 24px; color: var(--accent-red); font-size: 0.875rem; }
.guide-empty { text-align: center; padding: 40px 16px; }
.guide-empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
.guide-empty-text { font-size: 0.9375rem; color: var(--text-secondary); margin-bottom: 8px; }
.guide-empty-desc { font-size: 0.8125rem; color: var(--text-muted); }
.guide-link { color: var(--primary); text-decoration: none; }
.guide-list { display: flex; flex-direction: column; gap: 12px; }
.guide-rec-card { padding: 16px; border: 1px solid var(--border-subtle); transition: all var(--duration) var(--ease); }
.guide-rec-card.guide-exact { border-color: rgba(16,185,129,0.25); background: rgba(16,185,129,0.03); }
.guide-rec-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.guide-rec-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); }
.guide-rec-badge { font-size: 0.625rem; padding: 2px 8px; border-radius: 999px; font-weight: 600; flex-shrink: 0; }
.guide-rec-badge.low { background: rgba(16,185,129,0.12); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
.guide-rec-badge.mid { background: rgba(255,107,53,0.12); color: var(--accent-orange); border: 1px solid rgba(255,107,53,0.2); }
.guide-rec-badge.high { background: rgba(255,71,87,0.12); color: var(--accent-red); border: 1px solid rgba(255,71,87,0.2); }
.guide-rec-meta { display: flex; gap: 12px; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 6px; flex-wrap: wrap; }
.guide-rec-reason { font-size: 0.6875rem; color: var(--accent-green); margin-bottom: 8px; }
.guide-rec-checklist { margin-bottom: 10px; }
.guide-rec-cl-title { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; display: block; margin-bottom: 4px; }
.guide-rec-cl-item { font-size: 0.6875rem; color: var(--text-muted); padding: 2px 0 2px 12px; }
.guide-rec-cl-more { font-size: 0.625rem; color: var(--text-muted); padding: 2px 0 2px 12px; }

.modal-mask {
  position: fixed; inset: 0; background: rgba(4,12,32,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 24px;
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card { width: 100%; max-width: 560px; max-height: 85vh; padding: 0; overflow: hidden; animation: popIn 180ms ease; display: flex; flex-direction: column; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border-subtle); }
@keyframes popIn { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, rgba(16,185,129,0.08), transparent);
}
.modal-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary); font-weight: 600; }
.modal-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: transparent; color: var(--text-secondary); border: 1px solid transparent;
  cursor: pointer; font-size: 0.875rem; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease); font-family: inherit;
}
.modal-close:hover { background: rgba(255,255,255,0.05); border-color: var(--border-subtle); color: var(--text-primary); }
.modal-body { padding: 20px 20px 24px; overflow-y: auto; flex: 1; min-height: 0; }
.btn-xs { padding: 4px 10px; font-size: 0.75rem; border-radius: var(--radius); cursor: pointer; font-family: inherit; border: none; }
.btn-success { background: var(--accent-green); color: #fff; font-weight: 600; }
.btn-success:hover { opacity: 0.9; }

/* 弹窗推荐卡片详情区 */
.rec-section { margin-bottom: 10px; }
.rec-section-title { font-size: 0.75rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.warn-title { color: var(--accent-orange); }
.rec-section-body { font-size: 0.75rem; color: var(--text-secondary); line-height: 1.5; }
.rec-prep-list { display: flex; flex-wrap: wrap; gap: 4px; }
.rec-prep-chip { font-size: 0.6875rem; padding: 2px 8px; border-radius: 4px; background: rgba(255,255,255,0.04); color: var(--text-secondary); border: 1px solid var(--border-subtle); }
.rec-tag-list { display: flex; flex-wrap: wrap; gap: 4px; }
.rec-tag { font-size: 0.6875rem; padding: 2px 8px; border-radius: 4px; max-width: 100%; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.rec-tag-warn { background: rgba(255,107,53,0.08); color: var(--accent-orange); border: 1px solid rgba(255,107,53,0.15); }
.rec-tag-ok { background: rgba(16,185,129,0.08); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.15); }
.rec-tag-more { background: transparent; color: var(--text-muted); border: 1px dashed var(--border-subtle); }
.rec-cl-item { font-size: 0.6875rem; color: var(--text-muted); padding: 2px 0 2px 12px; }
.rec-cl-more { font-size: 0.625rem; color: var(--text-muted); padding: 2px 0 2px 12px; }
.rec-stop-warn { margin-top: 8px; padding: 6px 10px; background: rgba(255,71,87,0.06); border-radius: 4px; font-size: 0.6875rem; color: var(--accent-red); line-height: 1.5; }
.rec-view-btn { display: block; width: 100%; margin-top: 8px; padding: 8px; text-align: center; font-size: 0.75rem; border-radius: var(--radius); background: var(--primary-subtle); color: var(--primary); border: 1px solid transparent; cursor: pointer; font-family: inherit; transition: all var(--duration) var(--ease); }
.rec-view-btn:hover { background: rgba(37,99,235,0.12); border-color: var(--primary-dim); }

/* AI 动态生成流程卡片 */
.dynamic-guide-card {
  margin-top: 16px;
  padding: 0;
  overflow: hidden;
  border: 1px solid rgba(139,92,246,0.3);
  background: linear-gradient(135deg, rgba(139,92,246,0.05), rgba(37,99,235,0.03));
}
.dynamic-guide-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  background: rgba(139,92,246,0.08);
  border-bottom: 1px solid rgba(139,92,246,0.15);
}
.dynamic-guide-icon { font-size: 1.25rem; }
.dynamic-guide-title { font-size: 0.875rem; font-weight: 700; color: var(--text-primary); }
.dynamic-guide-note { font-size: 0.6875rem; color: var(--text-muted); margin-top: 2px; }
.dynamic-guide-body { padding: 14px 16px; }
.dg-title { font-size: 1rem; font-weight: 700; color: var(--text-primary); margin-bottom: 10px; }
.dg-risk { padding: 6px 10px; background: rgba(255,165,2,0.1); border-radius: 6px; font-size: 0.8125rem; color: var(--accent-orange); margin-bottom: 10px; }
.dg-tools { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; margin-bottom: 8px; font-size: 0.8125rem; }
.dg-label { color: var(--text-secondary); font-weight: 500; }
.dg-tool-chip { padding: 2px 8px; background: var(--bg-elevated); border: 1px solid var(--border-subtle); border-radius: 4px; font-size: 0.75rem; color: var(--text-secondary); }
.dg-duration { font-size: 0.8125rem; color: var(--text-muted); margin-bottom: 12px; }
.dg-steps { display: flex; flex-direction: column; gap: 8px; }
.dg-step { display: flex; gap: 10px; }
.dg-step-num { width: 24px; height: 24px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; background: var(--primary); color: #fff; font-size: 0.75rem; font-weight: 700; border-radius: 50%; }
.dg-step-body { flex: 1; min-width: 0; }
.dg-step-content { font-size: 0.8125rem; color: var(--text-primary); line-height: 1.6; }
.dg-step-tip { font-size: 0.75rem; color: var(--text-muted); margin-top: 2px; }
.dg-footer { margin-top: 12px; padding-top: 10px; border-top: 1px dashed var(--border-subtle); font-size: 0.6875rem; color: var(--text-muted); text-align: center; }

.modal-head-actions { display: flex; align-items: center; gap: 6px; }
.modal-refresh-btn {
  width: 28px; height: 28px; border-radius: 50%;
  background: transparent; color: var(--text-secondary); border: 1px solid transparent;
  cursor: pointer; font-size: 0.875rem; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease); font-family: inherit;
}
.modal-refresh-btn:hover { background: rgba(255,255,255,0.05); border-color: var(--border-subtle); color: var(--text-primary); }
.modal-refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }
</style>
