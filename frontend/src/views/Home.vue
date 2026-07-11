<template>
  <div class="container">
    <!-- 顶部欢迎区 -->
    <section class="hero">
      <div class="hero-left">
        <h1 class="hero-title">设备检修<span class="text-primary">智能系统</span></h1>
        <p class="hero-sub">基于大语言模型的工业设备故障诊断与作业辅助平台</p>
        <div class="hero-status">
          <span class="status-dot online"></span>
          <span>系统运行中</span>
          <span class="sep">|</span>
          <span>AI 引擎就绪</span>
          <span class="sep">|</span>
          <span class="status-dot warning"></span>
          <span>{{ warningCount }} 条预警待处理</span>
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

    <!-- 统计卡片 -->
    <section class="stats-grid">
      <div class="stat-card card">
        <div class="stat-icon blue">◈</div>
        <div class="stat-info">
          <div class="stat-value">{{ totalDevices }}</div>
          <div class="stat-label">注册设备</div>
          <div class="stat-trend up">↑ 2.4% 较上周</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon green">▣</div>
        <div class="stat-info">
          <div class="stat-value">{{ knowledgeCount }}</div>
          <div class="stat-label">知识条目</div>
          <div class="stat-trend up">↑ 5.1% 较上周</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon orange">◎</div>
        <div class="stat-info">
          <div class="stat-value">{{ todaySearch }}</div>
          <div class="stat-label">今日检索</div>
          <div class="stat-trend up">↑ 12 较昨日</div>
        </div>
      </div>
      <div class="stat-card card">
        <div class="stat-icon purple">⚠</div>
        <div class="stat-info">
          <div class="stat-value">{{ warningCount }}</div>
          <div class="stat-label">待处理预警</div>
          <div class="stat-trend down">↓ 3 较昨日</div>
        </div>
      </div>
    </section>

    <!-- 快捷入口 + 设备状态可视化 -->
    <section class="main-grid">
      <!-- 快捷入口 -->
      <div class="quick-section">
        <h2 class="section-title">快速操作</h2>
        <div class="quick-grid">
          <router-link to="/search" class="quick-card card">
            <span class="quick-icon">◎</span>
            <span class="quick-label">AI 智能检索</span>
            <span class="quick-desc">输入故障描述，获取结构化分析报告</span>
            <span class="quick-cta">开始检索 →</span>
          </router-link>
          <router-link to="/guide" class="quick-card card">
            <span class="quick-icon">⇢</span>
            <span class="quick-label">作业指导</span>
            <span class="quick-desc">标准操作流程与安全规范查询</span>
            <span class="quick-cta">查看规程 →</span>
          </router-link>
          <router-link to="/case" class="quick-card card">
            <span class="quick-icon">▣</span>
            <span class="quick-label">案例库</span>
            <span class="quick-desc">历史故障案例检索与参考</span>
            <span class="quick-cta">浏览案例 →</span>
          </router-link>
        </div>
      </div>

      <!-- 设备健康度雷达 -->
      <div class="health-section card">
        <div class="section-header">
          <h2 class="section-title">设备健康度分布</h2>
          <span class="section-meta">实时</span>
        </div>
        <div class="health-bars">
          <div class="health-item" v-for="h in healthData" :key="h.name">
            <div class="health-label-row">
              <span class="health-name">{{ h.name }}</span>
              <span class="health-value" :class="'val-' + h.level">{{ h.value }}%</span>
            </div>
            <div class="health-track">
              <div
                class="health-fill"
                :class="'fill-' + h.level"
                :style="{ width: h.value + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="bottom-grid">
      <!-- 故障预警 -->
      <div class="warning-section card">
        <div class="section-header">
          <h2 class="section-title">
            <span class="warning-icon">⚠</span>
            近期故障预警
          </h2>
          <span class="badge">{{ warningCount }}</span>
        </div>
        <div class="warning-list">
          <div class="warning-item" v-for="(w, i) in warnings" :key="i">
            <div class="w-level" :class="'lv-' + w.level"></div>
            <div class="w-body">
              <div class="w-title">
                {{ w.title }}
                <span class="w-tag" :class="'tag-' + w.level">{{ w.levelText }}</span>
              </div>
              <div class="w-meta">
                <span>◈ {{ w.device }}</span>
                <span>·</span>
                <span>{{ w.time }}</span>
              </div>
            </div>
            <button class="w-action" @click="handleWarning(w)">处置</button>
          </div>
          <div class="warning-empty" v-if="warnings.length === 0">暂无预警</div>
        </div>
      </div>

      <!-- 最近活动 -->
      <div class="activity-section card">
        <div class="section-header">
          <h2 class="section-title">最近活动</h2>
          <router-link to="/case" class="more-link">查看全部 →</router-link>
        </div>
        <div class="activity-list">
          <div class="activity-item" v-for="(item, i) in activities" :key="i">
            <span class="activity-dot" :class="item.type"></span>
            <div class="activity-content">
              <div class="activity-title">{{ item.title }}</div>
              <div class="activity-meta">
                <span class="activity-user">{{ item.user }}</span>
                <span class="activity-time">{{ item.time }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script>
export default {
  name: 'Home',
  data() {
    return {
      currentTime: '',
      currentDate: '',
      totalDevices: 128,
      knowledgeCount: 1024,
      todaySearch: 47,
      warningCount: 5,
      healthData: [
        { name: '旋转机械', value: 86, level: 'good' },
        { name: '电机系统', value: 72, level: 'mid' },
        { name: '液压系统', value: 91, level: 'good' },
        { name: '仪表测控', value: 64, level: 'low' },
        { name: '压力容器', value: 95, level: 'good' },
        { name: '输送装置', value: 58, level: 'low' }
      ],
      warnings: [
        { title: '3#离心泵振动值持续走高', level: 'high', levelText: '严重', device: '离心泵 P-103', time: '12 分钟前' },
        { title: '2#电机绝缘电阻下降', level: 'mid', levelText: '注意', device: '三相电机 M-202', time: '45 分钟前' },
        { title: '5#输送带托辊异响', level: 'mid', levelText: '注意', device: '皮带输送机 C-105', time: '1 小时前' },
        { title: '油箱液位低于下限', level: 'low', levelText: '提示', device: '液压站 H-301', time: '2 小时前' },
        { title: '压力变送器超差需校准', level: 'low', levelText: '提示', device: '变送器 PT-407', time: '3 小时前' }
      ],
      activities: [
        { title: '离心泵轴承过热故障分析完成', user: '张工', time: '5 分钟前', type: 'blue' },
        { title: '新增案例：电机绝缘老化处理', user: '李工', time: '1 小时前', type: 'green' },
        { title: '系统自检完成，所有模块正常', user: '系统', time: '3 小时前', type: 'orange' },
        { title: '知识库更新：阀门检修规程 v2.1', user: '王工', time: '昨天 18:24', type: 'blue' },
        { title: '作业指导新增「变频器调试」', user: '赵工', time: '昨天 14:10', type: 'green' }
      ]
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
      this.currentTime = now.toLocaleTimeString('zh-CN', {
        hour12: false,
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
      })
      this.currentDate = now.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        weekday: 'long'
      })
    },
    handleWarning(w) {
      this.$router.push({ path: '/search', query: { q: w.title } })
    }
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

.hero-title {
  font-size: 2rem;
  margin-bottom: 8px;
}

.text-primary {
  color: var(--primary);
}

.hero-sub {
  color: var(--text-secondary);
  font-size: 1rem;
  margin-bottom: 16px;
}

.hero-status {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  flex-wrap: wrap;
}

.hero-status .sep {
  color: var(--text-muted);
  margin: 0 4px;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.online {
  background: var(--accent-green);
  box-shadow: 0 0 8px var(--accent-green);
}

.status-dot.warning {
  background: var(--accent-orange);
  box-shadow: 0 0 8px var(--accent-orange);
}

.time-display {
  text-align: right;
}

.time-label {
  font-size: 0.75rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 1px;
}

.time-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 1.5rem;
  color: var(--primary);
  font-weight: 700;
  line-height: 1.2;
}

.date-value {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 28px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
}

.stat-icon {
  width: 52px;
  height: 52px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.375rem;
  flex-shrink: 0;
}

.stat-icon.blue { color: var(--primary); background: var(--primary-subtle); border: 1px solid rgba(0, 212, 255, 0.2); }
.stat-icon.green { color: var(--accent-green); background: rgba(0, 255, 136, 0.1); border: 1px solid rgba(0, 255, 136, 0.15); }
.stat-icon.orange { color: var(--accent-orange); background: rgba(255, 107, 53, 0.1); border: 1px solid rgba(255, 107, 53, 0.15); }
.stat-icon.purple { color: #a855f7; background: rgba(168, 85, 247, 0.1); border: 1px solid rgba(168, 85, 247, 0.15); }

.stat-info { flex: 1; }

.stat-value {
  font-size: 1.625rem;
  font-weight: 700;
  font-family: 'Orbitron', sans-serif;
  line-height: 1.1;
}

.stat-label {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-top: 4px;
}

.stat-trend {
  font-size: 0.6875rem;
  font-family: 'JetBrains Mono', monospace;
  margin-top: 6px;
}
.stat-trend.up { color: var(--accent-green); }
.stat-trend.down { color: var(--accent-orange); }

/* 通用区块 */
.main-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
  margin-bottom: 28px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 1rem;
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 1px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-meta {
  font-size: 0.6875rem;
  font-family: 'JetBrains Mono', monospace;
  color: var(--primary);
  padding: 2px 8px;
  background: var(--primary-subtle);
  border-radius: 2px;
}

.badge {
  background: var(--accent-orange);
  color: var(--bg-deep);
  font-size: 0.6875rem;
  font-weight: 700;
  border-radius: 999px;
  padding: 2px 8px;
  min-width: 20px;
  text-align: center;
}

.more-link {
  font-size: 0.75rem;
  color: var(--primary);
  text-decoration: none;
  cursor: pointer;
}
.more-link:hover { color: var(--primary-dim); }

/* 快捷入口 */
.quick-section { min-width: 0; }

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  height: 100%;
}

.quick-card {
  display: flex;
  flex-direction: column;
  gap: 8px;
  text-decoration: none;
  color: inherit;
  padding: 22px 20px;
}

.quick-icon {
  font-size: 1.75rem;
  color: var(--primary);
  margin-bottom: 4px;
}

.quick-label {
  font-size: 0.9375rem;
  font-weight: 600;
}

.quick-desc {
  font-size: 0.8125rem;
  color: var(--text-secondary);
  line-height: 1.5;
  flex: 1;
}

.quick-cta {
  font-size: 0.75rem;
  color: var(--primary);
  font-weight: 500;
  margin-top: 6px;
}

/* 健康度分布 */
.health-section {
  display: flex;
  flex-direction: column;
  padding: 22px 20px;
}

.health-bars {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.health-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.health-label-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.health-name {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.health-value {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.75rem;
  font-weight: 600;
}
.health-value.val-good { color: var(--accent-green); }
.health-value.val-mid { color: var(--accent-orange); }
.health-value.val-low { color: var(--accent-red); }

.health-track {
  width: 100%;
  height: 8px;
  background: rgba(255,255,255,0.06);
  border-radius: 999px;
  overflow: hidden;
}

.health-fill {
  height: 100%;
  border-radius: 999px;
  transition: width 0.8s var(--ease);
}
.health-fill.fill-good { background: linear-gradient(90deg, var(--accent-green), #00d084); box-shadow: 0 0 8px rgba(0, 255, 136, 0.4); }
.health-fill.fill-mid { background: linear-gradient(90deg, var(--accent-amber), var(--accent-orange)); box-shadow: 0 0 8px rgba(255, 165, 2, 0.4); }
.health-fill.fill-low { background: linear-gradient(90deg, var(--accent-red), #ff6b6b); box-shadow: 0 0 8px rgba(255, 71, 87, 0.4); }

/* 底部网格 */
.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

/* 故障预警 */
.warning-section { padding: 22px 20px; }

.warning-icon { color: var(--accent-orange); }

.warning-list {
  display: flex;
  flex-direction: column;
}

.warning-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border-subtle);
}
.warning-item:last-child { border-bottom: none; }

.w-level {
  width: 4px;
  height: 32px;
  border-radius: 2px;
  flex-shrink: 0;
}
.w-level.lv-high { background: var(--accent-red); box-shadow: 0 0 6px var(--accent-red); }
.w-level.lv-mid { background: var(--accent-orange); box-shadow: 0 0 6px var(--accent-orange); }
.w-level.lv-low { background: var(--accent-amber); }

.w-body { flex: 1; min-width: 0; }

.w-title {
  font-size: 0.875rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.w-tag {
  font-size: 0.625rem;
  padding: 1px 6px;
  border-radius: 2px;
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
  font-weight: 600;
}
.w-tag.tag-high { color: var(--accent-red); background: rgba(255,71,87,0.1); }
.w-tag.tag-mid { color: var(--accent-orange); background: rgba(255,107,53,0.1); }
.w-tag.tag-low { color: var(--accent-amber); background: rgba(255,165,2,0.1); }

.w-meta {
  margin-top: 4px;
  display: flex;
  gap: 6px;
  font-size: 0.75rem;
  color: var(--text-muted);
}

.w-action {
  padding: 4px 12px;
  font-size: 0.75rem;
  background: var(--primary-subtle);
  border: 1px solid var(--border-active);
  color: var(--primary);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  font-family: inherit;
}
.w-action:hover { background: var(--primary); color: var(--bg-deep); }

.warning-empty {
  padding: 32px 0;
  text-align: center;
  color: var(--text-muted);
  font-size: 0.875rem;
}

/* 活动列表 */
.activity-section { padding: 22px 20px; }

.activity-list { display: flex; flex-direction: column; }

.activity-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 4px;
  border-bottom: 1px solid var(--border-subtle);
}
.activity-item:last-child { border-bottom: none; }

.activity-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-top: 6px;
  flex-shrink: 0;
}
.activity-dot.blue { background: var(--primary); }
.activity-dot.green { background: var(--accent-green); }
.activity-dot.orange { background: var(--accent-orange); }

.activity-content { flex: 1; }

.activity-title {
  font-size: 0.875rem;
}

.activity-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
}

.activity-user {
  font-size: 0.75rem;
  color: var(--text-secondary);
}

.activity-time {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}
</style>
