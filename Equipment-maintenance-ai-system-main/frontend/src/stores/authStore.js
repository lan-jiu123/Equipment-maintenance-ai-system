import { reactive, readonly } from 'vue'

const TOKEN_KEY = 'equipai_token'
const USER_KEY = 'equipai_user'
const AVATAR_KEY = 'equipai_avatar'

function _normalizeFullname(user) {
  if (!user || typeof user !== 'object') return user
  if (!user.fullname) {
    user.fullname = user.username || '用户'
  }
  if (!user.role_label && user.role) {
    const rl = {
      sysadmin: '维修管理员',
      manager: '维修管理员',
      worker: '维修工'
    }[user.role]
    if (rl) user.role_label = rl
  }
  return user
}

const state = reactive({
  token: null,
  user: null,
  avatar: '',
  _hydrated: false,
  _version: 0
})

function _persist() {
  try {
    if (state.token) localStorage.setItem(TOKEN_KEY, state.token)
    else localStorage.removeItem(TOKEN_KEY)
    if (state.user) localStorage.setItem(USER_KEY, JSON.stringify(state.user))
    else localStorage.removeItem(USER_KEY)
    if (state.avatar) localStorage.setItem(AVATAR_KEY, state.avatar)
    else localStorage.removeItem(AVATAR_KEY)
  } catch (_) {}
  state._version++
}

export function hydrateAuth() {
  if (state._hydrated) return
  try {
    state.token = localStorage.getItem(TOKEN_KEY) || null
    const raw = localStorage.getItem(USER_KEY)
    if (raw) {
      try {
        state.user = _normalizeFullname(JSON.parse(raw))
      } catch { state.user = null }
    } else {
      state.user = null
    }
    state.avatar = localStorage.getItem(AVATAR_KEY) || ''
  } catch (_) {}
  state._hydrated = true
}

export function getToken() {
  if (!state._hydrated) hydrateAuth()
  return state.token
}

export function getUser() {
  if (!state._hydrated) hydrateAuth()
  return state.user
}

export function getAvatar() {
  if (!state._hydrated) hydrateAuth()
  return state.avatar
}

export function isLoggedIn() {
  if (!state._hydrated) hydrateAuth()
  return !!state.token
}

export function setToken(token) {
  state.token = token || null
  _persist()
}

export function setUser(user) {
  state.user = _normalizeFullname(user) || null
  _persist()
}

export function setAvatar(value) {
  state.avatar = value || ''
  _persist()
  try {
    window.dispatchEvent(new CustomEvent('equipai-avatar-changed', { detail: { value: state.avatar } }))
  } catch (_) {}
}

export function refreshUserFromMe(mePayload) {
  if (!mePayload) return
  const u = state.user ? { ...state.user } : {}
  for (const k of [
    'id', 'username', 'fullname', 'role', 'role_label',
    'avatar', 'avatar_preset',
    'email', 'mobile', 'tel', 'office',
    'dept', 'position', 'emp_no',
    'join_date', 'join_date_ts',
    'ticket_stats', 'created_at', 'status',
  ]) {
    if (mePayload[k] !== undefined && mePayload[k] !== null) u[k] = mePayload[k]
  }
  setUser(u)
}

export function login(user, token, avatar) {
  state.token = token || null
  state.user = _normalizeFullname(user) || null
  if (avatar !== undefined) state.avatar = avatar || ''
  _persist()
}

export function logout() {
  state.token = null
  state.user = null
  state.avatar = ''
  _persist()
}

export const authState = readonly(state)

hydrateAuth()
