<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { createTaskMediaLink, getTaskMedia } from "../api/tasks"

/**
 * 任务截图缩略图：进入视口才取字节，取到后转 object URL，卸载时释放。
 * 报告只下发 media_id，图片字节走 /api/tasks/{id}/media/{media_id}/（需 JWT，故不能用 <img src>）。
 */
const props = defineProps({
  taskId: { type: Number, required: true },
  mediaId: { type: Number, required: true },
  alt: { type: String, default: "执行截图" },
})

const root = ref(null)
const src = ref("")
const state = ref("idle")
const opening = ref(false)

let observer = null
let objectUrl = ""

function release() {
  if (objectUrl) {
    URL.revokeObjectURL(objectUrl)
    objectUrl = ""
  }
  src.value = ""
}

function stopObserve() {
  if (observer) {
    observer.disconnect()
    observer = null
  }
}

async function load() {
  if (state.value === "loading" || state.value === "ready") return
  state.value = "loading"
  try {
    const blob = await getTaskMedia(props.taskId, props.mediaId)
    if (!blob || blob.size === 0) throw new Error("空图片")
    release()
    objectUrl = URL.createObjectURL(blob)
    src.value = objectUrl
    state.value = "ready"
  } catch (_) {
    state.value = "failed"
  }
}

function observe() {
  if (!root.value) return
  if (typeof IntersectionObserver === "undefined") {
    load()
    return
  }
  observer = new IntersectionObserver(
    (entries) => {
      if (entries.some((entry) => entry.isIntersecting)) {
        stopObserve()
        load()
      }
    },
    { rootMargin: "200px" },
  )
  observer.observe(root.value)
}

/**
 * 在新标签打开原图：先同步开空窗口（避免异步调用被拦截），
 * 再签发短时直链并按当前 origin 补全地址导航。
 */
async function openInNewTab() {
  if (opening.value) return
  opening.value = true
  const win = window.open("", "_blank")
  try {
    const payload = await createTaskMediaLink(props.taskId, props.mediaId)
    const path = payload?.data?.url
    if (!payload?.status || !path) throw new Error("签发直链失败")
    const href = new URL(path, window.location.origin).href
    if (win) win.location.href = href
    else window.open(href, "_blank", "noopener")
  } catch (_) {
    win?.close()
  } finally {
    opening.value = false
  }
}

onMounted(observe)

onBeforeUnmount(() => {
  stopObserve()
  release()
})

watch(
  () => props.mediaId,
  () => {
    stopObserve()
    release()
    state.value = "idle"
    observe()
  },
)
</script>

<template>
  <div v-if="state !== 'failed'" ref="root" class="task-media-thumb">
    <img v-if="state === 'ready'" class="task-media-thumb__image" :src="src" :alt="alt" />
    <span v-else class="task-media-thumb__placeholder" aria-hidden="true"></span>
    <button
      v-if="state === 'ready'"
      type="button"
      class="task-media-thumb__open"
      :disabled="opening"
      @click="openInNewTab"
    >
      在新标签打开
    </button>
  </div>
</template>

<style src="./TaskMediaThumb.style.css" scoped></style>
