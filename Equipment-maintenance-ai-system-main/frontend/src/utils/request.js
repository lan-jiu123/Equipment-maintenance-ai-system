import { getToken, logout } from './auth'
import router from '../router'

const BASE_PREFIX = '/api'

function _message(text, level = 'error') {
  try {
    const ev = new CustomEvent('equipai-toast', {
      detail: { text, level }
    })
    window.dispatchEvent(ev)
  } catch (_) {}
  if (level === 'error') {
    console.error('[equipai]', text)
  } else {
    console.log('[equipai]', text)
  }
}

function _qs(params) {
  if (!params) return ''
  const parts = []
  for (const k of Object.keys(params)) {
    const v = params[k]
    if (v === undefined || v === null || v === '') continue
    parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v))
  }
  return parts.length ? '?' + parts.join('&') : ''
}

export async function request(path, options = {}) {
  const {
    method = 'GET',
    params = null,
    data = null,
    headers = {},
    silent = false,
    raw = false,
    timeoutMs = 30000
  } = options

  let url = path
  if (path.startsWith('/') && !path.startsWith('/api') && !path.startsWith('http')) {
    url = BASE_PREFIX + path
  }
  url += _qs(params)

  const hdrs = {
    Accept: 'application/json',
    ...headers
  }
  const token = getToken()
  if (token) {
    hdrs.Authorization = 'Bearer ' + token
  }
  if (data !== null && data !== undefined &&
      !(data instanceof FormData) &&
      !(data instanceof Blob) &&
      typeof data !== 'string') {
    hdrs['Content-Type'] = 'application/json'
  }

  const ctrl = new AbortController()
  const timer = setTimeout(() => ctrl.abort(), timeoutMs)

  let resp
  try {
    resp = await fetch(url, {
      method,
      headers: hdrs,
      body: data === null || data === undefined
        ? undefined
        : (data instanceof FormData || data instanceof Blob || typeof data === 'string'
            ? data
            : JSON.stringify(data)),
      credentials: 'same-origin',
      signal: ctrl.signal
    })
  } catch (e) {
    clearTimeout(timer)
    if (e && e.name === 'AbortError') {
      if (!silent) _message('请求超时，请检查后端是否启动')
      const err = new Error('请求超时')
      err.code = 'TIMEOUT'
      throw err
    }
    if (!silent) _message('网络连接失败，请检查后端服务是否启动')
    const err = new Error('网络连接失败')
    err.code = 'NETWORK_ERROR'
    throw err
  }
  clearTimeout(timer)

  if (resp.status === 401) {
    if (!silent) _message('登录已失效，请重新登录', 'warn')
    logout()
    const cur = window.location.hash || window.location.pathname + window.location.search
    router.replace({
      path: '/login',
      query: { redirect: cur !== '/login' && cur !== '' ? cur : undefined }
    })
    const err = new Error('未登录或登录已失效')
    err.code = 401
    throw err
  }

  if (raw) {
    if (!resp.ok && !silent) {
      _message('HTTP ' + resp.status + ' 错误')
    }
    return resp
  }

  let payload
  try {
    const txt = await resp.text()
    payload = txt ? JSON.parse(txt) : null
  } catch (e) {
    if (!silent) _message('响应格式错误（非 JSON）')
    const err = new Error('响应格式错误')
    err.code = resp.status || 'BAD_JSON'
    throw err
  }

  if (!payload || typeof payload !== 'object') {
    if (!silent) _message('响应结构错误')
    const err = new Error('响应结构错误')
    err.code = resp.status || 'BAD_RESP'
    throw err
  }

  const code = typeof payload.code === 'number' ? payload.code : (resp.ok ? 200 : resp.status)
  const msg = payload.msg || payload.message || (resp.ok ? '' : ('HTTP ' + resp.status))

  if (code === 401) {
    if (!silent) _message(msg || '登录已失效，请重新登录', 'warn')
    logout()
    router.replace({ path: '/login' })
    const err = new Error(msg || '未登录')
    err.code = 401
    throw err
  }

  if (code === 200 || code === 0 || code === '0') {
    return payload.data === undefined ? null : payload.data
  }

  if (!silent) _message(msg || ('操作失败，错误码 ' + code))
  const err = new Error(msg || ('错误码 ' + code))
  err.code = code
  err.payload = payload
  throw err
}

export function toast(msg, level = 'info') {
  _message(msg, level)
}
