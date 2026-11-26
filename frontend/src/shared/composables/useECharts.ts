import { ref, watch, onMounted, onUnmounted, nextTick } from "vue"
import * as echarts from "echarts"

export function useECharts(
  buildOption,
  watchSource,
  opts: { group?: string; devicePixelRatio?: number } = {},
) {
  const container = ref(null)
  let instance = null
  let resizeObserver = null

  function hasSize() {
    const el: any = container.value
    return !!el && el.clientWidth > 0 && el.clientHeight > 0
  }

  function renderChart() {
    if (!instance || instance.isDisposed()) return
    instance.setOption(buildOption(), { notMerge: true, lazyUpdate: false })
  }

  function initChart() {
    if (!container.value || !hasSize()) return

    const existing = echarts.getInstanceByDom(container.value)
    if (existing) existing.dispose()

    instance = echarts.init(container.value, null, {
      devicePixelRatio: opts.devicePixelRatio || window.devicePixelRatio || 2,
    })

    if (opts.group) {
      instance.group = opts.group
      echarts.connect(opts.group)
    }

    renderChart()
    ensureObserver()
  }

  function ensureObserver() {
    if (resizeObserver || !container.value) return
    resizeObserver = new ResizeObserver(() => {
      if (!container.value) return
      if (!instance || instance.isDisposed()) {
        initChart()
        return
      }
      instance.resize()
    })
    resizeObserver.observe(container.value)
  }

  onMounted(() =>
    nextTick(() => {
      ensureObserver()
      initChart()
    }),
  )

  watch(
    watchSource,
    () =>
      nextTick(() => {
        if (instance && !instance.isDisposed()) renderChart()
        else initChart()
      }),
    { deep: true },
  )

  onUnmounted(() => {
    resizeObserver?.disconnect()
    if (instance && !instance.isDisposed()) {
      instance.dispose()
    }
    instance = null
  })

  return { container }
}
