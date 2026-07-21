<template>
  <transition name="fade">
    <div v-if="visible" class="kr-mask" @click.self="handleClose">
      <div class="kr-dialog card">
        <div class="kr-header">
          <div class="kr-head-left">
            <span class="kr-icon">📝</span>
            <div>
              <div class="kr-title">提交知识贡献报告</div>
              <div class="kr-sub">您经过现场验证的实践方案，将由管理员审核后同步到知识库，让全体同事受益</div>
            </div>
          </div>
          <button class="kr-close" @click="handleClose">✕</button>
        </div>

        <div class="kr-body">
          <div class="kr-row kr-type-row">
            <div class="kr-label">归属知识类型</div>
            <div class="type-switch">
              <button
                class="type-btn"
                :class="{ active: form.type === 'case' }"
                @click="form.type = 'case'"
              >
                📚 案例库
                <em>历史故障案例</em>
              </button>
              <button
                class="type-btn"
                :class="{ active: form.type === 'guide' }"
                @click="form.type = 'guide'"
              >
                📖 作业指导
                <em>标准操作规程 SOP</em>
              </button>
            </div>
          </div>

          <div class="kr-grid">
            <div class="kr-row">
              <label class="kr-label required">问题标题</label>
              <input
                v-model="form.title"
                class="input"
                type="text"
                placeholder="例如：离心泵轴承过热（现场实测更换方案）"
              />
            </div>
            <div class="kr-row kr-half">
              <div>
                <label class="kr-label">关联设备</label>
                <input
                  v-model="form.device"
                  class="input"
                  type="text"
                  placeholder="如：离心泵 P-103"
                />
              </div>
              <div>
                <label class="kr-label">工单编号</label>
                <input
                  v-model="form.ticketId"
                  class="input"
                  type="text"
                  placeholder="如：TK-20260715-001"
                />
              </div>
            </div>
            <div class="kr-row">
              <label class="kr-label">故障等级</label>
              <div class="level-group">
                <button v-for="lv in levels" :key="lv.v" class="lv-btn" :class="'lv-' + lv.v + (form.level === lv.v ? ' active' : '')" @click="form.level = lv.v">
                  {{ lv.l }}
                </button>
              </div>
            </div>
          </div>

          <div class="kr-row">
            <label class="kr-label required">
              AI 未解决的问题描述
              <span class="label-hint">写清楚 AI 给了什么方案、现场实际遇到什么不同</span>
            </label>
            <textarea
              v-model="form.question"
              class="input"
              rows="3"
              placeholder="例如：AI 建议检查润滑，但现场拆解发现是轴承型号选错..."
            ></textarea>
          </div>

          <div class="kr-row">
            <label class="kr-label required">
              故障描述
              <span class="label-hint">描述故障现象、检测到的参数、初步判断</span>
            </label>
            <textarea
              v-model="form.fault"
              class="input"
              rows="3"
              placeholder="例如：离心泵轴承温度持续升高至85℃，噪音明显增大..."
            ></textarea>
          </div>

          <div class="kr-row">
            <label class="kr-label">
              维修过程
              <span class="label-hint">分步骤描述维修操作流程</span>
            </label>
            <textarea
              v-model="form.repairProcess"
              class="input"
              rows="4"
              placeholder="1. 断电停机，做好安全措施&#10;2. 拆卸泵体，检查轴承状态&#10;3. 更换损坏部件..."
            ></textarea>
          </div>

          <div class="kr-row">
            <label class="kr-label">
              使用方法/技术措施
              <span class="label-hint">使用的工具、技术手段、注意事项</span>
            </label>
            <textarea
              v-model="form.technicalMeasures"
              class="input"
              rows="4"
              placeholder="使用万用表测量线圈电阻&#10;使用红外测温仪监测温度&#10;注意事项：操作时需佩戴绝缘手套..."
            ></textarea>
          </div>

          <div class="kr-row">
            <label class="kr-label">
              维修结果
              <span class="label-hint">维修后的状态、验证数据、运行情况</span>
            </label>
            <textarea
              v-model="form.repairResult"
              class="input"
              rows="3"
              placeholder="更换轴承后试运行2小时，温度稳定在55℃以下&#10;噪音从85dB降至62dB&#10;设备运行正常"
            ></textarea>
          </div>

          <div class="kr-row">
            <label class="kr-label required">
              解决方案总结
              <span class="label-hint">综合描述完整解决方案</span>
            </label>
            <textarea
              v-model="form.solution"
              class="input"
              rows="4"
              placeholder="综合上述维修过程，总结完整解决方案..."
            ></textarea>
          </div>

          <div v-if="sourceHint" class="kr-source-hint">
            <span class="src-tag">{{ sourceHint }}</span>
            此报告将自动关联来源信息
          </div>
        </div>

        <div class="kr-footer">
          <div class="kr-err" v-if="errMsg">{{ errMsg }}</div>
          <div class="kr-actions">
            <button class="btn btn-outline" @click="handleClose">取消</button>
            <button class="btn btn-primary" :disabled="submitting" @click="handleSubmit">
              <span v-if="!submitting">提交报告</span>
              <span v-else>提交中...</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </transition>
