<template>
  <div class="container">
    <header class="page-header">
      <h1 class="page-title">作业指导</h1>
      <p class="page-desc">标准操作流程与安全规范 · 共 {{ steps.length }} 项作业规程</p>
    </header>

    <!-- 工具栏 -->
    <div class="guide-toolbar">
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

    <!-- 进度概览 -->
    <div class="progress-summary card" v-if="currentCat === '全部'">
      <div class="progress-item" v-for="s in summaryStats" :key="s.name">
        <div class="progress-name">{{ s.name }}</div>
        <div class="progress-bar-wrap">
          <div class="progress-bar" :style="{ width: s.percent + '%', background: s.color }"></div>
        </div>
        <div class="progress-count">{{ s.count }} 项</div>
      </div>
    </div>

    <!-- 时间线 -->
    <div class="timeline">
      <div v-for="(step, i) in filteredSteps" :key="i" class="timeline-item">
        <div class="timeline-marker">
          <div class="timeline-dot" :class="'cat-' + catClass(step.cat)"></div>
          <div v-if="i < filteredSteps.length - 1" class="timeline-line" :class="'line-' + catClass(step.cat)"></div>
        </div>
        <div class="timeline-content card" @click="step.open = !step.open">
          <div class="step-header">
            <div class="step-header-left">
              <span class="step-num">STEP {{ String(i + 1).padStart(2, '0') }}</span>
              <span class="step-cat-chip" :class="'cat-' + catClass(step.cat)">{{ step.cat }}</span>
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
                  :class="{ checked: step._done?.[ci] }"
                  @click.stop="toggleCheck(step, ci)"
                >
                  <span class="check-box">{{ step._done?.[ci] ? '✓' : '' }}</span>
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
              <div class="step-footer" v-if="step.estimate">
                <span class="estimate">⏱ 预计用时：{{ step.estimate }}</span>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="filteredSteps.length === 0" class="empty-state">
      <div class="empty-icon">⇢</div>
      <p>未找到匹配的作业步骤</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Guide',
  data() {
    return {
      currentCat: '全部',
      searchQuery: '',
      categories: ['全部', '机械', '电气', '安全', '液压', '仪表'],
      steps: [
        {
          cat: '机械',
          title: '拆卸前的准备工作',
          desc: '确认设备已完全停止运转，电源已切断并挂锁。准备好专用工具和清洁布，对零部件进行编号标记。',
          warn: '必须确保设备完全停止，禁止带载操作',
          estimate: '15 分钟',
          checklist: [
            '确认停机挂牌（LOTO）已落实',
            '介质出入口阀门已关闭并泄压',
            '专用工具、量具已备齐并校验',
            '零件编号标签准备完毕'
          ],
          refs: ['设备操作规程 §3.2', 'LOTO 安全管理制度'],
          open: true
        },
        {
          cat: '机械',
          title: '轴承拆卸与检查',
          desc: '使用拉马或液压工具均匀施力拆卸轴承。检查轴颈表面是否有磨损、划痕或腐蚀。测量轴颈尺寸，超出公差范围需更换。',
          estimate: '40 分钟',
          checklist: [
            '选择合适规格的三爪拉马',
            '施力方向与轴心保持一致',
            '轴颈表面清洁后做外观检查',
            '用千分尺测量轴颈圆度与圆柱度'
          ],
          refs: ['滚动轴承检修规程 §4.1'],
          open: false
        },
        {
          cat: '机械',
          title: '轴与联轴器对中校正',
          desc: '使用双表法测量径向和端面跳动，通过垫片调整电机底座，确保对中偏差在允许范围内。',
          warn: '严禁在运行状态下进行对中调整',
          estimate: '60 分钟',
          checklist: [
            '装好磁力表架，表针预压 1~2mm',
            '记录 0°、90°、180°、270° 四点读数',
            '径向偏差 ≤ 0.05mm，端面偏差 ≤ 0.03mm',
            '紧固地脚螺栓后复核对中值'
          ],
          refs: ['联轴器对中作业指导书'],
          open: false
        },
        {
          cat: '电气',
          title: '电机绕组检测',
          desc: '使用兆欧表测量绕组绝缘电阻，不低于 0.5MΩ。检查接线端子有无松动、烧蚀痕迹。',
          warn: '测试前必须断电并放电',
          estimate: '20 分钟',
          checklist: [
            '电机三相电源已断开并挂牌',
            '绕组对地充分放电（至少 1 分钟）',
            '500V 兆欧表测量相间/对地绝缘',
            '记录温度并换算至基准温度'
          ],
          refs: ['电机定期试验规程 §5'],
          open: false
        },
        {
          cat: '电气',
          title: '配电柜停电检修作业',
          desc: '执行停电、验电、挂地线、挂牌等安全步骤后再进行检修作业。',
          warn: '必须严格执行"两票三制"，严禁约时停送电',
          estimate: '30 分钟',
          checklist: [
            '办理工作票并获得许可',
            '操作票顺序停电并确认',
            '用合格验电器逐相验电',
            '在来电侧挂设三相短路接地线'
          ],
          refs: ['电业安全工作规程（发电厂和变电站部分）'],
          open: false
        },
        {
          cat: '电气',
          title: '变频器参数备份与调试',
          desc: '检修前通过操作面板或调试软件备份全部参数，装配完成后按负载特性重新核对关键参数。',
          estimate: '25 分钟',
          checklist: [
            '记录型号、固件版本与 SN 号',
            '使用专用软件或 SD 卡备份参数组',
            '核对电机铭牌参数（功率/电压/电流/极数）',
            '空载试运行并检查 U/f 曲线及电流波形'
          ],
          refs: ['变频器调试手册 §3'],
          open: false
        },
        {
          cat: '机械',
          title: '密封件更换',
          desc: '清理密封腔，检查轴套磨损。新密封件安装前涂抹适量润滑脂，注意方向正确。',
          estimate: '25 分钟',
          checklist: [
            '核对新密封件型号、材质、尺寸',
            '密封腔及轴套无残留与划伤',
            '弹簧侧朝向介质侧（或按箭头方向）',
            '安装后盘车无卡阻、无异常泄漏'
          ],
          refs: ['机械密封安装指南'],
          open: false
        },
        {
          cat: '液压',
          title: '液压系统换油与清洗',
          desc: '系统排空旧油后用专用冲洗油循环清洗，再注入同牌号新液压油并排气。',
          warn: '不同品牌、不同黏度等级液压油禁止混用',
          estimate: '90 分钟',
          checklist: [
            '油温 40°C 左右时放油，杂质随油带出',
            '油箱内壁用白面团粘净金属屑',
            '更换回油、吸油及高压过滤器滤芯',
            '注油至液位上限后空载循环排气 15 分钟'
          ],
          refs: ['液压系统维护规程 §6.2'],
          open: false
        },
        {
          cat: '仪表',
          title: '压力变送器现场校准',
          desc: '采用手持压力泵 + 精密数字压力表在现场对变送器做三点校准，记录误差并修正。',
          estimate: '35 分钟',
          checklist: [
            '关闭引压阀并泄压，拆下变送器',
            '0%、50%、100% 三点升压/降压各读取两次',
            '误差 ≤ 0.5%FS，否则调整零点与量程',
            '安装后做泄漏检查并在 DCS 侧核对读数'
          ],
          refs: ['过程仪表校准规范 JJF 1183'],
          open: false
        },
        {
          cat: '安全',
          title: '受限空间作业准入',
          desc: '按照"先通风、再检测、后作业"原则，落实气体检测、监护人、救援预案等措施。',
          warn: '作业期间监护人严禁离开，每 30 分钟复测一次气体浓度',
          estimate: '30 分钟（准入前）',
          checklist: [
            '办理受限空间作业票并经审批',
            '强制通风不少于 30 分钟',
            '检测 O₂ 19.5%~23.5%、可燃气体 LEL<10%、有毒气体合格',
            '外部监护人到位、三角架/救生索布好、通讯畅通'
          ],
          refs: ['GB 30871 化学品生产单位特殊作业安全规范'],
          open: false
        },
        {
          cat: '安全',
          title: '试运转与验收',
          desc: '装配完成后手动盘车确认无异常。通电试运行 30 分钟，监测振动、温度、电流三项指标。记录试运行数据。',
          warn: '试运转期间人员保持安全距离',
          estimate: '45 分钟',
          checklist: [
            '手动盘车 3~5 转无卡阻',
            '点动试车确认转向正确',
            '空载 15 分钟 + 额定负载 15 分钟',
            '振动、温度、电流记录齐全并签字验收'
          ],
          refs: ['设备检修验收规范 §7'],
          open: false
        },
        {
          cat: '仪表',
          title: '调节阀检修与定位器校准',
          desc: '解体清洗阀芯阀座，研磨密封面，更换填料。装配后对阀门定位器做行程校准。',
          estimate: '75 分钟',
          checklist: [
            '阀体介质排净并置换合格',
            '阀芯阀座密封面做着色或煤油渗漏试验',
            '填料函按对角线交替压紧，无卡阻',
            '4~20mA 输入对应 0~100% 行程，误差 ≤ 1%'
          ],
          refs: ['调节阀检修规程 §5.3'],
          open: false
        }
      ]
    }
  },
  computed: {
    filteredSteps() {
      let list = this.steps
      if (this.currentCat !== '全部') {
        list = list.filter(s => s.cat === this.currentCat)
      }
      const q = this.searchQuery.trim().toLowerCase()
      if (q) {
        list = list.filter(s =>
          s.title.toLowerCase().includes(q) ||
          s.desc.toLowerCase().includes(q) ||
          (s.checklist || []).some(x => x.toLowerCase().includes(q))
        )
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
      const total = this.steps.length || 1
      return this.categories
        .filter(c => c !== '全部')
        .map(name => ({
          name,
          count: this.categoryCount(name),
          percent: Math.round(this.categoryCount(name) / total * 100),
          color: colorMap[name] || 'var(--primary)'
        }))
    }
  },
  methods: {
    catClass(cat) {
      return ({ '机械': 'blue', '电气': 'green', '安全': 'orange', '液压': 'purple', '仪表': 'cyan' })[cat] || 'blue'
    },
    categoryCount(cat) {
      if (cat === '全部') return this.steps.length
      return this.steps.filter(s => s.cat === cat).length
    },
    toggleCheck(step, idx) {
      if (!step._done) this.$set(step, '_done', [])
      this.$set(step._done, idx, !step._done[idx])
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

/* 工具栏 */
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

/* 进度概览 */
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

/* 时间线 */
.timeline {
  position: relative;
}

.timeline-item {
  display: flex;
  gap: 20px;
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

.timeline-line {
  width: 2px;
  flex: 1;
  background: var(--border-subtle);
  margin: 4px 0;
}

/* 卡片内容 */
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

/* 检查清单 */
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

/* 参考标签 */
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
}

.estimate {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

/* 动画 */
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

/* 空状态 */
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
</style>
