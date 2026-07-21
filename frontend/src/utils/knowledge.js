import {
  listReportsApi,
  submitReportApi,
  reviewReportApi
} from './api'
import { getUser } from './auth'

const STORAGE_KEY = 'equipai:knowledge_reports'
const LAST_SYNC_KEY = 'equipai:knowledge_last_sync'

export const REPORT_STATUS = {
  PENDING: 'pending',
  APPROVED: 'approved',
  REJECTED: 'rejected',
  SYNCED_CASE: 'synced_case',
  SYNCED_GUIDE: 'synced_guide'
}

export const REPORT_STATUS_LABEL = {
  [REPORT_STATUS.PENDING]:      '待审核',
  [REPORT_STATUS.APPROVED]:     '已通过',
  [REPORT_STATUS.REJECTED]:     '已驳回',
  [REPORT_STATUS.SYNCED_CASE]:  '已入库·案例',
  [REPORT_STATUS.SYNCED_GUIDE]: '已入库·规程'
}

export const REPORT_SOURCE = {
  SEARCH: 'search',
  TICKET: 'ticket',
  MANUAL: 'manual'
}

export const REPORT_SOURCE_LABEL = {
  [REPORT_SOURCE.SEARCH]: 'AI检索未解决',
  [REPORT_SOURCE.TICKET]: '工单维修完成',
  [REPORT_SOURCE.MANUAL]: '主动提交'
}

export const KNOWLEDGE_TYPE = {
  CASE: 'case',
  GUIDE: 'guide'
}

const LEVEL_LABEL = {
  low:   { label: '提示',   cls: 'level-low'   },
  mid:   { label: '注意',   cls: 'level-mid'   },
  high:  { label: '严重（加急）',   cls: 'level-high'  }
}

export function getLevelMeta(level) {
  return LEVEL_LABEL[level] || LEVEL_LABEL.mid
}

