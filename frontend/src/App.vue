<template>
  <div class="app-wrapper">
    <TopNav v-if="showNav" />
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<script>
import TopNav from './layout/TopNav.vue'

export default {
  name: 'App',
  components: { TopNav },
  computed: {
    showNav() {
      return this.$route.path !== '/login'
    }
  }
}
</script>

<style scoped>
.app-wrapper {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.main-content {
  flex: 1;
  padding: 32px 0 64px;
}
</style>
