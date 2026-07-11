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
      <div class="stat-card card">
        <div class="stat-icon blue">📋</div>
        <div class="stat-info">
          <div class="stat-value">{{ totalOrders }}</div>
          <div class="stat-label">本月工单总数</div>
          <div class="stat-trend up">↑ 12% 较上月</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon orange">⏳</div>
        <div class="stat-info">
          <div class="stat-value">{{ pendingCount }}</div>
          <div class="stat-label">待派单</div>
          <div class="stat-trend down">↓ 2 较昨日</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ doneCount }}</div>
          <div class="stat-label">本月已完成</div>
          <div class="stat-trend up">↑ 8.3% 较上月</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon purple">🧑‍🔧</div>
        <div class="stat-info">
          <div class="stat-value">{{ totalWorkers }}</div>
          <div class="stat-label">在岗维修工</div>
          <div class="stat-trend up">↑ 1 名新入职</div>
        </div>
      </div>
    </section>

    <!-- 快捷操作 -->
    <section class="quick-section">
      <h2 class="section-title">管理入口</h2>
      <div class="quick-grid">
        <button class="quick-card card" @click="openDispatch">
          <span class="quick-icon">📤</span>
          <span class="quick-label">新建 / 派单</span>
          <span class="quick-desc">创建工单并指派给合适的维修工</span>
          <span class="quick-cta">立即派单 →</span>
        </button>
        <button class="quick-card card" @click="openTeam">
          <span class="quick-icon">👥</span>
          <span class="quick-label">人员管理</span>
          <span class="quick-desc">维修工排班、技能标签、绩效统计</span>
          <span class="quick-cta">查看团队 →</span>
        </button>
        <router-link to="/search" class="quick-card card">
          <span class="quick-icon">◎</span>
          <span class="quick-label">AI 辅助诊断</span>
          <span class="quick-desc">把棘手故障扔给 AI 获取结构化方案</span>
          <span class="quick-cta">开始检索 →</span>
        </router-link>
        <button class="quick-card card" @click="openReport">
          <span class="quick-icon">📊</span>
          <span class="quick-label">运维报表</span>
          <span class="quick-desc">月度完成率、SLA、MTTR 多维分析</span>
          <span class="quick-cta">生成报告 →</span>
        </button>
      </div>
    </section>

    <!-- 工单列表 + 团队负载 -->
    <section class="main-grid">
      <!-- 全部工单列表 -->
      <div class="order-section card">
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
            <div class="col-time">时限</div>
            <div class="col-action">操作</div>
          </div>
          <div v-for="o in filteredOrders" :key="o.id" class="order-row">
            <div class="col-id mono">{{ o.id }}</div>
            <div class="col-title">
              <div class="order-title">{{ o.title }}</div>
              <div class="order-device">◈ {{ o.device }}</div>
            </div>
            <div class="col-pri">
              <span class="pri-chip" :class="'pri-' + o.priority">{{ priorityText(o.priority) }}</span>
            </div>
            <div class="col-worker">
              <div class="worker-assign">
                <span class="worker-avatar">{{ (o.worker || '—').charAt(0) }}</span>
                <span class="worker-name">{{ o.worker || '待分配' }}</span>
              </div>
            </div>
            <div class="col-status">
              <span class="status-chip" :class="'st-' + o.status">{{ statusText(o.status) }}</span>
            </div>
            <div class="col-time mono" :class="{ overtime: isOvertime(o) }">{{ o.deadline }}</div>
            <div class="col-action">
              <button class="row-btn primary" @click="handleOrder(o)">处置</button>
              <button class="row-btn" @click="previewOrder(o)">详情</button>
            </div>
          </div>
          <div v-if="filteredOrders.length === 0" class="order-empty">当前筛选下无工单 🎉</div>
        </div>
      </div>

      <!-- 团队负载 -->
      <div class="team-section card">
        <div class="section-header">
          <h2 class="section-title"><span class="title-icon">👥</span>维修工负载</h2>
          <router-link to="/guide" class="more-link">排班 →</router-link>
        </div>
        <div class="team-list">
          <div v-for="w in workers" :key="w.name" class="team-item">
            <div class="team-left">
              <div class="team-avatar" :class="'av-' + w.color">{{ w.name.charAt(0) }}</div>
              <div class="team-meta">
                <div class="team-name">{{ w.name }}</div>
                <div class="team-skills">
                  <span v-for="s in w.skills" :key="s" class="skill-tag">{{ s }}</span>
                </div>
              </div>
            </div>
            <div class="team-load">
              <div class="load-top">
                <span>进行中 <b>{{ w.ongoing }}</b></span>
                <span class="mono">{{ w.load }}%</span>
              </div>
              <div class="load-track">
                <div class="load-fill" :class="loadClass(w.load)" :style="{ width: w.load + '%' }"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- 占位弹窗（演示用） -->
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
            <div class="placeholder-desc">这是「{{ modalTitle }}」的占位页面，后续可接入真实 API：<br>工单 CRUD、派单流转、人员排班、绩效报表等。</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { getUser } from '../utils/auth'

