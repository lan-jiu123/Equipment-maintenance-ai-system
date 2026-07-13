<template>
  <div class="container profile">
    <div class="page-header">
      <div>
        <h1 class="page-title">👤 个人信息</h1>
        <p class="page-sub">查看并更新您的账户信息</p>
      </div>
      <router-link class="btn btn-outline btn-sm" :to="backBtnPath">← {{ backBtnText }}</router-link>
    </div>

    <div class="profile-grid">
      <!-- 左侧：头像卡 -->
      <div class="card profile-aside">
        <div class="avatar-wrap" @click="openAvatarModal">
          <div class="big-avatar" :class="{ 'has-img': avatarSrc }">
            <img v-if="avatarSrc" :src="avatarSrc" alt="avatar" />
            <template v-else>{{ avatarInitial }}</template>
          </div>
          <div class="status-dot online"></div>
          <div class="avatar-edit-mask">
            <span class="edit-cam">📷</span>
            <span class="edit-txt">点击更换头像</span>
          </div>
        </div>
        <div class="profile-headline">
          <h2 class="profile-name">{{ displayName }}</h2>
          <span class="profile-badge" :class="isWorker ? 'worker' : 'manager'">
            <span class="badge-dot"></span>
            {{ badgeText }}
          </span>
        </div>
        <p class="profile-intro">{{ roleIntro }}</p>

        <ul class="profile-stats">
          <li v-for="(s, i) in stats" :key="i">
            <div class="stat-num">{{ s.num }}</div>
            <div class="stat-label">{{ s.label }}</div>
          </li>
        </ul>

        <div class="aside-sec">
          <h4>所属角色</h4>
          <div class="role-tags">
            <span
              v-for="(t, i) in roleTags"
              :key="i"
              class="role-tag"
              :class="t.cls"
            >{{ t.text }}</span>
          </div>
        </div>

        <div class="aside-sec">
          <h4>登录信息</h4>
          <div class="kv">
            <span class="k">首次登录</span>
            <span class="v">{{ userInfo.firstLogin }}</span>
          </div>
          <div class="kv">
            <span class="k">上次登录</span>
            <span class="v">{{ userInfo.lastLogin }}</span>
          </div>
          <div class="kv">
            <span class="k">登录 IP</span>
            <span class="v mono">{{ userInfo.lastIp }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧：信息区 -->
      <div class="profile-main">
        <div class="card main-block">
          <div class="block-head">
            <h3>基本信息</h3>
            <button class="btn btn-primary btn-sm" @click="saveBasic">保存修改</button>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label>用户名</label>
              <input class="input" v-model="basic.username" disabled />
            </div>
            <div class="form-field">
              <label>真实姓名</label>
              <input class="input" v-model="basic.realName" />
            </div>
            <div class="form-field">
              <label>工号</label>
              <input class="input mono" v-model="basic.empNo" disabled />
            </div>
            <div class="form-field">
              <label>所属部门</label>
              <select class="input" v-model="basic.dept">
                <option v-for="d in deptOptions" :key="d">{{ d }}</option>
              </select>
            </div>
            <div class="form-field">
              <label>岗位</label>
              <input class="input" v-model="basic.position" />
            </div>
            <div class="form-field">
              <label>入职日期</label>
              <input class="input mono" :value="basic.joinDate" disabled />
            </div>
          </div>
        </div>

        <div class="card main-block">
          <div class="block-head">
            <h3>联系方式</h3>
            <button class="btn btn-outline btn-sm" @click="saveContact">保存</button>
          </div>
          <div class="form-grid">
            <div class="form-field">
              <label>📱 手机号码</label>
              <input class="input mono" v-model="contact.mobile" maxlength="11" />
            </div>
            <div class="form-field">
              <label>📧 企业邮箱</label>
              <input class="input mono" v-model="contact.email" />
            </div>
            <div class="form-field">
              <label>☎️ 办公电话</label>
              <input class="input mono" v-model="contact.tel" />
            </div>
            <div class="form-field">
              <label>🪪 办公地点</label>
              <input class="input" v-model="contact.office" />
            </div>
          </div>
        </div>

        <div class="card main-block contrib-block">
          <div class="block-head">
            <h3>📚 我的知识贡献</h3>
            <button class="btn btn-primary btn-sm" @click="openContrib">+ 我要贡献</button>
          </div>
          <div class="contrib-stats">
            <div class="contrib-stat-item">
              <div class="cs-num">{{ kStats.total }}</div>
              <div class="cs-label">累计提交</div>
            </div>
            <div class="contrib-stat-item pending">
              <div class="cs-num">{{ kStats.pending }}</div>
              <div class="cs-label">待审核</div>
            </div>
            <div class="contrib-stat-item approved">
              <div class="cs-num">{{ kStats.approved }}</div>
              <div class="cs-label">已入库</div>
            </div>
            <div class="contrib-stat-item rejected">
              <div class="cs-num">{{ kStats.rejected }}</div>
              <div class="cs-label">已驳回</div>
            </div>
          </div>
          <div class="contrib-list" v-if="myReports.length > 0">
            <div v-for="r in myReports" :key="r.id" class="contrib-row">
              <div class="cr-head">
                <div class="cr-title">{{ r.title }}</div>
                <span class="cr-status" :class="'st-' + r.status">{{ statusLabel(r.status) }}</span>
              </div>
              <div class="cr-meta">
                <span class="cr-source">{{ sourceLabel(r.source) }}</span>
                <span class="cr-device" v-if="r.device">◈ {{ r.device }}</span>
                <span class="cr-time">{{ formatTime(r.submitTime) }}</span>
              </div>
              <div class="cr-body" v-if="r.status === 'rejected' && r.reviewRemark">
                <span class="cr-reject-label">驳回原因：</span>
                <span class="cr-reject-text">{{ r.reviewRemark }}</span>
              </div>
              <div class="cr-body" v-else-if="r.reviewRemark">
                <span class="cr-approve-label">审核备注：</span>
                <span class="cr-approve-text">{{ r.reviewRemark }}</span>
              </div>
            </div>
          </div>
          <div v-else class="contrib-empty">
            <div class="ce-icon">📚</div>
            <div class="ce-title">还没有知识贡献记录</div>
            <div class="ce-desc">在维修实践中发现 AI 无法解决的问题？提交您的有效方案，经审核后入库知识库！</div>
          </div>
        </div>

        <div class="card main-block">
          <div class="block-head">
            <h3>偏好设置</h3>
          </div>
          <div class="pref-list">
            <template v-if="isManager">
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">🔔 新工单提醒</div>
                  <div class="pref-desc">当有新的待派单或 SLA 预警时立即推送提醒</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.warnPush" checked />
                  <span class="slider"></span>
                </label>
              </div>
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">📧 每日运维摘要邮件</div>
                  <div class="pref-desc">每天 08:30 自动发送当日运维待办与昨日完成汇总</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.dailyMail" checked />
                  <span class="slider"></span>
                </label>
              </div>
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">📊 周报自动生成</div>
                  <div class="pref-desc">每周五 18:00 自动生成本周运维周报</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.weeklyReport" checked />
                  <span class="slider"></span>
                </label>
              </div>
            </template>
            <template v-else>
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">🔔 新派单提醒</div>
                  <div class="pref-desc">当有新的工单指派给你时立即推送提醒</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.warnPush" checked />
                  <span class="slider"></span>
                </label>
              </div>
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">⏰ SLA 倒计时提醒</div>
                  <div class="pref-desc">处理中工单临近 SLA 截止时间前 30 分钟提醒</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.slaRemind" checked />
                  <span class="slider"></span>
                </label>
              </div>
              <div class="pref-row">
                <div class="pref-info">
                  <div class="pref-name">🧾 维修报告模板</div>
                  <div class="pref-desc">默认使用标准模板自动填充维修报告字段</div>
                </div>
                <label class="switch">
                  <input type="checkbox" v-model="prefs.reportTpl" checked />
                  <span class="slider"></span>
                </label>
              </div>
            </template>
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">🌐 会话保持</div>
                <div class="pref-desc">关闭浏览器后是否保留登录状态 24 小时</div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="prefs.keepSession" />
                <span class="slider"></span>
              </label>
            </div>
            <div class="pref-row">
              <div class="pref-info">
                <div class="pref-name">🎨 启用动效</div>
                <div class="pref-desc">页面切换与卡片悬浮动画</div>
              </div>
              <label class="switch">
                <input type="checkbox" v-model="prefs.anim" checked />
                <span class="slider"></span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="toast.show" class="toast" :class="{ ok: toast.ok }">{{ toast.msg }}</div>

    <!-- 知识报告弹窗 -->
    <KnowledgeReport
      :visible="reportVisible"
      source="manual"
      @update:visible="v => reportVisible = v"
      @submitted="onReportSubmitted"
    />

    <!-- 头像选择 Modal -->
    <div v-if="modalOpen" class="modal-mask" @click.self="closeAvatarModal">
      <div class="modal-card card" @click.stop>
        <div class="modal-head">
          <h3>🎨 更换头像</h3>
          <button class="modal-close" @click="closeAvatarModal">✕</button>
        </div>

        <div class="modal-body">
          <div class="preview-row">
            <div class="preview-label">预览</div>
            <div class="preview-avatar" :class="{ 'has-img': previewSrc }">
              <img v-if="previewSrc" :src="previewSrc" alt="preview" />
              <template v-else>{{ avatarInitial }}</template>
            </div>
          </div>

          <div class="section">
            <h4>选择预设头像</h4>
            <div class="preset-grid">
              <div
                v-for="p in presets"
                :key="p.id"
                class="preset-item"
                :class="{ active: draftAvatar === p.id }"
                @click="selectPreset(p.id)"
              >
                <img :src="p.src" :alt="p.name" />
                <span class="preset-name">{{ p.name }}</span>
                <span v-if="draftAvatar === p.id" class="check">✓</span>
              </div>
            </div>
          </div>

          <div class="section">
            <h4>上传本地图片</h4>
            <div class="upload-area">
              <div class="upload-box">
                <div class="upload-icon">⬆</div>
                <div class="upload-text">
                  点击选择图片，支持 JPG / PNG / GIF，最大 2MB
                </div>
                <button class="btn btn-primary btn-sm" @click="triggerUpload">
                  📂 选择文件
                </button>
                <input
                  ref="fileInput"
                  type="file"
                  accept="image/*"
                  style="display:none"
                  @change="onFileSelected"
                />
              </div>
              <p v-if="uploadErr" class="upload-err">{{ uploadErr }}</p>
              <p v-else-if="draftAvatar && draftAvatar.startsWith('data:')" class="upload-ok">
                ✓ 已上传本地图片
              </p>
            </div>
          </div>

          <div class="section actions-sec">
            <button class="btn btn-outline btn-sm" @click="resetToDefault">
              使用默认字母头像
            </button>
          </div>
        </div>

        <div class="modal-foot">
          <button class="btn btn-outline" @click="closeAvatarModal">取消</button>
          <button class="btn btn-primary" @click="applyAvatar">保存头像</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  getUser,
  getAvatar,
  setAvatar,
  removeAvatar,
  resolveAvatarSrc,
  AVATAR_PRESETS
} from '../utils/auth'
import {
  fetchUserReports,
  fetchUserStats,
  getUserStats,
  getReportsByUser,
  REPORT_STATUS_LABEL,
  REPORT_SOURCE_LABEL
} from '../utils/knowledge'
import KnowledgeReport from '../components/KnowledgeReport.vue'
import { updateProfileApi } from '../utils/api'

