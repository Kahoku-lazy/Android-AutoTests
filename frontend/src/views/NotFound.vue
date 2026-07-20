<template>
  <div class="not-found">
    <div class="not-found__card">
      <div class="not-found__code">404</div>
      <h1 class="not-found__title">页面未找到</h1>
      <p class="not-found__desc">您访问的页面不存在或已被移除</p>
      <div class="not-found__actions">
        <el-button type="primary" @click="goHome">返回首页</el-button>
        <el-button @click="goBack">返回上一页</el-button>
      </div>
    </div>
    <div class="ac-footer" type="tree" />
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function goHome() {
  router.push('/dashboard')
}

function goBack() {
  if (window.history.length > 1) {
    router.back()
  } else {
    router.push('/dashboard')
  }
}
</script>

<style scoped>
.not-found {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 60px);
  padding: 40px 20px;
}

.not-found__card {
  text-align: center;
  padding: 60px 40px;
  background: var(--animal-bg-color, #fffbf5);
  border: 2px solid rgba(139, 115, 85, 0.12);
  border-radius: var(--animal-border-radius-lg, 24px);
  max-width: 480px;
  width: 100%;
}

.not-found__code {
  font-family: var(--font-display, 'Nunito', sans-serif);
  font-size: 96px;
  font-weight: 800;
  color: var(--app-yellow, #f7cd67);
  line-height: 1;
  margin-bottom: 16px;
}

.not-found__title {
  font-size: 22px;
  font-weight: 700;
  color: var(--animal-text-color, #4a3a28);
  margin: 0 0 8px;
}

.not-found__desc {
  font-size: 14px;
  color: var(--app-text-secondary, #988b7a);
  margin: 0 0 32px;
}

.not-found__actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