export default {
  name: 'AdminDashboard',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      totalOrders: 128,
      pendingCount: 12,
      ongingCount: 35,
      doneCount: 81,
      totalWorkers: 8,
      onlineWorkers: 6,
      slaRate: 94.2,
      highPriority: 3,
      activeOrderTab: 'all',
      orderTabs: [
        { key: 'all', label: '全部', count: 12 },
        { key: 'pending', label: '待派单', count: 3 },
        { key: 'ongoing', label: '进行中', count: 6 },
        { key: 'done', label: '已完成', count: 3 }
      ],
      orders: [
        { id: 'WO-20260711-012', title: '3#离心泵振动值持续走高', device: '离心泵 P-103', priority: 'high', worker: '李师傅', status: 'ongoing', deadline: '今日 14:00', created: '09:12' },
        { id: 'WO-20260711-011', title: '反应釜搅拌轴异响', device: '反应釜 R-201', priority: 'high', worker: '', status: 'pending', deadline: '今日 16:00', created: '09:30' },
        { id: 'WO-20260711-010', title: '5#输送带托辊异常磨损', device: '皮带机 C-105', priority: 'mid', worker: '赵工', status: 'ongoing', deadline: '今日 18:00', created: '08:50' },
        { id: 'WO-20260711-009', title: '液压站油温偏高告警', device: '液压站 H-301', priority: 'mid', worker: '王师傅', status: 'ongoing', deadline: '今日 20:00', created: '08:20' },
        { id: 'WO-20260711-008', title: '压力变送器校准', device: '变送器 PT-407', priority: 'low', worker: '', status: 'pending', deadline: '明日 12:00', created: '昨日 17:20' },
        { id: 'WO-20260711-007', title: '电机 M-202 绝缘预防性检测', device: '三相电机 M-202', priority: 'low', worker: '孙师傅', status: 'done', deadline: '—', created: '昨日 14:00' },
        { id: 'WO-20260711-006', title: '阀门 V-118 填料更换', device: '截止阀 V-118', priority: 'mid', worker: '李师傅', status: 'done', deadline: '—', created: '昨日 10:00' },
        { id: 'WO-20260711-005', title: '变频器参数优化', device: '变频器 VFD-03', priority: 'high', worker: '', status: 'pending', deadline: '今日 12:00', created: '昨日 09:00' },
        { id: 'WO-20260711-004', title: '空压机空气滤芯更换', device: '空压机 AC-02', priority: 'low', worker: '周师傅', status: 'done', deadline: '—', created: '前日' }
      ],
      workers: [
        { name: '李师傅', skills: ['旋转机械', '液压'], ongoing: 2, load: 82, color: 'a' },
        { name: '王师傅', skills: ['液压', '润滑'], ongoing: 1, load: 55, color: 'b' },
        { name: '赵工', skills: ['输送装置', '焊接'], ongoing: 1, load: 60, color: 'c' },
        { name: '孙师傅', skills: ['电气', '变频器'], ongoing: 0, load: 18, color: 'd' },
        { name: '周师傅', skills: ['通用机械', '管道'], ongoing: 0, load: 10, color: 'e' },
        { name: '钱师傅', skills: ['仪表', '校准'], ongoing: 1, load: 45, color: 'f' }
      ],
      modalOpen: false,
      modalTitle: ''
    }
  },
  computed: {
    displayName() {
      const u = getUser()
      return (u && (u.fullname || u.username)) || '王主任'
    },
    filteredOrders() {
      if (this.activeOrderTab === 'all') return this.orders
      return this.orders.filter(o => o.status === this.activeOrderTab)
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
      return { high: '高', mid: '中', low: '低' }[p]
    },
    statusText(s) {
      return { pending: '待派单', ongoing: '进行中', done: '已完成' }[s]
    },
    isOvertime(o) {
      return o.priority === 'high' && o.status !== 'done' && o.deadline.includes('今日')
    },
    loadClass(v) {
      if (v >= 80) return 'lv-high'
      if (v >= 50) return 'lv-mid'
      return 'lv-low'
    },
    handleOrder(o) {
      this.modalTitle = (o.status === 'pending' ? '派单：' : '处置：') + o.title
      this.modalOpen = true
    },
    previewOrder(o) {
      this.modalTitle = '工单详情：' + o.id
      this.modalOpen = true
    },
    openDispatch() { this.modalTitle = '新建工单 / 派单'; this.modalOpen = true },
    openTeam() { this.modalTitle = '人员管理（排班 / 技能 / 绩效）'; this.modalOpen = true },
    openReport() { this.modalTitle = '运维月度报表'; this.modalOpen = true }
  }
}
</script>

