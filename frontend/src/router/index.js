import { createRouter, createWebHistory } from 'vue-router'
import { isLoggedIn, getUser } from '../utils/auth'

import Home from '../views/Home.vue'
import Search from '../views/Search.vue'
import Guide from '../views/Guide.vue'
import Case from '../views/Case.vue'
import KnowledgeGraph from '../views/KnowledgeGraph.vue'
import Login from '../views/Login.vue'
import Profile from '../views/Profile.vue'
import Password from '../views/Password.vue'
import Logs from '../views/Logs.vue'
import AdminDashboard from '../views/AdminDashboard.vue'
import WorkerDashboard from '../views/WorkerDashboard.vue'
import Tickets from '../views/Tickets.vue'
import DeviceMgmt from '../views/DeviceMgmt.vue'
import UserMgmt from '../views/UserMgmt.vue'

export const ROLE_HOME = {
  sysadmin: '/home',
  manager: '/home',
  worker: '/desk'
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
  { path: '/home', component: Home, meta: { roles: ['sysadmin', 'manager'], label: '仪表盘' } },
  { path: '/admin', component: AdminDashboard, meta: { roles: ['sysadmin', 'manager'], label: '维修管理' } },
  { path: '/devices', component: DeviceMgmt, meta: { roles: ['sysadmin', 'manager'], label: '设备管理' } },
  { path: '/users', component: UserMgmt, meta: { roles: ['sysadmin', 'manager'], label: '用户管理' } },
  { path: '/desk', component: WorkerDashboard, meta: { roles: ['worker', 'manager'], label: '工作台' } },
  { path: '/tickets', component: Tickets, meta: { roles: ['worker', 'manager'], label: '我的工单' } },
  { path: '/worker', redirect: '/desk' },
  { path: '/search', component: Search, meta: { roles: ['sysadmin', 'manager', 'worker'], label: '智能检索' } },
  { path: '/guide', component: Guide, meta: { roles: ['sysadmin', 'manager', 'worker'], label: '作业指导' } },
  { path: '/case', component: Case, meta: { roles: ['sysadmin', 'manager', 'worker'], label: '案例库' } },
  { path: '/graph', component: KnowledgeGraph, meta: { roles: ['sysadmin', 'manager', 'worker'], label: '知识图谱' } },
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
