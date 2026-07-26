<template>
  <div class="container notification-center">
    <div class="page-head">
      <div>
        <h1>消息中心</h1>
        <p>查看系统发送给您的全部通知</p>
      </div>
      <button v-if="unreadCount" class="btn btn-outline" @click="markAllRead">全部标为已读</button>
    </div>

    <section class="card notification-card">
      <div class="list-head">
        <span>全部消息</span>
        <span class="count">{{ items.length }} 条<span v-if="unreadCount"> · {{ unreadCount }} 条未读</span></span>
      </div>
      <div v-if="loading" class="state">正在加载消息…</div>
      <div v-else-if="!items.length" class="state empty">
        <span>📭</span>
        <b>暂无消息</b>
      </div>
      <div v-else class="message-list">
        <article
          v-for="item in items"
          :key="item.id"
          class="message-item"
          :class="{ unread: !item.is_read, expanded: expandedId === item.id }"
          @click="open(item)"
        >
          <div class="message-icon">{{ icon(item.type) }}</div>
          <div class="message-main">
            <div class="message-title-row">
              <b>{{ item.title }}</b>
              <time>{{ formatTime(item.created_at_ts) }}</time>
            </div>
            <p>{{ item.content }}</p>
            <div v-if="expandedId === item.id" class="message-detail">
              {{ item.content }}
            </div>
          </div>
          <span v-if="!item.is_read" class="unread-dot"></span>
          <button class="delete-btn" title="删除消息" @click.stop="remove(item)">✕</button>
        </article>
      </div>
    </section>
  </div>
</template>

<script>
import { request, toast } from '../utils/request'

export default {
  name: 'Notifications',
  data() {
    return {
      items: [],
      unreadCount: 0,
      loading: false,
      expandedId: null
    }
  },
  created() {
    this.load()
  },
  methods: {
    async load() {
      this.loading = true
      try {
        const data = await request('/notifications', {
          params: { page: 1, size: 200, unread_only: 0 }
        })
        this.items = ((data && data.items) || []).map(item => ({
          ...item,
          is_read: !!item.is_read
        }))
        this.unreadCount = Number(data && data.unread_count) || 0
      } finally {
        this.loading = false
      }
    },
    async open(item) {
      this.expandedId = this.expandedId === item.id ? null : item.id
      if (item.is_read) return
      try {
        await request('/notifications/read', {
          method: 'POST',
          data: { ids: [item.id] },
          silent: true
        })
        item.is_read = true
        this.unreadCount = Math.max(0, this.unreadCount - 1)
      } catch (_) {}
    },
    async markAllRead() {
      await request('/notifications/read', { method: 'POST', data: { all: true } })
      this.items.forEach(item => { item.is_read = true })
      this.unreadCount = 0
      toast('已全部标为已读', 'success')
    },
    async remove(item) {
      await request('/notifications', {
        method: 'DELETE',
        data: { ids: [item.id] }
      })
      if (!item.is_read) this.unreadCount = Math.max(0, this.unreadCount - 1)
      this.items = this.items.filter(row => row.id !== item.id)
      if (this.expandedId === item.id) this.expandedId = null
    },
    icon(type) {
      if (type === 'report_approved') return '✅'
      if (type === 'report_rejected') return '❌'
      if (type === 'report_synced') return '📚'
      if (type === 'report_submitted') return '📨'
      if (type === 'ticket_assigned' || type === 'ticket_created') return '🎫'
      if (type === 'device_fault') return '⚠️'
      return '🔔'
    },
    formatTime(ts) {
      if (!ts) return ''
      return new Date(Number(ts) * 1000).toLocaleString('zh-CN', { hour12: false })
    }
  }
}
</script>

<style scoped>
.notification-center { max-width: 1080px; padding-top: 4px; }
.page-head {
  display: flex; align-items: flex-end; justify-content: space-between;
  gap: 20px; margin-bottom: 22px;
}
.page-head h1 { margin: 0 0 6px; font-size: 1.65rem; }
.page-head p { margin: 0; color: var(--text-muted); font-size: .875rem; }
.notification-card { padding: 0; }
.list-head {
  display: flex; justify-content: space-between; align-items: center;
  padding: 18px 22px; border-bottom: 1px solid var(--border-subtle);
  font-weight: 600;
}
.count { color: var(--text-muted); font-size: .8rem; font-weight: 400; }
.state {
  min-height: 240px; display: flex; align-items: center; justify-content: center;
  color: var(--text-muted);
}
.state.empty { flex-direction: column; gap: 10px; }
.state.empty span { font-size: 2.5rem; }
.message-list { display: flex; flex-direction: column; }
.message-item {
  position: relative; display: flex; gap: 14px; padding: 18px 22px;
  border-bottom: 1px solid var(--border-subtle); cursor: pointer;
  transition: background .18s ease;
}
.message-item:last-child { border-bottom: 0; }
.message-item:hover, .message-item.expanded { background: rgba(59,130,246,.055); }
.message-item.unread { background: rgba(37,99,235,.075); }
.message-icon {
  width: 40px; height: 40px; flex: 0 0 40px; display: grid; place-items: center;
  border-radius: 10px; background: rgba(59,130,246,.12); font-size: 1.15rem;
}
.message-main { flex: 1; min-width: 0; }
.message-title-row { display: flex; justify-content: space-between; gap: 18px; }
.message-title-row b { color: var(--text-primary); font-size: .925rem; }
.message-title-row time { color: var(--text-muted); font-size: .75rem; white-space: nowrap; }
.message-main p {
  margin: 7px 0 0; color: var(--text-secondary); font-size: .825rem;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.message-detail {
  margin-top: 13px; padding: 12px 14px; border: 1px solid var(--border-subtle);
  border-radius: var(--radius); background: rgba(255,255,255,.025);
  color: var(--text-secondary); font-size: .85rem; line-height: 1.7;
  white-space: pre-wrap;
}
.unread-dot {
  position: absolute; left: 8px; top: 25px; width: 7px; height: 7px;
  border-radius: 50%; background: var(--primary); box-shadow: 0 0 8px var(--primary);
}
.delete-btn {
  align-self: center; width: 30px; height: 30px; border-radius: 8px;
  border: 1px solid transparent; background: transparent; color: var(--text-muted);
  cursor: pointer;
}
.delete-btn:hover {
  color: var(--accent-red); border-color: rgba(239,68,68,.35);
  background: rgba(239,68,68,.08);
}
@media (max-width: 640px) {
  .page-head { align-items: flex-start; }
  .message-title-row { flex-direction: column; gap: 4px; }
  .message-main p { white-space: normal; }
}
</style>