const DEPT_OPTIONS = ['设备管理部', '生产运营部', '设备维修中心', '安全环保部']

const ROLE_PROFILE = {
  sysadmin: {
    badge: '维修管理员',
    intro: '负责车间设备维修工作的整体统筹：工单派发与调度、维修工排班与绩效、质量复核、SLA 监控及应急预案管理，保障生产设备高效稳定运行。',
    stats: [
      { num: 186, label: '累计登录' },
      { num: 412, label: '派发工单' },
      { num: 298, label: '复核通过' }
    ],
    roleTags: [
      { cls: 'admin', text: '维修管理员' },
      { cls: 'audit', text: '工单调度' },
      { cls: 'ops', text: '质量复核' }
    ],
    dept: '设备管理部',
    position: '设备管理主管',
    empPrefix: 'EMP-M-',
    joinDate: '2021-03-18',
    mobile: '139****6821',
    emailPrefix: 'guanli',
    tel: '021-8888-1001',
    office: '主厂区 · 中心办公楼 B403',
    prefs: { warnPush: true, dailyMail: true, weeklyReport: true, keepSession: false, anim: true }
  },
  manager: {
    badge: '维修管理员',
    intro: '负责车间设备维修工作的整体统筹：工单派发与调度、维修工排班与绩效、质量复核、SLA 监控及应急预案管理，保障生产设备高效稳定运行。',
    stats: [
      { num: 186, label: '累计登录' },
      { num: 412, label: '派发工单' },
      { num: 298, label: '复核通过' }
    ],
    roleTags: [
      { cls: 'admin', text: '维修管理员' },
      { cls: 'audit', text: '工单调度' },
      { cls: 'ops', text: '质量复核' }
    ],
    dept: '设备管理部',
    position: '设备管理主管',
    empPrefix: 'EMP-M-',
    joinDate: '2021-03-18',
    mobile: '139****6821',
    emailPrefix: 'guanli',
    tel: '021-8888-1001',
    office: '主厂区 · 中心办公楼 B403',
    prefs: { warnPush: true, dailyMail: true, weeklyReport: true, keepSession: false, anim: true }
  },
  worker: {
    badge: '一线检修员',
    intro: '负责厂区设备的日常巡检、故障抢修与预防性维护；按作业指导完成检修任务，规范填写维修报告并上报，保障设备安全与可用率。',
    stats: [
      { num: 241, label: '累计登录' },
      { num: 356, label: '完成维修' },
      { num: 487, label: 'AI 辅助检索' }
    ],
    roleTags: [
      { cls: 'ops', text: '一线检修员' },
      { cls: 'tech', text: '高级技工' },
      { cls: 'safe', text: '巡检员' }
    ],
    dept: '设备维修中心',
    position: '高级维修技工',
    empPrefix: 'EMP-W-',
    joinDate: '2022-07-05',
    mobile: '138****3947',
    emailPrefix: 'weixiu',
    tel: '021-8888-2017',
    office: '主厂区 · 维修车间 A207',
    prefs: { warnPush: true, slaRemind: true, reportTpl: true, keepSession: true, anim: true }
  }
}

