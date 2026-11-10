/**
 * useECharts — ECharts 实例生命周期管理
 *
 * 消除 Dashboard TrendBarChart 与 Report Generator
 * PassRateTrendChart / DailyPassFailChart 三处重复的
 * init → resize → watch → dispose 模板代码。
 *
 * 容器尺寸为 0（例如父级用 v-show 隐藏、或首帧还没布局）时**不初始化实例**，
 * 等 ResizeObserver 报告出非零尺寸再建；避免 ECharts 的
 * 「Can't get DOM width or height」告警与 0 尺寸画布。
 *
 * @param {Function} buildOption — 返回 ECharts option 对象的函数
 * @param {Function|Ref} watchSource — watch 的数据源（computed getter 或 ref）
 * @param {Object} opts
 * @param {String}  opts.group — echarts.connect 的组名（可选）
 * @param {Number}  opts.devicePixelRatio — 默认取 window.devicePixelRatio
 */
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

  /** 容器是否已经有可绘制的尺寸（隐藏容器的 clientWidth/Height 都是 0） */
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

  /** 尺寸变化时：还没实例就补建，有实例就 resize（隐藏 → 显示的路径也走这里） */
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
