/*
 * 后端功能模块页（独立页面，五个分层）
 *
 * 数据来源：
 *   data/board.js        → window.__BOARD__.backend（App 行 + 文件构成 + 跨 App 依赖，生成器产出）
 *   data/history.js      → window.__HISTORY__（历史快照，生成器追加）
 *   data/flow-backend.js → window.__FLOW_BACKEND__（流程时序，人工维护）
 */
(function () {
  "use strict";

  var BOARD = window.__BOARD__ || {};
  var BE = BOARD.backend || { apps: [], edges: [], internal: {}, pairs: [], totals: {} };
  var HISTORY = window.__HISTORY__ || [];
  var FLOW = window.__FLOW_BACKEND__ || { steps: [], source: "", caveat: "", updated: "" };

  function fmt(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  var app = Vue.createApp({
    data: function () {
      return {
        vueVersion: Vue.version,
        generatedAt: BOARD.generated_at || "未生成",
        commit: (BOARD.git && BOARD.git.commit) || "",
        dirty: Boolean(BOARD.git && BOARD.git.dirty),
        hasData: Boolean((BE.apps || []).length),
        apps: BE.apps || [],
        edges: BE.edges || [],
        internal: BE.internal || {},
        pairs: BE.pairs || [],
        totals: BE.totals || {},
        history: HISTORY,
        flow: FLOW,
        theme: VizCharts.tokens(),
        layers: [
          { key: "l1", no: "1", label: "数据总览" },
          { key: "l2", no: "2", label: "依赖关系" },
          { key: "l3", no: "3", label: "流程 / 时序" },
          { key: "l4", no: "4", label: "功能模块说明" },
          { key: "l5", no: "5", label: "历史趋势" }
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
      edgeCount: function () {
        return this.edges.length;
      },
      internalDeps: function () {
        var internal = this.internal || {};
        return Object.keys(internal)
          .map(function (key) {
            return { name: key, count: internal[key] };
          })
          .sort(function (a, b) {
            return b.count - a.count;
          });
      },
      modulePairs: function () {
        return this.pairs || [];
      },
      hasHistory: function () {
        return (this.history || []).length >= 2;
      },
      barOption: function () {
        return BoardOptions.moduleBar(this.apps, this.theme, "backend");
      },
      graphOption: function () {
        var theme = this.theme;
        var nodes = this.apps.map(function (row) {
          return {
            key: row.name,
            label: String(row.name).length > 16 ? String(row.name).slice(0, 15) + "…" : row.name,
            fullLabel: row.name,
            modules: Math.max(1, Number(row.files || 0)),
            loc: Number(row.loc || 0),
            internal: Number((this.internal || {})[row.name] || 0),
            color: row.shared ? theme.colors.engine : theme.colors.backend
          };
        }, this);
        return BoardOptions.depGraph(nodes, this.edges, theme);
      },
      historyOption: function () {
        return BoardOptions.historyLine(this.history, "backend", this.theme);
      }
    },
    methods: {
      fmt: fmt
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