function _hashStr(s, len = 4) {
  let h = 2166136261 >>> 0
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i)
    h = Math.imul(h, 16777619)
  }
  return String(h >>> 0).padStart(len, '0').slice(-len)
}

export default {
  name: 'Profile',
  components: { KnowledgeReport },
  data() {
    const user = getUser() || { username: 'admin', role: 'manager', fullname: '维修管理员' }
    const roleKey = user.role || 'manager'
    const cfg = ROLE_PROFILE[roleKey] || ROLE_PROFILE.manager
    const name = user.fullname || user.username || '用户'
    const hash = _hashStr(name + (user.username || ''))
    return {
      user,
      cfg,
      deptOptions: DEPT_OPTIONS,
      userInfo: {
        logins: cfg.stats[0].num,
        retrievals: 524,
        cases: 73,
        firstLogin: cfg.joinDate + ' 09:12',
        lastLogin: '2026-07-10 15:24',
        lastIp: '10.128.22.' + (parseInt(hash, 10) % 200 + 10)
      },
      basic: {
        username: user.username || 'admin',
        realName: name,
        empNo: user.emp_no || (cfg.empPrefix + String(20210000 + parseInt(hash, 10)).slice(-6)),
        dept: user.dept || cfg.dept,
        position: user.position || cfg.position,
        joinDate: user.join_date || cfg.joinDate
      },
      contact: {
        mobile: user.mobile || cfg.mobile,
        email: user.email || `${cfg.emailPrefix}.${(user.username || 'user').toLowerCase().replace(/[^a-z0-9]/g, '') || hash}@equipai.com`,
        tel: user.tel || cfg.tel,
        office: user.office || cfg.office
      },
      prefs: Object.assign({}, cfg.prefs),
      toast: { show: false, ok: true, msg: '' },
      presets: AVATAR_PRESETS,
      avatarSrc: '',
      modalOpen: false,
      draftAvatar: '',
      uploadErr: '',
      reportVisible: false,
      kStats: { total: 0, pending: 0, approved: 0, rejected: 0 },
      myReports: [],
      _kLoading: false,
      _kHydrated: false,
      _saving: false
    }
  },
  computed: {
    isWorker() {
      return this.user.role === 'worker'
    },
    isManager() {
      return !this.isWorker
    },
    backBtnText() {
      return this.isWorker ? '返回工作台' : '返回仪表盘'
    },
    backBtnPath() {
      return this.isWorker ? '/desk' : '/home'
    },
    displayName() {
      return this.user.fullname || this.user.username || '用户'
    },
    avatarInitial() {
      const n = this.displayName || 'U'
      const ch = n.charAt(0).toUpperCase()
      if (/[A-Z0-9]/.test(ch)) return ch
      const code = n.charCodeAt(0)
      return String.fromCharCode(65 + (code % 26))
    },
    badgeText() {
      return this.cfg.badge
    },
    roleIntro() {
      return this.cfg.intro
    },
    stats() {
      return this.cfg.stats
    },
    roleTags() {
      return this.cfg.roleTags
    },
    previewSrc() {
      return resolveAvatarSrc(this.draftAvatar)
    }
  },
  async created() {
    this.refreshAvatar()
    window.addEventListener('equipai-avatar-changed', this.refreshAvatar)
    window.addEventListener('equipai-knowledge-changed', this.refreshKnowledge)
    await this.refreshKnowledge({ initial: true })
  },
  beforeUnmount() {
    window.removeEventListener('equipai-avatar-changed', this.refreshAvatar)
    window.removeEventListener('equipai-knowledge-changed', this.refreshKnowledge)
  },
  methods: {
    refreshAvatar() {
      this.avatarSrc = resolveAvatarSrc(getAvatar())
    },
    async refreshKnowledge({ initial = false, force = false } = {}) {
      const u = (this.user && this.user.username) || 'worker'
      if (this._kLoading && !force) return
      this._kLoading = true
      try {
        const [stats, reports] = await Promise.all([
          fetchUserStats(u),
          fetchUserReports(u)
        ])
        this.kStats = stats
        this.myReports = reports
      } catch (_) {
        this.kStats = getUserStats(u)
        this.myReports = getReportsByUser(u)
      } finally {
        this._kLoading = false
        this._kHydrated = true
      }
    },
    openContrib() {
      this.reportVisible = true
    },
    onReportSubmitted(rec) {
      this.showToast(`✅ 报告「${rec.id}」提交成功，管理员将尽快审核`)
    },
    statusLabel(s) {
      return REPORT_STATUS_LABEL[s] || s
    },
    sourceLabel(s) {
      return REPORT_SOURCE_LABEL[s] || s
    },
    formatTime(ts) {
      if (!ts) return ''
      const d = new Date(ts)
      return d.toLocaleDateString('zh-CN') + ' ' + d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
    },
    showToast(msg, ok = true) {
      this.toast = { show: true, ok, msg }
      setTimeout(() => (this.toast.show = false), 1800)
    },
    async saveBasic() {
      if (this._saving) return
      this._saving = true
      try {
        const res = await updateProfileApi({
          fullname: this.basic.realName || null,
          empNo: this.basic.empNo || null,
          dept: this.basic.dept || null,
          position: this.basic.position || null,
          joinDate: this.basic.joinDate || null,
        })
        // request.js 成功时直接返回 payload.data（非完整 ApiResp），无异常即成功
        if (res && typeof res === 'object') {
          this._patchUser(res)
          this.showToast('✓ 基本信息已保存')
        } else {
          this.showToast('保存失败：返回格式异常', false)
        }
      } catch (e) {
        this.showToast('保存失败：' + (e && e.message ? e.message : '网络异常'), false)
      } finally {
        this._saving = false
      }
    },
    async saveContact() {
      if (this._saving) return
      this._saving = true
      try {
        const res = await updateProfileApi({
          mobile: this.contact.mobile || null,
          email: this.contact.email || null,
          tel: this.contact.tel || null,
          office: this.contact.office || null,
        })
        if (res && typeof res === 'object') {
          this._patchUser(res)
          this.showToast('✓ 联系方式已保存')
        } else {
          this.showToast('保存失败：返回格式异常', false)
        }
      } catch (e) {
        this.showToast('保存失败：' + (e && e.message ? e.message : '网络异常'), false)
      } finally {
        this._saving = false
      }
    },
    _patchUser(u) {
      if (!u || !this.user) return
      const keys = ['fullname','emp_no','dept','position','join_date',
                    'mobile','email','tel','office','role','role_label',
                    'avatar_preset','join_date_ts','id','username']
      for (const k of keys) {
        if (u[k] !== undefined && u[k] !== null) {
          this.user[k] = u[k]
        }
      }
      // 同步 reactive store
      try {
        const { setUser } = require('../utils/auth')
        setUser({ ...getUser(), ...this.user })
      } catch (_) {}
      // 同步 basic / contact 当下值，避免残留脏值
      if (u.fullname) this.basic.realName = u.fullname
      if (u.emp_no !== undefined) this.basic.empNo = u.emp_no || this.basic.empNo
      if (u.dept     !== undefined) this.basic.dept = u.dept || this.basic.dept
      if (u.position !== undefined) this.basic.position = u.position || this.basic.position
      if (u.join_date !== undefined) this.basic.joinDate = u.join_date || this.basic.joinDate
      if (u.mobile !== undefined) this.contact.mobile = u.mobile || this.contact.mobile
      if (u.email  !== undefined) this.contact.email = u.email || this.contact.email
      if (u.tel    !== undefined) this.contact.tel = u.tel || this.contact.tel
      if (u.office !== undefined) this.contact.office = u.office || this.contact.office
    },
    openAvatarModal() {
      this.draftAvatar = getAvatar()
      this.uploadErr = ''
      this.modalOpen = true
    },
    closeAvatarModal() {
      this.modalOpen = false
      this.uploadErr = ''
      const fi = this.$refs.fileInput
      if (fi) fi.value = ''
    },
    selectPreset(id) {
      this.draftAvatar = id
      this.uploadErr = ''
    },
    resetToDefault() {
      this.draftAvatar = ''
      this.uploadErr = ''
    },
    triggerUpload() {
      this.$refs.fileInput && this.$refs.fileInput.click()
    },
    onFileSelected(e) {
      const file = e.target && e.target.files && e.target.files[0]
      this.uploadErr = ''
      if (!file) return
      if (!/^image\//.test(file.type)) {
        this.uploadErr = '只能上传图片文件 (JPG / PNG / GIF)'
        return
      }
      if (file.size > 2 * 1024 * 1024) {
        this.uploadErr = '图片大小不能超过 2MB'
        return
      }
      const reader = new FileReader()
      reader.onload = () => {
        this.draftAvatar = String(reader.result || '')
      }
      reader.onerror = () => {
        this.uploadErr = '文件读取失败，请重试'
      }
      reader.readAsDataURL(file)
    },
    applyAvatar() {
      if (this.draftAvatar) {
        setAvatar(this.draftAvatar)
      } else {
        removeAvatar()
      }
      this.showToast('✓ 头像已更新')
      this.closeAvatarModal()
    }
  }
}
</script>

