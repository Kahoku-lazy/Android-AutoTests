<script setup>
/**
 * 平台数字人 — 占位页面（待开发）
 */
import { ref, onMounted } from 'vue'

const dots = ref('')
const messages = [
  '数字人 功能开发中，请耐心等待。。。',
  '我们的工程师正在努力构建中。。。',
  '即将为您带来全新的智能交互体验。。。',
]
const currentMsg = ref(0)

onMounted(() => {
  // Animated dots
  let count = 0
  setInterval(() => {
    count = (count + 1) % 4
    dots.value = '.'.repeat(count)
  }, 500)

  // Rotating messages
  setInterval(() => {
    currentMsg.value = (currentMsg.value + 1) % messages.length
  }, 3000)
})
</script>

<template>
  <div class="digital-human-page">
    <!-- Flowing light streams -->
    <div class="streams">
      <div v-for="i in 12" :key="'s'+i" class="stream" :style="{
        left: `${(i-1) * 8 + Math.random() * 4}%`,
        animationDelay: `${Math.random() * 8}s`,
        animationDuration: `${5 + Math.random() * 8}s`,
        width: `${1 + Math.random() * 2.5}px`,
      }" />
    </div>

    <!-- Background particles -->
    <div class="bg-particles">
      <div v-for="i in 20" :key="i" class="particle" :style="{
        left: `${Math.random() * 100}%`,
        animationDelay: `${Math.random() * 8}s`,
        animationDuration: `${6 + Math.random() * 6}s`,
        width: `${4 + Math.random() * 8}px`,
        height: `${4 + Math.random() * 8}px`,
      }" />
    </div>

    <div class="content-center">
      <!-- 火柴人 —— 西部世界维鲁特鲁威姿态（人+圈同转） -->
      <div class="arena">
        <div class="shadow" />
        <svg class="stickman" viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
          <!-- 圆圈 + 火柴人同一组，整体旋转 -->
          <g class="vitruvian">
            <circle cx="100" cy="100" r="88" class="orbit-ring orbit-1" />
            <circle cx="100" cy="100" r="88" class="orbit-ring orbit-2" />
            <circle cx="100" cy="100" r="88" class="orbit-ring orbit-3" />
            <!-- 头：圆顶内侧 -->
            <circle class="head" cx="100" cy="28" r="13" />
            <!-- 脊柱：颈 → 髋（圆心附近） -->
            <line class="spine" x1="100" y1="41" x2="100" y2="105" />
            <!-- 臂：近水平，指尖贴圆（约 9 / 3 点） -->
            <line class="arm arm-left" x1="100" y1="68" x2="14" y2="78" />
            <line class="arm arm-right" x1="100" y1="68" x2="186" y2="78" />
            <!-- 腿：外展贴圆（约 7 / 5 点） -->
            <line class="leg leg-left" x1="100" y1="105" x2="48" y2="178" />
            <line class="leg leg-right" x1="100" y1="105" x2="152" y2="178" />
          </g>
        </svg>
        <div class="base-glow" />
      </div>

      <!-- Title -->
      <h1 class="title">
        平台数字人
        <span class="badge-pending">待开发</span>
      </h1>

      <!-- Animated message -->
      <div class="message-box">
        <p class="message">
          {{ messages[currentMsg] }}<span class="cursor">|</span>
        </p>
        <p class="sub-message">
          感谢您的关注{{ dots }}
        </p>
      </div>

      <!-- Progress indicator -->
      <div class="progress-bar">
        <div class="progress-track">
          <div class="progress-fill" />
        </div>
        <span class="progress-label">Coming Soon</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.digital-human-page {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: #0a0a14;
  overflow: hidden;
}