<style scoped>
.hero {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32px 0 28px;
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
  padding: 22px 20px; cursor: pointer; text-align: left; font-family: inherit; border: 1px solid var(--border-subtle);
  transition: all var(--duration) var(--ease); border-radius: var(--radius-lg); background: var(--bg-card, rgba(255,255,255,0.02));
}
.quick-card:hover {
  transform: translateY(-2px); border-color: var(--primary-dim);
  box-shadow: 0 8px 24px rgba(0, 212, 255, 0.1);
}
.quick-icon { font-size: 1.75rem; color: var(--primary); margin-bottom: 4px; }
.quick-label { font-size: 0.9375rem; font-weight: 600; }
.quick-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.5; flex: 1; }
.quick-cta { font-size: 0.75rem; color: var(--primary); font-weight: 500; margin-top: 6px; }

/* 主体网格 */
.main-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 16px; }
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

.order-section, .team-section { padding: 22px 20px; }

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
}
.order-row:last-child { border-bottom: none; }
.col-id.mono, .col-time.mono { font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--text-secondary); }
.order-title { color: var(--text-primary); font-weight: 500; }
.order-device { color: var(--text-muted); font-size: 0.75rem; margin-top: 2px; }
.pri-chip {
  display: inline-block; padding: 2px 8px; border-radius: 2px; font-size: 0.6875rem; font-weight: 600;
  letter-spacing: 0.5px;
}
.pri-chip.pri-high { color: var(--accent-red); background: rgba(255,71,87,0.12); border: 1px solid rgba(255,71,87,0.2); }
.pri-chip.pri-mid { color: var(--accent-orange); background: rgba(255,107,53,0.12); border: 1px solid rgba(255,107,53,0.2); }
.pri-chip.pri-low { color: var(--accent-green); background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.15); }

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
.status-chip.st-pending { color: var(--accent-orange); background: rgba(255,107,53,0.1); border: 1px solid rgba(255,107,53,0.2); }
.status-chip.st-ongoing { color: var(--primary); background: var(--primary-subtle); border: 1px solid var(--border-active); }
.status-chip.st-done { color: var(--accent-green); background: rgba(0,255,136,0.1); border: 1px solid rgba(0,255,136,0.15); }

.col-time.overtime { color: var(--accent-red); font-weight: 600; }
.col-action { display: flex; gap: 6px; }
.row-btn {
  padding: 4px 10px; font-size: 0.75rem;
  background: transparent; color: var(--text-secondary);
  border: 1px solid var(--border-subtle); border-radius: var(--radius);
  cursor: pointer; font-family: inherit;
  transition: all var(--duration) var(--ease);
}
.row-btn:hover { border-color: var(--primary-dim); color: var(--text-primary); }
.row-btn.primary {
  background: var(--primary-subtle); color: var(--primary); border-color: var(--border-active);
}
.row-btn.primary:hover { background: var(--primary); color: var(--bg-deep); }
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
.team-avatar.av-a { background: linear-gradient(135deg, #00d4ff, #4fd6ff); }
.team-avatar.av-b { background: linear-gradient(135deg, #00ff88, #4ade80); }
.team-avatar.av-c { background: linear-gradient(135deg, #ffcc33, #ffa726); }
.team-avatar.av-d { background: linear-gradient(135deg, #a855f7, #c084fc); }
.team-avatar.av-e { background: linear-gradient(135deg, #fb7185, #f43f5e); }
.team-avatar.av-f { background: linear-gradient(135deg, #60a5fa, #22d3ee); }

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

/* Modal */
.modal-mask {
  position: fixed; inset: 0; background: rgba(4, 12, 32, 0.7); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 9999; padding: 24px;
  animation: fadeIn 150ms ease;
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
.modal-card {
  width: 100%; max-width: 520px; padding: 0; overflow: hidden;
  animation: popIn 180ms ease;
}
@keyframes popIn { from { opacity: 0; transform: translateY(8px) scale(0.98); } to { opacity: 1; transform: none; } }
.modal-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 16px 20px; border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
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

@media (max-width: 1100px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); }
  .quick-grid { grid-template-columns: repeat(2, 1fr); }
  .main-grid { grid-template-columns: 1fr; }
  .order-row { grid-template-columns: 110px 2fr 60px 90px 80px 90px; }
  .col-action { grid-column: 1 / -1; justify-content: flex-end; display: flex; }
}
</style>