const SEED_REPORTS = [
  {
    id: 1001,
    rid: 'KR-1001',
    submitter_name: '李师傅',
    userName: '李师傅',
    submitter_username: 'worker',
    userId: 'worker',
    submitter_id: 3,
    source: REPORT_SOURCE.TICKET,
    type: KNOWLEDGE_TYPE.CASE,
    title: '离心泵轴承过热（现场实测：更换303轴承后加注高温锂基脂）',
    device: '离心泵 P-103',
    level: 'mid',
    question: 'AI 建议检查润滑情况，但现场拆解后发现是轴承型号选择错误（原203改为303），且润滑脂不适用高温环境。',
    problem: 'AI 建议检查润滑情况，但现场拆解后发现是轴承型号选择错误（原203改为303），且润滑脂不适用高温环境。',
    cause: '轴承选型偏小+润滑脂高温失效，长时间运行累积热量导致温度报警。',
    solution: '1. 拆泵核对轴承型号，采购 303 型高温轴承替换；\n2. 清理轴承座，加注美孚高温锂基脂 XHP222；\n3. 首次运行连续监测轴承温度 2 小时，稳定在 58℃ 以下。',
    tag: '机械',
    status: REPORT_STATUS.PENDING,
    submit_time: Date.now() - 1000 * 60 * 40,
    submitTime: Date.now() - 1000 * 60 * 40,
    review_time: null,
    reviewer: null,
    review_remark: '',
    ticket_id: 'TK-20260711-003'
  },
  {
    id: 1002,
    rid: 'KR-1002',
    submitter_name: '张师傅',
    userName: '张师傅',
    submitter_username: 'worker2',
    userId: 'worker2',
    submitter_id: 4,
    source: REPORT_SOURCE.SEARCH,
    type: KNOWLEDGE_TYPE.GUIDE,
    title: 'CNC 主轴异响处理规程（敲击法判定轴承游隙）',
    device: 'CNC 加工中心 MC-205',
    level: 'high',
    question: 'AI 给出的排查步骤过于笼统，未给出主轴不拆机情况下的快速判定方法。',
    problem: 'AI 给出的排查步骤过于笼统，未给出主轴不拆机情况下的快速判定方法。',
    cause: 'AI 未覆盖现场快速检测技巧，常规拆机耗时 4 小时且影响产线进度。',
    solution: '主轴异响不拆机排查 3 步法：\n① 手动盘主轴 3 圈感受阻尼是否均匀；\n② 尼龙锤轻敲主轴端部，听是否有"咔哒"声判断游隙；\n③ 红外测温对比前后轴承温差，超过 8℃ 立即停机。\n若判定游隙超标，直接联系主轴厂商保修，勿自行拆解。',
    tag: '机械',
    status: REPORT_STATUS.PENDING,
    submit_time: Date.now() - 1000 * 60 * 95,
    submitTime: Date.now() - 1000 * 60 * 95,
    review_time: null,
    reviewer: null,
    review_remark: '',
    ticket_id: ''
  },
  {
    id: 1003,
    rid: 'KR-1003',
    submitter_name: '刘工',
    userName: '刘工',
    submitter_username: 'worker3',
    userId: 'worker3',
    submitter_id: 5,
    source: REPORT_SOURCE.MANUAL,
    type: KNOWLEDGE_TYPE.CASE,
    title: '压力变送器零点漂移（现场校准无需返厂）',
    device: '压力变送器 PT-407',
    level: 'low',
    question: '压力变送器显示值偏差 3.5%，AI 建议返厂，但现场可以通过 HART 手操器校准。',
    problem: '压力变送器显示值偏差 3.5%，AI 建议返厂，但现场可以通过 HART 手操器校准。',
    cause: '管道压力波动累积导致传感器零点偏移，属正常现场损耗，非硬件故障。',
    solution: '使用 HART 475 手操器：\n1. 接变送器端子，选择"校准-零点";\n2. 确认压力侧为大气压,按提示执行3次零点采集;\n3. 切换至高点校准,施加标准压力源 80%FS;\n4. 保存参数重启变送器,误差降至 0.2% 以内。',
    tag: '仪表',
    status: REPORT_STATUS.PENDING,
    submit_time: Date.now() - 1000 * 60 * 60 * 3,
    submitTime: Date.now() - 1000 * 60 * 60 * 3,
    review_time: null,
    reviewer: null,
    review_remark: '',
    ticket_id: ''
  }
]

let _cache = null
let _cacheDirty = true
let _isHydrating = false

function _normalize(r) {
  if (!r) return r
  r.submitter_name = r.submitter_name || r.submitter || r.userName || '用户'
  r.userName = r.userName || r.submitter_name
  r.submitter = r.submitter || r.submitter_name
  r.submitter_username = r.submitter_username || r.userId || 'unknown'
  r.userId = r.userId || r.submitter_username
  r.submitter_id = r.submitter_id || null
  r.problem = r.problem || r.question || ''
  r.question = r.question || r.problem || ''
  r.cause = r.cause || r.reason || r.rootCause || ''
  r.submit_time = r.submit_time || r.submitTime || 0
  r.submitTime = r.submitTime || r.submit_time
  r.review_time = r.review_time || r.reviewTime || null
  r.review_remark = r.review_remark || r.reviewRemark || ''
  r.ticket_id = r.ticket_id || r.ticketId || ''
  r.rid = r.rid || ('KR-' + (r.id || ''))
  if (!r.tag) {
    const dev = (r.device || '').toLowerCase()
    if (dev.includes('电机') || dev.includes('plc') || dev.includes('变频') || dev.includes('电气')) r.tag = '电气'
    else if (dev.includes('液压') || dev.includes('油')) r.tag = '液压'
    else if (dev.includes('仪表') || dev.includes('变送') || dev.includes('传感')) r.tag = '仪表'
    else if (dev.includes('安全') || dev.includes('阀')) r.tag = '安全'
    else r.tag = r.type === KNOWLEDGE_TYPE.GUIDE ? '机械' : '综合'
  }
  if (!r.summary) {
    const s = (r.solution || '').replace(/\n/g, ' ').trim()
    r.summary = s.length > 80 ? s.slice(0, 80) + '...' : s
  }
  if (!r.fault) r.fault = r.title || ''
  return r
}

