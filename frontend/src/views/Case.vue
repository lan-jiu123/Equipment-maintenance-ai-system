<template>
  <div class="container">
    <header class="page-header">
      <h1 class="page-title">案例库</h1>
      <p class="page-desc">历史故障案例检索与参考 · 共 {{ cases.length }} 条案例</p>
    </header>

    <!-- 搜索 + 筛选 -->
    <div class="search-toolbar">
      <div class="search-bar">
        <span class="search-icon">⌕</span>
        <input v-model="searchQuery" class="input" placeholder="搜索案例标题、设备类型、故障类型..." />
      </div>
      <div class="filter-tags">
        <button
          v-for="t in tagList"
          :key="t"
          class="filter-tag"
          :class="{ active: currentTag === t }"
          @click="currentTag = t"
        >{{ t }}</button>
      </div>
    </div>

    <!-- 案例网格 -->
    <div class="case-grid">
      <div
        v-for="(c, i) in filteredCases"
        :key="i"
        class="case-card card"
        :class="{ expanded: c._open }"
        @click="toggleCase(c)"
      >
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

        <!-- 展开详情 -->
        <transition name="expand">
          <div v-show="c._open" class="case-detail">
            <div class="detail-section">
              <div class="detail-label">故障现象</div>
              <p class="detail-text">{{ c.detail?.symptom || '暂无详细描述' }}</p>
            </div>
            <div class="detail-section">
              <div class="detail-label">诊断过程</div>
              <ol class="detail-list">
                <li v-for="(s, idx) in (c.detail?.diagnosis || [])" :key="idx">{{ s }}</li>
              </ol>
            </div>
            <div class="detail-section">
              <div class="detail-label">处置方案</div>
              <ul class="detail-list bullet">
                <li v-for="(s, idx) in (c.detail?.solution || [])" :key="idx">{{ s }}</li>
              </ul>
            </div>
            <div class="detail-section tips" v-if="c.detail?.tips">
              <div class="detail-label">经验与建议</div>
              <p class="detail-text">{{ c.detail.tips }}</p>
            </div>
            <div class="expand-arrow">▲ 收起</div>
          </div>
        </transition>

        <div class="toggle-hint" v-if="!c._open">点击查看详情 ▼</div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="filteredCases.length === 0" class="empty-state">
      <div class="empty-icon">▣</div>
      <p>未找到匹配的案例</p>
      <p class="empty-sub">尝试更换搜索关键词或选择其他分类</p>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Case',
  data() {
    return {
      searchQuery: '',
      currentTag: '全部',
      tagList: ['全部', '机械', '电气', '安全', '液压', '仪表'],
      cases: [
        {
          title: '离心泵轴承过热故障分析',
          tag: '机械',
          tagClass: 'blue',
          severity: 'high',
          date: '2024-12-15',
          summary: '某化工厂离心泵运行中轴承温度持续上升，最高达 95°C。经检查发现润滑脂老化变质，轴承滚道出现疲劳剥落。',
          device: '离心泵',
          fault: '轴承过热',
          detail: {
            symptom: '轴承端盖温度异常，运行时伴有沉闷金属摩擦声，振动值超标至 6.8mm/s。',
            diagnosis: [
              '使用测温枪测量轴承座各点温度，确认最高温度位于非驱动端轴承',
              '采集振动频谱分析，出现明显的轴承缺陷特征频率',
              '停机拆检后发现润滑脂碳化变黑，轴承滚道有明显疲劳剥落痕迹',
              '核对检修记录，距上次注脂已运行 4200 小时，超过规定周期'
            ],
            solution: [
              '更换同型号 SKF 6312-2RS 轴承一套',
              '清洗轴承腔并重新加注牌号为 Shell Alvania EP2 的润滑脂',
              '调整轴承间隙至 0.03~0.05mm 范围',
              '更新润滑维护周期表，注脂周期设定为 3000 小时'
            ],
            tips: '高温环境下轴承润滑脂寿命会缩短 30%~50%，建议增加巡检频次。'
          }
        },
        {
          title: '三相电机启动困难处理',
          tag: '电气',
          tagClass: 'green',
          severity: 'medium',
          date: '2024-12-10',
          summary: '电机启动时转速异常缓慢，电流持续偏高。检测发现定子绕组存在相间绝缘老化，需重绕线圈。',
          device: '三相异步电机',
          fault: '启动困难',
          detail: {
            symptom: '启动时间超过 15 秒，额定负载下无法达到额定转速，运行电流比正常值高 35%。',
            diagnosis: [
              '使用钳形电流表测量三相电流，发现三相不平衡度达 12%',
              '用兆欧表测量绝缘电阻，相间绝缘仅 0.12MΩ，远低于 0.5MΩ 标准',
              '直流电阻测试显示 A 相绕组电阻偏大 8%',
              '拆检发现绕组端部有绝缘老化龟裂及局部烧蚀痕迹'
            ],
            solution: [
              '拆除旧绕组并做好槽型及匝数记录',
              '使用同规格 QZY-2 180 级耐高温漆包线重绕线圈',
              '采用 VPI 真空压力浸漆工艺处理，150°C 烘干 12 小时',
              '组装后完成空载、短路及温升试验合格'
            ],
            tips: '潮湿环境下的电机应每 3 个月测量一次绝缘电阻，不合格时需烘干处理。'
          }
        },
        {
          title: '减速箱齿轮磨损修复',
          tag: '机械',
          tagClass: 'blue',
          severity: 'high',
          date: '2024-12-05',
          summary: '减速箱运行中出现周期性异响，拆解后发现高速级齿轮齿面点蚀严重，润滑油金属颗粒超标。',
          device: '齿轮减速箱',
          fault: '齿轮磨损',
          detail: {
            symptom: '减速箱有明显周期性异响，每转一圈出现一次冲击声，输出端有不规则跳动。',
            diagnosis: [
              '采集润滑油样做铁谱分析，发现大量齿轮磨损颗粒',
              '振动频谱存在明显的齿轮啮合频率及其谐波',
              '拆机检查高速级小齿轮，齿面出现 0.3mm 深的点蚀坑，分布在节圆附近',
              '轴承轴向间隙检测为 0.25mm，超出 0.08mm 标准'
            ],
            solution: [
              '更换同模数齿数的渗碳淬火齿轮副（材质 20CrMnTi）',
              '更换输入端圆锥滚子轴承，调整轴向间隙至 0.04~0.06mm',
              '清洗齿轮箱内部所有油路及油池',
              '加注 ISO VG320 工业极压齿轮油至规定油位'
            ],
            tips: '更换齿轮后 500 小时需首次换油，之后按 5000 小时周期换油。'
          }
        },
        {
          title: 'PLC 控制系统通信故障',
          tag: '电气',
          tagClass: 'green',
          severity: 'low',
          date: '2024-11-28',
          summary: '生产线 PLC 与上位机通信频繁中断。检查发现通信电缆屏蔽层接地不良，重新规范接地后恢复正常。',
          device: 'PLC 系统',
          fault: '通信中断',
          detail: {
            symptom: '上位机随机出现"通信超时"报警，每次持续 2~10 秒，每天发生 10~20 次不等。',
            diagnosis: [
              '抓取通信报文分析，存在大量 CRC 校验错误包',
              '使用示波器测量通信线，发现共模干扰尖峰达 5V 以上',
              '检查通信电缆走向，发现与动力电缆并行敷设距离超过 8 米',
              '检测屏蔽层接地情况，发现两端均未有效接地，且屏蔽层有断点'
            ],
            solution: [
              '更换带整体屏蔽的 Profibus DP 专用电缆',
              '重新规划布线，与动力电缆间距保持 30cm 以上',
              '通信屏蔽层在控制柜侧做单端可靠接地',
              '在 DP 总线终端加装有源终端电阻器'
            ],
            tips: '工业通信线缆建议每两年做一次性能检测，包括衰减、阻抗、屏蔽连续性。'
          }
        },
        {
          title: '压力容器安全阀校验',
          tag: '安全',
          tagClass: 'orange',
          severity: 'high',
          date: '2024-11-20',
          summary: '压力容器安全阀定期校验，发现起跳压力偏离设定值。清洗调整弹簧并重新校验合格。',
          device: '压力容器',
          fault: '安全阀异常',
          detail: {
            symptom: '年度送检校验，DN50 弹簧微启式安全阀起跳压力实测 1.12MPa，与整定值 1.0MPa 偏差 12%。',
            diagnosis: [
              '外观检查发现阀杆有轻微锈蚀痕迹',
              '拆卸后发现弹簧表面有腐蚀斑点，刚度下降',
              '密封面有微量积垢，可能导致阀门提前开启',
              '核对使用记录：已连续使用 4 年未解体检查'
            ],
            solution: [
              '使用金相砂纸逐道研磨密封面至镜面效果，做煤油渗漏试验合格',
              '更换同规格弹簧（材料 50CrVA）',
              '阀杆、导向套除锈、抛光，涂抹高温防卡剂',
              '在专用校验台上重新整定开启压力至 1.0MPa，偏差控制在 ±3% 以内'
            ],
            tips: '安全阀一般每年至少校验一次；用于腐蚀性介质的应缩短校验周期。'
          }
        },
        {
          title: '输送带跑偏调整',
          tag: '机械',
          tagClass: 'blue',
          severity: 'low',
          date: '2024-11-15',
          summary: '输送带运行时持续跑偏，调整托辊角度并张紧皮带后问题解决。需定期检查托辊转动灵活性。',
          device: '皮带输送机',
          fault: '跑偏',
          detail: {
            symptom: '皮带输送机长度 48m，带宽 B=800mm，运行时尾部向左侧跑偏 80mm，导致频繁撒料和边缘磨损。',
            diagnosis: [
              '空载运行观察跑偏位置，定位跑偏起始点在尾部改向滚筒处',
              '检查头尾滚筒平行度，误差 5mm/米，超出标准',
              '发现有 4 组托辊转动不灵活，其中 1 组卡死',
              '尾部重锤张紧装置配重块数量不足 3 块，张力偏小'
            ],
            solution: [
              '调整尾部改向滚筒左右张紧螺杆，使滚筒与机架中心线垂直度≤1mm/m',
              '更换 4 组损坏托辊，润滑其余所有托辊轴承',
              '添加张紧配重 3 块，使张紧力符合设计值',
              '在跑偏段加装 2 组自动调心托辊组做辅助纠偏'
            ],
            tips: '每次开机前应空转一周检视皮带状态；运行初期 30 分钟是跑偏易发期。'
          }
        },
        {
          title: '液压系统油温过高处理',
          tag: '液压',
          tagClass: 'purple',
          severity: 'medium',
          date: '2024-11-08',
          summary: '注塑机液压系统连续运行 2 小时后油温超过 75°C，报警停机。清洗冷却器、更换液压油后恢复正常。',
          device: '液压系统',
          fault: '油温过高',
          detail: {
            symptom: '系统压力正常但油温持续升高，超过 75°C 触发高温保护停机，冷却器进出口温差不足 3°C。',
            diagnosis: [
              '检查冷却水管路，流量正常但散热效果差',
              '拆解冷却器发现列管内壁结垢严重，厚度约 1.5mm',
              '油液检测发现黏度下降 22%，酸值超标',
              '溢流阀存在内泄，阀芯磨损导致节流发热增加'
            ],
            solution: [
              '对冷却器做化学除垢清洗，并做水压试验合格',
              '更换全部 L-HM46 抗磨液压油，清洗油箱和过滤器',
              '解体清洗溢流阀，配研阀芯或更换新阀',
              '增设 45°C 自动启风扇、60°C 报警的温度控制策略'
            ],
            tips: '液压系统推荐工作温度 30~60°C；长期超过 70°C 会大幅缩短密封件寿命。'
          }
        },
        {
          title: '压力变送器示值偏差校准',
          tag: '仪表',
          tagClass: 'cyan',
          severity: 'low',
          date: '2024-10-30',
          summary: '蒸汽管道压力变送器示值偏高 6%，现场校准后恢复准确。发现是引压管积液导致零点漂移。',
          device: '压力变送器',
          fault: '示值偏差',
          detail: {
            symptom: 'DCS 显示压力 2.35MPa，经标准压力表比对实测为 2.21MPa，偏差约 6%。',
            diagnosis: [
              '对变送器做 4~20mA 输出校验，线性误差在允许范围内',
              '检查零点发现有正偏移 0.14MPa，对应引压管液柱高度约 10m',
              '拆开引压管排放阀，放出约 150mL 冷凝水',
              '确认变送器安装位置低于取压点，未安装冷凝罐'
            ],
            solution: [
              '在引压管根部加装Φ100mm 冷凝罐，防止蒸汽直接进入变送器',
              '对变送器做零点迁移调整，扣除残余液柱静压影响',
              '重新对 0、50%、100% 三点做三点校准，误差≤0.2%FS',
              'DCS 量程与变送器保持一致，更新仪表台账'
            ],
            tips: '蒸汽压力测量建议在取压点附近安装冷凝罐，并定期（每月一次）排放积液。'
          }
        },
        {
          title: '电动执行器无法全开',
          tag: '仪表',
          tagClass: 'cyan',
          severity: 'medium',
          date: '2024-10-22',
          summary: 'DN200 电动调节阀运行中开到 85% 就无法继续，原因是限位开关凸轮移位，重新调整后正常。',
          device: '电动执行器',
          fault: '无法全开',
          detail: {
            symptom: 'DCS 给定 100% 开度指令，阀门只走到 85% 就停止，手动操作也无法继续打开。',
            diagnosis: [
              '测量执行器输入输出信号，DCS 给 20mA，执行器反馈只有 18.6mA，开位信号已触发',
              '拆开执行器电气罩，检查全开限位开关，发现已提前闭合',
              '检查行程凸轮紧固螺钉，有松动迹象',
              '对比阀杆行程标记，确实还有 15% 机械行程未使用'
            ],
            solution: [
              '先将执行器切换到就地手动模式',
              '手动摇到阀门机械全开位置，固定好阀杆',
              '重新调整全开限位凸轮使其刚好动作，同时调整电位器对应 20mA 输出',
              '做全程开关试验 3 次，验证开度与信号线性一致'
            ],
            tips: '每 6 个月对阀门行程限位与反馈做一次核对，特别是工艺改造或检修后必须重新标定。'
          }
        }
      ]
    }
  },
  computed: {
    filteredCases() {
      let list = this.cases
      if (this.currentTag !== '全部') {
        list = list.filter(c => c.tag === this.currentTag)
      }
      const q = this.searchQuery.trim().toLowerCase()
      if (q) {
        list = list.filter(c =>
          c.title.toLowerCase().includes(q) ||
          c.device.toLowerCase().includes(q) ||
          c.fault.toLowerCase().includes(q) ||
          c.summary.toLowerCase().includes(q)
        )
      }
      return list
    }
  },
  methods: {
    toggleCase(c) {
      this.$set(c, '_open', !c._open)
    },
    severityText(s) {
      return { low: '一般', medium: '较重', high: '严重' }[s] || '一般'
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
</style>