</template>

<script>
import { getUser } from '../utils/auth'
import { submitReport } from '../utils/knowledge'

export default {
  name: 'KnowledgeReport',
  props: {
    visible: { type: Boolean, default: false },
    preset: { type: Object, default: () => ({}) },
    source: { type: String, default: 'manual' }
  },
  data() {
    return {
      submitting: false,
      errMsg: '',
      form: {
        type: 'case',
        title: '',
        device: '',
        ticketId: '',
        level: 'mid',
        question: '',
        fault: '',
        repairProcess: '',
        technicalMeasures: '',
        repairResult: '',
        solution: ''
      },
      levels: [
        { v: 'low', l: '提示' },
        { v: 'mid', l: '注意' },
        { v: 'high', l: '严重' }
      ]
    }
  },
  computed: {
    sourceHint() {
      const map = {
        search: '来源：AI 检索未解决',
        ticket: '来源：工单维修完成',
        manual: ''
      }
      return map[this.source] || ''
    }
  },
  watch: {
    visible(nv) {
      if (nv) {
        this.submitting = false
        this.errMsg = ''
        this.form = {
          type: (this.preset && this.preset.type) || 'case',
          title: (this.preset && this.preset.title) || '',
          device: (this.preset && this.preset.device) || '',
          ticketId: (this.preset && this.preset.ticketId) || '',
          level: (this.preset && this.preset.level) || 'mid',
          question: (this.preset && this.preset.question) || '',
          repairProcess: (this.preset && this.preset.repairProcess) || '',
          technicalMeasures: (this.preset && this.preset.technicalMeasures) || '',
          repairResult: (this.preset && this.preset.repairResult) || '',
          solution: (this.preset && this.preset.solution) || ''
        }
      }
    }
  },
  methods: {
    handleClose() {
      if (this.submitting) return
      this.$emit('update:visible', false)
      this.$emit('close')
    },
    async handleSubmit() {
      this.errMsg = ''
      if (!this.form.title.trim()) { this.errMsg = '请填写问题标题'; return }
      if (!this.form.question.trim()) { this.errMsg = '请填写 AI 未解决的问题描述'; return }
      if (!this.form.solution.trim()) { this.errMsg = '请填写您的实践解决方案'; return }

      this.submitting = true
      try {
        const user = getUser()
        const rec = await submitReport({ ...this.form }, user, this.source)
        this.$emit('submitted', rec)
        this.$emit('update:visible', false)
      } catch (e) {
        this.errMsg = (e && e.message) ? e.message : '提交失败，请重试'
      } finally {
        this.submitting = false
      }
    }
  }
}
</script>

<style scoped>
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

.kr-mask {
  position: fixed; inset: 0;
  background: rgba(0, 0, 0, 0.65);
  backdrop-filter: blur(6px);
  z-index: 2000;
  display: flex; align-items: center; justify-content: center;
  padding: 24px;
}
.kr-dialog {
  width: 100%; max-width: 720px;
  max-height: 90vh;
  display: flex; flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--border-active);
  box-shadow: 0 20px 60px rgba(0,0,0,0.6), 0 0 0 1px var(--border-subtle);
}

