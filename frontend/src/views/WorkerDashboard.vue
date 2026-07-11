<template>
  <div class="container">
    <!-- 欢迎 + 顶部状态 -->
    <section class="hero">
      <div class="hero-left">
        <div class="role-tag worker">
          <span class="role-tag-icon">🔧</span>
          <span>维修工工作台</span>
        </div>
        <h1 class="hero-title">今天也要加油呀，{{ displayName }} 💪</h1>
        <p class="hero-sub">
          你有 <strong class="num-warn">{{ pendingMine }}</strong> 个待处理工单 ·
          本月已完成 <strong class="num-ok">{{ doneMine }}</strong> 单 ·
          平均处理时长 <strong class="num-ok">{{ avgTime }}</strong> 小时
        </p>
        <div class="hero-status">
          <span class="status-dot online"></span>
          <span>你目前处于【在岗】状态</span>
          <span class="sep">|</span>
          <span>团队排名：本月第 <b>{{ rank }}</b> / {{ totalWorkers }} 名</span>
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

    <!-- 个人统计卡 -->
    <section class="stats-grid">
      <div class="stat-card card">
        <div class="stat-icon orange">📌</div>
        <div class="stat-info">
          <div class="stat-value">{{ pendingMine }}</div>
          <div class="stat-label">我的待办</div>
          <div class="stat-trend down">含 {{ highUrgent }} 个加急</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon blue">🔄</div>
        <div class="stat-info">
          <div class="stat-value">{{ ongoingMine }}</div>
          <div class="stat-label">进行中</div>
          <div class="stat-trend up">需在今日内完成</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ doneMine }}</div>
          <div class="stat-label">本月已完成</div>
          <div class="stat-trend up">↑ 3 较上月同期</div>
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

    <!-- 快捷操作 -->
    <section class="quick-section">
      <h2 class="section-title">快捷入口</h2>
      <div class="quick-grid">
        <button class="quick-card card" @click="openReport">
          <span class="quick-icon">📝</span>
          <span class="quick-label">维修上报</span>
          <span class="quick-desc">发现设备异常，立即上报形成工单</span>
          <span class="quick-cta">我要上报 →</span>
        </button>
        <router-link :to="{ path: '/search', query: { q: '' } }" class="quick-card card">
          <span class="quick-icon">◎</span>
          <span class="quick-label">AI 查故障</span>
          <span class="quick-desc">不会修？输入现象秒出结构化处置步骤</span>
          <span class="quick-cta">去检索 →</span>
        </router-link>
        <router-link to="/guide" class="quick-card card">
          <span class="quick-icon">⇢</span>
          <span class="quick-label">作业指导</span>
          <span class="quick-desc">标准操作规程 SOP + 安全规范</span>
          <span class="quick-cta">查看规程 →</span>
        </router-link>
        <button class="quick-card card" @click="openMyProfile">
          <span class="quick-icon">🧾</span>
          <span class="quick-label">我的绩效</span>
          <span class="quick-desc">完成率 / SLA / 评价 等个人统计</span>
          <span class="quick-cta">查看详情 →</span>
        </button>
      </div>
    </section>

    <!-- 待办 + 已完成 -->
    <section class="main-grid">
      <!-- 待办工单 -->
      <div class="todo-section card">
        <div class="section-header">
          <h2 class="section-title">
            <span class="title-icon">📌</span>
            我的待办工单
          </h2>
          <div class="section-actions">
            <button
              v-for="t in todoTabs"
              :key="t.key"
              class="pill-btn"
              :class="{ active: activeTab === t.key }"
              @click="activeTab = t.key"
              type="button"
            >{{ t.label }}<span class="pill-num">{{ t.count }}</span></button>
          </div>
        </div>

        <div class="todo-list">
          <div
            v-for="(o, idx) in todoList"
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
                  <span class="todo-id mono">{{ o.id }}</span>
                  <span v-if="o.priority === 'high'" class="todo-urgent">⚡ 加急</span>
                </div>
                <div class="todo-title">{{ o.title }}</div>
                <div class="todo-meta">
                  <span>◈ {{ o.device }}</span>
                  <span class="dot">·</span>
                  <span>派单人：{{ o.dispatcher }}</span>
                  <span class="dot">·</span>
                  <span>{{ o.created }}</span>
                </div>
                <div class="todo-deadline" :class="{ ot: isOT(o) }">
                  ⏱ 截止：{{ o.deadline }}
                  <span v-if="isOT(o)" class="ot-badge">临近超时</span>
                </div>
              </div>
            </div>
            <div class="todo-actions">
              <button v-if="o.status === 'assigned'" class="act-btn primary" @click="acceptOrder(o)">接单</button>
              <button v-if="o.status === 'ongoing'" class="act-btn success" @click="submitReport(o)">
                提交维修报告
              </button>
              <button class="act-btn" @click="askAI(o)">AI 辅助</button>
              <button class="act-btn ghost" @click="viewDetail(o)">详情</button>
            </div>
          </div>
          <div v-if="todoList.length === 0" class="todo-empty">
            <div class="empty-icon">🎉</div>
            <div class="empty-title">太棒了！当前没有待办</div>
            <div class="empty-desc">你可以去「维修上报」主动发现问题，或看看案例库充充电～</div>
          </div>
        </div>
      </div>

      <!-- 最近完成 + 排名 -->
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
            <router-link to="/case" class="more-link">全部 →</router-link>
          </div>
          <div class="recent-list">
            <div v-for="h in recentDone" :key="h.id" class="recent-item">
              <div class="recent-dot ok"></div>
              <div class="recent-body">
                <div class="recent-title">{{ h.title }}</div>
                <div class="recent-meta">
                  <span>{{ h.device }}</span>
                  <span class="dot">·</span>
                  <span class="mono">{{ h.cost }}</span>
                  <span class="dot">·</span>
                  <span>{{ h.time }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 维修报告提交弹窗（占位） -->
    <div v-if="reportOpen" class="modal-mask" @click="reportOpen = false">
      <div class="modal-card card" @click.stop>
        <div class="modal-head">
          <h3>提交维修报告：{{ orderForReport && orderForReport.title }}</h3>
          <button class="modal-close" @click="reportOpen = false" type="button">✕</button>
        </div>
        <div class="modal-body">
          <div class="placeholder-box">
            <div class="placeholder-icon">📝</div>
            <div class="placeholder-title">维修报告（占位）</div>
            <div class="placeholder-desc">
              可在此填写：故障原因 / 更换配件 / 处理过程 / 试机结果 / 照片上传<br>
              提交后工单流转为「完成」，管理员可审核。
            </div>
            <button class="btn btn-primary" @click="fakeSubmit" style="margin-top: 20px;">确认提交（演示）</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 上报 / 个人绩效弹窗占位 -->
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
            <div class="placeholder-desc">「{{ modalTitle }}」模块为占位演示，后续可接入真实后端 API：<br>维修上报、个人绩效、派单详情等。</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getUser } from '../utils/auth'