/* ── Rainbow flowing background ── */
.digital-human-page::before {
  content: '';
  position: absolute;
  inset: -50%;
  width: 200%;
  height: 200%;
  background: conic-gradient(
    from 0deg at 50% 50%,
    transparent 0deg,
    rgba(136, 157, 240, 0.06) 30deg,
    rgba(179, 158, 243, 0.06) 60deg,
    transparent 90deg,
    rgba(25, 200, 185, 0.05) 120deg,
    transparent 150deg,
    rgba(248, 166, 178, 0.06) 180deg,
    transparent 210deg,
    rgba(247, 205, 103, 0.05) 240deg,
    rgba(111, 186, 44, 0.05) 270deg,
    transparent 300deg,
    rgba(136, 157, 240, 0.06) 330deg,
    transparent 360deg
  );
  background-size: 200% 100%;
  animation: rainbowFlow 8s linear infinite;
  z-index: 0;
}
@keyframes rainbowFlow {
  0% { transform: translateX(-50%) rotate(0deg); }
  100% { transform: translateX(50%) rotate(360deg); }
}

/* ── Water ripple overlay ── */
.digital-human-page::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 80px,
      rgba(136, 157, 240, 0.03) 80px,
      rgba(136, 157, 240, 0.06) 82px,
      transparent 82px,
      transparent 160px
    ),
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 200px,
      rgba(179, 158, 243, 0.04) 200px,
      rgba(179, 158, 243, 0.08) 203px,
      transparent 203px,
      transparent 400px
    );
  background-size: 400px 100%, 800px 100%;
  animation: waterRipple 6s linear infinite;
  z-index: 0;
  pointer-events: none;
}
@keyframes waterRipple {
  0% { background-position: 0 0, 0 0; }
  100% { background-position: 400px 0, 800px 0; }
}

/* ── Floating light streams ── */
.streams {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}
.stream {
  position: absolute;
  top: -10%;
  width: 2px;
  height: 120%;
  background: linear-gradient(
    to bottom,
    transparent,
    rgba(136, 157, 240, 0.15) 20%,
    rgba(179, 158, 243, 0.25) 40%,
    rgba(25, 200, 185, 0.2) 60%,
    rgba(247, 205, 103, 0.1) 80%,
    transparent
  );
  border-radius: 1px;
  animation: streamDrift linear infinite;
  opacity: 0;
}
@keyframes streamDrift {
  0% { transform: translateX(-40px); opacity: 0; }
  5% { opacity: 1; }
  90% { opacity: 1; }
  100% { transform: translateX(calc(100vw + 40px)); opacity: 0; }
}

/* ── Background particles ── */
.bg-particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.particle {
  position: absolute;
  bottom: -10px;
  border-radius: 50%;
  animation: floatUp linear infinite;
}
.particle:nth-child(5n+1) { background: rgba(136, 157, 240, 0.35); }
.particle:nth-child(5n+2) { background: rgba(25, 200, 185, 0.35); }
.particle:nth-child(5n+3) { background: rgba(248, 166, 178, 0.35); }
.particle:nth-child(5n+4) { background: rgba(247, 205, 103, 0.35); }
.particle:nth-child(5n+5) { background: rgba(111, 186, 44, 0.35); }
@keyframes floatUp {
  0% { transform: translateY(0) scale(1); opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 0.3; }
  100% { transform: translateY(-100vh) scale(0.5); opacity: 0; }
}

/* ── Center content ── */
.content-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  z-index: 1;
}

/* ── Arena: 西部世界仿真人 ── */
.arena {
  position: relative;
  width: 260px;
  height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.shadow {
  position: absolute;
  bottom: 30px;
  width: 80px;
  height: 10px;
  background: radial-gradient(ellipse, rgba(136,157,240,0.2) 0%, transparent 70%);
  border-radius: 50%;
}
.base-glow {
  position: absolute;
  bottom: 20px;
  width: 160px;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(136,157,240,0.4), rgba(25,200,185,0.4), transparent);
  border-radius: 1px;
  filter: blur(4px);
}