<style scoped>
.profile {
  max-width: 1200px;
}

.page-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 28px;
}

.page-title {
  font-size: 1.625rem;
  margin-bottom: 4px;
}

.page-sub {
  font-size: 0.8125rem;
  color: var(--text-secondary);
}

.profile-grid {
  display: grid;
  grid-template-columns: 320px 1fr;
  gap: 24px;
  align-items: flex-start;
}

/* === Aside === */
.profile-aside {
  position: sticky;
  top: 88px;
  display: flex;
  flex-direction: column;
  align-items: stretch;
}

.avatar-wrap {
  position: relative;
  align-self: center;
  margin-bottom: 18px;
  cursor: pointer;
  width: 96px;
}

.big-avatar {
  width: 96px;
  height: 96px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-dim));
  color: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
  font-size: 2.25rem;
  box-shadow: 0 0 0 3px var(--primary-subtle), 0 0 28px var(--primary-glow);
  overflow: hidden;
}
.big-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.big-avatar.has-img {
  color: transparent;
  background: #000;
}

.avatar-edit-mask {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.65);
  color: #fff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  opacity: 0;
  transition: opacity 200ms var(--ease);
  pointer-events: none;
}
.avatar-wrap:hover .avatar-edit-mask {
  opacity: 1;
}
.edit-cam {
  font-size: 1.25rem;
  line-height: 1;
  margin-bottom: 2px;
}
.edit-txt {
  font-size: 0.625rem;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.status-dot {
  position: absolute;
  right: 2px;
  bottom: 2px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid var(--bg-surface);
}
.status-dot.online {
  background: var(--accent-green);
  box-shadow: 0 0 10px var(--accent-green);
}

.profile-headline {
  text-align: center;
  margin-bottom: 12px;
}

.profile-name {
  font-size: 1.1875rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'Orbitron', sans-serif;
  letter-spacing: 1px;
  margin-bottom: 8px;
}

.profile-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  font-size: 0.6875rem;
  border-radius: 20px;
  background: var(--primary-subtle);
  color: var(--primary);
  border: 1px solid var(--border-active);
  letter-spacing: 0.5px;
}
.profile-badge.worker {
  background: rgba(0, 255, 136, 0.08);
  border-color: rgba(0, 255, 136, 0.3);
  color: var(--accent-green);
}
.profile-badge.worker .badge-dot {
  background: var(--accent-green);
  box-shadow: 0 0 6px var(--accent-green);
}
.profile-badge.manager {
  background: var(--primary-subtle);
  color: var(--primary);
  border-color: var(--border-active);
}
.profile-badge.manager .badge-dot {
  background: var(--primary);
  box-shadow: 0 0 6px var(--primary-glow);
}
.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.profile-intro {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
  line-height: 1.6;
  padding: 14px 0 18px;
  border-bottom: 1px dashed var(--border-subtle);
  margin-bottom: 18px;
}

