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
            <!-- 图片诊断结构化卡片 -->
            <div v-else-if="msg.vision" class="vision-card">
              <!-- 多 Agent 协同诊断流程（折叠，安全结果始终可见） -->
              <div v-if="msg.agentsTrajectory && msg.agentsTrajectory.length" class="agent-timeline">
                <div class="agent-timeline-head collapsible-header" @click="msg._showAgents = !msg._showAgents">
                  <span class="collapse-icon">{{ msg._showAgents ? '▼' : '▶' }}</span>
                  <span class="agent-timeline-title">🤖 AI协同诊断流程</span>
                </div>
                <div v-show="msg._showAgents" class="agent-steps">
                  <div
                    v-for="(agent, ai) in msg.agentsTrajectory"
                    :key="ai"
                    class="agent-step"
                    :class="'agent-' + agent.status"
                  >
                    <div class="agent-step-icon">{{ agent.icon }}</div>
                    <div class="agent-step-body">
                      <div class="agent-step-head">
                        <span class="agent-step-name">{{ agent.display_name || agent.name }}</span>
                        <span class="agent-step-status" :class="'as-' + agent.status">
                          {{ agent.status === 'success' ? '✅ 完成' : '❌ 失败' }}
                        </span>
                      </div>
                      <div v-if="agent.summary" class="agent-step-summary">{{ agent.summary }}</div>
                      <div v-if="agent.error" class="agent-step-error">{{ agent.error }}</div>
                    </div>
                  </div>
                </div>
                <!-- 安全审核结果（始终可见） -->
                <div v-if="msg.safetyReview && msg.safetyReview.passed != null" class="agent-safety-result safety-pass">
                  <div class="safety-result-head">
                    <span>🛡️ 安全审核完成</span>
                    <span v-if="msg.safetyReview.risk_level" class="safety-risk">风险等级：{{ msg.safetyReview.risk_level }}</span>
                  </div>
                  <div v-if="msg.safetyReview.warnings && msg.safetyReview.warnings.length" class="safety-warnings">
                    <div v-for="(w, wi) in msg.safetyReview.warnings" :key="wi" class="safety-warning-item">⚠ {{ w }}</div>
                  </div>
                </div>
              </div>
              <!-- 诊断头部：置信度仪表 -->
              <div class="vision-header">
                <div class="vision-header-left">
                  <span class="vision-icon">🔬</span>
                  <div>
                    <div class="vision-title">AI 图片诊断报告</div>
                    <div class="vision-subtitle">{{ msg.vision.equipment_category || '设备图片' }} · {{ msg.vision.fault_domain || '通用' }}领域</div>
                  </div>
                </div>
                <div class="confidence-meter" :class="confidenceLevel(msg.vision.confidence)">
                  <div class="confidence-ring">
                    <svg viewBox="0 0 36 36" class="confidence-svg">
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" stroke="var(--border-subtle)" stroke-width="3"/>
                      <path d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831" fill="none" :stroke="confidenceColor(msg.vision.confidence)" stroke-width="3" stroke-dasharray="100" :stroke-dashoffset="100 - (msg.vision.confidence || 0) * 100" stroke-linecap="round"/>
                    </svg>
                    <span class="confidence-text">{{ Math.round((msg.vision.confidence || 0) * 100) }}%</span>
                  </div>
                  <div class="confidence-labels">
                    <span class="confidence-label">置信度</span>
                    <span class="confidence-badge" :class="confidenceLevel(msg.vision.confidence)">
                      {{ confidenceLevelLabel(msg.vision.confidence) }}
                    </span>
                  </div>
                </div>
              </div>

              <!-- 设备/部件识别 -->
              <div class="vision-section">
                <div class="vision-section-title">🛠 设备部件识别</div>
                <div class="vision-ident-grid">
                  <div v-if="msg.vision.equipment" class="ident-item">
                    <span class="ident-label">设备型号</span>
                    <span class="ident-value">{{ msg.vision.equipment }}</span>
                  </div>
                  <div v-if="msg.vision.equipment_category" class="ident-item">
                    <span class="ident-label">设备类别</span>
                    <span class="ident-value">{{ msg.vision.equipment_category }}</span>
                  </div>
                  <div v-if="msg.vision.component_type" class="ident-item">
                    <span class="ident-label">部件类型</span>
                    <span class="ident-value">{{ msg.vision.component_type }}</span>
                  </div>
                  <div v-if="msg.vision.component" class="ident-item">
                    <span class="ident-label">具体部件</span>
                    <span class="ident-value ident-highlight">{{ msg.vision.component }}</span>
                  </div>
                </div>
              </div>

              <!-- 疑似故障（最多显示 3 条，可展开） -->
              <div v-if="msg.vision.suspected_faults && msg.vision.suspected_faults.length" class="vision-section">
                <div class="vision-section-title">⚠️ 主要疑似故障</div>
                <div class="fault-list">
                  <div v-for="(fault, fi) in (msg._showAllFaults ? msg.vision.suspected_faults : msg.vision.suspected_faults.slice(0, 3))" :key="fi" class="fault-item">{{ fi + 1 }}. {{ fault }}</div>
                  <button v-if="msg.vision.suspected_faults.length > 3" class="btn btn-text btn-xs" @click="msg._showAllFaults = !msg._showAllFaults">
                    {{ msg._showAllFaults ? '收起' : '展开更多 (' + (msg.vision.suspected_faults.length - 3) + '条)' }}
                  </button>
                </div>
              </div>

              <!-- 可见事实（折叠） -->
              <div v-if="msg.vision.visible_facts && msg.vision.visible_facts.length" class="vision-section collapsible" :class="{ open: msg._showFacts }">
                <div class="collapsible-header" @click="msg._showFacts = !msg._showFacts">
                  <span class="collapse-icon">{{ msg._showFacts ? '▼' : '▶' }}</span>
                  <span class="collapse-title">查看AI视觉分析依据</span>
                </div>
                <div v-if="msg._showFacts" class="collapsible-body">
                  <div class="tag-cloud">
                    <span v-for="(fact, fi) in msg.vision.visible_facts" :key="fi" class="tag-item fact-tag">{{ fact }}</span>
                  </div>
                </div>
              </div>

              <!-- OCR 识别文字（折叠） -->
              <div v-if="msg.vision.ocr_text && msg.vision.ocr_text.length" class="vision-section collapsible" :class="{ open: msg._showOCR }">
                <div class="collapsible-header" @click="msg._showOCR = !msg._showOCR">
                  <span class="collapse-icon">{{ msg._showOCR ? '▼' : '▶' }}</span>
                  <span class="collapse-title">OCR识别结果</span>
                </div>
                <div v-if="msg._showOCR" class="collapsible-body">
                  <div class="ocr-display">{{ msg.vision.ocr_text.join(' · ') }}</div>
                </div>
              </div>

              <!-- AI 可信提示（原人工复核） -->
              <div v-if="msg.vision.needs_human_review" class="vision-review-banner">
                <span class="review-icon">⚠️</span>
                <span>{{ msg.vision.review_reason || '图片无法确认完整型号，建议结合现场检测数据复核' }}</span>
              </div>

              <!-- 维修建议（诊断结论，压缩展示） -->
              <div v-if="msg.ragAnswer" class="vision-section vision-diagnosis">
                <div class="vision-section-title">📋 维修建议</div>
                <div class="msg-content structured" v-html="formatAnswer(msg.ragAnswer)"></div>
              </div>

              <!-- 跨模态关联提示 -->
              <div v-if="msg.crossModalHints && msg.crossModalHints.length" class="vision-cross-hint">
                <span class="cross-icon">📚</span>
                <span>{{ msg.crossModalHints[0] }}</span>
              </div>

              <!-- RAG 引用来源 -->
              <div v-if="msg.citations && msg.citations.length" class="citation-list">
                <div class="citation-title">📚 参考来源</div>
                <a v-for="source in msg.citations" :key="source.id" class="citation-card" :href="source.file_url" target="_blank" rel="noopener">
                  <span class="citation-id">[{{ source.id }}]</span>
                  <span class="citation-main">
                    <strong>《{{ source.document_title }}》</strong>
                    <small>第 {{ source.page_label }} 页 · {{ source.section_title || '未识别章节' }}</small>
                  </span>
                </a>
              </div>

              <!-- 参考知识（原跨模态匹配） -->
              <div v-if="msg.similarItems && msg.similarItems.length" class="vision-section">
                <div class="vision-section-title">📚 参考知识</div>
                <div class="similar-list">
                  <div v-for="(item, si) in msg.similarItems.slice(0, 4)" :key="si" class="similar-card" @click="goToSimilar(item)">
                    <div class="similar-type-badge" :class="item.type">
                      {{ item.type === 'case' ? '案例' : '指导' }}
                    </div>
                    <div class="similar-main">
                      <div class="similar-title">{{ item.title }}</div>
                      <div class="similar-meta">
                        <span v-if="item.device">{{ item.device }}</span>
                        <span v-if="item.device_type">{{ item.device_type }}</span>
                        <span v-if="item.tag" class="similar-tag">{{ item.tag }}</span>
                        <span v-if="item.relevance_score != null" class="similar-score" :class="item.relevance_score >= 0.75 ? 'score-high' : 'score-mid'">
                          {{ item.relevance_score >= 0.75 ? '高度匹配' : '相关参考' }}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- 无匹配知识 -->
              <div v-else-if="msg.crossModalHints && msg.crossModalHints.length" class="vision-cross-hint">
                <span class="cross-icon">📚</span>
                <span>{{ msg.crossModalHints[0] }}</span>
              </div>
            </div>

            <!-- 常规文本 AI 消息 -->
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

              <!-- AI 回答反馈：评分 + 修正（仅 AI 消息显示） -->
              <div v-if="msg.role === 'assistant' && !msg._feedbackSubmitted" class="feedback-bar">
                <span class="feedback-label">这个答案有帮助吗？</span>
                <button
                  class="feedback-btn"
                  :class="{ active: msg._feedbackRating === 'useful' }"
                  @click="submitFeedback(msg, 'useful')"
                  :disabled="msg._feedbackSubmitting"
                  title="有用"
                >👍 有用</button>
                <button
                  class="feedback-btn"
                  :class="{ active: msg._feedbackRating === 'useless' }"
                  @click="submitFeedback(msg, 'useless')"
                  :disabled="msg._feedbackSubmitting"
                  title="没用"
                >👎 没用</button>
                <button
                  class="feedback-btn feedback-btn-correction"
                  :class="{ active: msg._showCorrection }"
                  @click="toggleCorrection(msg)"
                  title="我要修正"
                >✏️ 修正</button>
              </div>
              <div v-if="msg.role === 'assistant' && msg._feedbackSubmitted" class="feedback-done">
                ✅ {{ msg._feedbackDoneText || '感谢反馈！' }}
                <span v-if="msg._feedbackRating === 'corrected'" class="feedback-corr-hint">（修正已提交，管理员审核后将用于优化系统）</span>
              </div>

              <!-- 修正输入区 -->
              <transition name="correction-slide">
                <div v-if="msg.role === 'assistant' && msg._showCorrection" class="correction-area">
                  <textarea
                    v-model="msg._correctionText"
                    class="correction-input"
                    rows="3"
                    placeholder="请描述您的修正建议：正确的步骤/原因/方案是什么？"
                    @keydown.ctrl.enter="submitFeedback(msg, 'corrected')"
                  ></textarea>
                  <div class="correction-actions">
                    <span class="correction-hint">按 Ctrl+Enter 快速提交</span>
                    <button
                      class="btn btn-primary btn-xs"
                      @click="submitFeedback(msg, 'corrected')"
                      :disabled="msg._feedbackSubmitting || !(msg._correctionText || '').trim()"
                    >{{ msg._feedbackSubmitting ? '提交中…' : '提交修正' }}</button>
                  </div>
                </div>
              </transition>
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

        <!-- 检索增强筛选条（可选） -->
        <div class="enhance-bar">
          <div class="enhance-title">
            <span class="enhance-icon">🔧</span>
            <span>检索增强（可选，提升精准度）</span>
          </div>
          <div class="enhance-filters">
            <div class="filter-item">
              <select v-model="selectedDeviceType" class="filter-select" @change="onDeviceTypeChange">
                <option value="">🏷️ 设备类型（全部）</option>
                <option v-for="t in deviceTypes" :key="t.value" :value="t.value">
                  {{ t.label }}
                </option>
              </select>
            </div>
            <div class="filter-item" v-if="selectedDeviceType && filteredDevices.length > 0">
              <select v-model="selectedDeviceModel" class="filter-select" @change="onDeviceChange">
                <option value="">📋 具体设备（全部）</option>
                <option v-for="d in filteredDevices" :key="d.id" :value="d.code">
                  {{ d.name }} <span v-if="d.code">({{ d.code }})</span>
                </option>
              </select>
            </div>
            <div class="filter-item">
              <select v-model="selectedDocumentId" class="filter-select" @change="onDocumentChange">
                <option value="">📖 检修手册（不指定）</option>
                <option v-for="doc in documentList" :key="doc.id" :value="doc.id">
                  {{ doc.title }}
                </option>
              </select>
            </div>
            <button
              v-if="selectedDeviceType || selectedDeviceModel || selectedDocumentId"
              type="button"
              class="filter-clear"
              @click="clearFilters"
            >清除筛选</button>
          </div>
          <div v-if="activeFilterTags.length" class="filter-tags">
            <span v-for="tag in activeFilterTags" :key="tag.key" class="filter-tag">
              {{ tag.icon }} {{ tag.label }}
              <button type="button" class="tag-close" @click="removeFilter(tag.key)">×</button>
            </span>
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

        <!-- 深度融合预览：展示将联合发送的信息 -->
        <div v-if="hasAnyInput" class="fusion-preview">
          <div class="fusion-preview-title">
            <span class="fusion-icon">🧠</span>
            <span>深度融合（将联合发送以下信息）</span>
          </div>
          <div class="fusion-preview-items">
            <div v-if="imageFile" class="fusion-item fusion-item-image">
              <span class="fusion-item-icon">🖼️</span>
              <span class="fusion-item-label">图片:</span>
              <span class="fusion-item-value">{{ imageFile.name }}</span>
              <span class="fusion-item-badge">视觉分析</span>
            </div>
            <div v-if="question.trim()" class="fusion-item">
              <span class="fusion-item-icon">📝</span>
              <span class="fusion-item-label">文本:</span>
              <span class="fusion-item-value">{{ question }}</span>
              <span class="fusion-item-badge">语义理解</span>
            </div>
            <div v-if="selectedDeviceType" class="fusion-item">
              <span class="fusion-item-icon">🏷️</span>
              <span class="fusion-item-label">类型:</span>
              <span class="fusion-item-value">{{ selectedDeviceType }}</span>
              <span class="fusion-item-badge">范围限定</span>
            </div>
            <div v-if="selectedDeviceModel" class="fusion-item">
              <span class="fusion-item-icon">📋</span>
              <span class="fusion-item-label">设备:</span>
              <span class="fusion-item-value">{{ deviceList.find(d => d.code === selectedDeviceModel)?.name || selectedDeviceModel }}</span>
              <span class="fusion-item-badge">精准定位</span>
            </div>
            <div v-if="selectedDocumentId" class="fusion-item">
              <span class="fusion-item-icon">📖</span>
              <span class="fusion-item-label">手册:</span>
              <span class="fusion-item-value">{{ documentList.find(d => d.id === selectedDocumentId)?.title || selectedDocumentId }}</span>
              <span class="fusion-item-badge">知识限定</span>
            </div>
          </div>
          <div class="fusion-preview-hint">
            以上信息将联合进行跨模态融合检索，提升诊断精准度
          </div>
        </div>

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
      // 检索增强：设备类型 / 具体设备 / 检修手册
      deviceList: [],
      documentList: [],
      selectedDeviceType: '',
      selectedDeviceModel: '',
      selectedDocumentId: '',
      deviceTypes: [
        { value: '机械', label: '⚙️ 机械' },
        { value: '电气', label: '⚡ 电气' },
        { value: '液压', label: '🔧 液压' },
        { value: '仪表', label: '📊 仪表' },
        { value: '安全', label: '🛡️ 安全' }
      ],
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
    hasAnyInput() {
      return !!(this.imageFile || this.question.trim() || this.selectedDeviceType || this.selectedDeviceModel || this.selectedDocumentId)
    },
    filteredDevices() {
      if (!this.selectedDeviceType) return this.deviceList
      return this.deviceList.filter(d => d.tag === this.selectedDeviceType)
    },
    activeFilterTags() {
      const tags = []
      if (this.selectedDeviceType) {
        const t = this.deviceTypes.find(x => x.value === this.selectedDeviceType)
        tags.push({ key: 'deviceType', icon: '🏷️', label: '类型: ' + (t ? t.label.replace(/^\S+\s*/, '') : this.selectedDeviceType) })
      }
      if (this.selectedDeviceModel) {
        const d = this.deviceList.find(x => x.code === this.selectedDeviceModel)
        const label = d ? (d.name + (d.code ? '(' + d.code + ')' : '')) : this.selectedDeviceModel
        tags.push({ key: 'device', icon: '📋', label: '设备: ' + label })
      }
      if (this.selectedDocumentId) {
        const doc = this.documentList.find(d => d.id === this.selectedDocumentId)
        tags.push({ key: 'doc', icon: '📖', label: '手册: ' + (doc ? doc.title : this.selectedDocumentId) })
      }
      return tags
    },
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
    this.loadDeviceList()
    this.loadDocumentList()
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
      const textFusionParts = []
      textFusionParts.push(text)
      if (this.selectedDeviceType) textFusionParts.push(`\n【设备类型】${this.selectedDeviceType}`)
      if (this.selectedDeviceModel) {
        const d = this.deviceList.find(x => x.code === this.selectedDeviceModel)
        textFusionParts.push(`【具体设备】${d ? d.name + '(' + d.code + ')' : this.selectedDeviceModel}`)
      }
      if (this.selectedDocumentId) {
        const doc = this.documentList.find(x => x.id === this.selectedDocumentId)
        textFusionParts.push(`【限定手册】${doc ? doc.title : '已指定'}`)
      }
      const hasEnhance = this.selectedDeviceType || this.selectedDeviceModel || this.selectedDocumentId
      const textContent = hasEnhance ? textFusionParts.join('\n') + '\n\n— 跨模态融合检索 —' : text
      this.messages.push({ role: 'user', content: textContent, time: Date.now() })
      this.question = ''
      this.clearFilters()
      this.loading = true
      this.$nextTick(() => this.scrollToBottom())

      let answered = false
      try {
        // ---- 通道 1：队友 RAG 接口（带知识库文档检索 + citations 引用）----
        let ragFallbackNeeded = true
        try {
          const token = localStorage.getItem('equipai_token') || ''
          const enhanceParams = this.buildEnhanceParams()
          const body = { question: text, top_k: 5, ...enhanceParams }
          const res = await fetch('/api/rag/ask', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
            body: JSON.stringify(body)
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
      // 构建融合摘要作为用户消息
      const fusionParts = []
      if (note) fusionParts.push(`【文本描述】${note}`)
      if (this.selectedDeviceType) fusionParts.push(`【设备类型】${this.selectedDeviceType}`)
      if (this.selectedDeviceModel) {
        const d = this.deviceList.find(x => x.code === this.selectedDeviceModel)
        fusionParts.push(`【具体设备】${d ? d.name + '(' + d.code + ')' : this.selectedDeviceModel}`)
      }
      if (this.selectedDocumentId) {
        const doc = this.documentList.find(x => x.id === this.selectedDocumentId)
        fusionParts.push(`【限定手册】${doc ? doc.title : '已指定'}`)
      }
      const fusionSummary = fusionParts.join('\n')

      this.messages.push({
        role: 'user',
        content: fusionSummary,
        image: preview,
        time: Date.now()
      })
      this.question = ''
      this.clearFilters()
      this.loading = true
      this.$nextTick(() => this.scrollToBottom())
      try {
        const form = new FormData()
        form.append('file', file, file.name)
        form.append('note', note)
        form.append('top_k', '5')
        const enhanceParams = this.buildEnhanceParams()
        if (enhanceParams.device_model) form.append('device_model', enhanceParams.device_model)
        if (enhanceParams.document_id) form.append('document_id', enhanceParams.document_id)
        if (enhanceParams.device_type) form.append('device_type', enhanceParams.device_type)
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
        this.messages.push({
          role: 'assistant',
          content: '',
          ragAnswer: rag.answer || '',
          citations: rag.citations || [],
          answerable: rag.answerable,
          vision: vision,
          similarItems: data.similar_items || [],
          crossModalHints: data.cross_modal_hints || [],
          agentsTrajectory: data.agents_trajectory || [],
          safetyReview: data.safety_review || {},
          llm_via: 'vision+rag',
          _showAgents: false,
          _showAllFaults: false,
          _showFacts: false,
          _showOCR: false,
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
      this.imageFile = null
      this.imagePreview = ''
      if (this.$refs.imageInput) this.$refs.imageInput.value = ''
    },
    // ========== 检索增强：加载设备/文档列表 ==========
    async loadDeviceList() {
      try {
        const token = localStorage.getItem('equipai_token') || ''
        const res = await fetch('/api/devices?page=1&size=200', {
          headers: { 'Authorization': 'Bearer ' + token }
        })
        if (res.ok) {
          const data = await res.json()
          const items = (data.data && data.data.items) || data.items || []
          const seen = new Set()
          this.deviceList = items
            .filter(d => {
              const key = d.code || d.name
              if (seen.has(key)) return false
              seen.add(key)
              return true
            })
            .sort((a, b) => (a.name || '').localeCompare(b.name || ''))
        }
      } catch (_e) {}
    },
    async loadDocumentList() {
      try {
        const token = localStorage.getItem('equipai_token') || ''
        const res = await fetch('/api/documents?limit=100', {
          headers: { 'Authorization': 'Bearer ' + token }
        })
        if (res.ok) {
          const data = await res.json()
          const items = data.items || []
          const seen = new Set()
          this.documentList = items
            .filter(doc => {
              const key = doc.title || doc.id
              if (seen.has(key)) return false
              seen.add(key)
              return true
            })
            .sort((a, b) => (a.title || '').localeCompare(b.title || ''))
        }
      } catch (_e) {}
    },
    onDeviceTypeChange() {
      this.selectedDeviceModel = ''
      if (this.selectedDeviceType) {
        this.loadDocumentList()
      }
    },
    onDeviceChange() {
      if (this.selectedDeviceModel) {
        this.loadDocumentList()
      }
    },
    onDocumentChange() {
      // 可扩展：选中文档后展示文档摘要
    },
    clearFilters() {
      this.selectedDeviceType = ''
      this.selectedDeviceModel = ''
      this.selectedDocumentId = ''
    },
    removeFilter(key) {
      if (key === 'deviceType') {
        this.selectedDeviceType = ''
        this.selectedDeviceModel = ''
      }
      if (key === 'device') this.selectedDeviceModel = ''
      if (key === 'doc') this.selectedDocumentId = ''
    },
    buildEnhanceParams() {
      const params = {}
      if (this.selectedDeviceType) {
        params.device_type = this.selectedDeviceType
      }
      if (this.selectedDeviceModel) {
        params.device_model = this.selectedDeviceModel
      }
      if (this.selectedDocumentId) {
        params.document_id = this.selectedDocumentId
      }
      return params
    },
    formatFileSize(size) {
      if (!size) return ''
      return size < 1024 * 1024 ? `${Math.round(size / 1024)} KB` : `${(size / 1024 / 1024).toFixed(1)} MB`
    },
    // ========== 视觉诊断卡片工具函数 ==========
    confidenceLevel(score) {
      if (!score && score !== 0) return 'unknown'
      if (score >= 0.6) return 'high'
      if (score >= 0.3) return 'medium'
      return 'low'
    },
    confidenceLevelLabel(score) {
      if (!score && score !== 0) return '未知'
      if (score >= 0.6) return '较高'
      if (score >= 0.3) return '一般'
      return '较低'
    },
    confidenceColor(score) {
      if (!score && score !== 0) return 'var(--text-muted)'
      if (score >= 0.6) return '#22c55e'
      if (score >= 0.3) return '#eab308'
      return '#ef4444'
    },
    goToSimilar(item) {
      if (item.type === 'case') {
        this.$router.push('/case')
      } else if (item.type === 'guide') {
        this.$router.push('/guide')
      }
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
          demo: m.demo,
          _feedbackSubmitted: m._feedbackSubmitted || false,
          _feedbackRating: m._feedbackRating || null,
          _feedbackDoneText: m._feedbackDoneText || '',
          _feedbackId: m._feedbackId || ''
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
    },
    // ========== AI 回答反馈 ==========
    _generateFeedbackId(msg) {
      if (!msg._feedbackId) {
        msg._feedbackId = 'fb_' + Date.now().toString(36) + '_' + Math.random().toString(36).slice(2, 8)
      }
      return msg._feedbackId
    },
    async submitFeedback(msg, rating) {
      if (msg._feedbackSubmitting) return
      if (rating === 'corrected' && !(msg._correctionText || '').trim()) return
      msg._feedbackSubmitting = true
      msg._feedbackRating = rating
      const feedbackId = this._generateFeedbackId(msg)
      const payload = {
        feedback_id: feedbackId,
        question: '',
        answer: msg.content || '',
        rating: rating,
        correction_text: rating === 'corrected' ? msg._correctionText : '',
        llm_via: msg.llm_via || '',
        fault_domain: '',
        device_model: '',
      }
      // 从历史消息中找到对应的用户提问
      const myIndex = this.messages.indexOf(msg)
      for (let i = myIndex - 1; i >= 0; i--) {
        if (this.messages[i].role === 'user') {
          payload.question = this.messages[i].content || ''
          break
        }
      }
      try {
        const token = localStorage.getItem('equipai_token') || ''
        const res = await fetch('/api/ai/feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token },
          body: JSON.stringify(payload)
        })
        const data = await res.json()
        if (data && (data.code === 200 || res.ok)) {
          msg._feedbackSubmitted = true
          msg._showCorrection = false
          msg._feedbackDoneText = rating === 'useful' ? '感谢反馈！'
            : rating === 'useless' ? '已收到您的反馈，我们将持续优化！'
            : '修正已提交，感谢您的贡献！'
        } else {
          msg._feedbackRating = null
          msg._feedbackDoneText = '提交失败，请重试'
        }
      } catch (e) {
        msg._feedbackRating = null
        msg._feedbackDoneText = '网络异常，提交失败'
      } finally {
        msg._feedbackSubmitting = false
      }
    },
    toggleCorrection(msg) {
      msg._showCorrection = !msg._showCorrection
      if (!msg._showCorrection && !msg._correctionText) {
        msg._feedbackRating = null
      }
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

/* AI 回答反馈 */
.feedback-bar {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.feedback-label {
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin-right: 4px;
}
.feedback-btn {
  padding: 4px 10px;
  font-size: 0.75rem;
  border-radius: 999px;
  border: 1px solid var(--border-subtle);
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s ease;
  font-family: inherit;
  line-height: 1.4;
}
.feedback-btn:hover {
  border-color: var(--primary);
  color: var(--text-primary);
}
.feedback-btn.active {
  background: var(--primary-subtle);
  border-color: var(--primary);
  color: var(--primary);
  font-weight: 600;
}
.feedback-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.feedback-btn-correction {
  margin-left: 4px;
}
.feedback-btn-correction.active {
  background: rgba(255, 165, 2, 0.1);
  border-color: var(--accent-orange);
  color: var(--accent-orange);
}
.feedback-done {
  margin-top: 10px;
  padding-top: 8px;
  font-size: 0.75rem;
  color: var(--accent-green);
  font-weight: 500;
  border-top: 1px dashed var(--border-subtle);
  line-height: 1.5;
}
.feedback-corr-hint {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-weight: 400;
}
.correction-area {
  margin-top: 8px;
  padding: 10px;
  background: rgba(255, 165, 2, 0.05);
  border: 1px solid rgba(255, 165, 2, 0.2);
  border-radius: var(--radius);
}
.correction-input {
  width: 100%;
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-primary);
  padding: 8px 10px;
  font-family: inherit;
  font-size: 0.8125rem;
  resize: vertical;
  line-height: 1.6;
  box-sizing: border-box;
}
.correction-input:focus {
  outline: none;
  border-color: var(--accent-orange);
  box-shadow: 0 0 0 2px rgba(255, 165, 2, 0.1);
}
.correction-input::placeholder {
  color: var(--text-muted);
}
.correction-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 8px;
}
.correction-hint {
  font-size: 0.6875rem;
  color: var(--text-muted);
}
.correction-slide-enter-active,
.correction-slide-leave-active {
  transition: all 0.2s ease;
  overflow: hidden;
}
.correction-slide-enter-from,
.correction-slide-leave-to {
  opacity: 0;
  transform: translateY(-6px);
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

/* 检索增强筛选条 */
.enhance-bar {
  padding: 12px 14px;
  border: 1px dashed var(--border-active);
  border-radius: var(--radius);
  background: var(--bg-elevated);
}

.enhance-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.enhance-icon {
  font-size: 1rem;
}

.enhance-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}

.filter-item {
  flex: 1;
  min-width: 180px;
}

.filter-select {
  width: 100%;
  padding: 7px 10px;
  font-size: 0.8125rem;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-primary);
  cursor: pointer;
  transition: border-color 0.2s;
}

.filter-select:hover {
  border-color: var(--primary);
}

.filter-select:focus {
  outline: none;
  border-color: var(--primary);
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.15);
}

.filter-select option {
  background: var(--bg-surface);
  color: var(--text-primary);
}

.filter-clear {
  padding: 7px 14px;
  font-size: 0.75rem;
  border-radius: 8px;
  border: 1px solid var(--border-subtle);
  background: var(--bg-surface);
  color: var(--text-muted);
  cursor: pointer;
  white-space: nowrap;
  transition: all 0.2s;
}

.filter-clear:hover {
  border-color: #ef4444;
  color: #ef4444;
}

.filter-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 10px;
}

.filter-tag {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  font-size: 0.75rem;
  background: var(--primary-subtle);
  color: var(--primary);
  border: 1px solid var(--primary);
  border-radius: 999px;
  font-weight: 500;
}

.tag-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  padding: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  font-size: 0.875rem;
  line-height: 1;
  border-radius: 50%;
  transition: background 0.2s;
}