function _seedIfEmpty() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(SEED_REPORTS.map(_normalize)))
    }
  } catch (_) {}
}

function _readCache() {
  if (_cache && !_cacheDirty) return _cache
  try {
    _seedIfEmpty()
    const raw = localStorage.getItem(STORAGE_KEY)
    _cache = raw ? (JSON.parse(raw) || []) : []
    _cache = _cache.map(_normalize)
  } catch (_) {
    _cache = JSON.parse(JSON.stringify(SEED_REPORTS)).map(_normalize)
  }
  _cacheDirty = false
  return _cache
}

function _writeCache(list) {
  _cache = list.map(_normalize)
  _cacheDirty = false
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(_cache))
    window.dispatchEvent(new CustomEvent('equipai-knowledge-changed'))
  } catch (_) {}
}

function _mergeWithCache(serverItems = []) {
  const cache = _readCache()
  const byRid = new Map()
  for (const r of cache) byRid.set(String(r.rid || r.id), r)
  for (const s of serverItems) {
    const key = String(s.rid || s.id)
    byRid.set(key, _normalize({ ...(byRid.get(key) || {}), ...s }))
  }
  const merged = Array.from(byRid.values()).sort(
    (a, b) => (b.submit_time || 0) - (a.submit_time || 0)
  )
  _writeCache(merged)
  return merged
}

function _markSync() {
  try {
    localStorage.setItem(LAST_SYNC_KEY, String(Date.now()))
  } catch (_) {}
}

export async function ensureHydrated({ force = false, scope = 'all' } = {}) {
  if (_isHydrating && !force) return _readCache()
  _isHydrating = true
  try {
    const res = await listReportsApi({ page: 1, size: 20000, scope })
    const items = (res && res.items) || []
    const merged = _mergeWithCache(items)
    _markSync()
    return merged
  } catch (e) {
    return _readCache()
  } finally {
    _isHydrating = false
  }
}

export function getReports() {
  return _readCache().sort((a, b) => (b.submit_time || 0) - (a.submit_time || 0))
}

export function getReportsByUser(username) {
  return getReports().filter(r =>
    (r.submitter_username === username) ||
    (r.userId === username) ||
    (String(r.submitter_id) === String(username))
  )
}

export function getReportsByStatus(status) {
  if (Array.isArray(status)) return getReports().filter(r => status.includes(r.status))
  return getReports().filter(r => r.status === status)
}

export function getPendingCount() {
  return getReportsByStatus(REPORT_STATUS.PENDING).length
}

export function getStats() {
  const all = getReports()
  return {
    total: all.length,
    pending: all.filter(r => r.status === REPORT_STATUS.PENDING).length,
    approved: all.filter(r =>
      [REPORT_STATUS.APPROVED, REPORT_STATUS.SYNCED_CASE, REPORT_STATUS.SYNCED_GUIDE].includes(r.status)
    ).length,
    rejected: all.filter(r => r.status === REPORT_STATUS.REJECTED).length,
    synced: all.filter(r =>
      [REPORT_STATUS.SYNCED_CASE, REPORT_STATUS.SYNCED_GUIDE].includes(r.status)
    ).length
  }
}

export function getReportStats() { return getStats() }

export function getUserStats(username) {
  const list = getReportsByUser(username)
  return {
    total: list.length,
    pending: list.filter(r => r.status === REPORT_STATUS.PENDING).length,
    approved: list.filter(r =>
      [REPORT_STATUS.APPROVED, REPORT_STATUS.SYNCED_CASE, REPORT_STATUS.SYNCED_GUIDE].includes(r.status)
    ).length,
    rejected: list.filter(r => r.status === REPORT_STATUS.REJECTED).length
  }
}