.profile-stats {
  list-style: none;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 22px;
}
.profile-stats li {
  text-align: center;
  padding: 10px 4px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
}
.stat-num {
  font-family: 'Orbitron', sans-serif;
  font-weight: 700;
  font-size: 1.0625rem;
  color: var(--primary);
  margin-bottom: 2px;
}
.stat-label {
  font-size: 0.625rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

.aside-sec {
  margin-bottom: 20px;
}
.aside-sec:last-child {
  margin-bottom: 0;
}
.aside-sec h4 {
  font-size: 0.6875rem;
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin-bottom: 10px;
}

.role-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.role-tag {
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 0.6875rem;
  font-weight: 500;
  border: 1px solid;
}
.role-tag.admin {
  color: var(--primary);
  background: var(--primary-subtle);
  border-color: var(--border-active);
}
.role-tag.audit {
  color: var(--accent-amber);
  background: rgba(255, 165, 2, 0.08);
  border-color: rgba(255, 165, 2, 0.3);
}
.role-tag.ops {
  color: var(--accent-red);
  background: rgba(255, 71, 87, 0.08);
  border-color: rgba(255, 71, 87, 0.3);
}
.role-tag.tech {
  color: #22d3ee;
  background: rgba(34, 211, 238, 0.08);
  border-color: rgba(34, 211, 238, 0.3);
}
.role-tag.safe {
  color: var(--accent-green);
  background: rgba(0, 255, 136, 0.08);
  border-color: rgba(0, 255, 136, 0.3);
}

.kv {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 7px 0;
  font-size: 0.75rem;
  border-bottom: 1px dashed var(--border-subtle);
}
.kv:last-child {
  border-bottom: none;
}
.kv .k {
  color: var(--text-secondary);
}
.kv .v {
  color: var(--text-primary);
  font-weight: 500;
}
.mono {
  font-family: 'JetBrains Mono', monospace;
  letter-spacing: 0.5px;
}

/* === Main === */
.profile-main {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.main-block h3 {
  font-size: 1rem;
  color: var(--text-primary);
}
.block-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--border-subtle);
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
.form-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.form-field label {
  font-size: 0.6875rem;
  font-weight: 500;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}

/* === Prefs === */
.pref-list {
  display: flex;
  flex-direction: column;
}
.pref-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 0;
  border-bottom: 1px dashed var(--border-subtle);
}
.pref-row:last-child {
  border-bottom: none;
}
.pref-name {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 3px;
}
.pref-desc {
  font-size: 0.6875rem;
  color: var(--text-secondary);
}

