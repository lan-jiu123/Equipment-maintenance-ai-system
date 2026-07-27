<template>
  <div class="container">
    <!-- 欢迎 + 顶部状态 -->
    <section class="hero">
      <div class="hero-left">
        <div class="role-tag">
          <span class="role-tag-icon">☗</span>
          <span>维修管理员工作台</span>
        </div>
        <h1 class="hero-title">你好，{{ displayName }} 👋</h1>
        <p class="hero-sub">今日概览：全车间 {{ totalOrders }} 个工单 · {{ pendingCount }} 个待派单 · {{ ongingCount }} 个进行中</p>
        <div class="hero-status">
          <span class="status-dot online"></span>
          <span>团队在线 {{ onlineWorkers }}/{{ totalWorkers }}</span>
          <span class="sep">|</span>
          <span>SLA 达标率 <strong>{{ slaRate }}%</strong></span>
          <span class="sep">|</span>
          <span class="status-dot warning"></span>
          <span>{{ highPriority }} 个高优先级待处理</span>
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

    <!-- 核心统计卡 -->
    <section class="stats-grid">
      <div class="stat-card card" data-cat="total">
        <div class="stat-icon">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ totalOrders }}</div>
          <div class="stat-label">本月工单总数</div>
          <div class="stat-trend up">↑ 实时</div>
        </div>
      </div>
      <div class="stat-card card" :class="{ 'is-alert': pendingCount > 0 }" data-cat="pending">
        <div class="stat-icon">⏳</div>
        <div class="stat-info">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待派单</div>
          <div class="stat-trend down">需尽快处理</div>
        </div>
      </div>
      <div class="stat-card card" data-cat="done">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ doneCount }}</div>
          <div class="stat-label">本月已完成</div>
          <div class="stat-trend up">累计进度</div>
        </div>
      </div>
      <div class="stat-card card" data-cat="team">
        <div class="stat-icon">🧑‍🔧</div>
        <div class="stat-info">
          <div class="stat-value">{{ totalWorkers }}</div>
          <div class="stat-label">在岗维修工</div>
          <div class="stat-trend up">团队总览</div>
        </div>
      </div>
    </section>

    <!-- 快捷操作 -->
    <section class="quick-section">
      <h2 class="section-title">快捷操作</h2>
      <div class="quick-grid">
        <button class="quick-card card" data-color="primary" @click="openDispatch()">
          <span class="quick-icon">📤</span>
          <span class="quick-body">
            <span class="quick-row">
              <span class="quick-label">新建 / 派单</span>
              <span class="quick-cta">立即派单 →</span>
            </span>
            <span class="quick-desc">创建工单并指派给合适的维修工</span>
          </span>
        </button>
        <router-link to="/users" class="quick-card card" data-color="green">
          <span class="quick-icon">👥</span>
          <span class="quick-body">
            <span class="quick-row">
              <span class="quick-label">人员管理</span>
              <span class="quick-cta">查看团队 →</span>
            </span>
            <span class="quick-desc">维修工排班、技能标签、绩效统计</span>
          </span>
        </router-link>
        <button class="quick-card card kr-quick" data-color="cyan" @click="goToReviewPending">
          <span class="quick-icon">📝</span>
          <span class="quick-body">
            <span class="quick-row">
              <span class="quick-label">知识报告审核</span>
              <span class="quick-cta">进入审核 →</span>
            </span>
            <span class="quick-desc">审核员工提交的实践方案，入库知识库</span>
          </span>
        </button>
        <router-link to="/search" class="quick-card card" data-color="violet">
          <span class="quick-icon">◎</span>
          <span class="quick-body">
            <span class="quick-row">
              <span class="quick-label">AI 辅助诊断</span>
              <span class="quick-cta">开始检索 →</span>
            </span>
            <span class="quick-desc">把棘手故障扔给 AI 获取结构化方案</span>
          </span>
        </router-link>
      </div>
    </section>

    <!-- 顶部主 Tab 切换 -->
    <section class="main-tabs-wrap">
      <div class="main-tabs card">
        <button
          v-for="t in mainTabs"
          :key="t.key"
          class="main-tab"
          :class="{ active: activeMainTab === t.key }"
          @click="activeMainTab = t.key"
        >
          <span class="mt-icon">{{ t.icon }}</span>
          <span class="mt-label">{{ t.label }}</span>
          <span v-if="t.count > 0" class="mt-badge" :class="t.badgeCls">{{ t.count }}</span>
        </button>
      </div>
    </section>

    <!-- 工单列表（全宽）-->
    <section class="order-section card" v-if="activeMainTab === 'order'">
      <div class="section-header">
        <h2 class="section-title">
          <span class="title-icon">📋</span>
          全部工单
        </h2>
        <div class="section-actions">
          <button
            v-for="t in orderTabs"
            :key="t.key"
            class="pill-btn"
            :class="{ active: activeOrderTab === t.key }"
            @click="activeOrderTab = t.key"
            type="button"
          >{{ t.label }}<span class="pill-num">{{ t.count }}</span></button>
        </div>
      </div>
      <div class="order-table">
        <div class="order-head order-row">
          <div class="col-id">工单号</div>
          <div class="col-title">标题 / 设备</div>
          <div class="col-pri">优先级</div>
          <div class="col-worker">处理人</div>
          <div class="col-status">状态</div>
          <div class="col-time">创建</div>
          <div class="col-action">操作</div>
        </div>
        <div v-if="ticketsLoading" class="order-empty">
          <div class="skeleton-wrap" style="padding:12px 8px;display:flex;flex-direction:column;gap:14px;">
            <div v-for="i in 5" :key="i" class="sk-todo" style="display:grid;grid-template-columns:140px 2fr 80px 120px 90px 100px 140px;gap:12px;">
              <span v-for="j in 7" :key="j" style="display:block;height:14px;border-radius:6px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
            </div>
          </div>
        </div>
        <template v-else>
          <div v-for="o in filteredOrders" :key="o.id" class="order-row">
            <div class="col-id mono">{{ o.code }}</div>
            <div class="col-title">
              <div class="order-title">{{ o.title }}</div>
              <div class="order-device">◈ {{ o.device_name || '未关联设备' }}</div>
            </div>
            <div class="col-pri">
              <span class="pri-chip" :class="'pri-' + o._priorityKey">{{ priorityText(o._priorityKey) }}</span>
            </div>
            <div class="col-worker">
              <div class="worker-assign">
                <span class="worker-avatar">{{ (o.assignee_name || '—').charAt(0) }}</span>
                <span class="worker-name">{{ o.assignee_name || '待分配' }}</span>
              </div>
            </div>
            <div class="col-status">
              <span class="status-chip" :class="'st-' + o._statusKey">{{ o.status_label || statusText(o._statusKey) }}</span>
            </div>
            <div class="col-time mono" :class="{ overtime: o._isOvertime }">{{ o.createdText }}</div>
            <div class="col-action">
              <button v-if="o.status === 'pending' || o.status === 'assigned'" class="row-btn primary" :disabled="o._op" @click="handleOrder(o)">
                {{ o.assignee_id ? '改派' : '派单' }}
              </button>
              <span v-else class="row-btn-placeholder" aria-hidden="true"></span>
              <button class="row-btn" @click="previewOrder(o)">详情</button>
              <button class="row-btn danger" @click="deleteOrder(o)">删除</button>
            </div>
          </div>
          <div v-if="filteredOrders.length === 0" class="order-empty">当前筛选下无工单 🎉</div>
        </template>
      </div>
    </section>

    <!-- 团队负载（全宽）-->
    <section class="team-section card" v-if="activeMainTab === 'team'">
      <div class="section-header">
        <h2 class="section-title"><span class="title-icon">👥</span>维修工负载</h2>
        <button class="more-link" style="border:none;background:transparent;cursor:pointer;" @click="loadAllUsers(true)">刷新 ↻</button>
      </div>
      <div class="team-list">
        <div v-if="usersLoading" class="todo-empty">
          <div class="skeleton-wrap" style="padding:4px 0;display:flex;flex-direction:column;gap:18px;">
            <div v-for="i in 5" :key="i" style="display:grid;grid-template-columns:40px 1fr 160px;gap:14px;align-items:center;">
              <span style="display:block;height:40px;width:40px;border-radius:50%;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
              <span style="display:block;height:14px;border-radius:6px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
              <span style="display:block;height:32px;border-radius:6px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
            </div>
          </div>
        </div>
        <template v-else>
          <div v-for="w in workers" :key="w.id" class="team-item">
            <div class="team-left">
              <div class="team-avatar" :class="'av-' + (w._colorIdx % 6 + 1)">{{ (w.fullname || w.username || 'U').charAt(0) }}</div>
              <div class="team-meta">
                <div class="team-name">{{ w.fullname || w.username }}</div>
                <div class="team-skills">
                  <span v-if="w._roleLabel" class="skill-tag">{{ w._roleLabel }}</span>
                  <span class="skill-tag">工号 {{ w.id }}</span>
                </div>
              </div>
            </div>
            <div class="team-load">
              <div class="load-top">
                <span>总工单 <b>{{ w._total || 0 }}</b></span>
                <span class="mono">{{ w._load }}%</span>
              </div>
              <div class="load-track">
                <div class="load-fill" :class="loadClass(w._load)" :style="{ width: w._load + '%' }"></div>
              </div>
              <div class="load-detail">
                <span class="ld-pending">待处理 {{ w._pending || 0 }}</span>
                <span class="ld-ongoing">进行中 {{ w._ongoing || 0 }}</span>
                <span class="ld-done">已完成 {{ w._done || 0 }}</span>
              </div>
            </div>
          </div>
          <div v-if="workers.length === 0" class="order-empty">暂无团队成员数据</div>
        </template>
      </div>
    </section>

    <!-- 知识报告审核面板 -->
    <section ref="knowledgePanel" class="knowledge-panel" v-if="activeMainTab === 'knowledge'">
      <div class="knowledge-layout">
        <!-- 报告列表 -->
        <div class="kr-list card">
          <div class="section-header">
            <h2 class="section-title">
              <span class="title-icon">📑</span>
              报告列表
            </h2>
            <div class="section-actions">
              <button
                v-for="t in krTabs"
                :key="t.key"
                class="pill-btn"
                :class="{ active: activeKrTab === t.key }"
                @click="activeKrTab = t.key"
              >{{ t.label }}<span class="pill-num">{{ t.count }}</span></button>
              <button class="pill-btn" @click="loadAllReports(true)" style="margin-left:4px;">刷新 ↻</button>
            </div>
          </div>
          <div class="kr-list-body">
            <div v-if="reportsLoading" style="padding:12px 0;">
              <div class="skeleton-wrap" style="display:flex;flex-direction:column;gap:16px;">
                <div v-for="i in 4" :key="i" style="padding:14px 16px;border-radius:8px;border:1px solid var(--border-subtle);">
                  <div style="display:flex;justify-content:space-between;gap:12px;margin-bottom:8px;">
                    <span style="display:block;height:16px;width:60%;border-radius:6px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
                    <span style="display:block;height:18px;width:70px;border-radius:999px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
                  </div>
                  <span style="display:block;height:12px;width:80%;border-radius:6px;margin-bottom:4px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
                  <span style="display:block;height:12px;width:45%;border-radius:6px;background:linear-gradient(90deg, rgba(255,255,255,0.03) 0%, rgba(148,163,184,0.08) 50%, rgba(255,255,255,0.03) 100%);background-size:200% 100%;animation:skeleton-shine 1.4s ease-in-out infinite;"></span>
                </div>
              </div>
            </div>
            <template v-else>
              <div
                v-for="r in filteredReports"
                :key="r.id"
                class="kr-list-item"
                :class="{ active: selectedReport && selectedReport.id === r.id, pending: r.status === 'pending' }"
                @click="selectReport(r)"
              >
                <div class="kli-head">
                  <div class="kli-title">{{ r.title }}</div>
                  <span class="cr-status" :class="'st-' + r.status">{{ r.status_label || statusLabel(r.status) }}</span>
                </div>
                <div class="kli-meta">
                  <span class="kli-source">{{ sourceLabel(r.source) }}</span>
                  <span class="kli-user">🧑 {{ r.submitter_name || '未知用户' }}</span>
                  <span class="kli-device" v-if="r.device">◈ {{ r.device }}</span>
                </div>
                <div class="kli-foot">
                  <span class="kli-type" :class="'type-' + r.type">
                    {{ r.type === 'case' ? '📚 案例库' : r.type === 'guide' ? '📖 作业指导' : '📋 未分类' }}
                  </span>
                  <span class="kli-time">{{ formatTime(r.submit_time_ts) }}</span>
                </div>
              </div>
              <div v-if="filteredReports.length === 0" class="kr-empty">
                <div class="ke-icon">🎉</div>
                <div class="ke-title">没有{{ activeKrTab === 'pending' ? '待审核' : '' }}报告</div>
                <div class="ke-desc" v-if="activeKrTab === 'pending'">当前所有知识报告已处理完毕</div>
                <div class="ke-desc" v-else>切换到其他标签页查看更多</div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </section>

    <!-- 派单弹窗 -->
    <div v-if="dispatchOpen" class="modal-mask" @click.self="closeDispatch">
      <div class="modal-card card" @click.stop>
        <div class="modal-head">
          <h3>{{ dispatchMode === 'create' ? '📤 新建工单并派单' : '🎯 派单：' + (dispatchTicket && dispatchTicket.title) }}</h3>
          <button class="modal-close" @click="closeDispatch" type="button">✕</button>
        </div>
        <div v-if="dispatchErr" class="dispatch-alert" role="alert" aria-live="assertive">
          <span class="dispatch-alert-icon">✕</span>
          <span>{{ dispatchErr }}</span>
        </div>
        <div class="modal-body" style="padding: 20px 24px; display:flex; flex-direction:column; gap:14px;">
          <div v-if="dispatchMode === 'create'" class="kr-row">
            <label class="kr-label required">工单标题</label>
            <input v-model="dispatchForm.title" class="input" minlength="2" maxlength="255" placeholder="如：3#离心泵振动值持续偏高" />
          </div>
          <div v-if="dispatchMode === 'create'" class="kr-row kr-double">
            <div>
              <label class="kr-label">关联设备</label>
              <input v-model="dispatchForm.device_name" class="input" placeholder="如：离心泵 P-103" />
            </div>
            <div>
              <label class="kr-label required">类别</label>
              <select v-model="dispatchForm.category" class="input" style="cursor:pointer;">
                <option value="" disabled>请选择类别...</option>
                <option value="机械">机械</option>
                <option value="电气">电气</option>
                <option value="安全">安全</option>
                <option value="仪表">仪表</option>
                <option value="液压">液压</option>
              </select>
            </div>
          </div>
          <div v-if="dispatchMode === 'create'" class="kr-row">
            <label class="kr-label required">问题描述</label>
            <textarea v-model="dispatchForm.problem" class="input" rows="3" minlength="5" placeholder="描述故障现象、检测到的参数、初步判断（至少5个字符）..."></textarea>
          </div>

          <div class="kr-row kr-double">
            <div>
              <label class="kr-label" :class="{ required: dispatchMode !== 'create' }">
                指派维修工<span v-if="dispatchMode === 'create'">（可选）</span>
              </label>
              <select v-model="dispatchForm.assignee_id" class="input" style="cursor:pointer;">
                <option :value="''" disabled>请选择维修工...</option>
                <option v-for="u in workers" :key="u.id" :value="String(u.id)">
                  {{ u.fullname || u.username }}（进行中 {{ u._ongoing || 0 }} · 负载 {{ u._load }}%）
                </option>
              </select>
            </div>
            <div>
              <label class="kr-label">优先级</label>
              <select v-model="dispatchForm.level" class="input" style="cursor:pointer;">
                <option value="low">低</option>
                <option value="mid">中</option>
                <option value="high">高（加急）</option>
              </select>
            </div>
          </div>

          <div class="kr-row">
            <label class="kr-label">派单备注（可选）</label>
            <textarea v-model="dispatchForm.remark" class="input" rows="2" placeholder="如：优先处理，需在今日14:00前完成；现场联系王班长..."></textarea>
          </div>
        </div>
        <div class="modal-foot" style="padding: 14px 24px; border-top:1px solid var(--border-subtle); display:flex; justify-content:flex-end; gap:10px;">
          <button class="btn btn-outline" @click="closeDispatch" type="button">取消</button>
          <button
            v-if="dispatchMode === 'create'"
            class="btn btn-primary"
            @click="submitDispatch('create')"
            :disabled="dispatchSubmitting || !!dispatchForm.assignee_id"
            :title="dispatchForm.assignee_id ? '已选择维修工，请使用创建并派单' : '创建待派单工单'"
            type="button"
          >
            创建
          </button>
          <button
            class="btn btn-primary"
            :class="{ 'needs-assignee': dispatchMode === 'create' && !dispatchForm.assignee_id }"
            :aria-disabled="dispatchMode === 'create' && !dispatchForm.assignee_id"
            :title="dispatchMode === 'create' && !dispatchForm.assignee_id ? '请先选择维修工' : ''"
            @click="submitDispatch('assign')"
            :disabled="dispatchSubmitting"
            type="button"
          >
            {{ dispatchSubmitting ? '提交中…' : (dispatchMode === 'create' ? '创建并派单' : '确认派单') }}
          </button>
        </div>
      </div>
    </div>

    <!-- 工单详情弹窗 -->
    <div v-if="previewOpen && previewTicket" class="modal-mask" @click.self="previewOpen = false">
      <div class="modal-card card" @click.stop style="max-width:640px;">
        <div class="modal-head">
          <h3>📋 工单详情 · {{ previewTicket.code }}</h3>
          <button class="modal-close" @click="previewOpen = false" type="button">✕</button>
        </div>
        <div class="modal-body" style="padding: 20px 24px; display:flex; flex-direction:column; gap:12px;">
          <div class="kr-field">
            <div class="kr-field-label">工单标题</div>
            <div class="kr-field-value" style="font-weight:600;">{{ previewTicket.title }}</div>
          </div>
          <div class="kr-row kr-double" style="display:grid; grid-template-columns: 1fr 1fr; gap: 12px;">
            <div class="kr-field">
              <div class="kr-field-label">关联设备</div>
              <div class="kr-field-value">{{ previewTicket.device_name || '—' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">类别</div>
              <div class="kr-field-value">{{ previewTicket.category || '—' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">优先级</div>
              <div class="kr-field-value">
                <span class="pri-chip" :class="'pri-' + previewTicket._priorityKey">{{ priorityText(previewTicket._priorityKey) }}</span>
              </div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">状态</div>
              <div class="kr-field-value">
                <span class="status-chip" :class="'st-' + previewTicket._statusKey">{{ previewTicket.status_label || statusText(previewTicket._statusKey) }}</span>
              </div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">处理人</div>
              <div class="kr-field-value">{{ previewTicket.assignee_name || '待分配' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">创建人</div>
              <div class="kr-field-value">{{ previewTicket.submitter_name || '系统' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">创建时间</div>
              <div class="kr-field-value mono">{{ previewTicket.createdText }}</div>
            </div>
          </div>
          <div class="kr-field">
            <div class="kr-field-label">问题描述</div>
            <div class="kr-field-value kr-text">{{ previewTicket.problem || '—' }}</div>
          </div>
            <div class="kr-field" v-if="previewTicket.solution">
              <div class="kr-field-label">解决方案</div>
              <div class="kr-field-value kr-text solution">{{ previewTicket.solution }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">备注</div>
              <div class="kr-field-value kr-text">{{ previewTicket.remark || '—' }}</div>
            </div>
          <div class="kr-field" v-if="previewTicket._attachments && previewTicket._attachments.length">
            <div class="kr-field-label">附件（{{ previewTicket._attachments.length }}）</div>
            <div class="attach-list">
              <div v-for="att in previewTicket._attachments" :key="att.id" class="attach-item">
                <span class="attach-name">{{ att.filename }}</span>
                <a class="attach-view" :href="`/api/attachments/${att.id}`" target="_blank">查看</a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 占位弹窗（演示用） -->

    <!-- 报告审核弹窗（独立 Modal） -->
    <div v-if="selectedReport" class="modal-mask" @click.self="selectedReport = null">
      <div class="modal-card card report-modal-card" @click.stop>
        <div class="modal-head report-modal-head">
          <div>
            <h3 class="report-modal-title">{{ selectedReport.title }}</h3>
            <div class="report-modal-sub">
              <span class="cr-status" :class="'st-' + selectedReport.status">{{ selectedReport.status_label || statusLabel(selectedReport.status) }}</span>
              <span>{{ selectedReport.submitter_name || '未知用户' }} · {{ formatTime(selectedReport.submit_time_ts) }}</span>
              <span v-if="selectedReport.review_time_ts && selectedReport.submit_time_ts !== selectedReport.review_time_ts">
                · 审核于 {{ formatTime(selectedReport.review_time_ts) }}
              </span>
              <span v-if="selectedReport.reviewer_name"> · 审核人：{{ selectedReport.reviewer_name }}</span>
            </div>
          </div>
          <button class="modal-close" @click="selectedReport = null" type="button">✕</button>
        </div>
        <div class="modal-body report-modal-body">
          <div class="kr-detail-body">
            <div class="kr-field">
              <div class="kr-field-label">适用设备</div>
              <div class="kr-field-value mono">{{ selectedReport.device || '—' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">问题描述</div>
              <div class="kr-field-value kr-text">{{ selectedReport.question || '—' }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">解决方案</div>
              <div class="kr-field-value kr-text solution">{{ selectedReport.solution || '—' }}</div>
            </div>
            <div class="kr-field" v-if="selectedReport.cause">
              <div class="kr-field-label">根因分析</div>
              <div class="kr-field-value kr-text">{{ selectedReport.cause }}</div>
            </div>
            <div class="kr-field">
              <div class="kr-field-label">建议入库</div>
              <div class="kr-field-value">
                <span class="kli-type" :class="'type-' + selectedReport.type">
                  {{ selectedReport.type === 'case' ? '📚 案例库' : selectedReport.type === 'guide' ? '📖 作业指导' : '📋 未分类（管理员决定）' }}
                </span>
              </div>
            </div>
            <div class="kr-field" v-if="selectedReport.review_remark">
              <div class="kr-field-label">{{ selectedReport.status === 'rejected' ? '驳回原因' : '审核备注' }}</div>
              <div class="kr-field-value kr-text" :class="{ reject: selectedReport.status === 'rejected' }">{{ selectedReport.review_remark }}</div>
            </div>
          </div>

          <!-- 审核操作：仅待审核 -->
          <div v-if="selectedReport.status === 'pending'" class="kr-review">
            <div class="kr-review-head">
              <h4 class="kr-review-title">📋 审核操作</h4>
            </div>
            <div class="kr-review-field">
              <div class="kr-field-label">入库目标（可调整）</div>
              <div class="kr-type-picker">
                <button
                  v-for="tp in krTypes"
                  :key="tp.key"
                  class="type-pick-btn"
                  :class="{ active: reviewForm.type === tp.key }"
                  @click="reviewForm.type = tp.key"
                  :disabled="reviewLoading"
                >{{ tp.icon }} {{ tp.label }}</button>
              </div>
            </div>
            <div class="kr-review-field">
              <div class="kr-field-label">审核备注<span class="req" v-if="reviewForm.action === 'reject'">*</span></div>
              <textarea
                v-model="reviewForm.remark"
                class="kr-textarea"
                rows="3"
                :disabled="reviewLoading"
                :placeholder="reviewForm.action === 'reject' ? '请务必告知驳回原因，帮助提交人改进方案...' : '（可选）补充入库说明或对方案的完善建议...'"
              ></textarea>
            </div>
            <div class="kr-review-actions">
              <button
                class="btn btn-danger"
                :disabled="reviewLoading"
                @click="doReview('reject')"
              >🚫 驳回（附原因）</button>
              <div class="kr-approve-group">
                <button
                  class="btn btn-primary"
                  :disabled="reviewLoading"
                  @click="doReview('approve')"
                >✓ 仅审核通过</button>
                <button
                  class="btn btn-success"
                  :disabled="reviewLoading"
                  @click="doReview(reviewForm.type === 'guide' ? 'sync_guide' : 'sync_case')"
                >📚 通过并直接入库</button>
              </div>
            </div>
            <div v-if="krTip" class="kr-tip" :class="{ ok: krTip.ok }">{{ krTip.text }}</div>
          </div>

          <!-- 已审核通过：操作同步入库 -->
          <div v-else-if="selectedReport.status === 'approved'" class="kr-review">
            <div class="kr-review-head">
              <h4 class="kr-review-title">📂 入库操作</h4>
              <span class="kr-approval-info">已审核通过 · 审核人：{{ selectedReport.reviewer_name || '管理员' }}</span>
            </div>
            <div class="kr-review-field">
              <div class="kr-field-label">同步到</div>
              <div class="kr-type-picker">
                <button
                  class="type-pick-btn"
                  :class="{ active: reviewForm.type === 'case' }"
                  @click="reviewForm.type = 'case'"
                  :disabled="reviewLoading"
                >📚 案例库</button>
                <button
                  class="type-pick-btn"
                  :class="{ active: reviewForm.type === 'guide' }"
                  @click="reviewForm.type = 'guide'"
                  :disabled="reviewLoading"
                >📖 作业指导</button>
              </div>
            </div>
            <div class="kr-review-actions">
              <button class="btn btn-success" :disabled="reviewLoading" @click="syncToLibrary">
                📤 立即同步入库
              </button>
            </div>
            <div v-if="krTip" class="kr-tip" :class="{ ok: krTip.ok }">{{ krTip.text }}</div>
          </div>

          <!-- 其他状态：信息展示 -->
          <div v-else class="kr-synced-info">
            <div v-if="selectedReport.status === 'synced_case'" class="krs-card synced-case">
              <div class="krs-icon">📚</div>
              <div class="krs-body">
                <div class="krs-title">已同步到案例库</div>
                <div class="krs-desc">可在「案例库」中查看此方案</div>
              </div>
              <router-link to="/case" class="btn btn-primary btn-sm">查看案例库 →</router-link>
            </div>
            <div v-else-if="selectedReport.status === 'synced_guide'" class="krs-card synced-guide">
              <div class="krs-icon">📖</div>
              <div class="krs-body">
                <div class="krs-title">已同步到作业指导</div>
                <div class="krs-desc">可在「作业指导」中查看此标准作业流程</div>
              </div>
              <router-link to="/guide" class="btn btn-primary btn-sm">查看作业指导 →</router-link>
            </div>
            <div v-else-if="selectedReport.status === 'rejected'" class="krs-card synced-reject">
              <div class="krs-icon">🚫</div>
              <div class="krs-body">
                <div class="krs-title">报告已驳回</div>
                <div class="krs-desc">已通知提交人根据原因进行修改后可再次提交</div>
              </div>
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
  listTicketsApi, assignTicketApi, createTicketApi, deleteTicketApi,
  listReportsApi, reviewReportApi,
  listUsersApi, userOptionsApi
} from '../utils/api'
import { toast as _toast } from '../utils/request'

const ROLE_LABEL = { worker: '一线检修员', manager: '维修管理员', sysadmin: '系统管理员' }
const LEVEL_ORDER = { critical: 0, high: 0, mid: 1, low: 2 }

function _fmtTsToText(ts) {
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
  return (d.getMonth() + 1) + '/' + d.getDate() + ' ' + hh + ':' + mm
}

function _isOvertimeTicket(t) {
  if (t._statusKey === 'done' || !t.submit_time_ts) return false
  const level = t._levelKey || 'mid'
  const hours = { high: 6, mid: 24, low: 48 }[level] || 24
  const dl = Number(t.submit_time_ts) * 1000 + hours * 3600 * 1000
  return Date.now() > dl
}

function _mapTicket(t) {
  let level = (t.level || 'mid').toLowerCase()
  if (level === 'critical') level = 'high'
  const status = (t.status || 'pending').toLowerCase()
  let statusKey = status
  if (status === 'doing') statusKey = 'ongoing'
  if (status === 'assigned') statusKey = 'confirming'
  if (status === 'over') statusKey = 'overdue'
  if (status === 'completed') statusKey = 'done'
  return {
    id: t.id,
    code: t.code || ('TK-' + t.id),
    title: t.title || '',
    device_id: t.device_id,
    device_name: t.device_name,
    category: t.category || '机械',
    level: level,
    level_label: t.level_label || '',
    _levelKey: level,
    _priorityKey: level,
    status: status,
    status_label: t.status_label || '',
    _statusKey: statusKey,
    assignee_id: t.assignee_id,
    assignee_name: t.assignee_name,
    submitter_name: t.submitter_name,
    problem: t.problem,
    solution: t.solution,
    remark: t.remark,
    submit_time_ts: t.submit_time_ts,
    finish_time_ts: t.finish_time_ts,
    createdText: _fmtTsToText(t.submit_time_ts),
    _isOvertime: false,
    _op: null
  }
}

function _mapReport(r) {
  return {
    id: r.id,
    rid: r.rid,
    title: r.title,
    device: r.device,
    type: (r.type || 'case').toLowerCase(),
    source: r.source || 'manual',
    level: r.level,
    question: r.question,
    cause: r.cause,
    solution: r.solution,
    status: r.status,
    status_label: r.status_label,
    submitter_id: r.submitter_id,
    submitter_name: r.submitter_name,
    submit_time_ts: r.submit_time_ts,
    reviewer_name: r.reviewer_name,
    review_remark: r.review_remark,
    review_time_ts: r.review_time_ts,
    sync_time_ts: r.sync_time_ts
  }
}

function _mapUser(u, allTickets) {
  const uid = Number(u.id)
  const doing = allTickets.filter(t => Number(t.assignee_id) === uid && t._statusKey === 'ongoing').length
  const done = allTickets.filter(t => Number(t.assignee_id) === uid && t._statusKey === 'done').length
  const pending = allTickets.filter(t => Number(t.assignee_id) === uid && t._statusKey === 'pending').length
  const total = pending + doing + done
  const load = Math.min(100, Math.round((doing / 3) * 100))
  return {
    id: uid,
    username: u.username,
    fullname: u.fullname,
    role: u.role,
    _roleLabel: u.role_label || ROLE_LABEL[u.role] || u.role,
    _colorIdx: (uid - 1) % 6,
    _pending: pending,
    _ongoing: doing,
    _done: done,
    _total: total,
    _load: load
  }
}

export default {
  name: 'AdminDashboard',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      timer: null,
      activeMainTab: 'order',
      activeOrderTab: 'all',
      _refreshTick: 0,
      _hydrating: true,
      allTickets: [],
      ticketsLoading: false,
      allUsers: [],
      usersLoading: false,
      allReports: [],
      reportsLoading: false,
      dispatchOpen: false,
      dispatchMode: 'assign',
      dispatchTicket: null,
      dispatchForm: { title: '', device_id: null, device_name: '', category: '', level: 'mid', problem: '', assignee_id: '', remark: '' },
      dispatchSubmitting: false,
      dispatchErr: '',
      _handledDispatchRoute: '',
      previewOpen: false,
      previewTicket: null,
      activeKrTab: 'pending',
      selectedReport: null,
      reviewForm: { type: 'case', remark: '', action: '' },
      reviewLoading: false,
      krTip: { ok: true, text: '' },
      toast: ''
    }
  },
  computed: {
    displayName() {
      const u = getUser()
      const base = (u && (u.fullname || u.username)) || ''
      if (!base) return '王主任'
      const surname = base.charAt(0)
      const role = (u && u.role) || 'sysadmin'
      if (role === 'worker') return surname + '师傅'
      return surname + '主任'
    },
    totalOrders() { return this.allTickets.length },
    pendingCount() { return this.allTickets.filter(t => t._statusKey === 'pending').length },
    confirmingCount() { return this.allTickets.filter(t => t._statusKey === 'confirming').length },
    ongingCount() { return this.allTickets.filter(t => t._statusKey === 'ongoing').length },
    doneCount() { return this.allTickets.filter(t => t._statusKey === 'done').length },
    totalWorkers() { return this.workers.length },
    onlineWorkers() { return Math.max(0, this.workers.filter(w => w._ongoing != null).length) },
    slaRate() {
      const done = this.allTickets.filter(t => t._statusKey === 'done')
      if (!done.length) return 96
      const ok = done.filter(t => !t._isOvertime).length
      return Math.round(ok / done.length * 100)
    },
    highPriority() {
      return this.allTickets.filter(t =>
        (t._statusKey === 'pending') &&
        (t._priorityKey === 'high')
      ).length
    },
    orderTabs() {
      const all = this.allTickets.length
      const pending = this.allTickets.filter(t => t._statusKey === 'pending').length
      const confirming = this.allTickets.filter(t => t._statusKey === 'confirming').length
      const ongoing = this.allTickets.filter(t => t._statusKey === 'ongoing').length
      const done = this.allTickets.filter(t => t._statusKey === 'done').length
      const overdue = this.allTickets.filter(t => t._statusKey === 'overdue').length
      return [
        { key: 'all', label: '全部', count: all },
        { key: 'pending', label: '待派单', count: pending },
        { key: 'confirming', label: '待确认', count: confirming },
        { key: 'ongoing', label: '进行中', count: ongoing },
        { key: 'done', label: '已完成', count: done },
        { key: 'overdue', label: '超时', count: overdue }
      ]
    },
    filteredOrders() {
      this._refreshTick
      const tab = this.activeOrderTab
      let arr = this.allTickets.slice()
      if (tab !== 'all') arr = arr.filter(t => t._statusKey === tab)
      // 按创建时间倒序排列（最新在前）
      arr.sort((a, b) => (b.submit_time_ts || 0) - (a.submit_time_ts || 0))
      return arr.map(t => {
        if (!t._isOvertime) t._isOvertime = _isOvertimeTicket(t)
        return t
      })
    },
    workers() {
      const ids = new Set()
      const core = this.allUsers
        .filter(u => u.role === 'worker' || u._roleLabel === '一线检修员')
        .map(u => _mapUser(u, this.allTickets))
      core.forEach(u => ids.add(Number(u.id)))
      this.allTickets.forEach(t => {
        if (t.assignee_id && !ids.has(Number(t.assignee_id))) {
          ids.add(Number(t.assignee_id))
          core.push(_mapUser({
            id: t.assignee_id,
            username: t.assignee_name,
            fullname: t.assignee_name,
            role: 'worker',
            role_label: '一线检修员'
          }, this.allTickets))
        }
      })
      return core
    },
    pendingReports() {
      return this.allReports.filter(r => r.status === 'pending').length
    },
    krStats() {
      const all = this.allReports
      return {
        total: all.length,
        pending: all.filter(r => r.status === 'pending').length,
        approved: all.filter(r => r.status === 'approved').length,
        synced: all.filter(r => r.status === 'synced_case' || r.status === 'synced_guide').length,
        rejected: all.filter(r => r.status === 'rejected').length
      }
    },
    mainTabs() {
      return [
        { key: 'order', label: '工单列表', icon: '📋', count: this.totalOrders, badgeCls: '' },
        { key: 'team', label: '团队负载', icon: '👥', count: 0, badgeCls: '' },
        { key: 'knowledge', label: '知识报告审核', icon: '📝', count: this.pendingReports, badgeCls: 'orange' }
      ]
    },
    krTabs() {
      return [
        { key: 'all', label: '全部', count: this.allReports.length },
        { key: 'pending', label: '待审核', count: this.krStats.pending },
        { key: 'approved', label: '已通过', count: this.krStats.approved },
        { key: 'synced', label: '已入库', count: this.krStats.synced },
        { key: 'rejected', label: '已驳回', count: this.krStats.rejected }
      ]
    },
    filteredReports() {
      const t = this.activeKrTab
      if (t === 'all') return this.allReports
      if (t === 'synced') return this.allReports.filter(r => r.status === 'synced_case' || r.status === 'synced_guide')
      return this.allReports.filter(r => r.status === t)
    },
    krTypes() {
      return [
        { key: 'case', label: '案例库', icon: '📚' },
        { key: 'guide', label: '作业指导', icon: '📖' }
      ]
    }
  },
  watch: {
    activeOrderTab() { this._refreshTick++ }
  },
  async created() {
    this._hydrating = true
    try {
      await Promise.all([
        this.loadAllTickets(),
        this.loadAllUsers(),
        this.loadAllReports()
      ])
    } finally {
      this._hydrating = false
    }
    this.resolveRouteTab()
    this._pickRouteReport()
    window.addEventListener('hashchange', this.resolveRouteTab)
  },
  mounted() {
    this.updateTime()
    this.timer = setInterval(this.updateTime, 1000)
    this.$watch(() => this.$route && this.$route.query, () => {
      this.resolveRouteTab()
      if (!this._hydrating) this._pickRouteReport()
    }, { immediate: true })
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer)
    window.removeEventListener('hashchange', this.resolveRouteTab)
  },
  methods: {
    resolveRouteTab() {
      const q = this.$route && this.$route.query
      if (!q) return
      if (q.tab === 'order') this.activeMainTab = 'order'
      if (q.tab === 'knowledge') this.activeMainTab = 'knowledge'
      const order = (q.order || '').toString()
      if (order && ['all', 'pending', 'confirming', 'ongoing', 'done', 'overdue'].indexOf(order) >= 0) {
        this.activeOrderTab = order
      }
      const kr = (q.kr || '').toString()
      if (kr && ['all', 'pending', 'approved', 'synced', 'rejected'].indexOf(kr) >= 0) {
        this.activeKrTab = kr
      }
      if (!this._hydrating && q.action === 'create' && q.device) {
        const routeKey = this.$route.fullPath
        if (this._handledDispatchRoute !== routeKey) {
          this._handledDispatchRoute = routeKey
          const code = String(q.device || '').trim()
          const name = String(q.device_name || '').trim()
          this.openDispatch()
          this.dispatchForm.device_id = Number(q.device_id) || null
          this.dispatchForm.title = String(q.title || `${name || code}故障维修`).trim()
          this.dispatchForm.device_name = [code, name].filter(Boolean).join(' ')
          this.dispatchForm.category = String(q.category || '')
          this.dispatchForm.problem = String(
            q.problem || `${name || code}处于故障停机状态，请安排检查并维修`
          ).trim()
        }
      }
    },
    _pickRouteReport() {
      const q = this.$route && this.$route.query
      const rid = q && q.rid ? Number(q.rid) : NaN
      if (!Number.isFinite(rid) || rid <= 0) return
      const target = this.allReports.find(r => Number(r.id) === rid)
      if (target) this.selectReport(target)
    },
    showToast(txt, ok = true) {
      if (ok) _toast(txt, 'success')
      else _toast(txt, 'error')
      this.toast = txt
      setTimeout(() => (this.toast = ''), 3800)
    },
    async loadAllTickets(force = false) {
      this.ticketsLoading = true
      try {
        const p = await listTicketsApi({ page: 1, size: 20000, scope: 'all' }) || {}
        const items = p.items || []
        this.allTickets = items.map(t => _mapTicket(t))
        this._refreshTick++
      } catch (e) {
        if (force || this.allTickets.length === 0) {
          _toast('工单加载失败：' + (e.message || '网络异常'), 'error')
        }
      } finally {
        this.ticketsLoading = false
      }
    },
    _optimisticTicketPatch(id, patch) {
      const idx = this.allTickets.findIndex(t => Number(t.id) === Number(id))
      if (idx >= 0) {
        const merged = { ...this.allTickets[idx], ...patch }
        this.allTickets.splice(idx, 1, merged)
        this._refreshTick++
        return merged
      }
      return null
    },
    async loadAllUsers(force = false) {
      this.usersLoading = true
      try {
        const p = await listUsersApi({ page: 1, size: 20000 }) || {}
        const items = p.items || []
        this.allUsers = items
      } catch (e) {
        if (force || this.allUsers.length === 0) {
          try {
            const opts = await userOptionsApi('worker') || []
            this.allUsers = (Array.isArray(opts) ? opts : []).map(o => ({
              id: o.id, username: o.username, fullname: o.fullname || o.label || o.username,
              role: 'worker', role_label: '一线检修员'
            }))
          } catch (_) {}
        }
      } finally {
        this.usersLoading = false
      }
    },
    async loadAllReports(force = false) {
      this.reportsLoading = true
      try {
        const p = await listReportsApi({ page: 1, size: 20000, scope: 'all' }) || {}
        const items = p.items || []
        this.allReports = items.map(r => _mapReport(r))
      } catch (e) {
        if (force || this.allReports.length === 0) {
          _toast('报告加载失败：' + (e.message || '网络异常'), 'error')
        }
      } finally {
        this.reportsLoading = false
      }
    },
    selectReport(r) {
      this.selectedReport = Object.assign({}, r)
      this.reviewForm = {
        type: (r.type && (r.type === 'case' || r.type === 'guide')) ? r.type : 'case',
        remark: '',
        action: ''
      }
      this.krTip = { ok: true, text: '' }
    },
    statusLabel(s) {
      return ({
        pending: '待审核',
        approved: '审核通过（待入库）',
        rejected: '已驳回',
        synced_case: '已入库案例',
        synced_guide: '已入库指南'
      })[s] || s
    },
    sourceLabel(s) {
      return ({ search: 'AI 检索场景', ticket: '工单场景', manual: '手工提交' })[s] || (s || '其他')
    },
    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(Number(ts) * 1000)
      return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    },
    showKrTip(text, ok = true) {
      this.krTip = { ok, text }
      setTimeout(() => (this.krTip = { ok: true, text: '' }), 3000)
    },
    async doReview(action) {
      if (!this.selectedReport) return
      this.reviewForm.action = action
      if (action === 'reject' && !this.reviewForm.remark.trim()) {
        this.showKrTip('❌ 请填写驳回原因，反馈给提交人', false)
        return
      }
      this.reviewLoading = true
      const rid = this.selectedReport.id
      try {
        await reviewReportApi(rid, action, this.reviewForm.remark || '')
        this.showKrTip(
          action === 'reject' ? '✓ 报告已驳回并通知提交人' :
          action === 'sync_case' ? '✓ 报告已通过并同步入库案例库' :
          action === 'sync_guide' ? '✓ 报告已通过并同步入库作业指导' :
          '✓ 报告已审核通过，可后续同步入库',
          true
        )
        await this.loadAllReports()
        const updated = this.allReports.find(r => r.id === rid)
        if (updated) this.selectReport(updated)
        else this.selectedReport = null
      } catch (e) {
        this.showKrTip('❌ 操作失败：' + (e.message || '未知错误'), false)
      } finally {
        this.reviewLoading = false
      }
    },
    async syncToLibrary() {
      if (!this.selectedReport) return
      this.reviewLoading = true
      const rid = this.selectedReport.id
      const action = this.reviewForm.type === 'guide' ? 'sync_guide' : 'sync_case'
      try {
        await reviewReportApi(rid, action, this.reviewForm.remark || '')
        this.showKrTip('✓ 已同步到' + (this.reviewForm.type === 'guide' ? '作业指导' : '案例库'), true)
        await this.loadAllReports()
        const updated = this.allReports.find(r => r.id === rid)
        if (updated) this.selectReport(updated)
      } catch (e) {
        this.showKrTip('❌ 同步失败：' + (e.message || '未知错误'), false)
      } finally {
        this.reviewLoading = false
      }
    },
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
      this.currentDate = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
    },
    priorityText(p) {
      return ({ critical: '高', high: '高', mid: '中', low: '低' })[p] || '中'
    },
    statusText(s) {
      return ({ pending: '待派单', confirming: '待确认', ongoing: '进行中', done: '已完成', overdue: '超时' })[s] || s
    },
    loadClass(v) {
      if (v >= 80) return 'lv-high'
      if (v >= 50) return 'lv-mid'
      return 'lv-low'
    },
    openDispatch(o) {
      if (this.workers.length === 0) {
        this.loadAllUsers(true)
      }
      if (o) {
        this.dispatchMode = 'assign'
        this.dispatchTicket = o
        this.dispatchForm = { title: o.title, device_id: o.device_id || null, device_name: o.device_name || '', category: o.category || '机械', level: o._levelKey || 'mid', problem: o.problem || '', assignee_id: o.assignee_id ? String(o.assignee_id) : '', remark: '' }
      } else {
        this.dispatchMode = 'create'
        this.dispatchTicket = null
        this.dispatchForm = { title: '', device_id: null, device_name: '', category: '', level: 'mid', problem: '', assignee_id: '', remark: '' }
      }
      this.dispatchErr = ''
      this.dispatchOpen = true
    },
    handleOrder(o) {
      if (o.status === 'pending' || o.status === 'assigned' || !o.assignee_id) {
        this.openDispatch(o)
      } else {
        this.previewOrder(o)
      }
    },
    closeDispatch() {
      this.dispatchOpen = false
      this.dispatchTicket = null
    },
    async submitDispatch(action = 'assign') {
      const f = this.dispatchForm
      this.dispatchErr = ''
      if (this.dispatchMode === 'create' && action === 'create' && f.assignee_id) {
        this.setDispatchError('已选择维修工，请点击“创建并派单”')
        return
      }
      if (this.dispatchMode === 'create') {
        if (!f.title.trim()) { this.setDispatchError('请填写工单标题'); return }
        if (f.title.trim().length < 2) { this.setDispatchError('工单标题至少需要2个字符'); return }
        if (!f.category) { this.setDispatchError('请选择工单类别'); return }
        if (!f.problem.trim()) { this.setDispatchError('请填写问题描述'); return }
        if (f.problem.trim().length < 5) { this.setDispatchError('问题描述不少于5字'); return }
      }
      const shouldAssign = this.dispatchMode !== 'create' || action === 'assign'
      if (shouldAssign && !f.assignee_id) { this.setDispatchError('请选择要指派的维修工'); return }
      this.dispatchSubmitting = true
      try {
        if (this.dispatchMode === 'create') {
          const payload = {
            title: f.title.trim(),
            device_id: f.device_id || null,
            device_name: f.device_name.trim(),
            category: f.category,
            level: f.level,
            problem: f.problem.trim(),
            assignee_id: shouldAssign ? Number(f.assignee_id) : null,
            remark: f.remark.trim()
          }
          await createTicketApi(payload)
          this.showToast(shouldAssign ? '✓ 工单创建并派单成功，等待员工确认' : '✓ 工单创建成功，等待派单', true)
        } else {
          const tid = this.dispatchTicket && this.dispatchTicket.id
          const saved = this._optimisticTicketPatch(tid, { _op: 'assign' })
          try {
            await assignTicketApi(tid, Number(f.assignee_id), f.remark || '', f.level)
            this._optimisticTicketPatch(tid, {
              status: 'assigned',
              status_label: '待确认',
              _statusKey: 'confirming',
              assignee_id: Number(f.assignee_id),
              assignee_name: this.workers.find(w => Number(w.id) === Number(f.assignee_id))?.fullname || '',
              _op: null
            })
            this.showToast('✓ 派单成功，等待员工确认', true)
          } catch (e) {
            if (saved) this._optimisticTicketPatch(tid, { status: saved.status, _statusKey: saved._statusKey, assignee_id: saved.assignee_id, assignee_name: saved.assignee_name, _op: null })
            throw e
          }
        }
        this.closeDispatch()
        setTimeout(() => {
          this.loadAllTickets()
          this.loadAllUsers()
        }, 300)
      } catch (e) {
        this.dispatchErr = '操作失败：' + (e.message || '请稍后重试')
      } finally {
        this.dispatchSubmitting = false
      }
    },
    setDispatchError(message) {
      this.dispatchErr = message
      _toast(message, 'error')
    },
    async previewOrder(o) {
      this.previewTicket = o
      this.previewOpen = true
      try {
        const res = await listAttachmentsApi(o.id)
        this.$set(this.previewTicket, '_attachments', res || [])
      } catch (e) {
        this.$set(this.previewTicket, '_attachments', [])
      }
    },
    async deleteOrder(o) {
      if (!confirm(`确定删除工单「${o.code}」？此操作不可恢复。`)) return
      try {
        await deleteTicketApi(o.id)
        this.loadAllTickets(true)
      } catch (e) {
        alert('删除失败：' + (e.message || '请重试'))
      }
    },
    goToReviewPending() {
      this.activeMainTab = 'knowledge'
      this.activeKrTab = 'pending'
      this.selectedReport = null
      this.$nextTick(() => {
        const panel = this.$refs.knowledgePanel
        if (panel && typeof panel.scrollIntoView === 'function') {
          panel.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      })
      try {
        const cur = (this.$route && this.$route.query) || {}
        if (cur.tab !== 'knowledge' || cur.kr !== 'pending' || cur.rid) {
          this.$router.replace({ path: '/admin', query: { tab: 'knowledge', kr: 'pending' } })
        }
      } catch (_) {}
    },
  }
}
</script>

<style scoped>
@keyframes skeleton-shine { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.container { max-width: var(--max-width); margin: 0 auto; padding: 16px 28px 64px; }

.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 0 16px;
  gap: 32px;
}

.role-tag {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  background: var(--primary-subtle);
  color: var(--primary);
  font-size: 0.75rem;
  font-weight: 600;
  border: 1px solid var(--border-active);
  margin-bottom: 14px;
}

.role-tag-icon { filter: drop-shadow(0 0 4px var(--primary-glow)); }

.hero-title { font-size: 1.75rem; margin-bottom: 8px; }
.hero-sub { color: var(--text-secondary); font-size: 0.9375rem; margin-bottom: 14px; }
.hero-status {
  display: flex; align-items: center; gap: 8px; font-size: 0.8125rem; color: var(--text-secondary); flex-wrap: wrap;
}
.hero-status .sep { color: var(--text-muted); margin: 0 4px; }
.hero-status strong { color: var(--accent-green); font-family: 'JetBrains Mono', monospace; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; }
.status-dot.online { background: var(--accent-green); box-shadow: 0 0 8px var(--accent-green); }
.status-dot.warning { background: var(--accent-orange); box-shadow: 0 0 8px var(--accent-orange); }

.time-display { text-align: right; }
.time-label { font-size: 0.75rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 1px; }
.time-value { font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: var(--primary); font-weight: 700; line-height: 1.2; }
.date-value { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }

/* 统计 */
.stats-grid {
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px;
}

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
.stat-card[data-cat="total"]::before,
.stat-card[data-cat="total"]::after   { background: var(--primary); }
.stat-card[data-cat="pending"]::before,
.stat-card[data-cat="pending"]::after { background: var(--accent-orange); }
.stat-card[data-cat="done"]::before,
.stat-card[data-cat="done"]::after   { background: var(--accent-green); }
.stat-card[data-cat="team"]::before,
.stat-card[data-cat="team"]::after   { background: var(--accent-cyan); }

.stat-icon {
  width: 52px; height: 52px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.375rem; flex-shrink: 0; position: relative; z-index: 1;
}
.stat-card[data-cat="total"] .stat-icon   { color: var(--primary);       background: var(--primary-subtle);              border: 1px solid var(--border-active); }
.stat-card[data-cat="pending"] .stat-icon { color: var(--accent-orange); background: rgba(245,158,11,0.10);               border: 1px solid rgba(245,158,11,0.18); }
.stat-card[data-cat="done"] .stat-icon    { color: var(--accent-green);  background: rgba(16,185,129,0.10);               border: 1px solid rgba(16,185,129,0.18); }
.stat-card[data-cat="team"] .stat-icon    { color: var(--accent-cyan);   background: rgba(6,182,212,0.10);                border: 1px solid rgba(6,182,212,0.18); }

.stat-info { flex: 1; min-width: 0; }
.stat-value { font-size: 1.625rem; font-weight: 700; font-family: 'Orbitron', sans-serif; line-height: 1.1; }
.stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }
.stat-trend { font-size: 0.6875rem; font-family: 'JetBrains Mono', monospace; margin-top: 6px; }
.stat-trend.up { color: var(--accent-green); }
.stat-trend.down { color: var(--accent-orange); }

/* 待派单呼吸红光（仅 pendingCount > 0 时渲染 .is-alert）*/
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
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
  50%      { box-shadow: 0 0 22px 4px rgba(245, 158, 11, 0.40); }
}
@keyframes alertBar {
  0%, 100% { opacity: 0.6; }
  50%      { opacity: 1; }
}
@keyframes alertIcon {
  0%, 100% { box-shadow: 0 0 0 0 rgba(245, 158, 11, 0); }
  50%      { box-shadow: 0 0 16px 3px rgba(245, 158, 11, 0.55); }
}

/* 快捷入口（水平横卡）*/
.quick-section { margin-bottom: 28px; }
.section-title {
  font-size: 1rem; color: var(--text-secondary); text-transform: uppercase; letter-spacing: 1px;
  font-weight: 600; margin: 0 0 16px; display: flex; align-items: center; gap: 8px;
}
.title-icon { filter: drop-shadow(0 0 4px var(--primary-glow)); }
.quick-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
.quick-card {
  display: flex; flex-direction: row; align-items: center; gap: 12px;
  text-decoration: none; color: inherit;
  padding: 14px 16px; cursor: pointer; text-align: left; font-family: inherit;
  border: 1px solid var(--border-subtle);
  transition: all var(--duration) var(--ease); border-radius: var(--radius-lg);
  background: var(--bg-card, rgba(255,255,255,0.02));
}
.quick-card:hover {
  transform: translateY(-2px); border-color: var(--border-active);
  box-shadow: 0 8px 24px rgba(0, 212, 255, 0.1);
}
.quick-icon {
  width: 48px; height: 48px; border-radius: var(--radius);
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem; flex-shrink: 0;
}
/* data-color 主题色 */
.quick-card[data-color="primary"] .quick-icon { color: var(--primary);       background: var(--primary-subtle);              border: 1px solid var(--border-active); }
.quick-card[data-color="green"]   .quick-icon { color: var(--accent-green);  background: rgba(16,185,129,0.10);               border: 1px solid rgba(16,185,129,0.18); }
.quick-card[data-color="cyan"]    .quick-icon { color: var(--accent-cyan);   background: rgba(6,182,212,0.10);                border: 1px solid rgba(6,182,212,0.18); }
.quick-card[data-color="violet"]  .quick-icon { color: #a78bfa;              background: rgba(167,139,250,0.12);               border: 1px solid rgba(167,139,250,0.20); }
.quick-card[data-color="orange"]  .quick-icon { color: var(--accent-orange); background: rgba(245,158,11,0.10);               border: 1px solid rgba(245,158,11,0.18); }
.quick-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.quick-row { display: flex; align-items: baseline; justify-content: space-between; gap: 8px; }
.quick-label { font-size: 0.9375rem; font-weight: 600; color: var(--text-primary); }
.quick-desc {
  font-size: 0.75rem; color: var(--text-muted); line-height: 1.4;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.quick-cta { font-size: 0.75rem; color: var(--text-secondary); font-weight: 500; flex-shrink: 0; }
.quick-card:hover .quick-cta { color: var(--primary); }

/* 工单区域 / 团队区域：全宽单栏 */
.order-section,
.team-section { padding: 22px 20px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.section-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.pill-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 5px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 500;
  color: var(--text-secondary); background: transparent;
  border: 1px solid var(--border-subtle); cursor: pointer; font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.pill-btn:hover { color: var(--text-primary); border-color: var(--primary-dim); }
.pill-btn.active { color: var(--primary); background: var(--primary-subtle); border-color: var(--border-active); }
.pill-num {
  display: inline-block; min-width: 18px; padding: 0 5px; height: 18px; line-height: 18px;
  border-radius: 9px; font-size: 0.625rem; font-family: 'JetBrains Mono', monospace;
  background: rgba(255,255,255,0.06); text-align: center;
}
.pill-btn.active .pill-num { background: rgba(0, 212, 255, 0.2); color: var(--primary); }

.order-section { padding: 22px 20px; }
.team-section { padding: 22px 20px; }

/* 工单表格 */
.order-table { display: flex; flex-direction: column; }
.order-row {
  display: grid;
  grid-template-columns: 150px 2fr 80px 120px 90px 110px 140px;
  gap: 12px;
  align-items: center;
  padding: 12px 0;
  border-bottom: 1px solid var(--border-subtle);
  font-size: 0.8125rem;
}
.order-head {
  font-size: 0.6875rem; color: var(--text-muted); text-transform: uppercase;
  letter-spacing: 1px; padding: 6px 0; border-bottom: 1px solid var(--border-subtle);
  position: sticky; top: 0; background: var(--bg-surface); z-index: 2;
}
.order-row:last-child { border-bottom: none; }
.col-id.mono, .col-time.mono { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-secondary); }
.order-title { color: var(--text-primary); font-weight: 500; }
.order-device { color: var(--text-muted); font-size: 0.75rem; margin-top: 2px; }
.pri-chip {
  display: inline-block; padding: 2px 8px; border-radius: 2px; font-size: 0.6875rem; font-weight: 600;
  letter-spacing: 0.5px;
}
.pri-chip.pri-high { color: var(--accent-red);    background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.22); }
.pri-chip.pri-mid  { color: var(--accent-orange); background: rgba(245,158,11,0.12);border: 1px solid rgba(245,158,11,0.22); }
.pri-chip.pri-low  { color: var(--accent-green);  background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.18); }

.worker-assign { display: flex; align-items: center; gap: 8px; }
.worker-avatar {
  width: 26px; height: 26px; border-radius: 50%;
  background: var(--primary-subtle); color: var(--primary);
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; font-size: 0.75rem; font-family: 'Orbitron', sans-serif;
  flex-shrink: 0;
}
.worker-name { font-size: 0.8125rem; }

.status-chip {
  display: inline-block; padding: 3px 10px; border-radius: 999px;
  font-size: 0.6875rem; font-weight: 600;
}
.status-chip.st-pending { color: var(--accent-orange); background: rgba(245,158,11,0.1); border: 1px solid rgba(245,158,11,0.22); }
.status-chip.st-confirming { color: var(--accent-purple); background: rgba(139,92,246,0.12); border: 1px solid rgba(139,92,246,0.28); }
.status-chip.st-ongoing { color: var(--primary);       background: var(--primary-subtle); border: 1px solid var(--border-active); }
.status-chip.st-done    { color: var(--accent-green);   background: rgba(16,185,129,0.1); border: 1px solid rgba(16,185,129,0.18); }
.status-chip.st-overdue { color: var(--accent-red);     background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.25); }

.col-time.overtime { color: var(--accent-red); font-weight: 600; }
.col-action {
  display: grid;
  grid-template-columns: repeat(3, 42px);
  gap: 6px;
  justify-content: end;
}
.order-head .col-action { display: block; text-align: center; }
.row-btn {
  width: 42px; min-height: 30px; padding: 4px 6px; font-size: 0.75rem;
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  cursor: pointer; font-family: inherit; white-space: nowrap;
  transition: all var(--duration) var(--ease);
}
.row-btn-placeholder { width: 42px; min-height: 30px; }
.row-btn:hover { border-color: var(--primary-dim); color: var(--text-primary); }
.row-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.row-btn.primary {
  background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active);
}
.row-btn.primary:hover { background: var(--primary); color: var(--bg-deep); }
.row-btn.success { background: rgba(16,185,129,0.15); color: var(--accent-green); border-color: rgba(16,185,129,0.3); }
.row-btn.success:hover { background: var(--accent-green); color: #fff; }
.row-btn.danger { background: rgba(239,68,68,0.15); color: var(--accent-red); border-color: rgba(239,68,68,0.3); }
.row-btn.danger:hover { background: var(--accent-red); color: #fff; }
.order-empty { padding: 32px 0; text-align: center; color: var(--text-muted); font-size: 0.875rem; }

/* 团队负载 */
.more-link { font-size: 0.75rem; color: var(--primary); text-decoration: none; cursor: pointer; }
.more-link:hover { color: var(--primary-dim); }
.team-list { display: flex; flex-direction: column; gap: 14px; }
.team-item { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.team-left { display: flex; align-items: center; gap: 10px; min-width: 0; }
.team-avatar {
  width: 36px; height: 36px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  font-weight: 800; font-family: 'Orbitron', sans-serif; font-size: 0.875rem;
  flex-shrink: 0; color: var(--bg-deep);
}
.team-avatar.av-1 { background: linear-gradient(135deg, var(--primary), var(--accent-cyan)); }
.team-avatar.av-2 { background: linear-gradient(135deg, var(--accent-green), #34d399); }
.team-avatar.av-3 { background: linear-gradient(135deg, var(--accent-orange), #fbbf24); }
.team-avatar.av-4 { background: linear-gradient(135deg, var(--accent-purple), #c084fc); }
.team-avatar.av-5 { background: linear-gradient(135deg, #fb7185, var(--accent-red)); }
.team-avatar.av-6 { background: linear-gradient(135deg, #60a5fa, var(--accent-cyan)); }

.team-meta { min-width: 0; }
.team-name { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); }
.team-skills { display: flex; gap: 4px; flex-wrap: wrap; margin-top: 3px; }
.skill-tag {
  font-size: 0.625rem; padding: 1px 6px; border-radius: 2px;
  background: rgba(255,255,255,0.05); color: var(--text-muted);
  border: 1px solid var(--border-subtle);
}
.team-load { flex: 1; max-width: 160px; min-width: 120px; }
.load-top { display: flex; justify-content: space-between; font-size: 0.75rem; color: var(--text-secondary); margin-bottom: 5px; }
.load-top b { color: var(--text-primary); font-family: 'JetBrains Mono', monospace; }
.load-top .mono { font-family: 'JetBrains Mono', monospace; font-weight: 600; color: var(--text-primary); }
.load-track { width: 100%; height: 6px; background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden; }
.load-fill { height: 100%; border-radius: 999px; transition: width 0.6s var(--ease); }
.load-fill.lv-low { background: linear-gradient(90deg, var(--accent-green), #00d084); }
.load-fill.lv-mid { background: linear-gradient(90deg, var(--accent-amber, #ffa726), var(--accent-orange)); }
.load-fill.lv-high { background: linear-gradient(90deg, var(--accent-orange), var(--accent-red)); }
.load-detail { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; font-size: 0.625rem; color: var(--text-muted); }
.ld-pending { color: var(--accent-orange); }
.ld-ongoing { color: var(--primary); }
.ld-done { color: var(--accent-green); }
.ld-overdue { color: var(--accent-red); font-weight: 600; }

/* Modal */
.modal-mask {
  position: fixed; inset: 0; background: rgba(4, 12, 32, 0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 24px;
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card {
  width: 100%; max-width: 560px; max-height: 90vh; padding: 0; overflow: hidden;
  display: flex; flex-direction: column;
  animation: popIn 180ms ease;
}
@keyframes popIn { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
}
.modal-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary); font-weight: 600; }
.dispatch-alert {
  margin: 12px 20px 0;
  padding: 10px 14px;
  border: 1px solid rgba(255, 71, 87, 0.75);
  border-radius: 8px;
  background: rgba(255, 71, 87, 0.1);
  color: #ff838c;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 0.875rem;
  font-weight: 600;
  flex-shrink: 0;
}
.dispatch-alert-icon {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--accent-red);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  flex-shrink: 0;
}
.modal-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: transparent; color: var(--text-secondary); border: 1px solid transparent;
  cursor: pointer; font-size: 0.875rem; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease); font-family: inherit;
}
.modal-close:hover { background: rgba(255,255,255,0.05); border-color: var(--border-subtle); color: var(--text-primary); }
.modal-body { padding: 28px 20px 32px; overflow-y: auto; flex: 1; min-height: 0; }
.placeholder-box { text-align: center; }
.placeholder-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.8; }
.placeholder-title { font-size: 1.125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.placeholder-desc { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }

/* 主 Tab */
.main-tabs-wrap { margin-bottom: 24px; }
.main-tabs {
  display: flex;
  gap: 6px;
  padding: 8px;
}
.main-tab {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 18px;
  border: 1px solid transparent;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-secondary);
  transition: all var(--duration) var(--ease);
  position: relative;
}
.main-tab:hover { color: var(--text-primary); background: rgba(255,255,255,0.03); }
.main-tab.active {
  color: var(--primary);
  background: var(--primary-subtle);
  border-color: var(--border-active);
  box-shadow: inset 0 0 0 1px rgba(37,99,235,0.25);
}
.mt-icon { font-size: 1.125rem; }
.mt-badge {
  padding: 2px 9px;
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: 999px;
  background: #f59e0b;
  color: #fff;
  font-family: 'JetBrains Mono', monospace;
  animation: pulse-badge 2s ease-in-out infinite;
}
.mt-badge.orange { background: #f59e0b; }
@keyframes pulse-badge {
  0%, 100% { box-shadow: 0 0 0 0 rgba(255,165,2,0.4); }
  50% { box-shadow: 0 0 0 5px rgba(255,165,2,0); }
}

.kr-quick {
  border: 1px solid rgba(245,158,11,0.25);
  background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(37,99,235,0.04));
}
.kr-quick:hover {
  border-color: rgba(255,165,2,0.5);
  box-shadow: 0 8px 24px rgba(255,165,2,0.12);
}
.kr-quick .quick-icon { color: #f59e0b; }
.kr-quick-cta { color: #f59e0b; }
.kr-quick-cta b {
  padding: 2px 10px;
  background: rgba(255,165,2,0.15);
  border-radius: 999px;
  color: #f59e0b;
  border: 1px solid rgba(255,165,2,0.3);
}

/* === 知识报告审核面板 === */
.knowledge-panel { display: flex; flex-direction: column; gap: 20px; }

.knowledge-layout {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 16px;
}
.kr-list { padding: 20px; }
.kr-list-body {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-height: 640px;
  overflow-y: auto;
}
.kr-list-item {
  padding: 14px 16px;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  background: var(--bg-deep);
  cursor: pointer;
  transition: all var(--duration);
}
.kr-list-item:hover { border-color: var(--border-hover, var(--primary-dim)); transform: translateY(-1px); }
.kr-list-item.active {
  border-color: var(--primary);
  background: var(--primary-subtle);
  box-shadow: 0 0 0 1px rgba(0,212,255,0.25);
}
.kr-list-item.pending { border-left: 3px solid #f59e0b; }
.kli-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 8px;
}
.kli-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  line-height: 1.4;
}
.kli-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  font-size: 0.6875rem;
  color: var(--text-secondary);
}
.kli-source {
  padding: 2px 8px;
  background: var(--bg-card, rgba(255,255,255,0.02));
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
}
.kli-device { color: var(--primary); }
.kli-foot {
  margin-top: 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.kli-type {
  font-size: 0.6875rem;
  padding: 2px 10px;
  border-radius: 4px;
  border: 1px solid;
  font-weight: 500;
}
.kli-type.type-case  { color: var(--accent-green);  background: rgba(16,185,129,0.1); border-color: rgba(16,185,129,0.3); }
.kli-type.type-guide { color: var(--accent-cyan);   background: rgba(6,182,212,0.1);  border-color: rgba(6,182,212,0.3); }
.kli-time { color: var(--text-muted); font-size: 0.6875rem; }

.kr-empty {
  padding: 60px 20px;
  text-align: center;
}
.ke-icon { font-size: 3rem; margin-bottom: 10px; opacity: 0.7; }
.ke-title { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.ke-desc { font-size: 0.8125rem; color: var(--text-secondary); }

/* 报告详情 */
.kr-detail {
  padding: 0;
  display: flex;
  flex-direction: column;
  max-height: 780px;
}
.kr-detail-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
}
.kr-detail-title {
  margin: 0 0 6px;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--text-primary);
}
.kr-detail-sub {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 0.75rem;
  color: var(--text-secondary);
}
.kr-detail-body {
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
  flex: 1;
}
.kr-field-label {
  font-size: 0.6875rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
  font-weight: 600;
  margin-bottom: 6px;
}
.kr-field-value {
  font-size: 0.9375rem;
  color: var(--text-primary);
  line-height: 1.6;
}
.kr-field-value.kr-text {
  padding: 12px 14px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  white-space: pre-wrap;
  word-break: break-word;
}
.kr-field-value.kr-text.solution {
  border-left: 3px solid var(--accent-green);
  background: linear-gradient(90deg, rgba(0,255,136,0.05), transparent);
}
.kr-field-value.kr-text.reject {
  border-left: 3px solid var(--accent-red);
  background: linear-gradient(90deg, rgba(255,71,87,0.05), transparent);
  color: var(--text-primary);
}
.mono { font-family: 'JetBrains Mono', monospace; }

/* 审核操作区 */
.kr-review {
  padding: 18px 24px 22px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-deep);
}
.kr-review-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
  gap: 10px;
}
.kr-review-title {
  margin: 0;
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
}
.kr-approval-info {
  font-size: 0.75rem;
  color: var(--accent-green);
  font-weight: 500;
}
.kr-review-field { margin-bottom: 14px; }
.req { color: var(--accent-red); margin-left: 2px; }
.kr-type-picker {
  display: flex; gap: 10px;
}
.type-pick-btn {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-card, rgba(255,255,255,0.02));
  border-radius: var(--radius);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 500;
  transition: all var(--duration);
}
.type-pick-btn:hover:not(:disabled) {
  border-color: var(--border-hover, var(--primary-dim));
  color: var(--text-primary);
}
.type-pick-btn.active {
  border-color: var(--primary);
  background: var(--primary-subtle);
  color: var(--primary);
  font-weight: 600;
  box-shadow: 0 0 0 1px rgba(0,212,255,0.25);
}
.type-pick-btn:disabled { opacity: 0.55; cursor: not-allowed; }

.kr-textarea {
  width: 100%;
  padding: 10px 12px;
  background: var(--bg-card, rgba(255,255,255,0.02));
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 0.875rem;
  line-height: 1.5;
  resize: vertical;
  min-height: 80px;
  outline: none;
  transition: all var(--duration);
  box-sizing: border-box;
}
.kr-textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-subtle); }
.kr-textarea:disabled { opacity: 0.6; cursor: not-allowed; }

.kr-review-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  flex-wrap: wrap;
}
.kr-approve-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 18px;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.875rem;
  border: 1px solid transparent;
  cursor: pointer;
  font-family: inherit;
  transition: all var(--duration) var(--ease);
  text-decoration: none;
  white-space: nowrap;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; transform: none !important; }
.btn.needs-assignee {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn-primary.needs-assignee:hover {
  transform: none;
  box-shadow: none;
}
.btn-sm { padding: 6px 12px; font-size: 0.75rem; border-radius: 6px; }
.btn-outline {
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border-subtle);
}
.btn-outline:hover:not(:disabled) { border-color: var(--primary-dim); color: var(--text-primary); }
.btn-primary {
  background: var(--primary);
  color: #04141f;
  border-color: var(--primary);
  box-shadow: 0 2px 10px rgba(0,212,255,0.2);
}
.btn-primary:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,212,255,0.3); }
.btn-success {
  background: var(--accent-green);
  color: #052e16;
  border-color: var(--accent-green);
  box-shadow: 0 2px 10px rgba(0,255,136,0.2);
}
.btn-success:hover:not(:disabled) { transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,255,136,0.3); }
.btn-danger {
  background: rgba(255,71,87,0.12);
  color: var(--accent-red);
  border-color: rgba(255,71,87,0.4);
}
.btn-danger:hover:not(:disabled) {
  background: rgba(255,71,87,0.2);
  border-color: var(--accent-red);
  transform: translateY(-1px);
}

.kr-tip {
  margin-top: 14px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 0.8125rem;
  font-weight: 500;
  border: 1px solid;
}
.kr-tip.ok {
  color: var(--accent-green);
  background: rgba(0,255,136,0.08);
  border-color: rgba(0,255,136,0.3);
}
.kr-tip:not(.ok) {
  color: var(--accent-red);
  background: rgba(255,71,87,0.08);
  border-color: rgba(255,71,87,0.3);
}

/* 已入库/已驳回提示 */
.kr-synced-info {
  padding: 20px 24px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-deep);
}
.krs-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-subtle);
}
.krs-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.375rem;
  flex-shrink: 0;
}
.synced-case .krs-icon { background: rgba(34,211,238,0.15); color: #22d3ee; }
.synced-guide .krs-icon { background: rgba(167,139,250,0.15); color: #a78bfa; }
.synced-reject .krs-icon { background: rgba(255,71,87,0.15); color: var(--accent-red); }
.krs-body { flex: 1; min-width: 0; }
.krs-title { font-size: 0.9375rem; font-weight: 700; color: var(--text-primary); margin-bottom: 3px; }
.krs-desc { font-size: 0.75rem; color: var(--text-secondary); }

/* 详情空态 */
.kr-detail-empty {
  padding: 60px 40px;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.kde-icon { font-size: 4rem; margin-bottom: 16px; opacity: 0.7; }
.kde-title { font-size: 1.125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 6px; }
.kde-desc { font-size: 0.875rem; color: var(--text-secondary); max-width: 320px; line-height: 1.6; }

/* 状态标签通用样式 */
.cr-status {
  padding: 3px 10px;
  font-size: 0.6875rem;
  border-radius: 999px;
  font-weight: 500;
  border: 1px solid;
  flex-shrink: 0;
}
.cr-status.st-pending      { color: #f59e0b; background: rgba(255,165,2,0.1); border-color: rgba(255,165,2,0.3); }
.cr-status.st-approved     { color: var(--accent-green); background: rgba(0,255,136,0.1); border-color: rgba(0,255,136,0.3); }
.cr-status.st-rejected     { color: var(--accent-red); background: rgba(255,71,87,0.1); border-color: rgba(255,71,87,0.3); }
.cr-status.st-synced_case  { color: #22d3ee; background: rgba(34,211,238,0.1); border-color: rgba(34,211,238,0.3); }
.cr-status.st-synced_guide { color: #a78bfa; background: rgba(167,139,250,0.1); border-color: rgba(167,139,250,0.3); }

/* 派单弹窗表单 */
.kr-row { margin-bottom: 0; }
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
.kr-err { font-size: 0.75rem; color: var(--accent-red); font-weight: 500; margin-top: 6px; }
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
  background: rgba(0,212,255,0.04);
  box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
}
.input::placeholder { color: var(--text-muted); }

.toast {
  position: fixed; left: 50%; bottom: 40px;
  transform: translateX(-50%);
  padding: 12px 26px;
  background: var(--accent-green);
  color: #052e16;
  font-weight: 600; font-size: 0.875rem;
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(0,255,136,0.3);
  z-index: 9999;
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }

.todo-empty { padding: 28px 4px; }

@media (max-width: 1300px) {
  .quick-grid { grid-template-columns: repeat(3, 1fr); }
  .knowledge-layout { grid-template-columns: 1fr; }
}
@media (max-width: 800px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .order-row { grid-template-columns: 110px 2fr 60px 90px 80px 90px; }
  .col-action { grid-column: 1 / -1; justify-content: end; }
}
@media (max-width: 600px) {
  .main-tab { flex-direction: column; gap: 4px; padding: 10px; }
  .quick-grid { grid-template-columns: 1fr; }
  .kr-review-actions { flex-direction: column; align-items: stretch; }
  .kr-review-actions .btn { width: 100%; }
  .kr-approve-group { flex-direction: column; }
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
}

/* ===== 报告审核 Modal（启用滑动 + flex 滚动修复） ===== */
.report-modal-head .report-modal-title {
  margin: 0 0 6px 0;
  font-size: 1.05rem;
  color: var(--text-primary);
  font-weight: 700;
  line-height: 1.4;
}
.report-modal-head .report-modal-sub {
  font-size: 0.8rem;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.report-modal-head .report-modal-sub .cr-status {
  font-size: 0.72rem;
  padding: 2px 10px;
}
.report-modal-body {
  padding: 20px 26px 26px;
  overflow-y: auto; /* 竖向滚动：内容超出 body 高度就可滚 */
  overflow-x: hidden;
  flex: 1 1 auto;
  min-height: 0; /* flex 子项关键：让 overflow 生效 */
  scroll-behavior: smooth;
}

/* 自定义细滚动条（深色主题不突兀） */
.report-modal-body::-webkit-scrollbar {
  width: 8px;
}
.report-modal-body::-webkit-scrollbar-track {
  background: transparent;
}
.report-modal-body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.25);
  border-radius: 999px;
  border: 2px solid transparent;
  background-clip: padding-box;
}
.report-modal-body::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.45);
  background-clip: padding-box;
  border: 2px solid transparent;
}
/* Firefox 滚动条 */
.report-modal-body {
  scrollbar-width: thin;
  scrollbar-color: rgba(148, 163, 184, 0.35) transparent;
}
</style>