export default {
  name: 'WorkerDashboard',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      pendingMine: 3,
      ongoingMine: 2,
      doneMine: 28,
      avgTime: 3.6,
      onTimeRate: 96.4,
      totalWorkers: 8,
      rank: 2,
      highUrgent: 1,
      activeTab: 'all',
      todoTabs: [
        { key: 'all', label: '全部', count: 5 },
        { key: 'urgent', label: '加急', count: 1 },
        { key: 'assigned', label: '待接单', count: 1 }
      ],
      myOrders: [
        { id: 'WO-20260711-012', title: '3#离心泵振动值持续走高', device: '离心泵 P-103', priority: 'high', status: 'ongoing', dispatcher: '王主任', created: '今日 09:12', deadline: '今日 14:00' },
        { id: 'WO-20260711-010', title: '5#输送带托辊异常磨损', device: '皮带机 C-105', priority: 'mid', status: 'ongoing', dispatcher: '王主任', created: '今日 08:50', deadline: '今日 18:00' },
        { id: 'WO-20260711-006', title: '阀门 V-118 填料更换', device: '截止阀 V-118', priority: 'mid', status: 'assigned', dispatcher: '王主任', created: '今日 08:30', deadline: '今日 20:00' },
        { id: 'WO-20260710-021', title: '空压机 AC-01 压力不足排查', device: '空压机 AC-01', priority: 'low', status: 'assigned', dispatcher: '王主任', created: '昨日 17:20', deadline: '明日 12:00' },
        { id: 'WO-20260710-018', title: '照明系统例行检查', device: '车间照明 L-ALL', priority: 'low', status: 'assigned', dispatcher: '王主任', created: '昨日 15:00', deadline: '本周五 18:00' }
      ],
      ranking: [
        { name: '赵工', skill: '输送 / 焊接', done: 34 },
        { name: '李师傅', skill: '旋转机械 / 液压', done: 28, me: true },
        { name: '王师傅', skill: '液压 / 润滑', done: 25 },
        { name: '钱师傅', skill: '仪表 / 校准', done: 22 },
        { name: '孙师傅', skill: '电气 / 变频器', done: 20 }
      ],
      recentDone: [
        { id: 1, title: '冷却塔风机轴承更换', device: '冷却塔 CT-01', cost: '2.5h', time: '今日 08:10' },
        { id: 2, title: '反应釜机械密封检修', device: '反应釜 R-201', cost: '4.0h', time: '昨日 16:30' },
        { id: 3, title: '输送带调偏及托辊更换', device: '皮带机 C-103', cost: '1.8h', time: '昨日 10:40' },
        { id: 4, title: '齿轮箱润滑油更换', device: '减速机 G-102', cost: '1.2h', time: '前天' }
      ],
      reportOpen: false,
      orderForReport: null,
      modalOpen: false,
      modalTitle: ''
    }
  },
  computed: {
    displayName() {
      const u = getUser()
      return (u && (u.fullname || u.username)) || '李师傅'
    },
    todoList() {
      if (this.activeTab === 'urgent') return this.myOrders.filter(o => o.priority === 'high')
      if (this.activeTab === 'assigned') return this.myOrders.filter(o => o.status === 'assigned')
      return this.myOrders
    }
  },
  mounted() {
    this.updateTime()
    this.timer = setInterval(this.updateTime, 1000)
  },
  beforeUnmount() {
    clearInterval(this.timer)
  },
  methods: {
    updateTime() {
      const now = new Date()
      this.currentTime = now.toLocaleTimeString('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' })
      this.currentDate = now.toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })
    },
    priorityText(p) {
      return { high: '急', mid: '中', low: '低' }[p]
    },
    isOT(o) {
      return o.priority === 'high' && o.deadline.includes('今日')
    },
    acceptOrder(o) {
      o.status = 'ongoing'
      this.pendingMine--
      this.ongoingMine++
    },
    submitReport(o) {
      this.orderForReport = o
      this.reportOpen = true
    },
    fakeSubmit() {
      if (this.orderForReport) {
        const i = this.myOrders.findIndex(x => x.id === this.orderForReport.id)
        if (i >= 0) this.myOrders.splice(i, 1)
        this.ongoingMine--
        this.doneMine++
      }
      this.reportOpen = false
    },
    askAI(o) {
      this.$router.push({ path: '/search', query: { q: o.title } })
    },
    viewDetail(o) {
      this.modalTitle = '工单详情：' + o.id
      this.modalOpen = true
    },
    openReport() { this.modalTitle = '维修上报（发现异常一键上报）'; this.modalOpen = true },
    openMyProfile() { this.modalTitle = '我的绩效'; this.modalOpen = true }
  }
}
</script>