.switch {
  position: relative;
  width: 44px;
  height: 24px;
  flex-shrink: 0;
}
.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}
.slider {
  position: absolute;
  cursor: pointer;
  inset: 0;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: 24px;
  transition: all var(--duration) var(--ease);
}
.slider::before {
  content: '';
  position: absolute;
  width: 18px;
  height: 18px;
  left: 2px;
  top: 50%;
  transform: translateY(-50%);
  border-radius: 50%;
  background: var(--text-muted);
  transition: all var(--duration) var(--ease);
}
.switch input:checked + .slider {
  background: var(--primary-subtle);
  border-color: var(--border-active);
}
.switch input:checked + .slider::before {
  left: 22px;
  background: var(--primary);
  box-shadow: 0 0 8px var(--primary-glow);
}

.btn-sm {
  padding: 6px 16px;
  font-size: 0.8125rem;
}

/* === Toast === */
.toast {
  position: fixed;
  bottom: 48px;
  left: 50%;
  transform: translateX(-50%);
  padding: 10px 20px;
  background: var(--bg-elevated);
  color: var(--text-primary);
  border: 1px solid var(--border-active);
  border-radius: var(--radius);
  font-size: 0.8125rem;
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.4), var(--shadow-glow);
  z-index: 1000;
  animation: toastIn 240ms var(--ease);
}
.toast.ok {
  border-color: rgba(0, 255, 136, 0.4);
}
@keyframes toastIn {
  from { opacity: 0; transform: translate(-50%, 10px); }
  to   { opacity: 1; transform: translate(-50%, 0); }
}