.kr-header {
  padding: 18px 24px;
  border-bottom: 1px solid var(--border-subtle);
  display: flex; justify-content: space-between; align-items: flex-start;
  background: linear-gradient(135deg, rgba(0,212,255,0.08), transparent 60%);
}
.kr-head-left { display: flex; gap: 14px; align-items: flex-start; }
.kr-icon { font-size: 1.75rem; line-height: 1; }
.kr-title { font-size: 1.0625rem; font-weight: 600; color: var(--text-primary); }
.kr-sub { font-size: 0.75rem; color: var(--text-secondary); margin-top: 4px; max-width: 440px; line-height: 1.5; }

.kr-close {
  width: 32px; height: 32px;
  background: transparent;
  color: var(--text-muted);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
}
.kr-close:hover { color: var(--accent-red); border-color: var(--accent-red); background: rgba(255,71,87,0.08); }

.kr-body {
  padding: 20px 24px;
  overflow-y: auto;
  flex: 1;
  display: flex; flex-direction: column; gap: 16px;
}

.kr-label {
  display: block;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  margin-bottom: 6px;
  font-weight: 500;
}
.kr-label.required::before {
  content: '*'; color: var(--accent-red);
  margin-right: 4px;
}
.label-hint {
  font-size: 0.6875rem;
  color: var(--text-muted);
  font-weight: 400;
  margin-left: 6px;
}

.kr-type-row .type-switch {
  display: grid; grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.type-btn {
  padding: 14px 18px;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
  color: var(--text-secondary);
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  font-size: 0.875rem;
  font-weight: 600;
  transition: all var(--duration) var(--ease);
  display: flex; flex-direction: column; gap: 4px;
}
.type-btn em {
  font-size: 0.6875rem;
  font-weight: 400;
  font-style: normal;
  color: var(--text-muted);
}
.type-btn:hover { border-color: var(--border-active); color: var(--text-primary); }
.type-btn.active {
  background: var(--primary-subtle);
  border-color: var(--primary);
  color: var(--primary);
  box-shadow: 0 0 0 3px rgba(0,212,255,0.08);
}
.type-btn.active em { color: rgba(0,212,255,0.8); }

.kr-grid { display: flex; flex-direction: column; gap: 16px; }
.kr-half { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }

.level-group { display: flex; gap: 8px; }
.lv-btn {
  flex: 1;
  padding: 8px 0;
  border-radius: var(--radius);
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
  cursor: pointer;
  font-family: inherit;
  font-size: 0.8125rem;
  color: var(--text-secondary);
  transition: all var(--duration) var(--ease);
}
.lv-btn:hover { border-color: var(--border-active); color: var(--text-primary); }
.lv-btn.lv-low.active   { color: var(--accent-amber);   border-color: var(--accent-amber);   background: rgba(255,165,2,0.08); }
.lv-btn.lv-mid.active   { color: var(--accent-orange);  border-color: var(--accent-orange);  background: rgba(255,107,53,0.08); }
.lv-btn.lv-high.active  { color: var(--accent-red);     border-color: var(--accent-red);     background: rgba(255,71,87,0.08); }

.kr-source-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  background: var(--primary-subtle);
  padding: 8px 12px;
  border-radius: var(--radius);
  border: 1px solid var(--border-active);
  display: flex; align-items: center; gap: 8px;
}
.src-tag {
  font-size: 0.6875rem;
  padding: 2px 8px;
  border-radius: 999px;
  background: var(--primary);
  color: var(--bg-deep);
  font-weight: 600;
}

.kr-footer {
  padding: 14px 24px;
  border-top: 1px solid var(--border-subtle);
  display: flex; justify-content: space-between; align-items: center;
  background: rgba(255,255,255,0.015);
}
.kr-err {
  font-size: 0.75rem;
  color: var(--accent-red);
  font-weight: 500;
}
.kr-actions { display: flex; gap: 10px; }

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
}
.input:focus {
  outline: none;
  border-color: var(--primary);
  background: rgba(0,212,255,0.04);
  box-shadow: 0 0 0 3px rgba(0,212,255,0.1);
}
.input::placeholder { color: var(--text-muted); }
</style>