<style scoped>
.hero { display: flex; justify-content: space-between; align-items: center; padding: 32px 0 28px; gap: 32px; }
.role-tag {
  display: inline-flex; align-items: center; gap: 6px; padding: 4px 12px;
  border-radius: 999px; font-size: 0.75rem; font-weight: 600; border: 1px solid var(--border-active);
  margin-bottom: 14px;
}
.role-tag { background: var(--primary-subtle); color: var(--primary); }
.role-tag.worker { background: rgba(0,255,136,0.1); color: var(--accent-green); border-color: rgba(0,255,136,0.2); }
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

/* 统计 */
.stats-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 28px; }
.stat-card { display: flex; align-items: center; gap: 14px; }
.stat-icon {
  width: 52px; height: 52px; border-radius: var(--radius-lg);
  display: flex; align-items: center; justify-content: center; font-size: 1.375rem; flex-shrink: 0;
}
.stat-icon.blue { color: var(--primary); background: var(--primary-subtle); border: 1px solid rgba(0,212,255,0.2); }
.stat-icon.green { color: var(--accent-green); background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.15); }
.stat-icon.orange { color: var(--accent-orange); background: rgba(255,107,53,0.1); border: 1px solid rgba(255,107,53,0.15); }
.stat-icon.purple { color: #a855f7; background: rgba(168,85,247,0.1); border: 1px solid rgba(168,85,247,0.15); }
.stat-info { flex: 1; }
.stat-value { font-size: 1.625rem; font-weight: 700; font-family: 'Orbitron', sans-serif; line-height: 1.1; }
.stat-label { font-size: 0.8125rem; color: var(--text-secondary); margin-top: 4px; }
.stat-trend { font-size: 0.6875rem; font-family: 'JetBrains Mono', monospace; margin-top: 6px; }
.stat-trend.up { color: var(--accent-green); }
.stat-trend.down { color: var(--accent-orange); }

/* 快捷入口 */
.quick-section { margin-bottom: 28px; }
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
.quick-card:hover { transform: translateY(-2px); border-color: var(--accent-green, #00ff88); box-shadow: 0 8px 24px rgba(0,255,136,0.08); }
.quick-icon { font-size: 1.75rem; color: var(--accent-green, #00ff88); margin-bottom: 4px; }
.quick-label { font-size: 0.9375rem; font-weight: 600; }
.quick-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5; flex: 1; }
.quick-cta { font-size: 0.75rem; color: var(--accent-green, #00ff88); font-weight: 500; margin-top: 6px; }

/* 主体网格 */
.main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; gap: 12px; flex-wrap: wrap; }
.section-actions { display: flex; gap: 6px; flex-wrap: wrap; }
.pill-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 5px 12px;
  border-radius: 999px; font-size: 0.75rem; font-weight: 500; color: var(--text-secondary);
  background: transparent; border: 1px solid var(--border-subtle);
  cursor: pointer; font-family: inherit; transition: all var(--duration) var(--ease);
}
.pill-btn:hover { color: var(--text-primary); border-color: var(--primary-dim); }
.pill-btn.active { color: var(--accent-green, #00ff88); background: rgba(0,255,136,0.1); border-color: rgba(0,255,136,0.25); }
.pill-num {
  display: inline-block; min-width: 18px; padding: 0 5px; height: 18px; line-height: 18px;
  border-radius: 9px; font-size: 0.625rem; font-family: 'JetBrains Mono', monospace;
  background: rgba(255,255,255,0.06); text-align: center;
}
.pill-btn.active .pill-num { background: rgba(0,255,136,0.15); color: var(--accent-green); }

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
.todo-pri.p-low { background: rgba(0,255,136,0.1); color: var(--accent-green); border: 1px solid rgba(0,255,136,0.15); }

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
.act-btn.primary { background: var(--primary); color: var(--bg-deep); border-color: var(--primary); font-weight: 600; }
.act-btn.primary:hover { background: var(--primary-dim); }
.act-btn.success { background: var(--accent-green, #00ff88); color: #00261a; border-color: var(--accent-green, #00ff88); font-weight: 600; }
.act-btn.success:hover { opacity: 0.9; }
.act-btn.ghost { opacity: 0.7; }

.todo-empty { padding: 48px 12px; text-align: center; }
.empty-icon { font-size: 2.5rem; margin-bottom: 12px; }
.empty-title { font-size: 1rem; font-weight: 700; color: var(--accent-green, #00ff88); margin-bottom: 4px; }
.empty-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.6; }

/* 右侧：排名 + 最近完成 */
.side-grid { display: flex; flex-direction: column; gap: 16px; }
.side-card { padding: 22px 20px; }
.more-link { font-size: 0.75rem; color: var(--primary); text-decoration: none; cursor: pointer; }
.more-link:hover { color: var(--primary-dim); }

.rank-list { display: flex; flex-direction: column; gap: 10px; }
.rank-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 10px; border-radius: var(--radius);
  transition: all var(--duration) var(--ease);
}
.rank-item:hover { background: rgba(255,255,255,0.03); }
.rank-item.me { background: rgba(0,255,136,0.06); border: 1px solid rgba(0,255,136,0.15); }
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
.rank-item.me .rank-av { background: rgba(0,255,136,0.15); color: var(--accent-green); }
.rank-info { flex: 1; min-width: 0; }
.rank-name { font-size: 0.875rem; font-weight: 600; color: var(--text-primary); display: flex; align-items: center; gap: 6px; }
.me-tag {
  font-size: 0.625rem; padding: 1px 6px; border-radius: 2px;
  background: rgba(0,255,136,0.15); color: var(--accent-green);
  border: 1px solid rgba(0,255,136,0.25); font-weight: 600;
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

/* Modal 通用 */
.modal-mask {
  position: fixed; inset: 0; background: rgba(4,12,32,0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 24px;
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card { width: 100%; max-width: 560px; padding: 0; overflow: hidden; animation: popIn 180ms ease; }
@keyframes popIn { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, rgba(0,255,136,0.08), transparent);
}
.modal-head h3 { margin: 0; font-size: 1rem; color: var(--text-primary); font-weight: 600; }
.modal-close {
  width: 28px; height: 28px; border-radius: 50%;
  background: transparent; color: var(--text-secondary); border: 1px solid transparent;
  cursor: pointer; font-size: 0.875rem; display: flex; align-items: center; justify-content: center;
  transition: all var(--duration) var(--ease); font-family: inherit;
}
.modal-close:hover { background: rgba(255,255,255,0.05); border-color: var(--border-subtle); color: var(--text-primary); }
.modal-body { padding: 28px 20px 32px; }
.placeholder-box { text-align: center; }
.placeholder-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.8; }
.placeholder-title { font-size: 1.125rem; font-weight: 700; color: var(--text-primary); margin-bottom: 8px; }
.placeholder-desc { font-size: 0.875rem; color: var(--text-secondary); line-height: 1.7; }

.btn-primary {
  padding: 10px 24px;
  background: var(--primary);
  color: var(--bg-deep);
  border: 1px solid var(--primary);
  border-radius: var(--radius);
  font-weight: 600;
  cursor: pointer;
  font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.btn-primary:hover { background: var(--primary-dim); border-color: var(--primary-dim); }

@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
}
</style>