/* ========== Avatar Modal ========== */
.modal-mask {
  position: fixed;
  inset: 0;
  background: rgba(4, 8, 26, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
  animation: maskIn 200ms var(--ease);
}
@keyframes maskIn {
  from { opacity: 0; }
  to   { opacity: 1; }
}
.modal-card {
  width: 100%;
  max-width: 520px;
  padding: 0;
  overflow: hidden;
  animation: cardIn 260ms var(--ease);
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.6), 0 0 48px rgba(0, 212, 255, 0.12);
}
@keyframes cardIn {
  from { opacity: 0; transform: translateY(20px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 22px;
  border-bottom: 1px solid var(--border-subtle);
  background: linear-gradient(135deg, var(--primary-subtle), transparent);
}
.modal-head h3 {
  font-size: 1.0625rem;
}
.modal-close {
  width: 30px;
  height: 30px;
  background: transparent;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  color: var(--text-secondary);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--duration) var(--ease);
}
.modal-close:hover {
  color: var(--accent-red);
  border-color: rgba(255, 71, 87, 0.4);
  background: rgba(255, 71, 87, 0.08);
}
.modal-body {
  padding: 22px;
}
.section + .section {
  margin-top: 22px;
}
.section h4 {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 1px;
  text-transform: uppercase;
  color: var(--text-secondary);
  margin-bottom: 12px;
}

.preview-row {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 14px 16px;
  background: var(--bg-deep);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
  margin-bottom: 22px;
}
.preview-label {
  font-size: 0.75rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}
.preview-avatar {
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--primary), var(--primary-dim));
  color: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  font-family: 'Orbitron', sans-serif;
  font-size: 1.75rem;
  box-shadow: 0 0 0 2px var(--primary-subtle), 0 0 22px var(--primary-glow);
  overflow: hidden;
}
.preview-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.preview-avatar.has-img {
  color: transparent;
  background: #000;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.preset-item {
  position: relative;
  padding: 10px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition: all var(--duration) var(--ease);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.preset-item:hover {
  border-color: var(--border-hover);
  transform: translateY(-2px);
}
.preset-item.active {
  border-color: var(--primary);
  background: var(--primary-subtle);
  box-shadow: 0 0 0 1px var(--primary), var(--shadow-glow);
}
.preset-item img {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  object-fit: cover;
  display: block;
  border: 1px solid var(--border-subtle);
}
.preset-item.active img {
  border-color: var(--primary);
}
.preset-name {
  font-size: 0.6875rem;
  color: var(--text-primary);
  font-weight: 500;
}
.preset-item .check {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 20px;
  height: 20px;
  background: var(--primary);
  color: var(--bg-deep);
  border-radius: 50%;
  font-size: 0.6875rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
}

.upload-box {
  padding: 22px;
  background: var(--bg-deep);
  border: 2px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  transition: all var(--duration) var(--ease);
}
.upload-box:hover {
  border-color: var(--primary);
  background: var(--primary-subtle);
}
.upload-icon {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--primary);
  color: var(--bg-deep);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 4px;
  box-shadow: 0 0 16px var(--primary-glow);
}
.upload-text {
  font-size: 0.75rem;
  color: var(--text-secondary);
  text-align: center;
}
.upload-err {
  margin-top: 10px;
  font-size: 0.75rem;
  color: var(--accent-red);
  background: rgba(255, 71, 87, 0.08);
  border: 1px solid rgba(255, 71, 87, 0.25);
  border-radius: var(--radius);
  padding: 8px 12px;
}
.upload-ok {
  margin-top: 10px;
  font-size: 0.75rem;
  color: var(--accent-green);
  background: rgba(0, 255, 136, 0.08);
  border: 1px solid rgba(0, 255, 136, 0.25);
  border-radius: var(--radius);
  padding: 8px 12px;
}
.actions-sec {
  display: flex;
  justify-content: flex-end;
  padding-top: 4px;
}

