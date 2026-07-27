<template>
  <div class="container">
    <section class="hero">
      <div class="hero-left">
        <div class="role-tag worker">
          <span class="role-tag-icon">🔧</span>
          <span>维修工工作台</span>
        </div>
        <h1 class="hero-title">今天也要加油呀，{{ displayName }} 💪</h1>
        <p class="hero-sub">
          你有 <strong class="num-warn">{{ pendingMine }}</strong> 个待接单 ·
          <strong class="num-ok">{{ ongoingMine }}</strong> 个进行中 ·
          本月已完成 <strong class="num-ok">{{ doneMine }}</strong> 单
        </p>
        <div class="hero-status">
          <span class="status-dot online"></span>
          <span>你目前处于【在岗】状态</span>
          <span class="sep">|</span>
          <span class="status-dot warning"></span>
          <span>{{ highUrgent }} 个加急单需优先处理</span>
        </div>
      </div>
      <div class="hero-right">
        <div class="time-display">
          <div class="time-label">系统时间</div>
          <div class="time-value">{{ currentTime }}</div>
          <div class="date-value">{{ currentDate }}</div>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <div class="stat-card card">
        <div class="stat-icon orange">📌</div>
        <div class="stat-info">
          <div class="stat-value">{{ pendingMine }}</div>
          <div class="stat-label">待处理</div>
          <div class="stat-trend down">含 {{ highUrgent }} 个加急</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon blue">🔄</div>
        <div class="stat-info">
          <div class="stat-value">{{ ongoingMine }}</div>
          <div class="stat-label">进行中</div>
          <div class="stat-trend up">需今日内完成</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ doneMine }}</div>
          <div class="stat-label">本月已完成</div>
          <div class="stat-trend up">团队平均 {{ teamAvg }} 单</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon purple">🏆</div>
        <div class="stat-info">
          <div class="stat-value">{{ onTimeRate }}%</div>
          <div class="stat-label">按时完成率</div>
          <div class="stat-trend up">团队平均 89%</div>
        </div>
      </div>
    </section>

    <section class="quick-section">
      <h2 class="section-title">快捷操作</h2>
      <div class="quick-grid">
        <button class="quick-card card fault-card" @click="openFaultReport">
          <span class="quick-icon">⚠️</span>
          <span class="quick-label">故障设备上报</span>
          <span class="quick-desc">发现设备异常 / 故障一键上报，直接入库故障停机设备</span>
          <span class="quick-cta fault-cta">去上报 →</span>
        </button>
        <router-link :to="{ path: '/search', query: { q: '' } }" class="quick-card card">
          <span class="quick-icon">🔍</span>
          <span class="quick-label">AI 查故障</span>
          <span class="quick-desc">输入故障现象，AI秒出处置方案</span>
          <span class="quick-cta">去检索 →</span>
        </router-link>
        <button class="quick-card card contrib-card" @click="openContrib">
          <span class="quick-icon">📚</span>
          <span class="quick-label">我要贡献方案</span>
          <span class="quick-desc">提交实践经验，帮助更多同事</span>
          <span class="quick-cta contrib-cta">
            <b v-if="myStats.pending">{{ myStats.pending }} 已提交</b>
            <span v-else>去贡献 →</span>
          </span>
        </button>
        <router-link to="/guide" class="quick-card card">
          <span class="quick-icon">📋</span>
          <span class="quick-label">作业指导</span>
          <span class="quick-desc">标准操作规程 SOP + 安全规范</span>
          <span class="quick-cta">查看规程 →</span>
        </router-link>
      </div>
    </section>

    <section class="main-grid">
      <div class="todo-section card">
        <div class="section-header">
          <h2 class="section-title">
            <span class="title-icon">📌</span>
            待处理工单
          </h2>
          <div class="section-actions">
            <button
              v-for="t in todoTabs"
              :key="t.key"
              class="pill-btn"
              :class="{ active: activeTab === t.key }"
              @click="activeTab = t.key; page = 1"
              type="button"
            >{{ t.label }}<span class="pill-num">{{ t.count }}</span></button>
            <router-link to="/tickets" class="more-link">查看全部 →</router-link>
          </div>
        </div>

        <div class="todo-list">
          <div v-if="loading" class="todo-loading">
            <div class="skeleton-wrap">
              <div v-for="i in 3" :key="i" class="sk-todo"><span></span><span></span><span></span><span></span></div>
            </div>
          </div>
          <div
            v-for="o in pagedTodos"
            :key="o.id"
            class="todo-item"
            :class="{ urgent: o.priority === 'high' }"
          >
            <div class="todo-left">
              <div class="todo-pri" :class="'p-' + o.priority">
                {{ priorityText(o.priority) }}
              </div>
              <div class="todo-main">
                <div class="todo-head">
                  <span class="todo-id mono">{{ o.code || ('WO-' + o.id) }}</span>
                  <span v-if="o.priority === 'high'" class="todo-urgent">⚡ 加急</span>
                </div>
                <div class="todo-title">{{ o.title }}</div>
                <div class="todo-meta">
                  <span>◈ {{ o.device_name || '未关联设备' }}</span>
                  <span class="dot">·</span>
                  <span>{{ o.createdText }}</span>
                </div>
                <div class="todo-deadline" :class="{ ot: isOT(o) }">
                  ⏱ 预计截止：{{ o.deadlineText || '未设置' }}
                  <span v-if="isOT(o)" class="ot-badge">临近超时</span>
                </div>
              </div>
            </div>
            <div class="todo-actions">
              <button class="act-btn primary" :disabled="o._op" @click="acceptOrder(o)">
                {{ o._op === 'accept' ? '处理中…' : '开始处理' }}
              </button>
              <button class="act-btn" @click="askAI(o)">AI 辅助</button>
              <button class="act-btn guide-btn" @click="showGuideRecommend(o)">作业指导</button>
            </div>
          </div>
          <div v-if="!loading && todoList.length === 0" class="todo-empty">
            <div class="empty-icon">🎉</div>
            <div class="empty-title">太棒了！当前没有待处理工单</div>
            <div class="empty-desc">你可以去「我的工单」查看进行中或已完成的工单</div>
          </div>
        </div>

        <div v-if="todoList.length > size" class="pagination">
          <div class="muted pagination-info">共 {{ todoList.length }} 条 · 第 {{ page }} / {{ totalPages }} 页</div>
          <div class="pagination-ctrl">
            <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page=1">首页</button>
            <button class="btn btn-outline btn-xs" :disabled="page<=1" @click="page--">上一页</button>
            <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page++">下一页</button>
            <button class="btn btn-outline btn-xs" :disabled="page>=totalPages" @click="page=totalPages">末页</button>
          </div>
        </div>
      </div>

      <div class="side-grid">
        <div class="card side-card">
          <div class="section-header">
            <h2 class="section-title"><span class="title-icon">🏅</span>本月团队榜单</h2>
          </div>
          <div class="rank-list">
            <div v-for="(r, i) in ranking" :key="r.name" class="rank-item" :class="{ me: r.me }">
              <div class="rank-no" :class="'r' + (i + 1)">{{ i + 1 }}</div>
              <div class="rank-av">{{ r.name.charAt(0) }}</div>
              <div class="rank-info">
                <div class="rank-name">{{ r.name }}<span v-if="r.me" class="me-tag">我</span></div>
                <div class="rank-sub">{{ r.skill }}</div>
              </div>
              <div class="rank-num mono">{{ r.done }}</div>
            </div>
          </div>
        </div>

        <div class="card side-card">
          <div class="section-header">
            <h2 class="section-title"><span class="title-icon">✅</span>我最近完成</h2>
            <router-link to="/tickets" class="more-link">全部 →</router-link>
          </div>
          <div class="recent-list">
            <div v-for="h in recentDone" :key="h.id" class="recent-item">
              <div class="recent-dot ok"></div>
              <div class="recent-body">
                <div class="recent-title">{{ h.title }}</div>
                <div class="recent-meta">
                  <span>{{ h.device_name || '通用' }}</span>
                  <span class="dot">·</span>
                  <span>{{ h.finishText }}</span>
                </div>
              </div>
            </div>
            <div v-if="!loading && recentDone.length === 0" class="muted center" style="padding:24px 0;font-size:0.75rem;">
              暂无完成记录
            </div>
          </div>
        </div>
      </div>
    </section>

    <div v-if="reportOpen" class="modal-mask" @click="reportOpen = false">
      <div class="modal-card card" @click.stop>
        <div class="modal-head">
          <h3>提交维修报告：{{ orderForReport && orderForReport.title }}</h3>
          <button class="modal-close" @click="reportOpen = false" type="button">✕</button>
        </div>
        <div class="modal-body">
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
              <input v-model="finishForm.parts" class="input" placeholder="如：303型高温轴承 ×1" type="text" />
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
              <b>📝 此方案已验证有效，同步贡献给知识库</b>
              <em>由管理员审核后入库案例库 / 作业指导，帮助更多同事</em>
            </span>
          </label>
          <div v-if="finishErr" class="kr-err">{{ finishErr }}</div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-outline" @click="reportOpen = false">取消</button>
          <button class="btn btn-success" @click="fakeSubmit" :disabled="finishSubmitting">
            {{ finishSubmitting ? '提交中…' : '确认提交' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 故障设备上报弹窗 -->
    <div v-if="faultReportOpen" class="modal-mask" @click="faultReportOpen = false">
      <div class="modal-card fault-modal card" @click.stop>
        <div class="modal-head">
          <h3>⚠️ 故障设备上报</h3>
          <button class="modal-close" @click="faultReportOpen = false" type="button">✕</button>
        </div>
        <div class="modal-body">
          <!-- 设备选择：可输入 + 自定义下拉列表 -->
          <div class="fault-row device-select-row">
            <label class="fault-label required">设备名称</label>
            <input v-model="faultForm.name" name="fault_dev_name" class="input" placeholder="输入或选择设备名称" autocomplete="off" @focus="deviceListShow = true" @input="onDeviceInput" @blur="setTimeout(() => deviceListShow = false, 200)" />
            <div v-if="deviceListShow && filteredDevices.length" class="device-dropdown">
              <div v-for="d in filteredDevices" :key="d.id" class="device-dropdown-item" @mousedown.prevent="selectDevice(d)">
                <span class="dd-code">{{ d.code }}</span>
                <span class="dd-name">{{ d.name }}</span>
              </div>
            </div>
          </div>

          <!-- 设备信息（选中已有设备后自动填充，选"其他"时手动填写） -->
          <div class="fault-device-info">
            <div class="fault-row fault-row-2">
              <div><label class="fault-label required">设备编号</label><input v-model="faultForm.code" class="input" placeholder="如：MC-999" /></div>
              <div>
                <label class="fault-label required">设备类型</label>
                <select v-model="faultForm.tag" class="input">
                  <option value="机械">机械</option>
                  <option value="电气">电气</option>
                  <option value="液压">液压</option>
                  <option value="仪表">仪表</option>
                  <option value="安全">安全</option>
                  <option value="综合">综合</option>
                </select>
              </div>
            </div>
            <div class="fault-row fault-row-2">
              <div><label class="fault-label required">所在区域</label><input v-model="faultForm.location" class="input" placeholder="如：车间 A / 3号线" /></div>
              <div><label class="fault-label">型号/规格</label><input v-model="faultForm.spec" class="input" placeholder="如：SKF-6308" /></div>
            </div>
            <div class="fault-row">
              <label class="fault-label required">设备状态</label><input v-model="faultForm.device_status" class="input" placeholder="如：故障停机" autocomplete="off" />
            </div>
          </div>

          <!-- 故障描述 -->
          <div class="fault-row">
            <label class="fault-label required">故障现象详细说明</label>
            <textarea v-model="faultForm.desc" class="input" rows="4" placeholder="详细描述故障现象：设备启动后持续异响，温度超过 70℃，空载运行电流超标..." autocomplete="new-password"></textarea>
          </div>

          <!-- 附件上传 -->
          <div class="fault-row">
            <label class="fault-label">附件上传（选填，多文件，单文件≤10MB）</label>
            <div class="attach-area">
              <label class="btn btn-outline btn-xs attach-picker">
                📷 选择文件
                <input ref="faultAttachInput" type="file" multiple accept="image/jpeg,image/png,image/webp,application/pdf" @change="handleFaultAttach" />
              </label>
              <span class="attach-hint">{{ faultAttachFiles.length }} 个文件已选</span>
            </div>
            <div v-if="faultAttachFiles.length" class="attach-list">
              <div v-for="(f, fi) in faultAttachFiles" :key="fi" class="attach-item">
                <span class="attach-name">{{ f.name }}</span>
                <button type="button" class="btn btn-xs btn-danger" @click="removeAttach(fi)">删除</button>
              </div>
            </div>
          </div>

          <!-- 自动填充信息 -->
          <div class="fault-row fault-auto-info">
            <span>📋 上报人：{{ currentUser }}</span>
            <span>🕐 上报时间：{{ currentReportTime }}</span>
          </div>

          <div v-if="faultErr" class="kr-err">{{ faultErr }}</div>
        </div>
        <div class="modal-foot">
          <button class="btn btn-outline" @click="faultReportOpen = false">取消</button>
          <button class="btn btn-warning" @click="submitFaultReport" :disabled="faultSubmitting">
            {{ faultSubmitting ? '提交中…' : '提交上报' }}
          </button>
        </div>
      </div>
    </div>

    <div v-if="modalOpen" class="modal-mask" @click="modalOpen = false">
      <div class="modal-card card" @click.stop>
        <div class="modal-head">
          <h3>{{ modalTitle }}</h3>
          <button class="modal-close" @click="modalOpen = false" type="button">✕</button>
        </div>
        <div class="modal-body">
          <div class="placeholder-box">
            <div class="placeholder-icon">🚧</div>
            <div class="placeholder-title">功能开发中</div>
            <div class="placeholder-desc">「{{ modalTitle }}」模块为占位演示，后续可接入真实后端 API。</div>
          </div>
        </div>
      </div>
    </div>

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
          <div v-else-if="guideModalItems.length === 0" class="guide-empty">
            <div class="guide-empty-icon">📭</div>
            <div class="guide-empty-text">暂未找到匹配的作业指导</div>
            <div class="guide-empty-desc">可前往<a href="/guide" class="guide-link">作业指导库</a>浏览全部规程</div>
          </div>
          <div v-else class="guide-list">
            <div
              v-for="(item, gi) in guideModalItems"
              :key="gi"
              class="guide-rec-card card"
              :class="{ 'guide-exact': item.match_reason.includes('精确') }"
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

              <!-- 作业前准备（浓缩） -->
              <div v-if="item.guide.preparation && item.guide.preparation.length" class="rec-section">
                <div class="rec-section-title">🔧 作业前准备</div>
                <div class="rec-prep-list">
                  <span v-for="(p, pi) in item.guide.preparation" :key="pi" class="rec-prep-chip">{{ p.item }}: {{ p.detail }}</span>
                </div>
              </div>

              <!-- 安全控制点（浓缩为标签） -->
              <div v-if="item.guide.safety_control && item.guide.safety_control.length" class="rec-section">
                <div class="rec-section-title warn-title">⚠️ 安全控制点</div>
                <div class="rec-tag-list">
                  <span v-for="(sc, si) in item.guide.safety_control.slice(0, 3)" :key="si" class="rec-tag rec-tag-warn">{{ sc }}</span>
                  <span v-if="item.guide.safety_control.length > 3" class="rec-tag rec-tag-more">+{{ item.guide.safety_control.length - 3 }}</span>
                </div>
              </div>

              <!-- 验收标准（浓缩为标签） -->
              <div v-if="item.guide.acceptance_criteria && item.guide.acceptance_criteria.length" class="rec-section">
                <div class="rec-section-title">✅ 验收标准</div>
                <div class="rec-tag-list">
                  <span v-for="(ac, ai) in item.guide.acceptance_criteria.slice(0, 3)" :key="ai" class="rec-tag rec-tag-ok">{{ ac }}</span>
                  <span v-if="item.guide.acceptance_criteria.length > 3" class="rec-tag rec-tag-more">+{{ item.guide.acceptance_criteria.length - 3 }}</span>
                </div>
              </div>

              <!-- 合规校验项预览 -->
              <div v-if="item.guide.checklist && item.guide.checklist.length" class="rec-section">
                <div class="rec-section-title">📋 合规校验项（{{ item.guide.checklist.length }}项）</div>
                <div v-for="(chk, ci) in item.guide.checklist.slice(0, 3)" :key="ci" class="rec-cl-item">✓ {{ chk }}</div>
                <div v-if="item.guide.checklist.length > 3" class="rec-cl-more">+{{ item.guide.checklist.length - 3 }} 项</div>
              </div>

              <!-- 停止条件警告 -->
              <div v-if="item.guide.stop_conditions && item.guide.stop_conditions.length" class="rec-stop-warn">
                🚫 如现场存在：{{ item.guide.stop_conditions.slice(0, 2).join('、') }} 等，请暂停执行并评估
              </div>

              <button class="rec-view-btn" @click="goGuideDetail(item.guide.id)">📄 查看完整指导详情 →</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <KnowledgeReport
      :visible="reportVisible"
      source="manual"
      @update:visible="v => reportVisible = v"
      @submitted="onReportSubmitted"
    />

    <transition name="toast">
      <div v-if="toast" class="toast">{{ toast }}</div>
    </transition>
  </div>
</template>

<script>
import { getUser } from '../utils/auth'
import { fetchUserStats, getUserStats } from '../utils/knowledge'
import KnowledgeReport from '../components/KnowledgeReport.vue'
import {
  listTicketsApi, acceptTicketApi, completeTicketApi, submitReportApi,
  listDevicesApi, reportFaultApi, recommendGuidesForTicketApi
} from '../utils/api'
import { toast as _toast } from '../utils/request'

const LEVEL_TO_PRIORITY = { low: 'low', mid: 'mid', high: 'high', critical: 'high' }
const LEVEL_LABEL = { low: '低', mid: '中', high: '高（加急）', critical: '高（加急）' }

function _tsToText(ts) {
  if (!ts) return '-'
  const d = new Date(Number(ts) * 1000)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  const sameDay = d.toDateString() === now.toDateString()
  const yest = new Date(now.getTime() - 86400000)
  const isYest = d.toDateString() === yest.toDateString()
  const hh = d.getHours().toString().padStart(2, '0')
  const mm = d.getMinutes().toString().padStart(2, '0')
  if (sameDay && diff < 86400000) return '今日 ' + hh + ':' + mm
  if (isYest) return '昨日 ' + hh + ':' + mm
  return (d.getMonth() + 1) + '月' + d.getDate() + '日 ' + hh + ':' + mm
}

function _deadlineFromTs(ts, level) {
  if (!ts) return { text: '未设置', ot: false }
  const start = new Date(Number(ts) * 1000).getTime()
  const addH = { low: 48, mid: 24, high: 6, critical: 6 }[level] || 24
  const dl = start + addH * 3600 * 1000
  const now = Date.now()
  const remainMs = dl - now
  const d = new Date(dl)
  const text = (d.getMonth() + 1) + '/' + d.getDate() + ' ' +
    d.getHours().toString().padStart(2, '0') + ':' +
    d.getMinutes().toString().padStart(2, '0')
  const ot = remainMs > 0 && remainMs < 2 * 3600 * 1000
  return { text, ot }
}

function _mapTicket(t, meId) {
  let level = t.level || 'mid'
  if (level === 'critical') level = 'high'
  const dl = _deadlineFromTs(t.submit_time_ts, level)
  const isAssignedToMe = t.assignee_id && Number(t.assignee_id) === Number(meId)
  return {
    id: t.id,
    code: t.code || ('WO-' + t.id),
    title: t.title,
    device_name: t.device_name,
    priority: LEVEL_TO_PRIORITY[level] || 'mid',
    level: level,
    level_label: t.level_label || LEVEL_LABEL[level] || '中',
    status: t.status === 'pending' && isAssignedToMe ? 'pending'
          : t.status === 'pending' && !isAssignedToMe ? 'pending'
          : (t.status === 'processing' || t.status === 'doing' || t.status === 'overdue' || t.status === 'over') ? 'ongoing'
          : (t.status === 'completed' || t.status === 'done') ? 'done'
          : t.status || 'pending',
    status_label: t.status_label || '-',
    submitter_name: t.submitter_name || '系统',
    assignee_name: t.assignee_name,
    problem: t.problem,
    solution: t.solution,
    createdText: _tsToText(t.submit_time_ts),
    deadlineText: dl.text,
    _deadlineOT: dl.ot,
    finishText: _tsToText(t.finish_time_ts),
    costText: (t.submit_time_ts && t.finish_time_ts)
      ? (Math.max(0.1, (t.finish_time_ts - t.submit_time_ts) / 3600).toFixed(1) + 'h')
      : '-',
    _op: null
  }
}

export default {
  name: 'WorkerDashboard',
  components: { KnowledgeReport },
  data() {
    return {
      currentTime: '',
      currentDate: '',
      timer: null,
      activeTab: 'all',
      page: 1,
      size: 5,
      loading: false,
      _hydrating: true,
      _refreshTick: 0,
      allTickets: [],
      meId: null,
      reportOpen: false,
      orderForReport: null,
      finishForm: { solution: '', parts: '', hours: '', contrib: true },
      finishSubmitting: false,
      finishErr: '',
      modalOpen: false,
      modalTitle: '',
      reportVisible: false,
      toast: '',
      myStats: { total: 0, pending: 0, approved: 0, rejected: 0 },
      _statsLoading: false,
      _statsHydrated: false,
      faultReportOpen: false,
      faultSubmitting: false,
      faultErr: '',
      faultAttachFiles: [],
      deviceList: [],
      faultForm: { device_id: null, desc: '', code: '', name: '', tag: '机械', location: '', spec: '', device_status: '故障停机' },
      deviceListShow: false,
      guideModalOpen: false,
      guideModalLoading: false,
      guideModalError: '',
      guideModalTicket: null,
      guideModalItems: []
    }
  },
  computed: {
    displayName() {
      const u = getUser()
      const base = (u && (u.fullname || u.username)) || ''
      if (!base) return '李师傅'
      const surname = base.charAt(0)
      return surname + '师傅'
    },
    myActive() {
      const meId = this.meId
      return this.allTickets.filter(t => t.status === 'pending')
    },
    pendingMine() { return this.myActive.length },
    ongoingMine() { return this.allTickets.filter(t => t.status === 'ongoing').length },
    highUrgent() { return this.myActive.filter(t => t.priority === 'high').length },
    doneMine() {
      return this.allTickets.filter(t => t.status === 'completed' || t.status === 'done').length
    },
    avgTime() {
      const done = this.allTickets.filter(t => t.status === 'completed' || t.status === 'done')
      if (!done.length) return '3.6'
      let total = 0, n = 0
      for (const t of done) {
        if (t.costText && t.costText.endsWith('h')) {
          const v = parseFloat(t.costText)
          if (!isNaN(v)) { total += v; n++ }
        }
      }
      return n ? (total / n).toFixed(1) : '3.6'
    },
    onTimeRate() {
      const done = this.allTickets.filter(t => t.status === 'completed' || t.status === 'done')
      if (!done.length) return 96
      const ok = done.filter(t => !t._deadlineOT).length
      return Math.round(ok / done.length * 100)
    },
    teamAvg() {
      return Math.max(10, Math.round(this.doneMine * 0.8))
    },
    totalWorkers() { return 8 },
    rank() {
      const me = this.doneMine
      let better = 0
      const seed = [34, 28, 25, 22, 20, 17, 15, 12]
      for (const s of seed) if (s > me) better++
      return Math.min(8, better + 1)
    },
    todoTabs() {
      const all = this.myActive.length
      const urgent = this.myActive.filter(t => t.priority === 'high').length
      return [
        { key: 'all',      label: '全部',   count: all },
        { key: 'urgent',   label: '加急',   count: urgent }
      ]
    },
    todoList() {
      if (this.activeTab === 'urgent') return this.myActive.filter(t => t.priority === 'high')
      return this.myActive
    },
    totalPages() { return Math.max(1, Math.ceil(this.todoList.length / this.size)) },
    pagedTodos() {
      const s = (this.page - 1) * this.size
      return this.todoList.slice(s, s + this.size)
    },
    ranking() {
      const me = this.displayName
      const arr = [
        { name: '赵工',   skill: '输送 / 焊接',     done: 34 },
        { name: me,       skill: '旋转机械 / 液压', done: this.doneMine, me: true },
        { name: '王师傅', skill: '液压 / 润滑',     done: 25 },
        { name: '钱师傅', skill: '仪表 / 校准',     done: 22 },
        { name: '孙师傅', skill: '电气 / 变频器',   done: 20 }
      ]
      arr.sort((a, b) => b.done - a.done)
      return arr
    },
    recentDone() {
      const done = this.allTickets.filter(t => t.status === 'completed' || t.status === 'done')
        .sort((a, b) => (b.finish_time_ts || 0) - (a.finish_time_ts || 0))
      return done.slice(0, 5)
    }
  },
  watch: {
    activeTab() { this.page = 1 },
    totalPages(p) { if (this.page > p) this.page = p }
  },
  async created() {
    this._hydrating = true
    const cur = getUser()
    this.meId = (cur && cur.id) ? Number(cur.id) : null
    window.addEventListener('equipai-knowledge-changed', this.refreshStats)
    try {
      await Promise.all([
        this.refreshStats(),
        this.loadAll()
      ])
    } finally {
      this._hydrating = false
    }
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer)
    window.removeEventListener('equipai-knowledge-changed', this.refreshStats)
  },
  mounted() {
    this.updateTime()
    this.timer = setInterval(this.updateTime, 1000)
  },
  methods: {
    async refreshStats({ force = false } = {}) {
      const u = getUser()
      const username = (u && u.username) || 'worker'
      if (this._statsLoading && !force) return
      this._statsLoading = true
      try {
        this.myStats = await fetchUserStats(username)
      } catch (_) {
        this.myStats = getUserStats(username)
      } finally {
        this._statsLoading = false
        this._statsHydrated = true
      }
    },
    async loadAll() {
      this.loading = true
      try {
        const p = await listTicketsApi({ page: 1, size: 20000, scope: 'mine' }) || {}
        const items = p.items || []
        this.allTickets = items.map(t => _mapTicket(t, this.meId))
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
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
      this.currentDate = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
    },
    priorityText(p) {
      return { high: '急', mid: '中', low: '低' }[p] || '中'
    },
    isOT(o) { return !!o._deadlineOT },
    async acceptOrder(o) {
      const id = o.id
      const saved = this._optimisticPatch(id, { _op: 'accept' })
      try {
        await acceptTicketApi(id)
        this._optimisticPatch(id, { status: 'ongoing', _op: null })
        _toast('已接单：' + (o.title || ''), 'success')
        setTimeout(() => this.loadAll(), 300)
      } catch (e) {
        if (saved) this._optimisticPatch(id, { status: saved.status, _op: null })
        _toast('接单失败：' + (e.message || '重试'), 'error')
      }
    },
    submitReport(o) {
      this.orderForReport = o
      this.finishForm = { solution: '', parts: '', hours: '', contrib: true }
      this.finishErr = ''
      this.reportOpen = true
    },
    async fakeSubmit() {
      const o = this.orderForReport
      if (!o) return
      this.finishErr = ''
      if (!this.finishForm.solution.trim()) {
        this.finishErr = '请填写现场处置步骤及解决方案'
        return
      }
      const id = o.id
      const saved = this._optimisticPatch(id, { _op: 'complete' })
      this.finishSubmitting = true
      try {
        await completeTicketApi(id, this.finishForm.solution.trim())
        this._optimisticPatch(id, {
          status: 'completed',
          finish_time_ts: Math.floor(Date.now() / 1000),
          solution: this.finishForm.solution,
          _op: null
        })
        let contribMsg = ''
        if (this.finishForm.contrib) {
          try {
            const user = getUser()
            const parts = this.finishForm.parts ? ('更换部件：' + this.finishForm.parts + '\n') : ''
            const hours = this.finishForm.hours ? ('工时：' + this.finishForm.hours + '小时\n') : ''
            const resp = await submitReportApi({
              type: 'case',
              title: (o.device_name ? '【' + o.device_name + '】' : '') + (o.title || '现场处置实践'),
              device: o.device_name || '',
              level: o.priority || 'mid',
              question: '原工单问题描述：\n' + (o.problem || o.title || '') +
                '\n\n工单系统派单后，现场按常规思路处理，实际处置方案如下：',
              solution: parts + hours + this.finishForm.solution.trim(),
              ticket_id: String(o.id)
            })
            if (resp && resp.rid) contribMsg = '（知识报告 ' + resp.rid + ' 已提交审核）'
          } catch (e2) { /* 静默 */ contribMsg = '（知识报告提交失败，可稍后手动上报）' }
        }
        _toast('工单完成上报 ' + contribMsg, 'success')
        this.toast = '工单完成上报 ' + contribMsg
        setTimeout(() => (this.toast = ''), 4000)
        this.reportOpen = false
        setTimeout(() => this.loadAll(), 400)
      } catch (e) {
        if (saved) this._optimisticPatch(id, { status: saved.status, solution: saved.solution, _op: null })
        this.finishErr = '提交失败：' + (e.message || '请重试')
      } finally {
        this.finishSubmitting = false
      }
    },
    askAI(o) {
      this.$router.push({ path: '/search', query: { q: o.title } })
    },
    viewDetail(o) {
      const lines = [
        '工单号：' + (o.code || o.id),
        '标题：' + o.title,
        '设备：' + (o.device_name || '-'),
        '等级：' + (o.level_label || '-'),
        '状态：' + (o.status_label || o.status),
        '创建：' + o.createdText,
        '预计截止：' + (o.deadlineText || '-'),
        '',
        '问题描述：' + (o.problem || '（未填写）')
      ]
      if (o.solution) lines.push('', '解决方案：' + o.solution)
      alert(lines.join('\n'))
    },
    openContrib() { this.reportVisible = true },
    onReportSubmitted(rec) {
      this.toast = '✅ 报告「' + (rec.rid || rec.id) + '」提交成功，管理员将尽快审核'
      setTimeout(() => (this.toast = ''), 3500)
    },
    openReport() { this.modalTitle = '维修上报（发现异常一键上报）'; this.modalOpen = true },
    openMyProfile() { this.modalTitle = '我的绩效'; this.modalOpen = true },
    get selectedDevice() {
      return (this.deviceList || []).find(d => d.id === this.faultForm.device_id) || {}
    },
    get currentUser() {
      const u = getUser()
      return (u && (u.fullname || u.username)) || '未知'
    },
    get currentReportTime() {
      const now = new Date()
      return now.toLocaleString('zh-CN')
    },
    statusLabel(s) {
      return ({ normal: '正常运行', repairing: '维修中', down: '故障停机' })[s] || s
    },
    async showGuideRecommend(o) {
      this.guideModalTicket = o
      this.guideModalOpen = true
      await this.refreshGuideRecommend()
    },
    async refreshGuideRecommend() {
      if (!this.guideModalTicket) return
      this.guideModalLoading = true
      this.guideModalError = ''
      this.guideModalItems = []
      try {
        const res = await recommendGuidesForTicketApi(this.guideModalTicket.id)
        this.guideModalItems = (res && res.recommended) || []
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
    },
    async openFaultReport() {
      this.faultErr = ''
      this.faultAttachFiles = []
      this.faultForm = { device_id: '__other__', desc: '', code: '', name: '', tag: '机械', location: '', spec: '', device_status: '故障停机' }
      this.faultReportOpen = true
      try {
        const res = await listDevicesApi({ page: 1, size: 2000 })
        const items = (res && (res.items || res.data && res.data.items)) || []
        this.deviceList = Array.isArray(items) ? items.filter(d => d && d.id) : []
      } catch (e) { /* ignore */ }
    },
    get filteredDevices() {
      if (!this.faultForm) return []
      const list = Array.isArray(this.deviceList) ? this.deviceList.filter(d => d && d.id) : []
      const kw = (this.faultForm.name || '').trim().toLowerCase()
      if (!kw) return list
      return list.filter(d =>
        (d.name || '').toLowerCase().includes(kw) || (d.code || '').toLowerCase().includes(kw)
      )
    },
    onDeviceInput() {
      const match = Array.isArray(this.deviceList) ? this.deviceList.find(d => d && d.id && d.name === this.faultForm.name) : null
      if (match) {
        this.faultForm.device_id = match.id
        this.faultForm.code = match.code || ''
        this.faultForm.tag = match.tag || '机械'
        this.faultForm.location = match.location || ''
        this.faultForm.spec = match.spec || ''
        this.faultForm.device_status = match.status === 'down' ? '故障停机' : match.status === 'repairing' ? '维修中' : '故障停机'
      } else {
        this.faultForm.device_id = null
      }
    },
    selectDevice(d) {
      this.faultForm.device_id = d.id
      this.faultForm.name = d.name || ''
      this.faultForm.code = d.code || ''
      this.faultForm.tag = d.tag || '机械'
      this.faultForm.location = d.location || ''
      this.faultForm.spec = d.spec || ''
      this.faultForm.device_status = d.status === 'down' ? '故障停机' : d.status === 'repairing' ? '维修中' : '故障停机'
      this.deviceListShow = false
    },
    async handleFaultAttach(event) {
      const files = Array.from(event.target.files || [])
      const okTypes = ['image/jpeg', 'image/png', 'image/webp', 'application/pdf']
      for (const f of files) {
        if (!okTypes.includes(f.type)) { this.faultErr = '仅支持 JPG/PNG/WebP/PDF'; continue }
        if (f.size > 10 * 1024 * 1024) { this.faultErr = '文件不能超过 10MB'; continue }
        if (!this.faultAttachFiles.find(x => x.name === f.name && x.size === f.size)) {
          // Object.freeze 防止 Vue 2 响应式系统破坏 File 对象导致上传失败
          this.faultAttachFiles.push(Object.freeze(f))
        }
      }
      this.faultErr = ''
      if (this.$refs.faultAttachInput) this.$refs.faultAttachInput.value = ''
    },
    removeAttach(idx) { this.faultAttachFiles.splice(idx, 1) },
    async submitFaultReport() {
      this.faultErr = ''
      if (!this.faultForm.name.trim()) { this.faultErr = '请填写设备名称'; return }
      if (!this.faultForm.desc.trim()) { this.faultErr = '请填写故障现象描述'; return }
      this.faultSubmitting = true
      try {
        await reportFaultApi(this.faultForm, this.faultAttachFiles)
        this.faultReportOpen = false
        this.faultAttachFiles = []
        _toast('✓ 故障已上报，设备已标记为故障停机，已通知维修管理员', 'success')
      } catch (e) {
        this.faultErr = '提交失败：' + (e.message || '请重试')
      } finally {
        this.faultSubmitting = false
      }
    }
  }
}
</script>

<style scoped>
.hero { display: flex; justify-content: space-between; align-items: center; padding: 32px 0 28px; gap: 32px; flex-wrap: wrap; }
.role-tag {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border-active);
  margin-bottom: 14px;
}
.role-tag { background: var(--primary-subtle); color: var(--primary); }
.role-tag.worker { background: rgba(16,185,129,0.10); color: var(--accent-green); border-color: rgba(16,185,129,0.2); }
.role-tag-icon { filter: drop-shadow(0 0 4px currentColor); }

.hero-title { font-size: 1.75rem; margin-bottom: 8px; }
.hero-sub { color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 14px; }
.hero-sub strong { font-family: 'JetBrains Mono', monospace; font-weight: 700; }
.hero-sub .num-warn { color: var(--accent-orange); }
.hero-sub .num-ok { color: var(--accent-green); }
.hero-status { display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; color: var(--text-secondary); flex-wrap: wrap; }
.hero-status .sep { color: var(--text-muted); margin: 0 4px; }
.hero-status b { color: var(--accent-green); font-family: 'JetBrains Mono', monospace; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.online { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
.status-dot.warning { background: var(--accent-orange); box-shadow: 0 0 8px var(--accent-orange); }
.time-display { text-align: right; }
.time-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
.time-value { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: var(--accent-green); font-weight: 700; line-height: 1.2; }
.date-value { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }

.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
.stat-card { display: flex; align-items: center; gap: 14px; }
.stat-icon {
  width: 52px; height: 52px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center; font-size: 1.375rem; flex-shrink: 0;
}
.stat-icon.blue { color: var(--primary); background: var(--primary-subtle); border: 1px solid rgba(37,99,235,0.12); }
.stat-icon.green { color: var(--accent-green); background: rgba(16,185,129,0.10); border: 1px solid rgba(16,185,129,0.15); }
.stat-icon.orange { color: var(--accent-orange); background: rgba(255,107,53,0.1); border: 1px solid rgba(255,107,53,0.15); }
.stat-icon.purple { color: var(--accent-cyan); background: rgba(6,182,212,0.10); border: 1px solid rgba(6,182,212,0.15); }
.stat-info { flex: 1; }
.stat-value { font-size: 1.625rem; font-weight: 700; font-family: 'Orbitron', sans-serif; line-height: 1.1; }
.stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }
.stat-trend { font-size: 0.6875rem; font-family: 'JetBrains Mono', monospace; margin-top: 6px; }
.stat-trend.up { color: var(--accent-green); }
.stat-trend.down { color: var(--accent-orange); }

.quick-section { margin-bottom: 24px; }
.section-title {
  font-size: 1rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px;
  font-weight: 600; margin: 0 0 16px; display: flex; align-items: center; gap: 8px;
}
.title-icon { filter: drop-shadow(0 0 4px var(--primary-glow)); }
.quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; }
.quick-card {
  display: flex; flex-direction: column; gap: 8px; text-decoration: none; color: inherit;
  padding: 22px 20px; cursor: pointer; text-align: left; font-family: inherit;
  border: 1px solid var(--border-subtle); border-radius: var(--radius-lg);
  background: var(--bg-card, rgba(255,255,255,0.02));
  transition: all var(--duration) var(--ease);
}
.quick-card:hover { transform: translateY(-2px); border-color: var(--accent-green); box-shadow: 0 8px 24px rgba(16,185,129,0.08); }
.fault-card { border-left: 3px solid #ffc107; }
.fault-card:hover { border-color: #ffc107; box-shadow: 0 8px 24px rgba(255,193,7,0.15); }
.fault-cta { color: #ffc107; }
.fault-modal { max-width: 560px; background: var(--bg-surface) !important; }
.fault-modal .modal-body { overflow-y: auto; flex: 1; min-height: 0; }
.device-select-row { position: relative; }
.device-dropdown { position: absolute; top: 100%; left: 0; right: 0; z-index: 100; max-height: 200px; overflow-y: auto; background: var(--bg-elevated); border: 1px solid var(--border-active); border-radius: var(--radius); margin-top: 4px; box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.device-dropdown-item { display: flex; gap: 10px; padding: 8px 12px; cursor: pointer; transition: background 0.15s; }
.device-dropdown-item:hover { background: var(--primary-subtle); }
.dd-code { font-size: 0.75rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; min-width: 80px; }
.dd-name { font-size: 0.8125rem; color: var(--text-primary); }
.fault-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 12px; }
.fault-row-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.fault-label { font-size: 0.8125rem; color: var(--text-secondary); font-weight: 500; }
.fault-label.required::after { content: '*'; color: var(--accent-red); margin-left: 4px; }
.fault-hint { font-size: 0.75rem; color: var(--text-muted); padding: 8px 0; }
.fault-device-info { background: rgba(255,255,255,0.02); border: 1px solid var(--border-subtle); border-radius: var(--radius); padding: 12px; margin-bottom: 12px; }
.fault-static { font-size: 0.8125rem; color: var(--text-primary); padding: 6px 0; }
.fault-auto-info { display: flex; gap: 16px; font-size: 0.75rem; color: var(--text-muted); padding: 8px 0; }
.attach-area { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.attach-picker { position: relative; overflow: hidden; cursor: pointer; margin: 0; }
.attach-picker input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
.attach-hint { font-size: 0.75rem; color: var(--text-muted); }
.btn-xs { padding: 4px 10px; font-size: 0.75rem; }
.quick-icon { font-size: 1.75rem; color: var(--accent-green); margin-bottom: 4px; }
.quick-label { font-size: 0.9375rem; font-weight: 600; }
.quick-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5; flex: 1; }
.quick-cta { font-size: 0.75rem; color: var(--accent-green); font-weight: 500; margin-top: 6px; }
.contrib-card {
  border: 1px solid rgba(255, 165, 2, 0.3);
  background: linear-gradient(135deg, rgba(255, 165, 2, 0.08), rgba(0, 212, 255, 0.05));
}
.contrib-card:hover {
  border-color: rgba(255, 165, 2, 0.5);
  box-shadow: 0 8px 24px rgba(255, 165, 2, 0.12);
}
.contrib-card .quick-icon { color: var(--accent-orange); }
.contrib-card .quick-cta { color: var(--accent-orange); }
.contrib-cta b {
  padding: 2px 10px;
  background: rgba(255, 165, 2, 0.15);
  border-radius: 999px;
  color: var(--accent-orange);
  border: 1px solid rgba(255, 165, 2, 0.3);
}

.toast {
  position: fixed; left: 50%; bottom: 40px;
  transform: translateX(-50%);
  padding: 12px 26px;
  background: var(--accent-green);
  color: #052e16;
  font-weight: 600; font-size: 0.875rem;
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(16,185,129,0.3);
  z-index: 9999;
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }

.main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.section-actions { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.pill-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
  border-radius: 999px; font-size: 0.75rem; font-weight: 500; color: var(--text-secondary);
  background: transparent; border: 1px solid var(--border-subtle);
  cursor: pointer; font-family: inherit; transition: all var(--duration) var(--ease);
}
.pill-btn:hover { color: var(--text-primary); border-color: var(--primary-dim); }
.pill-btn.active { color: var(--accent-green); background: rgba(16,185,129,0.10); border-color: rgba(16,185,129,0.25); }
.pill-num {
  display: inline-block; min-width: 18px; padding: 0 5px; height: 18px; line-height: 18px;
  border-radius: 9px; font-size: 0.625rem; font-family: 'JetBrains Mono', monospace;
  background: rgba(255,255,255,0.06); text-align: center;
}
.pill-btn.active .pill-num { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.more-link { font-size: 0.75rem; color: var(--primary); text-decoration: none; cursor: pointer; }
.more-link:hover { color: var(--primary-dim); }

.todo-section { padding: 22px 20px; min-width: 0; }
.todo-list { display: flex; flex-direction: column; gap: 12px; }
.todo-item {
  display: flex; justify-content: space-between; gap: 16px;
  padding: 16px; border-radius: var(--radius-lg);
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border-subtle);
  transition: all var(--duration) var(--ease);
}
.todo-item:hover { border-color: var(--primary-dim); }
.todo-item.urgent {
  border-color: rgba(255,71,87,0.3);
  background: linear-gradient(90deg, rgba(255,71,87,0.06), transparent);
}
.todo-left { display: flex; gap: 12px; min-width: 0; flex: 1; }
.todo-pri {
  width: 38px; height: 38px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-size: 0.875rem; flex-shrink: 0;
}
.todo-pri.p-high { background: rgba(255,71,87,0.15); color: var(--accent-red); border: 1px solid rgba(255,71,87,0.25); }
.todo-pri.p-mid { background: rgba(255,107,53,0.12); color: var(--accent-orange); border: 1px solid rgba(255,107,53,0.2); }
.todo-pri.p-low { background: rgba(16,185,129,0.10); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.15); }

.todo-main { flex: 1; min-width: 0; }
.todo-head { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; }
.todo-id { font-size: 0.6875rem; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; letter-spacing: 0.5px; }
.todo-urgent {
  font-size: 0.625rem; padding: 2px 6px;
  background: rgba(255,71,87,0.15); color: var(--accent-red);
  border: 1px solid rgba(255,71,87,0.25); border-radius: 2px;
  font-weight: 700; letter-spacing: 0.5px;
}
.todo-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); margin-bottom: 4px; }
.todo-meta { font-size: 0.75rem; color: var(--text-muted); display: flex; gap: 4px; flex-wrap: wrap; }
.todo-meta .dot { color: var(--text-muted); opacity: 0.6; }
.todo-deadline { margin-top: 8px; font-size: 0.75rem; color: var(--text-secondary); display: flex; align-items: center; gap: 8px; }
.todo-deadline.ot { color: var(--accent-red); font-weight: 600; }
.ot-badge {
  font-size: 0.625rem; padding: 1px 6px; border-radius: 2px;
  background: rgba(255,71,87,0.15); color: var(--accent-red);
  border: 1px solid rgba(255,71,87,0.25);
}

.todo-actions { display: flex; flex-direction: column; gap: 6px; justify-content: center; flex-shrink: 0; }
.act-btn {
  padding: 6px 14px; font-size: 0.75rem; border-radius: var(--radius);
  cursor: pointer; font-family: inherit; transition: all var(--duration) var(--ease);
  border: 1px solid var(--border-subtle); background: transparent; color: var(--text-secondary);
}
.act-btn:hover { border-color: var(--primary-dim); color: var(--text-primary); }
.act-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.act-btn.primary { background: var(--primary); color: var(--bg-deep); border-color: var(--primary); font-weight: 600; }
.act-btn.primary:hover { background: var(--primary-dim); }
.act-btn.success { background: var(--accent-green); color: #052e16; border-color: var(--accent-green); font-weight: 600; }
.act-btn.success:hover { opacity: 0.9; }

.todo-empty { padding: 48px 12px; text-align: center; }
.empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
.empty-title { font-size: 1rem; font-weight: 700; color: var(--accent-green); margin-bottom: 4px; }
.empty-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.6; }

.todo-loading { padding: 12px 4px; }
.skeleton-wrap { display: flex; flex-direction: column; gap: 18px; }
.sk-todo { display: grid; grid-template-columns: 38px 2fr 1fr; gap: 14px; }
.sk-todo span {
  display: block; height: 14px; border-radius: 6px;
  background: linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(37,99,235,0.08) 50%, rgba(255,255,255,0.03) 100%);
  background-size: 200% 100%;
  animation: skeleton-shine 1.4s ease-in-out infinite;
}
.sk-todo span:nth-child(1) { height: 38px; border-radius: 10px; }
.sk-todo span:nth-child(2) { width: 90%; }
.sk-todo span:nth-child(3) { width: 70%; margin: auto 0; }
.sk-todo span:nth-child(4) { grid-column: 2/3; width: 75%; height: 12px; }
@keyframes skeleton-shine {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.side-grid { display: flex; flex-direction: column; gap: 16px; }
.side-card { padding: 22px 20px; }

.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: var(--radius);
  transition: all var(--duration) var(--ease);
}
.rank-item:hover { background: rgba(255,255,255,0.03); }
.rank-item.me { background: rgba(16,185,129,0.06); border: 1px solid rgba(16,185,129,0.15); }
.rank-no {
  width: 24px; height: 24px; border-radius: 6px;
  display: flex; align-items: center; justify-content: center;
  font-family: 'Orbitron', sans-serif; font-weight: 800; font-size: 0.8125rem;
  color: var(--text-secondary); background: rgba(255,255,255,0.04); flex-shrink: 0;
}
.rank-no.r1 { color: var(--bg-deep); background: linear-gradient(135deg, #ffcc33, #ffa726); }
.rank-no.r2 { color: var(--bg-deep); background: linear-gradient(135deg, #e0e0e0, #9e9e9e); }
.rank-no.r3 { color: var(--bg-deep); background: linear-gradient(135deg, #d4a373, #a0522d); }
.rank-av {
  width: 32px; height: 32px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  background: var(--primary-subtle); color: var(--primary);
  font-weight: 700; font-family: 'Orbitron', sans-serif; font-size: 0.8125rem;
  flex-shrink: 0;
}
.rank-item.me .rank-av { background: rgba(16,185,129,0.15); color: var(--accent-green); }
.rank-info { flex: 1; min-width: 0; }
.rank-name { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 6px; }
.me-tag {
  font-size: 0.625rem; padding: 1px 6px; border-radius: 2px;
  background: rgba(16,185,129,0.15); color: var(--accent-green);
  border: 1px solid rgba(16,185,129,0.25); font-weight: 600;
}
.rank-sub { font-size: 0.6875rem; color: var(--text-muted); margin-top: 2px; }
.rank-num { font-size: 0.9375rem; font-weight: 700; color: var(--text-primary); }

.recent-list { display: flex; flex-direction: column; }
.recent-item {
  display: flex; align-items: flex-start; gap: 10px;
  padding: 10px 0; border-bottom: 1px solid var(--border-subtle);
}
.recent-item:last-child { border-bottom: none; }
.recent-dot { width: 8px; height: 8px; border-radius: 50%; margin-top: 6px; flex-shrink: 0; }
.recent-dot.ok { background: var(--accent-green); box-shadow: 0 0 6px var(--accent-green); }
.recent-body { flex: 1; min-width: 0; }
.recent-title { font-size: 0.8125rem; color: var(--text-primary); font-weight: 500; }
.recent-meta { font-size: 0.6875rem; color: var(--text-muted); margin-top: 3px; display: flex; gap: 4px; flex-wrap: wrap; }
.recent-meta .dot { opacity: 0.6; }
.center { text-align: center; }

.modal-mask {
  position: fixed; inset: 0; background: rgba(4,12,32,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 24px;
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card { width: 100%; max-width: 560px; max-height: 85vh; padding: 0; overflow: hidden; animation: popIn 180ms ease; display: flex; flex-direction: column; }
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
.modal-foot { padding: 14px 20px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: flex-end; gap: 10px; }

.placeholder-box { text-align: center; }
.placeholder-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.8; }
.placeholder-title { font-size: 1.125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.placeholder-desc { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }

.kr-row { margin-bottom: 14px; }
.kr-row.kr-double { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.kr-label {
  display: block;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}
.kr-label.required::before {
  content: '*';
  color: var(--accent-red);
  margin-right: 4px;
}
.kr-err { font-size: 0.75rem; color: var(--accent-red); font-weight: 500; margin-top: 10px; }

.input {
  width: 100%;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-primary);
  padding: 10px 12px;
  font-family: inherit;
  font-size: 0.875rem;
  transition: all var(--duration) var(--ease);
  resize: vertical;
  line-height: 1.6;
  box-sizing: border-box;
}
.input:focus {
  outline: none;
  border-color: var(--primary);
  background: rgba(37,99,235,0.04);
  box-shadow: 0 0 0 3px rgba(37,99,235,0.10);
}
.input::placeholder { color: var(--text-muted); }

.contrib-check {
  display: flex;
  gap: 14px;
  padding: 14px 16px;
  cursor: pointer;
  margin-top: 4px;
  background: rgba(37,99,235,0.04);
  border: 1px dashed var(--border-active);
  transition: all var(--duration) var(--ease);
  user-select: none;
  align-items: flex-start;
}
.contrib-check.checked {
  background: rgba(16,185,129,0.08);
  border-color: rgba(16,185,129,0.35);
}
.cc-box {
  width: 20px; height: 20px; flex-shrink: 0;
  border-radius: 6px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  display: flex; align-items: center; justify-content: center;
  margin-top: 1px;
  transition: all var(--duration) var(--ease);
}
.contrib-check.checked .cc-box {
  background: var(--accent-green);
  border-color: var(--accent-green);
  box-shadow: 0 0 10px rgba(16,185,129,0.4);
}
.cc-check {
  color: #052e16;
  font-weight: 900;
  font-size: 0.8125rem;
}
.cc-text { display: flex; flex-direction: column; gap: 3px; }
.cc-text b { font-size: 0.875rem; color: var(--text-primary); }
.cc-text em { font-size: 0.75rem; color: var(--text-secondary); font-style: normal; }

.btn-outline {
  padding: 8px 18px;
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.8125rem;
  transition: all var(--duration) var(--ease);
}
.btn-outline:hover { border-color: var(--primary-dim); color: var(--text-primary); }
.btn-success {
  background: linear-gradient(135deg, var(--accent-green), #10b981);
  color: #052e16;
  border: 1px solid rgba(16,185,129,0.3);
  font-weight: 600;
  padding: 8px 20px;
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  transition: all var(--duration) var(--ease);
}
.btn-success:hover { filter: brightness(1.08); box-shadow: 0 4px 14px rgba(16,185,129,0.2); }
.btn-success:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-warning { background: linear-gradient(135deg, #ffc107, #ff9800); color: #1a1a2e; border: 1px solid rgba(255,193,7,0.3); font-weight: 600; padding: 8px 20px; border-radius: var(--radius); cursor: pointer; font-family: inherit; font-size: 0.875rem; transition: all var(--duration) var(--ease); }
.btn-warning:hover { filter: brightness(1.08); box-shadow: 0 4px 14px rgba(255,193,7,0.25); }
.btn-warning:disabled { opacity: 0.5; cursor: not-allowed; }

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
.guide-rec-card {
  padding: 16px; border: 1px solid var(--border-subtle);
  transition: all var(--duration) var(--ease);
}
.guide-rec-card.guide-exact {
  border-color: rgba(16,185,129,0.25);
  background: rgba(16,185,129,0.03);
}
.guide-rec-header { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 8px; }
.guide-rec-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); }
.guide-rec-badge {
  font-size: 0.625rem; padding: 2px 8px; border-radius: 999px; font-weight: 600; flex-shrink: 0;
}
.guide-rec-badge.low { background: rgba(16,185,129,0.12); color: var(--accent-green); border: 1px solid rgba(16,185,129,0.2); }
.guide-rec-badge.mid { background: rgba(255,107,53,0.12); color: var(--accent-orange); border: 1px solid rgba(255,107,53,0.2); }
.guide-rec-badge.high { background: rgba(255,71,87,0.12); color: var(--accent-red); border: 1px solid rgba(255,71,87,0.2); }
.guide-rec-meta { display: flex; gap: 12px; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 6px; flex-wrap: wrap; }
.guide-rec-reason { font-size: 0.6875rem; color: var(--accent-green); margin-bottom: 8px; }
.guide-rec-checklist { margin-bottom: 10px; }
.guide-rec-cl-title { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; display: block; margin-bottom: 4px; }
.guide-rec-cl-item { font-size: 0.6875rem; color: var(--text-muted); padding: 2px 0 2px 12px; }
.guide-rec-cl-more { font-size: 0.625rem; color: var(--text-muted); padding: 2px 0 2px 12px; }
.btn-sm { padding: 6px 14px; font-size: 0.75rem; border-radius: var(--radius); cursor: pointer; border: none; font-family: inherit; }

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
.modal-head-actions { display: flex; align-items: center; gap: 6px; }
.modal-refresh-btn {
  width: 28px; height: 28px; border-radius: 50%;
  background: transparent; color: var(--text-secondary); border: 1px solid transparent;
  cursor: pointer; font-size: 0.875rem; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease); font-family: inherit;
}
.modal-refresh-btn:hover { background: rgba(255,255,255,0.05); border-color: var(--border-subtle); color: var(--text-primary); }
.modal-refresh-btn:disabled { opacity: 0.4; cursor: not-allowed; }

.pagination {
  display: flex; justify-content: space-between; align-items: center;
  padding: 14px 0 0; margin-top: 16px; border-top: 1px dashed var(--border-subtle);
}
.pagination-info { font-size: 0.75rem; }
.pagination-ctrl { display: flex; gap: 6px; }
.btn-xs { padding: 4px 10px; font-size: 0.6875rem; }

.muted { color: var(--text-muted); font-size: 0.75rem; font-family: 'JetBrains Mono', monospace; }

@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
}
</style>