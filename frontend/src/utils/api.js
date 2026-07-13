import { request } from './request'

function _toSearchParams(obj) {
  const out = {}
  if (!obj || typeof obj !== 'object') return out
  for (const k of Object.keys(obj)) {
    const v = obj[k]
    if (v === undefined || v === null || v === '') continue
    out[k] = v
  }
  return out
}

// ======================================================
// 鉴权
// ======================================================
export async function loginApi({ username, password, role }) {
  return request('/api/login', {
    method: 'POST',
    data: { username: username.trim(), password, role }
  })
}

export async function meApi() {
  return request('/api/me', { silent: true })
}

export async function changePasswordApi({ old_password, new_password }) {
  return request('/api/user/password', {
    method: 'POST',
    data: { old_password, new_password }
  })
}

// 当前登录用户修改自己的 profile（个人信息）
export async function updateProfileApi(payload) {
  const body = {
    fullname: payload.fullname ?? null,
    emp_no: payload.empNo ?? null,
    dept: payload.dept ?? null,
    position: payload.position ?? null,
    join_date: payload.joinDate ?? null,
    mobile: payload.mobile ?? null,
    email: payload.email ?? null,
    tel: payload.tel ?? null,
    office: payload.office ?? null,
  }
  return request('/api/me', { method: 'PUT', data: body })
}

// ======================================================
// 仪表盘
// ======================================================
export async function dashboardOverviewApi() {
  return request('/api/dashboard/overview')
}

// ======================================================
// 设备管理
// ======================================================
export async function listDevicesApi({ page = 1, size = 20, keyword, tag, status } = {}) {
  return request('/api/devices', {
    params: _toSearchParams({ page, size, keyword, tag, status })
  })
}

export async function deviceStatsApi() {
  return request('/api/devices/stats')
}

export async function getDeviceApi(id) {
  return request('/api/devices/' + id)
}

export async function createDeviceApi(payload) {
  return request('/api/devices', { method: 'POST', data: payload })
}

export async function updateDeviceApi(id, payload) {
  return request('/api/devices/' + id, { method: 'PUT', data: payload })
}

export async function deleteDeviceApi(id) {
  return request('/api/devices/' + id, { method: 'DELETE' })
}

export async function listDeviceTagsApi() {
  return request('/api/devices/tags')
}

// ======================================================
// 工单管理
// ======================================================
export async function listTicketsApi({
  page = 1, size = 20, keyword,
  status, scope = 'all',
  assignee_id, submitter_id
} = {}) {
  return request('/api/tickets', {
    params: _toSearchParams({ page, size, keyword, status, scope, assignee_id, submitter_id })
  })
}

export async function createTicketApi(payload) {
  return request('/api/tickets', { method: 'POST', data: payload })
}

export async function getTicketApi(id) {
  return request('/api/tickets/' + id)
}

export async function assignTicketApi(id, assignee_id, remark) {
  return request(`/api/tickets/${id}/assign`, {
    method: 'POST',
    data: { assignee_id, remark }
  })
}

export async function acceptTicketApi(id) {
  return request(`/api/tickets/${id}/accept`, { method: 'POST' })
}

export async function completeTicketApi(id, solution) {
  return request(`/api/tickets/${id}/complete`, {
    method: 'POST',
    data: { solution }
  })
}

export async function markTicketOverdueApi(id) {
  return request(`/api/tickets/${id}/mark_overdue`, { method: 'POST' })
}

// ======================================================
// 知识报告
// ======================================================
export async function listReportsApi({
  page = 1, size = 20, keyword,
  status, type, scope = 'all'
} = {}) {
  return request('/api/reports', {
    params: _toSearchParams({ page, size, keyword, status, type, scope })
  })
}

export async function submitReportApi(payload) {
  return request('/api/reports', { method: 'POST', data: payload })
}

export async function getReportApi(id) {
  return request('/api/reports/' + id)
}

export async function reviewReportApi(id, action, review_remark = '') {
  return request(`/api/reports/${id}/review`, {
    method: 'POST',
    data: { action, review_remark }
  })
}

// ======================================================
// 案例库
// ======================================================
export async function listCasesApi({
  page = 1, size = 20, keyword,
  tag, level, source = 'all'
} = {}) {
  return request('/api/cases', {
    params: _toSearchParams({ page, size, keyword, tag, level, source })
  })
}

export async function listCaseTagsApi() {
  return request('/api/cases/tags')
}

export async function getCaseApi(id) {
  return request('/api/cases/' + id)
}

// ======================================================
// 作业指导库
// ======================================================
export async function listGuidesApi({
  page = 1, size = 20, keyword,
  device_type, source = 'all'
} = {}) {
  return request('/api/guides', {
    params: _toSearchParams({ page, size, keyword, device_type, source })
  })
}

export async function listGuideTypesApi() {
  return request('/api/guides/types')
}

export async function getGuideApi(id) {
  return request('/api/guides/' + id)
}

// ======================================================
// 用户管理（仅管理员）
// ======================================================
export async function listUsersApi({
  page = 1, size = 50, keyword, role
} = {}) {
  return request('/api/users', {
    params: _toSearchParams({ page, size, keyword, role })
  })
}

export async function userOptionsApi(role) {
  return request('/api/users/options', {
    params: role ? { role } : null
  })
}

export async function getUserApi(id) {
  return request('/api/users/' + id)
}

export async function createUserApi(payload) {
  return request('/api/users', { method: 'POST', data: payload })
}

export async function updateUserApi(id, payload) {
  return request('/api/users/' + id, { method: 'PUT', data: payload })
}

export async function resetUserPasswordApi(id) {
  return request(`/api/users/${id}/reset_password`, { method: 'POST' })
}

export async function deleteUserApi(id) {
  return request('/api/users/' + id, { method: 'DELETE' })
}