.modal-foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 22px;
  border-top: 1px solid var(--border-subtle);
  background: var(--bg-deep);
}

/* === Knowledge Contribution === */
.contrib-block .block-head h3 {
  font-size: 1rem;
  color: var(--text-primary);
}
.contrib-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 22px;
}
.contrib-stat-item {
  padding: 16px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  text-align: center;
}
.cs-num {
  font-size: 1.75rem;
  font-weight: 700;
  color: var(--text-primary);
  font-family: 'Orbitron', sans-serif;
  line-height: 1;
}
.cs-label {
  margin-top: 8px;
  font-size: 0.6875rem;
  color: var(--text-secondary);
  letter-spacing: 0.5px;
}
.contrib-stat-item.pending .cs-num { color: var(--accent-amber, #ffa502); }
.contrib-stat-item.approved .cs-num { color: var(--accent-green, #00ff88); }
.contrib-stat-item.rejected .cs-num { color: var(--accent-red, #ff4757); }

.contrib-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.contrib-row {
  padding: 14px 16px;
  background: var(--bg-deep);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius);
  transition: all var(--duration);
}
.contrib-row:hover { border-color: var(--border-hover); }
.cr-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
}
.cr-title {
  font-size: 0.9375rem;
  font-weight: 600;
  color: var(--text-primary);
  flex: 1;
}
.cr-status {
  flex-shrink: 0;
  padding: 3px 10px;
  font-size: 0.6875rem;
  border-radius: 999px;
  font-weight: 500;
  border: 1px solid;
}
.cr-status.st-pending { color: var(--accent-amber); background: rgba(255,165,2,0.1); border-color: rgba(255,165,2,0.3); }
.cr-status.st-approved { color: var(--accent-green); background: rgba(0,255,136,0.1); border-color: rgba(0,255,136,0.3); }
.cr-status.st-rejected { color: var(--accent-red); background: rgba(255,71,87,0.1); border-color: rgba(255,71,87,0.3); }
.cr-status.st-synced_case { color: #22d3ee; background: rgba(34,211,238,0.1); border-color: rgba(34,211,238,0.3); }
.cr-status.st-synced_guide { color: #a78bfa; background: rgba(167,139,250,0.1); border-color: rgba(167,139,250,0.3); }
.cr-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 0.6875rem;
  color: var(--text-secondary);
}
.cr-source {
  padding: 2px 8px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 4px;
  color: var(--text-secondary);
}
.cr-device { color: var(--primary); }
.cr-time { opacity: 0.8; }
.cr-body {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px dashed var(--border-subtle);
  font-size: 0.8125rem;
  line-height: 1.6;
}
.cr-reject-label { color: var(--accent-red); font-weight: 600; }
.cr-reject-text { color: var(--text-primary); }
.cr-approve-label { color: var(--accent-green); font-weight: 600; }
.cr-approve-text { color: var(--text-primary); }

.contrib-empty {
  padding: 40px 20px;
  text-align: center;
  background: var(--bg-deep);
  border: 1px dashed var(--border-subtle);
  border-radius: var(--radius-lg);
}
.ce-icon { font-size: 3rem; margin-bottom: 12px; opacity: 0.5; }
.ce-title { font-size: 1rem; font-weight: 600; color: var(--text-primary); margin-bottom: 6px; }
.ce-desc { font-size: 0.8125rem; color: var(--text-secondary); line-height: 1.6; max-width: 480px; margin: 0 auto; }

/* === Responsive === */
@media (max-width: 880px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
  .profile-aside {
    position: static;
  }
  .form-grid {
    grid-template-columns: 1fr;
  }
}
</style>
