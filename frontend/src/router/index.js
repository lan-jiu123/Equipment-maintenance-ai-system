import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, getUser } from '../utils/auth'

import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Guide from '../views/Guide.vue'
import Case from '../views/Case.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import Password from '../views/Password.vue'
import Logs from '../views/Logs.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import WorkerDashboard from '../views/WorkerDashboard.vue'

export const ROLE_HOME = {
  sysadmin: '/home',
  manager: '/admin',
  worker: '/worker'
}

export function getRoleHome(role) {
  return ROLE_HOME[role] || '/home'
}

const routes = [
  { path: '/login', component: Login, meta: { public: true } },
  { path: '/', redirect: () => {
    const u = getUser()
    return getRoleHome(u && u.role)
  }},
  { path: '/home', component: Home, meta: { roles: ['sysadmin', 'manager'] } },
  { path: '/admin', component: AdminDashboard, meta: { roles: ['sysadmin', 'manager'] } },
  { path: '/worker', component: WorkerDashboard, meta: { roles: ['worker', 'manager'] } },
  { path: '/search', component: Search, meta: { roles: ['sysadmin', 'manager', 'worker'] } },
  { path: '/guide', component: Guide, meta: { roles: ['sysadmin', 'manager', 'worker'] } },
  { path: '/case', component: Case, meta: { roles: ['sysadmin', 'manager', 'worker'] } },
  { path: '/profile', component: Profile, meta: { roles: ['sysadmin', 'manager', 'worker'] } },
  { path: '/password', component: Password, meta: { roles: ['sysadmin', 'manager', 'worker'] } },
  { path: '/logs', component: Logs, meta: { roles: ['sysadmin', 'manager'] } }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach((to, _from, next) => {
  if (to.meta.public) {
    next()
  } else if (isLoggedIn()) {
    const u = getUser()
    const role = u && u.role
    const allowed = to.meta.roles
    if (allowed && role && !allowed.includes(role)) {
      next({ path: getRoleHome(role), replace: true })
    } else {
      next()
    }
  } else {
    next({ path: '/login', query: { redirect: to.fullPath } })
  }
})

export default router
