<script setup>
import { ref, onMounted } from 'vue'
import { animate } from 'animejs'
import { Card } from 'animal-island-vue'
import client from '@/shared/api-client.js'

const greetRef = ref(null)
const username = ref('')
const now = new Date()
const hour = now.getHours()
const greeting = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
const dateStr = now.toLocaleDateString('zh-CN', {
  year: 'numeric', month: 'long', day: 'numeric', weekday: 'long',
})

onMounted(async () => {
  try {
    const { data } = await client.get('/ai/auth/me')
    if (data.ok && data.user) username.value = data.user.username
  } catch {}
  if (greetRef.value) {
    animate(greetRef.value, {
      opacity: [0, 1],
      translateY: [12, 0],
      duration: 700,
      ease: 'outCubic',
    })
  }
})
</script>

<template>
  <Card color="warm-peach-pink" pattern="warm-peach-pink" class="welcome-banner">
    <div ref="greetRef" class="welcome-banner__inner">
      <div class="welcome-banner__text">
        <h1 class="welcome-banner__greeting">{{ greeting }}, {{ username || 'User' }}</h1>
        <p class="welcome-banner__date">{{ dateStr }}</p>
        <p class="welcome-banner__desc">
          自动化测试平台 · Android / iOS 跨端 UI 测试框架
        </p>
      </div>
      <div class="welcome-banner__visual">
        <svg viewBox="0 0 120 120" class="welcome-banner__shapes">
          <circle cx="60" cy="60" r="45" fill="none" stroke="var(--accent-pink)" stroke-width="1.2" opacity="0.25">
            <animateTransform attributeName="transform" type="rotate" from="0 60 60" to="360 60 60" dur="20s" repeatCount="indefinite" />
          </circle>
          <circle cx="60" cy="60" r="28" fill="none" stroke="var(--animal-primary-color)" stroke-width="1.8" opacity="0.35">
            <animateTransform attributeName="transform" type="rotate" from="360 60 60" to="0 60 60" dur="15s" repeatCount="indefinite" />
          </circle>
          <circle cx="60" cy="60" r="14" fill="var(--animal-success-color)" opacity="0.2">
            <animate attributeName="r" values="12;18;12" dur="3s" repeatCount="indefinite" />
          </circle>
        </svg>
      </div>
    </div>
  </Card>
</template>

<style scoped>
.welcome-banner {
  overflow: hidden;
}

.welcome-banner :deep(.animal-card-body) {
  padding: 0;
}

.welcome-banner__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28px 32px;
  gap: 24px;
}

@media (max-width: 600px) {
  .welcome-banner__inner { flex-direction: column; align-items: flex-start; padding: 20px 24px; }
}

.welcome-banner__text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.welcome-banner__greeting {
  font-family: var(--font-display, Nunito, sans-serif);
  font-size: 28px;
  font-weight: 800;
  color: var(--animal-text-color, #794f27);
  margin: 0;
  line-height: 1.2;
}

.welcome-banner__date {
  font-size: 14px;
  color: var(--animal-text-color-secondary, #9f927d);
  margin: 0;
}

.welcome-banner__desc {
  font-size: 13px;
  color: var(--animal-text-color-secondary, #9f927d);
  margin: 6px 0 0;
  opacity: 0.7;
}

.welcome-banner__visual {
  flex-shrink: 0;
}

.welcome-banner__shapes {
  width: 100px;
  height: 100px;
}
</style>
