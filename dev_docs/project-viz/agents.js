/*
 * 智能体功能模块页（独立页面，五个分层）
 *
 * 数据来源：
 *   data/board.js   → window.__BOARD__.agents（模块清单 + 依赖边，生成器产出）
 *   data/history.js → window.__HISTORY__（历史快照，生成器追加）
 *   data/flow.js    → window.__FLOW__（流程时序，人工维护）
 * 图表仍走统一底层 charts/chart-framework.js 的 <viz-chart>。
 */
(function () {
  "use strict";

  var EMPTY_AGENTS = { groups: [], totals: {}, imports: { edges: [], internal: {}, pairs: [] } };
  var BOARD = window.__BOARD__ || {};
  var AGENTS = BOARD.agents || EMPTY_AGENTS;
  var HISTORY = window.__HISTORY__ || [];
  var FLOW = window.__FLOW__ || { steps: [], source: "", caveat: "", updated: "" };

  /* 目录中文名：标签统一读作「<中文>模块：<目录名>」，比裸目录名好读 */
  var GROUP_TITLES = {
    workflow: "工作流",
    tools: "角色工具",
    models: "模型与工厂",
    rag: "检索增强",
    realtime_vocie: "语音会话",
    middleware: "中间件",
    messaging: "事件与计费",
    config: "角色与模型配置",
    knowledge_chat: "知识库会话",
    "(根)": "装配与入口"
  };

  function fmt(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  function groupLabel(group) {
    var key = group.key === "(根)" ? "根级" : group.key;
    var title = GROUP_TITLES[group.key];
    return title ? title + "模块：" + key : group.label;
  }

  var app = Vue.createApp({
    data: function () {
      return {
        vueVersion: Vue.version,
        generatedAt: BOARD.generated_at || "未生成",
        commit: (BOARD.git && BOARD.git.commit) || "",
        dirty: Boolean(BOARD.git && BOARD.git.dirty),
        hasData: Boolean((AGENTS.groups || []).length),
        groups: AGENTS.groups || [],
        totals: AGENTS.totals || {},
        imports: AGENTS.imports || EMPTY_AGENTS.imports,
        history: HISTORY,
        flow: FLOW,
        activeGroup: "",
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
      groupCount: function () {
        return this.groups.length;
      },
      /* 目录 Tab：标签 =「中文模块：目录名」，角标是模块数 */
      groupTabs: function () {
        return this.groups.map(function (group) {
          return {
            key: group.key,
            label: groupLabel(group),
            count: group.totals.modules
          };
        });
      },
      currentTitle: function () {
        return groupLabel(this.currentGroup);
      },
      currentKey: function () {
        if (this.activeGroup) return this.activeGroup;
        return this.groups.length ? this.groups[0].key : "";
      },
      currentGroup: function () {
        var key = this.currentKey;
        var found = null;
        this.groups.forEach(function (group) {
          if (group.key === key) found = group;
        });
        return found || { key: "", label: "无数据", modules: [], totals: {} };
      },
      edgeCount: function () {
        return (this.imports.edges || []).length;
      },
      labelOf: function () {
        var map = {};
        this.groups.forEach(function (group) {
          map[group.key] = group.label;
        });
        return map;
      },
      internalDeps: function () {
        var internal = this.imports.internal || {};
        var self = this;
        return Object.keys(internal)
          .map(function (key) {
            return { key: key, label: self.labelOf[key] || key, count: internal[key] };
          })
          .sort(function (a, b) {
            return b.count - a.count;
          });
      },
      modulePairs: function () {
        return (this.imports.pairs || []).map(function (pair) {
          return { from: pair.from, to: pair.to, count: pair.count };
        });
      },
      hasHistory: function () {
        return (this.history || []).length >= 2;
      },
      historyOption: function () {
        return BoardOptions.agentsHistory(this.history, this.theme);
      },
      option: function () {
        /* 图表与 Tab 用同一套目录命名（「工作流模块：workflow」），避免两处叫法不一致 */
        var groups = this.groups.map(function (group) {
          return Object.assign({}, group, { label: groupLabel(group) });
        });
        return BoardOptions.agentsBar({ groups: groups, totals: this.totals }, this.theme);
      },
      graphOption: function () {
        return BoardOptions.agentsGraph(
          { groups: this.groups, imports: this.imports },
          this.theme
        );
      }
    },
    methods: {
      fmt: fmt,
      selectGroup: function (key) {
        this.activeGroup = key;
      },
      groupTitle: function (group) {
        return groupLabel(group);
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
