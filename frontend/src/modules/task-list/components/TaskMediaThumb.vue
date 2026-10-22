<script setup>
import { onBeforeUnmount, onMounted, ref, watch } from "vue"
import { getTaskMedia } from "../api/tasks"

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
  </div>
</template>

<style src="./TaskMediaThumb.style.css" scoped></style>