export async function fetchUserStats(username) {
  try {
    await ensureHydrated({ scope: 'mine', force: false })
  } catch (_) {}
  return getUserStats(username)
}

export async function fetchUserReports(username) {
  try {
    await ensureHydrated({ scope: 'mine', force: false })
  } catch (_) {}
  return getReportsByUser(username)
}

export async function submitReport(data, user, source = REPORT_SOURCE.MANUAL) {
  const u = user || getUser() || {}
  const payload = {
    title: String(data.title || '').trim(),
    device: String(data.device || '').trim(),
    type: data.type || KNOWLEDGE_TYPE.CASE,
    source: source || data.source || REPORT_SOURCE.MANUAL,
    level: data.level || 'mid',
    tag: data.tag || '',
    question: String(data.question || data.problem || '').trim(),
    cause: String(data.cause || data.reason || '').trim(),
    solution: String(data.solution || '').trim(),
    repair_process: String(data.repairProcess || '').trim(),
    technical_measures: String(data.technicalMeasures || '').trim(),
    repair_result: String(data.repairResult || '').trim(),
    summary: String(data.summary || '').trim(),
    ticket_id: String(data.ticket_id || data.ticketId || '').trim()
  }

  const tempId = 'tmp-' + Date.now().toString(36)
  const optimisticRecord = {
    id: tempId,
    rid: 'KR-PENDING',
    submitter_name: (u && u.fullname) || payload.submitter_name || '用户',
    userName: (u && u.fullname) || payload.submitter_name || '用户',
    submitter_username: (u && u.username) || 'unknown',
    userId: (u && u.username) || 'unknown',
    submitter_id: (u && u.id) ? Number(u.id) : null,
    ...payload,
    status: REPORT_STATUS.PENDING,
    submit_time: Date.now(),
    submitTime: Date.now(),
    review_time: null,
    reviewer: null,
    review_remark: '',
    _op: 'submitting'
  }

  const list = _readCache()
  list.unshift(optimisticRecord)
  _writeCache(list)

  try {
    const serverRec = await submitReportApi(payload)
    const updated = _mergeWithCache([serverRec])
    const idx = updated.findIndex(r => String(r.rid || r.id) === String(serverRec.rid || serverRec.id))
    return idx >= 0 ? updated[idx] : serverRec
  } catch (e) {
    const cl = _readCache()
    const badIdx = cl.findIndex(r => r.id === tempId || r._op === 'submitting')
    if (badIdx >= 0) {
      cl[badIdx]._op = null
      cl[badIdx]._error = e.message || '提交失败'
      _writeCache(cl)
    }
    throw e
  }
}

export async function reviewReport(id, action, reviewer, remark = '') {
  const list = _readCache()
  const idx = list.findIndex(r => String(r.id) === String(id) || String(r.rid) === String(id))
  let saved = null
  if (idx >= 0) {
    saved = JSON.parse(JSON.stringify(list[idx]))
    list[idx]._op = 'reviewing'
    _writeCache(list)
  }

  try {
    const useId = saved && saved.id ? saved.id : id
    const serverRec = await reviewReportApi(useId, action, remark)
    _mergeWithCache([serverRec])
    return serverRec
  } catch (e) {
    if (saved && idx >= 0) {
      const cl = _readCache()
      cl[idx] = saved
      _writeCache(cl)
    }
    throw e
  }
}

export async function syncReportToLibrary(id, type = 'case') {
  const action = type === 'guide' ? 'sync_guide' : 'sync_case'
  return reviewReport(id, action, null, '审核通过，已同步入知识库。')
}

export function resetSeedReports() {
  _cacheDirty = true
  localStorage.setItem(STORAGE_KEY, JSON.stringify(SEED_REPORTS.map(_normalize)))
  try { window.dispatchEvent(new CustomEvent('equipai-knowledge-changed')) } catch (_) {}
}
