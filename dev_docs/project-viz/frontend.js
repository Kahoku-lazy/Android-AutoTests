/*
 * 前端功能模块页（独立页面，五个分层）
 *
 * 数据来源：
 *   data/board.js         → window.__BOARD__.frontend（模块行 + 路由 + 依赖边，生成器产出）
 *   data/history.js       → window.__HISTORY__（历史快照，生成器追加）
 *   data/flow-frontend.js → window.__FLOW_FRONTEND__（流程时序，人工维护）
 */
(function () {
  "use strict";

  var BOARD = window.__BOARD__ || {};
  var FE = BOARD.frontend || { modules: [], edges: [], routesByModule: {}, totals: {}, pages: [] };
  var HISTORY = window.__HISTORY__ || [];
  var FLOW = window.__FLOW_FRONTEND__ || { steps: [], source: "", caveat: "", updated: "" };

  /* 模块中文名：Tab 读作「<中文>模块：<目录名>」，与智能体页保持同一写法 */
  var MODULE_TITLES = {
    "case-manager": "用例管理",
    "task-list": "任务清单",
    "dashboard": "仪表盘",
    "device-pool": "设备池",
    workflow: "页面流",
    "ai-assistant": "AI 助手",
    "knowledge-assistant": "知识库助手",
    "report-generator": "报告生成",
    "serial-log": "串口日志",
    "bug-manager": "BUG 管理"
  };

  var EMPTY_PAGE_MODULE = { name: "", pages: [], components: 0, calls: [] };

  function fmt(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  function moduleLabel(name) {
    var title = MODULE_TITLES[name];
    return title ? title + "模块：" + name : name;
  }

  var app = Vue.createApp({
    data: function () {
      return {
        vueVersion: Vue.version,
        generatedAt: BOARD.generated_at || "未生成",
        commit: (BOARD.git && BOARD.git.commit) || "",
        dirty: Boolean(BOARD.git && BOARD.git.dirty),
        hasData: Boolean((FE.modules || []).length),
        modules: FE.modules || [],
        edges: FE.edges || [],
        routesByModule: FE.routesByModule || {},
        pageModules: FE.pages || [],
        activePageModule: "",
        totals: FE.totals || {},
        history: HISTORY,
        flow: FLOW,
        theme: VizCharts.tokens(),
        layers: [
          { key: "l1", no: "1", label: "数据总览" },
          { key: "l2", no: "2", label: "依赖关系" },
          { key: "l3", no: "3", label: "流程 / 时序" },
          { key: "l4", no: "4", label: "功能模块说明" },
          { key: "l5", no: "5", label: "页面构成" },
          { key: "l6", no: "6", label: "历史趋势" }
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
      outRank: function () {
        var sums = {};
        this.edges.forEach(function (edge) {
          sums[edge.from] = (sums[edge.from] || 0) + Number(edge.count || 0);
        });
        return Object.keys(sums)
          .map(function (key) {
            return { name: key, count: sums[key] };
          })
          .sort(function (a, b) {
            return b.count - a.count;
          })
          .slice(0, 8);
      },
      inRank: function () {
        var sums = {};
        this.edges.forEach(function (edge) {
          sums[edge.to] = (sums[edge.to] || 0) + Number(edge.count || 0);
        });
        return Object.keys(sums)
          .map(function (key) {
            return { name: key, count: sums[key] };
          })
          .sort(function (a, b) {
            return b.count - a.count;
          })
          .slice(0, 8);
      },
      pageTabs: function () {
        return this.pageModules.map(function (module) {
          return {
            key: module.name,
            label: moduleLabel(module.name),
            count: module.pages.length
          };
        });
      },
      currentPageKey: function () {
        if (this.activePageModule) return this.activePageModule;
        return this.pageModules.length ? this.pageModules[0].name : "";
      },
      currentPageModule: function () {
        var key = this.currentPageKey;
        var found = null;
        this.pageModules.forEach(function (module) {
          if (module.name === key) found = module;
        });
        return found || EMPTY_PAGE_MODULE;
      },
      currentPageTitle: function () {
        return moduleLabel(this.currentPageModule.name);
      },
      currentPages: function () {
        return this.currentPageModule.pages || [];
      },
      hasHistory: function () {
        return (this.history || []).length >= 2;
      },
      barOption: function () {
        return BoardOptions.moduleBar(this.modules, this.theme, "frontend");
      },
      graphOption: function () {
        var theme = this.theme;
        var nodes = this.modules.map(function (row) {
          return {
            key: row.name,
            label: String(row.name).length > 14 ? String(row.name).slice(0, 13) + "…" : row.name,
            fullLabel: row.name,
            modules: 1,
            loc: Number(row.loc || 0),
            internal: 0,
            /* 共享层用引擎色区分，其余用前端色 */
            color: row.shared ? theme.colors.engine : theme.colors.frontend
          };
        });
        return BoardOptions.depGraph(nodes, this.edges, theme);
      },
      historyOption: function () {
        return BoardOptions.historyLine(this.history, "frontend", this.theme);
      }
    },
    methods: {
      fmt: fmt,
      routesOf: function (name) {
        return this.routesByModule[name] || [];
      },
      selectPageModule: function (key) {
        this.activePageModule = key;
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