.tag-close:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* 深度融合预览 */
.fusion-preview {
  padding: 12px 14px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(139, 92, 246, 0.08));
  border: 1px solid rgba(37, 99, 235, 0.3);
  border-radius: var(--radius);
  margin-top: 8px;
}

.fusion-preview-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--primary);
  margin-bottom: 10px;
}

.fusion-icon {
  font-size: 1rem;
}

.fusion-preview-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.fusion-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8125rem;
  padding: 6px 10px;
  background: var(--bg-surface);
  border-radius: 6px;
  border: 1px solid var(--border-subtle);
}

.fusion-item-image {
  border-left: 3px solid #8b5cf6;
}

.fusion-item-icon {
  font-size: 0.875rem;
}

.fusion-item-label {
  color: var(--text-muted);
  font-weight: 500;
  white-space: nowrap;
}

.fusion-item-value {
  flex: 1;
  min-width: 0;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fusion-item-badge {
  font-size: 0.6875rem;
  padding: 2px 8px;
  border-radius: 4px;
  background: var(--primary-subtle);
  color: var(--primary);
  font-weight: 500;
  white-space: nowrap;
}

.fusion-preview-hint {
  margin-top: 10px;
  font-size: 0.75rem;
  color: var(--text-muted);
  text-align: center;
}

/* 视觉诊断卡片 ============================================= */
/* ===== AI 协同诊断流程轨迹 ===== */
.agent-timeline {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 12px;
  margin-bottom: 4px;
  background: var(--bg-subtle, rgba(255,255,255,0.02));
  border-radius: 10px;
  border: 1px solid var(--border-subtle);
}
.agent-timeline-head {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  padding: 2px 0;
  user-select: none;
}
.agent-timeline-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}
.agent-steps {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin: 6px 0 2px;
}
.agent-step {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 6px;
  background: var(--bg-deep, rgba(0,0,0,0.15));
}
.agent-step-icon {
  font-size: 1rem;
  line-height: 1.4;
  flex-shrink: 0;
  width: 24px;
  text-align: center;
}
.agent-step-body {
  flex: 1;
  min-width: 0;
}
.agent-step-head {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.agent-step-name {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
}
.agent-step-status {
  font-size: 0.6875rem;
  padding: 1px 6px;
  border-radius: 4px;
}
.agent-step-status.as-success {
  color: var(--accent-green, #4ade80);
  background: rgba(74, 222, 128, 0.1);
}
.agent-step-status.as-failed {
  color: var(--accent-red, #f87171);
  background: rgba(248, 113, 113, 0.1);
}
.agent-step-duration {
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin-left: auto;
  font-family: 'JetBrains Mono', monospace;
}
.agent-step-summary {
  font-size: 0.75rem;
  color: var(--text-secondary);
  margin-top: 2px;
  line-height: 1.3;
}
.agent-step-error {
  font-size: 0.75rem;
  color: var(--accent-red, #f87171);
  margin-top: 2px;
}
.agent-safety-result {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 0.75rem;
  margin-top: 2px;
  background: rgba(74, 222, 128, 0.06);
  border: 1px solid rgba(74, 222, 128, 0.15);
}
.safety-result-head {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: var(--accent-green, #4ade80);
}
.safety-risk {
  font-weight: 400;
  opacity: 0.8;
  color: var(--text-secondary);
}
.safety-warnings {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding-left: 4px;
}
.safety-warning-item {
  font-size: 0.7rem;
  color: var(--accent-orange, #fbbf24);
  line-height: 1.4;
}

.vision-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
/* 头部 */
.vision-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-subtle);
}
.vision-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vision-icon {
  font-size: 1.75rem;
  filter: drop-shadow(0 0 6px rgba(0,212,255,0.4));
}
.vision-title {
  font-size: 0.9375rem;
  font-weight: 700;
  color: var(--text-primary);
}
.vision-subtitle {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-top: 2px;
}
/* 置信度仪表 */
.confidence-meter {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
}
.confidence-ring {
  position: relative;
  width: 40px;
  height: 40px;
}
.confidence-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}
.confidence-text {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 700;
  font-family: 'JetBrains Mono', monospace;
}
.confidence-meter.high .confidence-text { color: #22c55e; }
.confidence-meter.medium .confidence-text { color: #eab308; }
.confidence-meter.low .confidence-text { color: #ef4444; }
.confidence-labels {
  display: flex;
  flex-direction: column;
  gap: 1px;
}
.confidence-label { font-size: 0.625rem; color: var(--text-muted); }
.confidence-badge {
  font-size: 0.625rem;
  font-weight: 600;
  padding: 1px 6px;
  border-radius: 4px;
  display: inline-block;
  text-align: center;
}
.confidence-badge.high { background: rgba(34,197,94,0.15); color: #22c55e; }
.confidence-badge.medium { background: rgba(234,179,8,0.15); color: #eab308; }
.confidence-badge.low { background: rgba(239,68,68,0.15); color: #ef4444; }
.confidence-badge.unknown { background: rgba(100,116,139,0.15); color: #94a3b8; }

/* 各区块 */
.vision-section {
  padding: 8px 0;
}
.vision-section-title {
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 8px;
  letter-spacing: 0.3px;
}
.vision-ident-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
}
.ident-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 6px 10px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 6px;
}
.ident-label {
  font-size: 0.625rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
.ident-value {
  font-size: 0.8125rem;
  color: var(--text-primary);
  font-weight: 500;
}
.ident-highlight {
  color: var(--primary);
  font-weight: 700;
}
/* 标签云 */
.tag-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.tag-item {
  display: inline-block;
  padding: 3px 10px;
  font-size: 0.75rem;
  border-radius: 999px;
  font-weight: 500;
  line-height: 1.4;
}
.fact-tag {
  background: rgba(37,99,235,0.1);
  color: #60a5fa;
  border: 1px solid rgba(37,99,235,0.2);
}
.fault-tag {
  background: rgba(239,68,68,0.1);
  color: #f87171;
  border: 1px solid rgba(239,68,68,0.2);
}
.kw-tag {
  background: rgba(139,92,246,0.1);
  color: #a78bfa;
  border: 1px solid rgba(139,92,246,0.2);
}
/* OCR 显示 */
.ocr-display {
  font-family: 'JetBrains Mono', monospace;
  font-size: 0.8125rem;
  color: var(--text-primary);
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: 1px dashed var(--border-active);
  border-radius: 6px;
  line-height: 1.6;
}
/* 人工复核横幅 */
.vision-review-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  font-size: 0.75rem;
  color: var(--accent-orange);
  background: rgba(255,165,2,0.1);
  border: 1px solid rgba(255,165,2,0.2);
  border-radius: 6px;
}
.review-icon { font-size: 0.9375rem; }
/* 诊断结论 */
.vision-diagnosis {
  border-top: 1px solid var(--border-subtle);
  margin-top: 4px;
  padding-top: 12px;
}
/* 跨模态提示 */
.vision-cross-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  font-size: 0.6875rem;
  color: var(--text-muted);
  background: linear-gradient(135deg, rgba(139,92,246,0.08), rgba(37,99,235,0.08));
  border: 1px solid rgba(139,92,246,0.15);
  border-radius: 6px;
}
.cross-icon { font-size: 0.8125rem; }

/* 折叠区块 */
.vision-section.collapsible {
  padding: 4px 0;
  margin: 0;
  border: none;
}
.collapsible-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  cursor: pointer;
  border-radius: 6px;
  background: var(--bg-subtle, rgba(255,255,255,0.02));
  border: 1px solid var(--border-subtle);
  user-select: none;
  transition: background var(--duration);
}
.collapsible-header:hover {
  background: var(--primary-subtle, rgba(0,212,255,0.06));
}
.collapse-icon {
  font-size: 0.65rem;
  color: var(--text-muted);
  width: 12px;
  text-align: center;
}
.collapse-title {
  font-size: 0.75rem;
  color: var(--text-secondary);
  font-weight: 500;
}
.collapsible-body {
  padding: 8px 4px 2px;
}

/* 故障列表 */
.fault-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.fault-item {
  font-size: 0.8rem;
  color: var(--text-primary);
  padding: 3px 0;
  line-height: 1.4;
}
.fault-list .btn-text {
  align-self: flex-start;
  font-size: 0.7rem;
  color: var(--primary);
  padding: 2px 8px;
  margin-top: 2px;
  background: none;
  border: none;
  cursor: pointer;
}
.fault-list .btn-text:hover {
  text-decoration: underline;
}

/* 相似案例 */
.similar-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.similar-card {
  display: flex;
  gap: 10px;
  padding: 8px 12px;
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s ease;
}
.similar-card:hover {
  border-color: var(--border-active);
  background: var(--primary-subtle);
}
.similar-type-badge {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.625rem;
  font-weight: 700;
  border-radius: 6px;
}
.similar-type-badge.case {
  background: rgba(37,99,235,0.15);
  color: #60a5fa;
}
.similar-type-badge.guide {
  background: rgba(139,92,246,0.15);
  color: #a78bfa;
}
.similar-main {
  flex: 1;
  min-width: 0;
}
.similar-title {
  font-size: 0.8125rem;
  font-weight: 600;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.similar-meta {
  display: flex;
  gap: 6px;
  font-size: 0.6875rem;
  color: var(--text-muted);
  margin-top: 2px;
  flex-wrap: wrap;
}
.similar-tag {
  padding: 0 4px;
  background: var(--primary-subtle);
  color: var(--primary);
  border-radius: 3px;
}
.similar-score {
  padding: 0 6px;
  font-size: 0.6875rem;
  font-weight: 600;
  border-radius: 4px;
  margin-left: auto;
  white-space: nowrap;
}
.similar-score.score-high {
  color: var(--accent-green, #4ade80);
  background: rgba(74, 222, 128, 0.1);
}
.similar-score.score-mid {
  color: var(--accent-orange, #f59e0b);
  background: rgba(255, 245, 157, 0.1);
}
.similar-desc {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  margin-top: 3px;
  line-height: 1.4;
}

@media (max-width: 600px) {
  .filter-item {
    min-width: 100%;
  }
  .enhance-filters {
    flex-direction: column;
  }
  .vision-ident-grid {
    grid-template-columns: 1fr;
  }
  .vision-header {
    flex-direction: column;
  }
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
