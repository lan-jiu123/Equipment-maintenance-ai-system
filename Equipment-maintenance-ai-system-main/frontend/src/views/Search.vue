<template>
  <div class="container">
    <div class="search-page">
      <!-- 页面标题 -->
      <header class="page-header">
        <h1 class="page-title">AI 智能检索</h1>
        <p class="page-desc">输入设备故障现象（可上传故障图片），AI 将结合知识库输出结构化诊断报告</p>
      </header>

      <!-- 快捷操作栏 -->
      <!-- 快捷操作栏（文档流内初始位置）-->
      <div class="chat-toolbar">
        <div class="toolbar-left">
          <button class="btn btn-outline btn-xs" @click="clearChat" :disabled="messages.length === 0">
            清空对话
          </button>
          <button class="btn btn-outline btn-xs" @click="clearHistoryConfirm" :disabled="!hasHistory">
            清除历史记录
          </button>
        </div>
        <div class="toolbar-right">
          <span
            class="history-hint history-hint--link"
            v-if="hasHistory"
            @click.stop="onToggleHistory"
          >
            已保存 {{ savedSessions.length }} 轮历史 ▾
          </span>
        </div>
      </div>

      <!-- 悬浮快捷按钮：对话开始后漂浮在右上角，宽度 = 两个按钮 -->
      <div class="fab-toolbar" v-if="messages.length > 0">
        <button class="btn btn-outline btn-xs" @click="clearChat" title="清空对话">清空</button>
        <button class="btn btn-outline btn-xs" @click="clearHistoryConfirm" :disabled="!hasHistory" title="清除历史记录">清历史</button>
      </div>

      <!-- 对话区 -->
      <div class="chat-area" ref="chatArea">
        <!-- 欢迎消息（初始状态） -->
        <div v-if="messages.length === 0" class="welcome-card card">
          <!-- 主体：左（标题+示例）+ 右狗狗 -->
          <div class="welcome-content">
            <div class="welcome-left">
              <div class="welcome-icon">◎</div>
              <h3>欢迎使用智能检索</h3>
              <p>描述设备异常现象、上传故障图片，或点击下方示例快速开始：</p>
              <div class="quick-examples">
                <button
                  v-for="(ex, i) in examples"
                  :key="i"
                  class="example-chip"
                  @click="askWithExample(ex)"
                >
                  <span class="chip-icon">◎</span>
                  <span class="chip-text">{{ ex }}</span>
                </button>
              </div>
            </div>
            <div class="welcome-mascot" aria-hidden="true">
              <img :src="dogPng" alt="" class="mascot-img" />
              <div class="mascot-glow"></div>
            </div>
          </div>
        </div>

        <!-- 消息列表 -->
        <div v-for="(msg, i) in messages" :key="i" class="msg-row" :class="msg.role">
          <div class="msg-bubble">
            <!-- 用户消息：支持图片 -->
            <div v-if="msg.role === 'user'" class="msg-content">
              <img v-if="msg.image" :src="msg.image" alt="用户上传图片" class="user-upload-img" />
              <div v-if="msg.content">{{ msg.content }}</div>
            </div>
            <!-- AI 消息：结构化渲染 + 参考来源 -->
            <div v-else>
              <div class="msg-content structured" v-html="formatAnswer(msg.content)"></div>
              <!-- 参考来源卡片（RAG 检索引用） -->
              <div v-if="msg.citations && msg.citations.length" class="citation-list">
                <div class="citation-title">📚 参考来源</div>
                <a
                  v-for="source in msg.citations"
                  :key="source.id"
                  class="citation-card"
                  :href="source.file_url"
                  target="_blank"
                  rel="noopener"
                >
                  <span class="citation-id">[{{ source.id }}]</span>
                  <span class="citation-main">
                    <strong>《{{ source.document_title }}》</strong>
                    <small>第 {{ source.page_label }} 页 · {{ source.section_title || '未识别章节' }}</small>
                  </span>
                </a>
              </div>
              <!-- 本地知识库 refs（兼容旧 /api/ai/ask 接口返回） -->
              <div v-if="msg.refs && msg.refs.length" class="citation-list">
                <div class="citation-title">📁 内部知识库匹配</div>
                <div
                  v-for="(ref, ri) in msg.refs"
                  :key="ri"
                  class="citation-card"
                >
                  <span class="citation-id">[{{ ri + 1 }}]</span>
                  <span class="citation-main">
                    <strong>{{ kindLabel(ref.kind) }}：{{ ref.title }}</strong>
                    <small v-if="ref.device">设备：{{ ref.device }}</small>
                    <small v-if="ref.solution" class="ref-snippet">{{ (ref.solution || '').slice(0, 80) }}{{ ref.solution && ref.solution.length > 80 ? '…' : '' }}</small>
                  </span>
                </div>
              </div>
            </div>
            <div class="msg-time">{{ formatMsgTime(msg.time) }}<span v-if="msg.llm_via" class="via-tag"> · {{ viaLabel(msg.llm_via) }}</span></div>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="loading" class="msg-row assistant">
          <div class="msg-bubble">
            <div class="typing-indicator">
              <span></span><span></span><span></span>
            </div>
            <div class="msg-time">AI 分析中...</div>
          </div>
        </div>
      </div>

      <!-- 输入区 -->
      <form class="input-area" @submit.prevent="askAI">
        <!-- 图片上传（队友新增） -->
        <div class="image-upload-row">
          <label class="btn btn-outline btn-xs image-picker">
            📷 选择故障图片
            <input
              ref="imageInput"
              type="file"
              accept="image/jpeg,image/png,image/webp"
              :disabled="loading"
              @change="selectImage"
            />
          </label>
          <span class="image-hint">支持 JPG / PNG / WebP，发送前自动压缩</span>
        </div>
        <div v-if="imagePreview" class="image-preview-card">
          <img :src="imagePreview" alt="待诊断图片预览" />
          <div class="image-preview-info">
            <strong>{{ imageFile && imageFile.name }}</strong>
            <small>{{ formatFileSize(imageFile && imageFile.size) }}</small>
            <button type="button" class="remove-image" @click="clearImage" :disabled="loading">移除</button>
          </div>
        </div>
        <textarea
          v-model="question"
          class="input search-input"
          placeholder="输入设备故障描述，按 Ctrl+Enter 发送..."
          :disabled="loading"
          rows="2"
          @keydown="handleKeydown"
        />
        <div class="input-actions">
          <div class="input-tip">{{ question.length }} / 500</div>
          <button type="submit" class="btn btn-primary send-btn" :disabled="loading || (!question.trim() && !imageFile)">
            {{ imageFile ? '图片诊断 ↑' : '发送 ↑' }}
          </button>
        </div>
      </form>

      <!-- AI 未解决 → 贡献方案入口（你的原有功能） -->
      <div v-if="messages.length > 0" class="contrib-row card">
        <div class="contrib-left">
          <span class="contrib-icon">💡</span>
          <div class="contrib-text">
            <div class="contrib-title">AI 没有解决您的问题？</div>
            <div class="contrib-sub">您的现场实践方案，经管理员审核后将写入知识库，帮助更多同事</div>
          </div>
        </div>
        <button class="btn btn-primary btn-sm contrib-btn" @click="openContrib">
          📝 贡献实践方案 →
        </button>
      </div>

      <!-- 历史对话面板 -->
      <div v-if="showHistoryPanel" class="history-panel card">
        <div class="history-panel-header">
          <strong>历史对话</strong>
          <button class="btn btn-outline btn-xs" @click="showHistoryPanel = false">关闭</button>
        </div>
        <div class="history-panel-list">
          <div
            v-for="(s, i) in savedSessions"
            :key="s.id"
            class="history-item"
            @click="loadSession(s)"
          >
            <div class="history-item-dot">{{ i + 1 }}</div>
            <div class="history-item-main">
              <div class="history-item-title">{{ (s.messages.find(m => m.role === 'user') || {}).content || '（无内容）' }}</div>
              <div class="history-item-meta">{{ s.messages.length }} 条消息 · {{ formatDate(s.time) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 提交成功提示 -->
      <transition name="toast">
        <div v-if="toast" class="toast">{{ toast }}</div>
      </transition>
    </div>
  </div>

  <KnowledgeReport
    :visible="reportVisible"
    :preset="reportPreset"
    source="search"
    @update:visible="v => reportVisible = v"
    @submitted="onReportSubmitted"
  />
</template>

<script>
import KnowledgeReport from '../components/KnowledgeReport.vue'
import dogPng from './狗狗 .png'

const STORAGE_KEY = 'equipai_search_history'
const MAX_HISTORY = 10

export default {
  name: 'Search',
  components: { KnowledgeReport },
  data() {
    return {
      dogPng,
      question: '',
      messages: [],
      loading: false,
      savedSessions: [],
      reportVisible: false,
      toast: '',
      showHistoryPanel: false,
      // 图片相关（队友新增）
      imageFile: null,
      imagePreview: '',
      // 示例：合并双方（你的工业设备示例 + 队友的汽车维修示例）
      examples: [
        '离心泵运行时轴承温度超过 80°C，伴随异常振动',
        '电机启动困难，且运行电流明显偏高',
        '减速箱齿轮磨损严重，有异响',
        '输送带运行时持续跑偏，物料洒落',
        '火花塞电极间隙的标准范围是多少？',
        '气缸压缩压力低于标准值时如何进一步判断？'
      ]
    }
  },
  computed: {
    hasHistory() {
      return this.savedSessions.length > 0
    },
    reportPreset() {
      const userQ = this.messages.filter(m => m.role === 'user').slice(-1)[0]
      return {
        type: 'case',
        title: userQ ? ((userQ.content || '').slice(0, 60) || '智能检索场景方案') : '',
        device: '',
        level: 'mid',
        question: userQ
          ? ('用户检索问题：' + (userQ.content || '') + '\n\nAI 给出的方案不够具体/未解决实际问题，现场情况与 AI 建议有出入：（请补充实际差异）')
          : '',
        solution: '',
        ticketId: ''
      }
    }
  },
  created() {
    this.loadHistory()
  },
  mounted() {
    this.$nextTick(() => this.scrollToBottom())
  },
  methods: {
    openContrib() {
      this.reportVisible = true
    },
    onReportSubmitted(rec) {
      this.toast = `✅ 报告「${rec.id}」提交成功，管理员将尽快审核`
      setTimeout(() => this.toast = '', 3500)
    },
    handleKeydown(e) {
      if (e.ctrlKey && e.key === 'Enter') {
        e.preventDefault()
        this.askAI()
      }
    },
    askWithExample(text) {
      this.question = text
      this.askAI()
    },
    // ========== 统一入口：文字 / 图片 ==========
    async askAI() {
      const text = this.question.trim()
      if ((!text && !this.imageFile) || this.loading) return
      if (text.length > 500) return

      // 有图片：走图片诊断接口（队友新增）
      if (this.imageFile) {
        await this.diagnoseImage(text)
        return
      }

      // 纯文字：优先走 RAG 接口（/api/rag/ask），失败自动降级到旧 /api/ai/ask 接口
      this.messages.push({ role: 'user', content: text, time: Date.now() })
      this.question = ''
      this.loading = true
      this.$nextTick(() => this.scrollToBottom())

      let answered = false
      try {
        // ---- 通道 1：队友 RAG 接口（带知识库文档检索 + citations 引用）----
        let ragFallbackNeeded = true
        try {
          const token = localStorage.getItem('equipai_token') || ''
          const res = await fetch('/api/rag/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ question: text, top_k: 5 })
          })
          const data = await res.json()
          // RAG 结果合格的判断：HTTP 成功 + (明确可回答 或 有引用来源)
          if (res.ok && data) {
            const hasAnswer = data.answerable === true || (data.citations && data.citations.length > 0)
            if (hasAnswer && (data.answer || typeof data === 'string')) {
              this.messages.push({
                role: 'assistant',
                content: data.answer || data,
                citations: data.citations || [],
                answerable: data.answerable,
                llm_via: 'rag-hybrid',
                time: Date.now()
              })
              answered = true
              ragFallbackNeeded = false
            }
          }
        } catch (_e) {
          ragFallbackNeeded = true
        }

        // ---- 通道 2：你的原有 /api/ai/ask 接口（本地案例+作业指导+员工报告 + LLM 兜底 / 离线完整结构）----
        // 当 RAG 无结论时必走，保证用户总能拿到【故障现象/原因分析/处理步骤/风险提示】4 段完整答案
        if (!answered) {
          const token = localStorage.getItem('equipai_token') || ''
          const res = await fetch('/api/ai/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify({ text })
          })
          const data = await res.json()
          if (data.code === 200) {
            const payload = data.data || {}
            this.messages.push({
              role: 'assistant',
              content: typeof payload === 'string' ? payload : (payload.answer || JSON.stringify(payload)),
              refs: payload.refs || [],
              llm_via: payload.llm_via || (payload.offline ? 'offline-local' : 'legacy-ai'),
              time: Date.now()
            })
            answered = true
          } else {
            this.messages.push({
              role: 'assistant',
              content: '❌ 请求失败：' + (data.msg || '未知错误'),
              time: Date.now()
            })
            answered = true
          }
        }
      } catch (err) {
        // 通道 3：纯前端离线 demo 兜底（服务器断开也能看演示效果）
        const demoAnswer = this.generateDemoAnswer(text)
        this.messages.push({ role: 'assistant', content: demoAnswer, time: Date.now(), llm_via: 'demo-offline', demo: true })
      } finally {
        this.loading = false
        this.saveCurrentSession()
        this.$nextTick(() => this.scrollToBottom())
      }
    },
    // ========== 图片压缩 + 诊断（队友新增） ==========
    async selectImage(event) {
      const file = event.target.files && event.target.files[0]
      if (!file) return
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        alert('仅支持 JPG、PNG 或 WebP 图片')
        this.clearImage()
        return
      }
      try {
        const compressed = await this.compressImage(file)
        if (this.imagePreview) URL.revokeObjectURL(this.imagePreview)
        this.imageFile = compressed
        this.imagePreview = URL.createObjectURL(compressed)
      } catch (e) {
        alert('图片读取或压缩失败，请更换图片重试')
        this.clearImage()
      }
    },
    compressImage(file) {
      if (file.type === 'image/webp' && file.size <= 2 * 1024 * 1024) return Promise.resolve(file)
      return new Promise((resolve, reject) => {
        const img = new Image()
        const url = URL.createObjectURL(file)
        img.onload = () => {
          const maxSide = 1600
          const scale = Math.min(1, maxSide / Math.max(img.width, img.height))
          const canvas = document.createElement('canvas')
          canvas.width = Math.max(1, Math.round(img.width * scale))
          canvas.height = Math.max(1, Math.round(img.height * scale))
          const ctx = canvas.getContext('2d')
          ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
          URL.revokeObjectURL(url)
          canvas.toBlob(blob => {
            if (!blob) return reject(new Error('canvas export failed'))
            const name = file.name.replace(/\.[^.]+$/, '') + '.jpg'
            resolve(new File([blob], name, { type: 'image/jpeg', lastModified: Date.now() }))
          }, 'image/jpeg', 0.82)
        }
        img.onerror = () => {
          URL.revokeObjectURL(url)
          reject(new Error('image load failed'))
        }
        img.src = url
      })
    },
    async diagnoseImage(note) {
      const file = this.imageFile
      const preview = this.imagePreview
      this.messages.push({
        role: 'user',
        content: note || '请识别这张故障图片并检索相关维修资料。',
        image: preview,
        time: Date.now()
      })
      this.question = ''
      this.loading = true
      this.$nextTick(() => this.scrollToBottom())
      try {
        const form = new FormData()
        form.append('file', file, file.name)
        form.append('note', note)
        form.append('top_k', '5')
        const token = localStorage.getItem('equipai_token') || ''
        const res = await fetch('/api/images/diagnose', {
          method: 'POST',
          headers: { 'Authorization': 'Bearer ' + token },
          body: form
        })
        const data = await res.json()
        if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : '图片诊断失败')
        const vision = data.vision_analysis || {}
        const rag = data.diagnosis || {}
        const facts = (vision.visible_facts || []).join('；') || '未识别到明确可见异常'
        const ocr = (vision.ocr_text || []).join('；') || '未识别到文字或型号'
        const faults = (vision.suspected_faults || []).join('；') || '暂无可靠故障推测'
        const visionText = `【图片识别】\n设备：${vision.equipment || '无法确定'}\n部件：${vision.component || '无法确定'}\n可见事实：${facts}\nOCR：${ocr}\n疑似故障：${faults}\n置信度：${Math.round((vision.confidence || 0) * 100)}%\n人工复核：${vision.review_reason || '建议由专业人员复核'}`
        const retrieval = rag.retrieval || {}
        const coverage = typeof retrieval.lexical_coverage === 'number'
          ? `${Math.round(retrieval.lexical_coverage * 100)}%`
          : '未知'
        const retrievalText = `【检索过程】\n检索关键词：${data.retrieval_query || '未生成'}\n证据关键词覆盖率：${coverage}`
        const ragText = rag.answer || '现有知识库证据不足，未生成检修步骤。'
        this.messages.push({
          role: 'assistant',
          content: visionText + '\n\n' + retrievalText + '\n\n' + ragText,
          citations: rag.citations || [],
          answerable: rag.answerable,
          vision: vision,
          llm_via: 'vision+rag',
          time: Date.now()
        })
        this.clearImage()
      } catch (err) {
        this.messages.push({ role: 'assistant', content: '❌ 图片诊断失败：' + err.message, time: Date.now() })
      } finally {
        this.loading = false
        this.saveCurrentSession()
        this.$nextTick(() => this.scrollToBottom())
      }
    },
    clearImage() {
      if (this.imagePreview) URL.revokeObjectURL(this.imagePreview)
      this.imageFile = null
      this.imagePreview = ''
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    formatFileSize(size) {
      if (!size) return ''
      return size < 1024 * 1024 ? `${Math.round(size / 1024)} KB` : `${(size / 1024 / 1024).toFixed(1)} MB`
    },
    // ========== 工具函数 ==========
    kindLabel(k) {
      return { case: '故障案例', guide: '作业指导', report: '员工方案' }[k] || '知识库条目'
    },
    viaLabel(v) {
      const map = {
        'rag-hybrid': '知识库+AI混合检索',
        'legacy-ai': 'AI 智能模式',
        'offline-local': '本地知识库（离线）',
        'openai-sdk': 'LLM SDK 调用',
        'requests-fallback': 'LLM HTTP 调用',
        'demo-offline': '本地示例（服务器未连接）',
        'vision+rag': '图片识别+知识检索'
      }
      return map[v] || v
    },
    generateDemoAnswer(text) {
      return `【故障初步诊断】\n根据您描述的现象："${text}"，初步判断可能存在以下问题：\n\n【可能原因】\n1. 机械磨损：运动部件长期运行产生疲劳、间隙增大\n2. 润滑失效：润滑油变质或不足，导致摩擦热累积\n3. 安装偏差：同轴度或水平度超出允许范围\n\n【建议检查项】\n- 检查润滑系统状态，确认油位和油质\n- 测量关键部位温度和振动值\n- 检查紧固件扭矩，确认无松动\n- 运行状态下监听异常噪音部位\n\n【处置建议】\n建议立即降低负载运行，安排计划停机检修。如需详细作业步骤，请前往「作业指导」页面查询标准SOP。`
    },
    formatAnswer(text) {
      if (!text) return ''
      // 队友新增：先做 HTML 转义防止 XSS
      let html = text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
      // 你的原有：结构化渲染
      html = html
        .replace(/【(.*?)】/g, '<div class="tag">[$1]</div>')
        .replace(/\n\s*\n/g, '</p><p>')
        .replace(/\n([0-9]+)\.\s*/g, '<br><span class="num">$1.</span> ')
        .replace(/\n[-•]\s*/g, '<br><span class="bullet">›</span> ')
        .replace(/\n-/g, '<br>-')
        .replace(/\n/g, '<br>')
      return '<p>' + html + '</p>'
    },
    formatMsgTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    },
    scrollToBottom() {
      // 容器已不设 max-height，交给页面自身滚动条控制
      window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
    },
    clearChat() {
      this.messages = []
    },
    clearHistoryConfirm() {
      if (confirm('确定要清除所有本地对话历史吗？')) {
        localStorage.removeItem(STORAGE_KEY)
        this.savedSessions = []
        this.messages = []
        this.showHistoryPanel = false
      }
    },
    onToggleHistory() {
      this.showHistoryPanel = !this.showHistoryPanel
    },
    loadSession(s) {
      this.messages = (s.messages || []).map(m => ({ ...m }))
      this.showHistoryPanel = false
      this.$nextTick(() => this.scrollToBottom())
    },
    formatDate(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      const pad = n => String(n).padStart(2, '0')
      return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}`
    },
    saveCurrentSession() {
      if (this.messages.length === 0) return
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        const list = raw ? JSON.parse(raw) : []
        // 不保存图片 preview blob（URL.revoke 后无法还原）和过大字段
        const latest = this.messages.map(m => ({
          role: m.role, content: m.content, time: m.time,
          citations: m.citations, refs: m.refs, llm_via: m.llm_via, answerable: m.answerable,
          demo: m.demo
        })).slice(0, 50)
        list.unshift({ id: Date.now(), time: Date.now(), messages: latest })
        while (list.length > MAX_HISTORY) list.pop()
        localStorage.setItem(STORAGE_KEY, JSON.stringify(list))
        this.savedSessions = list
      } catch (e) {}
    },
    loadHistory() {
      try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (raw) {
          const list = JSON.parse(raw)
          this.savedSessions = list || []
          if (list && list.length > 0 && list[0].messages) {
            this.messages = list[0].messages
          }
        }
      } catch (e) {}
    }
  }
}
</script>

<style scoped>
.search-page {
  max-width: 860px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  min-height: calc(100vh - 200px);
}

.page-header {
  text-align: center;
  margin-bottom: 24px;
}

.page-title {
  font-size: 1.75rem;
  margin-bottom: 8px;
}

.page-desc {
  color: var(--text-secondary);
  font-size: 0.9375rem;
}

/* 工具条：恢复为文档流内正常定位 */
.chat-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.toolbar-left {
  display: flex;
  gap: 8px;
}

.history-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
}
.history-hint--link {
  cursor: pointer;
  color: var(--primary);
}
.history-hint--link:hover {
  text-decoration: underline;
}

/* 历史对话面板 */
.history-panel {
  margin-bottom: 16px;
  padding: 16px 20px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
}
.history-panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  font-size: 0.9375rem;
}
.history-panel-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 320px;
  overflow-y: auto;
}
.history-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}
.history-item:hover {
  border-color: var(--border-active);
  background: var(--primary-subtle);
}
.history-item.active {
  border-color: var(--primary);
  background: var(--primary-subtle);
}
.history-item-dot {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: var(--primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.6875rem;
  font-weight: 700;
  flex-shrink: 0;
}
.history-item-main {
  flex: 1;
  min-width: 0;
}
.history-item-title {
  font-size: 0.8125rem;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-item-meta {
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin-top: 2px;
}
.history-item-load {
  flex-shrink: 0;
}

/* 历史面板动画 */
.slide-down-enter-active, .slide-down-leave-active { transition: all 0.25s; }
.slide-down-enter-from, .slide-down-leave-to { opacity: 0; transform: translateY(-8px); }

/* 悬浮工具栏：fixed 固定在右上，宽度自适应（两个按钮） */
.fab-toolbar {
  position: fixed;
  top: calc(var(--nav-height, 56px) + 12px);
  right: 24px;
  z-index: 95;
  display: flex;
  gap: 6px;
  padding: 6px 10px;
  background: var(--bg-surface, #161b22);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  width: max-content;
}

.btn-xs {
  padding: 5px 12px;
  font-size: 0.75rem;
}

/* 参考来源（队友新增） */
.citation-list {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid var(--border-color, var(--border-subtle));
}

.citation-title {
  margin-bottom: 8px;
  color: var(--text-secondary);
  font-size: 0.75rem;
  font-weight: 600;
}

.citation-card {
  display: flex;
  gap: 8px;
  margin-top: 6px;
  padding: 8px 10px;
  color: inherit;
  text-decoration: none;
  background: rgba(37, 99, 235, 0.06);
  border: 1px solid rgba(37, 99, 235, 0.16);
  border-radius: 8px;
}

.citation-card:hover {
  border-color: var(--primary-color, var(--primary));
}

.citation-id {
  color: var(--primary-color, var(--primary));
  font-weight: 700;
}

.citation-main {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.citation-main small {
  margin-top: 2px;
  color: var(--text-muted);
}

.ref-snippet {
  color: var(--text-secondary);
}

/* 用户上传图片 */
.user-upload-img {
  max-width: 260px;
  max-height: 200px;
  border-radius: 8px;
  margin-bottom: 8px;
  border: 1px solid var(--border-subtle);
  display: block;
}

/* 对话通道标签 */
.via-tag {
  color: var(--primary);
  margin-left: 4px;
  font-weight: 500;
}

/* 对话区：占满剩余高度，页面级滚动条控制 */
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0 16px;
}

/* 欢迎卡片 */
.welcome-card {
  padding: 24px 28px;
  text-align: left;
}

.welcome-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.welcome-left {
  flex: 1 1 auto;
  min-width: 0;
}

.welcome-icon {
  font-size: 1.75rem;
  color: var(--primary);
  margin-bottom: 6px;
  text-align: left;
}

.welcome-card h3 {
  margin-bottom: 6px;
  text-align: left;
  font-size: 1.05rem;
}

.welcome-card p {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-bottom: 12px;
  text-align: left;
}

.quick-examples {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 5px;
  text-align: left;
  flex: 1 1 auto;
  min-width: 0;
}

/* mascot 容器（右侧，适配竖版狗图） */
.welcome-mascot {
  flex: 0 0 250px;
  height: 350px;
  position: relative;
  overflow: hidden;
}

.mascot-img {
  position: absolute;
  left: 0;
  bottom: 0;
  width: 250px;
  height: 350px;
  object-fit: contain;
  z-index: 2;
  filter:
    drop-shadow(0 0 14px rgba(0, 212, 255, 0.5))
    drop-shadow(0 0 28px rgba(0, 212, 255, 0.25));
}

/* 圆形呼吸光晕 */
.mascot-glow {
  position: absolute;
  left: 50%;
  bottom: 10px;
  transform: translateX(-50%);
  width: 95px;
  height: 95px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.22) 0%, transparent 70%);
  z-index: 1;
  animation: mascot-glow-pulse 4s ease-in-out infinite;
}

@keyframes mascot-glow-pulse {
  0%, 100% { opacity: 0.4; transform: translateX(-50%) scale(1); }
  50% { opacity: 0.9; transform: translateX(-50%) scale(1.15); }
}

.example-chip {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 0.95rem;
  line-height: 1.35;
  transition: all var(--duration) var(--ease);
  text-align: left;
  font-family: inherit;
}

.example-chip:hover {
  background: var(--primary-subtle);
  border-color: var(--border-active);
  color: var(--text-primary);
}

.chip-icon {
  color: var(--primary);
  flex-shrink: 0;
  margin-top: 1px;
  font-size: 0.95rem;
}

.chip-text {
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

/* 消息行 */
.msg-row {
  display: flex;
  margin-bottom: 16px;
}

.msg-row.user {
  justify-content: flex-end;
}

.msg-row.assistant {
  justify-content: flex-start;
}

.msg-bubble {
  max-width: 85%;
  padding: 14px 18px;
  border-radius: var(--radius-lg);
  line-height: 1.7;
  font-size: 0.9375rem;
  position: relative;
}

.user .msg-bubble {
  background: rgba(0, 212, 255, 0.1);
  border: 1px solid var(--border-active);
  border-bottom-right-radius: 2px;
}

.assistant .msg-bubble {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-bottom-left-radius: 2px;
}

.msg-time {
  margin-top: 8px;
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
  text-align: right;
}

.assistant .msg-time {
  text-align: left;
}

/* 结构化回答 */
.msg-content.structured p {
  margin: 0;
}

.msg-content.structured :deep(.tag) {
  display: inline-block;
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--primary);
  background: var(--primary-subtle);
  padding: 2px 10px;
  border-radius: 2px;
  margin: 10px 0 6px;
  letter-spacing: 1px;
}

.msg-content.structured :deep(.num) {
  color: var(--accent-green);
  font-weight: 600;
  font-family: 'JetBrains Mono', monospace;
  margin-right: 4px;
}

.msg-content.structured :deep(.bullet) {
  color: var(--primary);
  margin-right: 6px;
}

/* 加载动画 */
.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 4px 0 10px;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--primary);
  opacity: 0.4;
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) { animation-delay: 0.2s; }
.typing-indicator span:nth-child(3) { animation-delay: 0.4s; }

@keyframes typing {
  0%, 60%, 100% { opacity: 0.3; transform: translateY(0); }
  30% { opacity: 1; transform: translateY(-4px); }
}

/* 输入区 */
.input-area {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-top: 18px;
  border-top: 1px solid var(--border-subtle);
}

/* 队友新增：图片上传 */
.image-upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
}

.image-picker input {
  display: none;
}

.image-hint {
  color: var(--text-muted);
  font-size: 0.75rem;
}

.image-preview-card {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 10px;
  border: 1px solid var(--border-active);
  border-radius: var(--radius);
  background: var(--primary-subtle);
}

.image-preview-card img {
  width: 92px;
  height: 72px;
  object-fit: cover;
  border-radius: 6px;
}

.image-preview-info {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 4px;
}

.image-preview-info strong {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-preview-info small {
  color: var(--text-muted);
}

.remove-image {
  align-self: flex-start;
  padding: 0;
  color: #ef4444;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.search-input {
  font-size: 0.9375rem;
  padding: 12px 16px;
  resize: none;
  line-height: 1.6;
  font-family: inherit;
}

.input-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.input-tip {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-family: 'JetBrains Mono', monospace;
}

.send-btn {
  flex-shrink: 0;
  padding: 10px 22px;
}

/* 贡献入口（你的原有功能） */
.contrib-row {
  margin-top: 20px;
  padding: 14px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 20px;
  background: linear-gradient(135deg, rgba(168,85,247,0.1), rgba(0,212,255,0.08));
  border: 1px dashed var(--border-active);
}
.contrib-left { display: flex; gap: 14px; align-items: center; }
.contrib-icon {
  font-size: 1.75rem;
  filter: drop-shadow(0 0 8px rgba(255,165,2,0.4));
}
.contrib-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
}
.contrib-sub {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 3px;
}
.contrib-btn { font-size: 0.8125rem; padding: 8px 16px; }
.btn-sm { padding: 8px 16px; font-size: 0.8125rem; }

/* Toast */
.toast {
  position: fixed;
  left: 50%;
  bottom: 40px;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: var(--accent-green);
  color: #052e16;
  font-weight: 600;
  font-size: 0.875rem;
  border-radius: 999px;
  box-shadow: 0 8px 24px rgba(0,255,136,0.3), 0 0 0 2px rgba(0,255,136,0.15);
  z-index: 9999;
}
.toast-enter-active, .toast-leave-active { transition: all 0.3s; }
.toast-enter-from, .toast-leave-to { opacity: 0; transform: translate(-50%, 20px); }
</style>