/* ── Stickman + ring（同组旋转） ── */
.stickman {
  position: absolute;
  width: 240px;
  height: 240px;
  overflow: visible;
  z-index: 2;
}
.stickman .vitruvian {
  transform-origin: 100px 100px;
  animation: circleSpin 8s linear infinite;
}
@keyframes circleSpin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
.orbit-ring {
  fill: none;
  stroke-width: 1.5;
}
.orbit-1 {
  stroke: rgba(136, 157, 240, 0.45);
  stroke-dasharray: 8 4;
}
.orbit-2 {
  stroke: rgba(25, 200, 185, 0.35);
  stroke-dasharray: 20 12;
  animation: orbitShift2 3s ease-in-out infinite;
}
.orbit-3 {
  stroke: rgba(179, 158, 243, 0.28);
  stroke-dasharray: 3 8;
  animation: orbitShift3 2.5s ease-in-out infinite;
}
@keyframes orbitShift2 {
  0%, 100% { stroke-dashoffset: 0; }
  50% { stroke-dashoffset: 16; }
}
@keyframes orbitShift3 {
  0%, 100% { stroke-dashoffset: 0; }
  50% { stroke-dashoffset: -11; }
}
.stickman .head {
  fill: none;
  stroke: #c8d8f8;
  stroke-width: 2.5;
}
.stickman .spine,
.stickman .arm,
.stickman .leg {
  stroke: #c8d8f8;
  stroke-width: 2.5;
  stroke-linecap: round;
}

/* ── Title (rainbow gradient text) ── */
.title {
  font-size: var(--app-size-2xl);
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-family: var(--app-font, 'Nunito', 'PingFang SC', sans-serif);
  background: linear-gradient(
    90deg,
    #6fba2c 0%,
    #19c8b9 15%,
    #889df0 30%,
    #b39ef3 45%,
    #f8a6b2 60%,
    #f7cd67 75%,
    #f7a8c4 90%,
    #6fba2c 100%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: titleRainbow 4s linear infinite;
}
@keyframes titleRainbow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
.badge-pending {
  font-size: var(--app-size-sm);
  font-weight: 600;
  padding: 3px 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, #f7cd67, #f8a6b2, #b39ef3, #19c8b9);
  background-size: 300% 100%;
  color: #1a0a2e;
  animation: badgeGlow 2s ease-in-out infinite, badgeRainbow 4s linear infinite;
}
@keyframes badgeGlow {
  0%, 100% { box-shadow: 0 0 8px rgba(247, 205, 103, 0.3); }
  50% { box-shadow: 0 0 20px rgba(179, 158, 243, 0.5); }
}
@keyframes badgeRainbow {
  0% { background-position: 0% 50%; }
  100% { background-position: 300% 50%; }
}

/* ── Message ── */
.message-box {
  text-align: center;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.message {
  font-size: var(--app-size-lg);
  color: #c8d0e8;
  margin: 0;
  transition: opacity 0.5s ease;
  text-shadow: 0 0 20px rgba(136,157,240,0.3);
}
.cursor {
  background: linear-gradient(180deg, #889df0, #f8a6b2);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: blink 1s step-end infinite;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
.sub-message {
  font-size: var(--app-size-sm);
  color: #8890b0;
  margin: 0;
}

/* ── Progress bar ── */
.progress-bar {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  width: 260px;
}
.progress-track {
  width: 100%;
  height: 4px;
  background: rgba(136, 157, 240, 0.15);
  border-radius: 2px;
  overflow: hidden;
}
.progress-fill {
  width: 30%;
  height: 100%;
  background: linear-gradient(90deg, #6fba2c, #19c8b9, #889df0, #b39ef3, #f8a6b2, #f7cd67);
  background-size: 200% 100%;
  border-radius: 2px;
  animation: progressSlide 3s ease-in-out infinite, progressRainbow 3s linear infinite;
}
@keyframes progressSlide {
  0% { width: 10%; }
  50% { width: 60%; }
  100% { width: 10%; }
}
@keyframes progressRainbow {
  0% { background-position: 0% 50%; }
  100% { background-position: 200% 50%; }
}
.progress-label {
  font-size: var(--app-size-xs);
  color: #5a6090;
  letter-spacing: 2px;
  text-transform: uppercase;
}
</style>
