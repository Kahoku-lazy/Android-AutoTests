/*
 * 总览页应用：只读 window.__BOARD__.overview（生成器算好的结论数据）。
 *
 * 这一页刻意不画图表：结论用数字 + 领域矩阵 + 分数条表达，
 * 图表留给明细页（真要看分布/依赖/趋势时再下钻）。
 */
(function () {
  "use strict";

  var BOARD = window.__BOARD__ || {};
  var OVERVIEW = BOARD.overview || { kpis: [], domains: [], tiers: {}, health: {}, delta: [] };

  function fmt(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  var TIER_LABELS = { direct: "直连", via: "间接", none: "无" };

  var app = Vue.createApp({
    data: function () {
      return {
        vueVersion: Vue.version,
        generatedAt: BOARD.generated_at || "未生成",
        commit: (BOARD.git && BOARD.git.commit) || "",
        dirty: Boolean(BOARD.git && BOARD.git.dirty),
        hasData: Boolean((OVERVIEW.domains || []).length),
        domains: OVERVIEW.domains || [],
        tiers: OVERVIEW.tiers || { direct: 0, via: 0, none: 0 },
        health: OVERVIEW.health || { score: 0, target: 85, parts: [], weights: {} },
        delta: OVERVIEW.delta || [],
        rawKpis: OVERVIEW.kpis || []
      };
    },
    computed: {
      kpis: function () {
        var self = this;
        return (this.rawKpis || []).map(function (kpi) {
          var state = "neutral";
          if (kpi.key === "alignment") {
            var pct = Number(kpi.pct || 0);
            state = pct >= 100 ? "good" : pct >= 60 ? "warn" : "bad";
          } else if (kpi.key === "health") {
            state = self.healthState;
          }
          return Object.assign({}, kpi, { state: state });
        });
      },
      commitTitle: function () {
        var parts = [];
        if (this.commit) parts.push("commit " + this.commit);
        parts.push(this.dirty ? "工作区有未提交改动" : "工作区干净");
        return parts.join(" · ");
      },
      weights: function () {
        return this.health.weights || {};
      },
      healthState: function () {
        var score = Number(this.health.score || 0);
        if (score >= 85) return "good";
        if (score >= 70) return "warn";
        return "bad";
      },
      churnText: function () {
        var total = this.delta.reduce(function (sum, item) {
          return sum + Number(item.diff || 0);
        }, 0);
        return (total >= 0 ? "+" : "") + fmt(total) + " 行";
      }
    },
    methods: {
      fmt: fmt,
      tierLabel: function (key) {
        return TIER_LABELS[key] || key;
      }
    }
  });

  app.mount("#app");
})();
