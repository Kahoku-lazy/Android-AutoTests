/*
 * 项目看板 · 应用层（Vue 3 全局构建，免打包）
 *
 * 数据来源：data/board.js（window.__BOARD__，由 tools/gen_board_data.py 生成）。
 * 为什么不用 fetch：双击打开是 file:// 协议，fetch 会被 CORS 拦掉；<script> 不受限。
 */
(function () {
  "use strict";

  var EMPTY = {
    generated_at: "",
    git: { commit: "", dirty: false },
    notes: {
      features: { frontend: "", backend: "", engine: "", caveat: "" },
      methods: "",
      loc: "",
      files: "",
      scope: ""
    },
    categories: [],
    grand_totals: { features: 0, files: 0, classes: 0, methods: 0, loc: 0 }
  };

  var BOARD = window.__BOARD__ || EMPTY;
  var TILTS = [-0.6, 0.8, -1.1, 0.7, -0.9, 1.2];

  function fmt(value) {
    var number = Number(value || 0);
    return number.toLocaleString("zh-CN");
  }

  /* 统一图表底层：注册 <viz-chart> 到 app（Vue 3 没有 Vue.component） */
  var app = Vue.createApp({
    data: function () {
      var totals = BOARD.grand_totals || EMPTY.grand_totals;
      return {
        vueVersion: Vue.version,
        hasData: Boolean(BOARD.categories && BOARD.categories.length),
        generatedAt: BOARD.generated_at || "未生成",
        commit: (BOARD.git && BOARD.git.commit) || "",
        dirty: Boolean(BOARD.git && BOARD.git.dirty),
        notes: BOARD.notes || EMPTY.notes,
        categories: BOARD.categories || [],
        grand: totals,
        theme: VizCharts.tokens(),
        metrics: BoardOptions.metrics,
        /* 分类筛选：全局生效（总量图 + 明细图 + 表格），"all" = 全仓 */
        filters: [
          { key: "all", label: "全部" },
          { key: "frontend", label: "前端" },
          { key: "backend", label: "后端" },
          { key: "engine", label: "引擎" }
        ],
        activeCategory: "all",
        todo: [
          "依赖关系视图：谁 import 谁（按引擎 关联模块 + AST import 交叉校验）",
          "流程 / 时序视图：一次任务从下发到报告的链路",
          "按功能下钻：点某模块看它的功能清单与入口",
          "历史趋势：需要多次快照存档后再看"
        ]
      };
    },
    computed: {
      commitTitle: function () {
        var parts = [];
        if (this.commit) parts.push("commit " + this.commit);
        parts.push(this.dirty ? "工作区有未提交改动" : "工作区干净");
        return parts.join(" · ");
      },
      /* 图表配置只算数据，不建实例（实例交给 <viz-chart>） */
      visibleCategories: function () {
        if (this.activeCategory === "all") return this.categories;
        return this.categories.filter(function (category) {
          return category.key === this.activeCategory;
        }, this);
      },
      scopeLabel: function () {
        return BoardOptions.scopeLabel(BOARD, this.activeCategory);
      },
      scopeTotals: function () {
        return BoardOptions.scopeTotals(BOARD, this.activeCategory);
      },
      totalsOption: function () {
        return BoardOptions.totalsBar(BOARD, this.theme, this.activeCategory);
      },
      donutOption: function () {
        return BoardOptions.donut(BOARD, this.theme, this.activeCategory);
      },
      /* 明细图共用：当前范围里的模块行数 */
      scopeRows: function () {
        var rows = 0;
        this.visibleCategories.forEach(function (category) {
          rows += category.modules.length;
        });
        return rows;
      },
      /* 五张明细图共用的行顺序（按代码行降序）：同一模块在五图里同一行 */
      moduleOrder: function () {
        return BoardOptions.moduleOrder(BOARD, this.activeCategory);
      },
      /* 分层明细：一个指标一张图（功能 → 文件 → 类 → 方法 → 代码行），顺序即数组顺序 */
      metricCharts: function () {
        var rows = this.scopeRows;
        var height = String(Math.min(720, Math.max(200, rows * 22 + 64))) + "px";
        var order = this.moduleOrder;
        return this.metrics.map(function (metric) {
          return {
            key: metric.key,
            label: metric.label,
            height: height,
            option: BoardOptions.bar(BOARD, metric.key, this.theme, this.activeCategory, order)
          };
        }, this);
      },
      maxLoc: function () {
        var max = 0;
        (this.categories || []).forEach(function (category) {
          category.modules.forEach(function (row) {
            if (Number(row.loc) > max) max = Number(row.loc);
          });
        });
        return max || 1;
      }
    },
    methods: {
      fmt: fmt,
      setFilter: function (key) {
        this.activeCategory = key;
      },
      isFiltered: function (key) {
        return this.activeCategory === key;
      },
      categoryColor: function (key) {
        return (this.theme.colors || {})[key] || "transparent";
      },
      tilt: function (index) {
        return TILTS[index % TILTS.length] + "deg";
      },
      /* 条形按"最大的模块"归一，否则全是短条看不出差异 */
      bar: function (loc) {
        return ((Number(loc || 0) / this.maxLoc) * 100).toFixed(1) + "%";
      },
      /* 文字标签仍报"占全仓比例" */
      pct: function (loc) {
        var total = Number(this.grand.loc || 0);
        if (!total) return "0%";
        return ((Number(loc || 0) / total) * 100).toFixed(1) + "%";
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
