/*
 * 统一图表底层（本目录所有图表必须走这里，禁止各自 new echarts）
 *
 * 解决的是四个重复问题：实例生命周期（建/更新/销毁）、容器尺寸变化、
 * 主题取值（CSS 令牌 → ECharts）、无动画偏好。
 *
 * 对外只有三样东西：
 *   window.VizCharts.tokens()                读令牌，返回画图用的主题对象
 *   window.VizCharts.create(el, option, {})  建实例，返回 {update, resize, dispose}
 *   <viz-chart :option="…" height="…" />     Vue 全局组件（自动建/更新/销毁）
 *
 * 为什么 CSS 令牌要转一道：ECharts 只吃具体颜色字符串，canvas 读不到 var(--x)。
 * 所以颜色一律从 :root 的 computed style 取，保证和页面用同一套令牌。
 */
(function () {
  "use strict";

  var root = document.documentElement;

  function css(name, fallback) {
    var value = window.getComputedStyle(root).getPropertyValue(name);
    return (value || "").trim() || fallback || "";
  }

  /** 读页面令牌，产出 ECharts 能用的主题对象。 */
  function tokens() {
    return {
      ink: css("--ink", "#1e1e24"),
      paper: css("--paper", "#fffef5"),
      card: css("--app-bg-card", "#ffffff"),
      subtle: css("--app-bg-subtle", "#fffef5"),
      secondary: css("--app-text-secondary", "#96918c"),
      stat: css("--app-stat-text", "#5d5950"),
      font: css("--app-font", "monospace"),
      /* ECharts 只接受数字字号；12 = 令牌 --app-size-xs，最小档 */
      fontSize: 12,
      reduceMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      colors: {
        frontend: css("--c-case", "#4ecdc4"),
        backend: css("--c-device", "#6bcb77"),
        engine: css("--c-element", "#a78bfa")
      },
      /* 单序列图（总量）用强调色；高亮/选中用 dashboard 黄 */
      accent: css("--c-workflow", "#89cff0"),
      highlight: css("--c-dashboard", "#f7c948")
    };
  }

  /** 建一个图表实例；返回句柄，调用方必须在卸载时 dispose。 */
  function create(el, option) {
    if (!window.echarts) {
      throw new Error("ECharts 未加载：检查 vendor/echarts.common.min.js 是否在页面里");
    }
    var chart = window.echarts.init(el, null, { renderer: "canvas" });
    chart.setOption(option);

    /* 容器尺寸变化（窗口缩放 / 侧栏折叠 / 字体加载）都只在这里处理一次 */
    var observer = new ResizeObserver(function () {
      chart.resize();
    });
    observer.observe(el);

    return {
      instance: chart,
      update: function (next) {
        chart.setOption(next, true);
      },
      resize: function () {
        chart.resize();
      },
      dispose: function () {
        observer.disconnect();
        chart.dispose();
      }
    };
  }

  /** 注册全局组件 <viz-chart>：负责挂载、随数据更新、卸载销毁。传入 app 实例（Vue 3 无全局 Vue.component）。 */
  function register(app) {
    app.component("viz-chart", {
      props: {
        option: { type: Object, required: true },
        height: { type: String, default: "320px" },
        label: { type: String, default: "" }
      },
      template:
        '<div class="viz-chart" role="img" :aria-label="label" :style="{ height: height }"></div>',
      mounted: function () {
        this.handle = create(this.$el, this.option);
      },
      watch: {
        option: {
          deep: true,
          handler: function (next) {
            if (this.handle) this.handle.update(next);
          }
        }
      },
      beforeUnmount: function () {
        if (this.handle) {
          this.handle.dispose();
          this.handle = null;
        }
      }
    });
  }

  window.VizCharts = { tokens: tokens, create: create, register: register };
})();
