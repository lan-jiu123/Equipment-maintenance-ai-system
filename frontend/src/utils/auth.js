const TOKEN_KEY = 'equipai_token'
const USER_KEY = 'equipai_user'
const AVATAR_KEY = 'equipai_avatar'

const svg1 = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'>
<defs>
  <radialGradient id='bg1' cx='50%' cy='30%' r='75%'>
    <stop offset='0%' stop-color='#4fd6ff'/><stop offset='100%' stop-color='#0c3a66'/>
  </radialGradient>
  <linearGradient id='helmet' x1='0' x2='0' y1='0' y2='1'>
    <stop offset='0%' stop-color='#ffcc33'/><stop offset='100%' stop-color='#e08a00'/>
  </linearGradient>
</defs>
<rect width='200' height='200' rx='100' fill='url(#bg1)'/>
<circle cx='100' cy='145' r='50' fill='#1c2b4a' opacity='0.4'/>
<path d='M45 100 Q100 40 155 100 L150 108 Q100 58 50 108 Z' fill='url(#helmet)' stroke='#7a4e00' stroke-width='2'/>
<rect x='58' y='98' width='84' height='10' rx='5' fill='#2ecc71'/>
<circle cx='100' cy='80' r='24' fill='#ffd7a8' stroke='#d19a5c' stroke-width='1.5'/>
<circle cx='90' cy='78' r='4' fill='#1b2a49'/>
<circle cx='110' cy='78' r='4' fill='#1b2a49'/>
<circle cx='91' cy='77' r='1.2' fill='#fff'/>
<circle cx='111' cy='77' r='1.2' fill='#fff'/>
<path d='M88 89 Q100 97 112 89' stroke='#8b2c2c' stroke-width='2.5' fill='none' stroke-linecap='round'/>
<path d='M82 68 Q86 66 90 68' stroke='#c17a4a' stroke-width='1.5' fill='none'/>
<path d='M110 68 Q114 66 118 68' stroke='#c17a4a' stroke-width='1.5' fill='none'/>
<circle cx='82' cy='84' r='3.5' fill='#ff9fa6' opacity='0.7'/>
<circle cx='118' cy='84' r='3.5' fill='#ff9fa6' opacity='0.7'/>
<path d='M100 25 L102 35 L112 37 L104 41 L106 51 L100 45 L94 51 L96 41 L88 37 L98 35 Z' fill='#fff7cc' opacity='0.9'/>
</svg>`

const svg2 = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'>
<defs>
  <radialGradient id='bg2' cx='50%' cy='40%' r='75%'>
    <stop offset='0%' stop-color='#6e8cff'/><stop offset='100%' stop-color='#0b1440'/>
  </radialGradient>
  <linearGradient id='body' x1='0' x2='0' y1='0' y2='1'>
    <stop offset='0%' stop-color='#e9f2ff'/><stop offset='100%' stop-color='#7f9fe0'/>
  </linearGradient>
</defs>
<rect width='200' height='200' rx='100' fill='url(#bg2)'/>
<path d='M100 18 L104 28 L114 30 L106 34 L108 44 L100 38 L92 44 L94 34 L86 30 L96 28 Z' fill='#00d4ff'/>
<line x1='100' y1='18' x2='100' y2='28' stroke='#00d4ff' stroke-width='2'/>
<rect x='50' y='50' width='100' height='82' rx='24' fill='url(#body)' stroke='#3b5fae' stroke-width='3'/>
<rect x='62' y='66' width='76' height='36' rx='12' fill='#0a1530' stroke='#00d4ff' stroke-width='2'/>
<circle cx='82' cy='84' r='9' fill='#00ff88'>
  <animate attributeName='r' values='8;10;8' dur='1.4s' repeatCount='indefinite'/>
</circle>
<circle cx='118' cy='84' r='9' fill='#00ff88'>
  <animate attributeName='r' values='8;10;8' dur='1.4s' begin='0.2s' repeatCount='indefinite'/>
</circle>
<circle cx='82' cy='84' r='3' fill='#0a1530'/>
<circle cx='118' cy='84' r='3' fill='#0a1530'/>
<rect x='80' y='110' width='40' height='6' rx='3' fill='#0a1530'/>
<rect x='86' y='111' width='3' height='4' fill='#00d4ff'/>
<rect x='92' y='111' width='3' height='4' fill='#00ff88'/>
<rect x='98' y='111' width='3' height='4' fill='#ffcc33'/>
<rect x='104' y='111' width='3' height='4' fill='#ff6b35'/>
<rect x='110' y='111' width='3' height='4' fill='#ff4757'/>
<rect x='70' y='140' width='60' height='18' rx='9' fill='#3b5fae' stroke='#00d4ff' stroke-width='2'/>
<circle cx='82' cy='149' r='3' fill='#00ff88'/>
<circle cx='100' cy='149' r='3' fill='#00d4ff'/>
<circle cx='118' cy='149' r='3' fill='#ffcc33'/>
<path d='M36 100 Q50 94 52 112' stroke='#3b5fae' stroke-width='8' fill='none' stroke-linecap='round'/>
<path d='M164 100 Q150 94 148 112' stroke='#3b5fae' stroke-width='8' fill='none' stroke-linecap='round'/>
<circle cx='36' cy='100' r='10' fill='#7f9fe0' stroke='#3b5fae' stroke-width='2'/>
<circle cx='164' cy='100' r='10' fill='#7f9fe0' stroke='#3b5fae' stroke-width='2'/>
</svg>`

