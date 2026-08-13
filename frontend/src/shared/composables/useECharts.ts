/**
 * useECharts — ECharts 实例生命周期管理
 *
 * 消除 Dashboard TrendBarChart 与 Report Generator
 * PassRateTrendChart / DailyPassFailChart 三处重复的
 * init → resize → watch → dispose 模板代码。
 *
 * @param {Function} buildOption — 返回 ECharts option 对象的函数
 * @param {Function|Ref} watchSource — watch 的数据源（computed getter 或 ref）
 * @param {Object} opts
 * @param {String}  opts.group — echarts.connect 的组名（可选）
 * @param {Number}  opts.devicePixelRatio — 默认取 window.devicePixelRatio
 */
import { ref, watch, onMounted, onUnmounted, nextTick } from 'vue';
import * as echarts from 'echarts';

export function useECharts(buildOption, watchSource, opts: { group?: string; devicePixelRatio?: number } = {}) {
  const container = ref(null);
  let instance = null;
  let resizeObserver = null;

  function renderChart() {
    if (!instance || instance.isDisposed()) return;
    instance.setOption(buildOption(), { notMerge: true, lazyUpdate: false });
  }

  function initChart() {
    if (!container.value) return;

    const existing = echarts.getInstanceByDom(container.value);
    if (existing) existing.dispose();

    instance = echarts.init(container.value, null, {
      devicePixelRatio: opts.devicePixelRatio || window.devicePixelRatio || 2,
    });

    if (opts.group) {
      instance.group = opts.group;
      echarts.connect(opts.group);
    }

    renderChart();

    resizeObserver = new ResizeObserver(() => {
      if (instance && !instance.isDisposed()) instance.resize();
    });
    resizeObserver.observe(container.value);
  }

  onMounted(() => nextTick(initChart));

  watch(watchSource, () => nextTick(renderChart), { deep: true });

  onUnmounted(() => {
    resizeObserver?.disconnect();
    if (instance && !instance.isDisposed()) {
      instance.dispose();
    }
    instance = null;
  });

  return { container };
}