const svg3 = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'>
<defs>
  <radialGradient id='bg3' cx='50%' cy='30%' r='75%'>
    <stop offset='0%' stop-color='#ff9ac4'/><stop offset='100%' stop-color='#4a1650'/>
  </radialGradient>
  <linearGradient id='hair' x1='0' x2='0' y1='0' y2='1'>
    <stop offset='0%' stop-color='#2c1a12'/><stop offset='100%' stop-color='#0a0604'/>
  </linearGradient>
</defs>
<rect width='200' height='200' rx='100' fill='url(#bg3)'/>
<circle cx='100' cy='155' r='48' fill='#1e0c28' opacity='0.5'/>
<path d='M68 80 Q60 50 100 46 Q140 50 132 80 L138 115 Q100 122 62 115 Z' fill='url(#hair)'/>
<path d='M132 78 Q152 82 154 108 Q150 118 138 115' fill='url(#hair)'/>
<path d='M68 78 Q48 82 46 108 Q50 118 62 115' fill='url(#hair)'/>
<path d='M100 52 Q112 40 126 44 Q126 34 118 30 Q108 38 100 52' fill='#2c1a12'/>
<circle cx='100' cy='85' r='28' fill='#ffe0c8' stroke='#d3996a' stroke-width='1.5'/>
<path d='M100 62 Q94 58 88 62 Q92 54 100 55 Q108 54 112 62 Q106 58 100 62 Z' fill='#2c1a12' opacity='0.85'/>
<path d='M86 78 Q90 82 94 78' stroke='#2c1a12' stroke-width='2' fill='none' stroke-linecap='round'/>
<path d='M106 78 Q110 82 114 78' stroke='#2c1a12' stroke-width='2' fill='none' stroke-linecap='round'/>
<circle cx='90' cy='88' r='4.2' fill='#3e2314'/>
<circle cx='110' cy='88' r='4.2' fill='#3e2314'/>
<circle cx='91' cy='86.5' r='1.3' fill='#fff'/>
<circle cx='111' cy='86.5' r='1.3' fill='#fff'/>
<circle cx='82' cy='95' r='4' fill='#ff9ab5' opacity='0.65'/>
<circle cx='118' cy='95' r='4' fill='#ff9ab5' opacity='0.65'/>
<path d='M94 100 Q100 103 106 100 L105 105 Q100 108 95 105 Z' fill='#d7424c' stroke='#8b2428' stroke-width='0.8'/>
<path d='M96 101 L104 101' stroke='#fff' stroke-width='0.8'/>
<path d='M60 148 Q100 118 140 148 L140 170 L60 170 Z' fill='#2b6cb0'/>
<path d='M60 148 Q100 118 140 148 L140 152 Q100 126 60 152 Z' fill='#4fa3e8'/>
<circle cx='100' cy='156' r='4' fill='#ffd966' stroke='#c89b2a' stroke-width='1'/>
<circle cx='160' cy='52' r='2' fill='#fff' opacity='0.7'/>
<circle cx='40' cy='62' r='1.5' fill='#fff' opacity='0.7'/>
<circle cx='150' cy='80' r='1' fill='#fff' opacity='0.8'/>
</svg>`

function svgToDataUri(svg) {
  return 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(svg)
}

export const AVATAR_PRESETS = [
  { id: 'preset:0', name: '', src: svgToDataUri(svg1) },
  { id: 'preset:1', name: '', src: svgToDataUri(svg2) },
  { id: 'preset:2', name: '', src: svgToDataUri(svg3) }
]

export function resolveAvatarSrc(value) {
  if (!value) return ''
  if (value.startsWith('preset:')) {
    const p = AVATAR_PRESETS.find(x => x.id === value)
    return p ? p.src : ''
  }
  return value
}

export function getAvatar() {
  return localStorage.getItem(AVATAR_KEY) || ''
}

export function setAvatar(value) {
  localStorage.setItem(AVATAR_KEY, value || '')
  try {
    window.dispatchEvent(new CustomEvent('equipai-avatar-changed', { detail: { value: value || '' } }))
  } catch (_) {}
}

export function removeAvatar() {
  localStorage.removeItem(AVATAR_KEY)
  try {
    window.dispatchEvent(new CustomEvent('equipai-avatar-changed', { detail: { value: '' } }))
  } catch (_) {}
}

export function getToken() {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token)
}

export function removeToken() {
  localStorage.removeItem(TOKEN_KEY)
}

export function getUser() {
  const raw = localStorage.getItem(USER_KEY)
  try {
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function setUser(user) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function removeUser() {
  localStorage.removeItem(USER_KEY)
}

export function isLoggedIn() {
  return !!getToken()
}

export function logout() {
  removeToken()
  removeUser()
  removeAvatar()
}
