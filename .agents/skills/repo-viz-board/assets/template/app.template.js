/**
 * 看板前端模板（repo-viz-board）。
 *
 * 数据来自 window.__BOARD__（生成器写的 board.js），页面不 fetch：
 * file:// 下 fetch 本地 JSON 会被 CORS 拦。
 *
 * 要改的地方只有三处：
 *   1. MODULE_COLOR_KEY：模块 → 令牌色名（令牌在 styles.css 的 :root）
 *   2. DIAGRAM_LAYOUT / DIAGRAM_EDGES：手绘关系图的坐标与边
 *   3. 图表函数调用（unitTrendColumn 等，来自 charts/board-options.js）
 */
(function () {
  "use strict";

  var DATA = window.__BOARD__ || {};
  var MODULES = DATA.modules || [];
  var RELATIONS = DATA.relations || [];

  // ① 模块 → 颜色（键名是 chart-framework.js 里 tokens().colors 的键）
  var MODULE_COLOR_KEY = {
    accounts: "frontend",
    ai_assistant: "backend"
    // ...
  };

  // ② 架构图：节点坐标（viewBox 1180×480）与边
  var DIAGRAM_LAYOUT = {
    accounts: { x: 90, y: 70, w: 220, h: 54, tilt: -0.4 }
    // ...
  };

  var DIAGRAM_EDGES = [
    // { from: "a", to: "b", label: "谁用谁" }
  ];

  function fmt(value) {
    return Number(value || 0).toLocaleString("en-US");
  }

  /* 模块色 → 同色系深浅两档（卡片数字的深→浅渐变） */
  function shadePair(hex) {
    var value = String(hex || "#888888").trim();
    var parts = [136, 136, 136];
    if (value.charAt(0) === "#") {
      if (value.length === 4) {
        value = "#" + value[1] + value[1] + value[2] + value[2] + value[3] + value[3];
      }
      parts = [parseInt(value.slice(1, 3), 16), parseInt(value.slice(3, 5), 16), parseInt(value.slice(5, 7), 16)];
    }
    var r = parts[0] / 255, g = parts[1] / 255, b = parts[2] / 255;
    var max = Math.max(r, g, b), min = Math.min(r, g, b);
    var l = (max + min) / 2, s = 0, h = 0;
    if (max !== min) {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      else if (max === g) h = ((b - r) / d + 2) / 6;
      else h = ((r - g) / d + 4) / 6;
    }
    h *= 360;
    s *= 100;
    var toHex = function (hh, ss, ll) {
      ss /= 100;
      ll /= 100;
      var c = (1 - Math.abs(2 * ll - 1)) * ss;
      var hp = (hh % 360) / 60;
      var x = c * (1 - Math.abs((hp % 2) - 1));
      var rgb = [0, 0, 0];
      if (hp < 1) rgb = [c, x, 0];
      else if (hp < 2) rgb = [x, c, 0];
      else if (hp < 3) rgb = [0, c, x];
      else if (hp < 4) rgb = [0, x, c];
      else if (hp < 5) rgb = [x, 0, c];
      else rgb = [c, 0, x];
      var m = ll - c / 2;
      var out = rgb.map(function (v) {
        var n = Math.round((v + m) * 255);
        n = Math.max(0, Math.min(255, n));
        return ("0" + n.toString(16)).slice(-2);
      });
      return "#" + out.join("");
    };
    return { deep: toHex(h, Math.min(100, s * 1.05), 36), light: toHex(h, Math.max(20, s * 0.85), 78) };
  }

  /* 正交折线：直角 + 8px 圆角；端口只从节点边中点出 */
  function orthPath(points) {
    var radius = 8;
    var d = "";
    for (var i = 0; i < points.length; i += 1) {
      var point = points[i];
      if (i === 0) {
        d += "M " + point[0] + " " + point[1];
        continue;
      }
      var prev = points[i - 1];
      var next = points[i + 1];
      if (!next) {
        d += " L " + point[0] + " " + point[1];
        continue;
      }
      var inDx = point[0] - prev[0];
      var inDy = point[1] - prev[1];
      var outDx = next[0] - point[0];
      var outDy = next[1] - point[1];
      var inLen = Math.hypot(inDx, inDy) || 1;
      var outLen = Math.hypot(outDx, outDy) || 1;
      var r = Math.min(radius, inLen / 2, outLen / 2);
      var start = [point[0] - (inDx / inLen) * r, point[1] - (inDy / inLen) * r];
      var finish = [point[0] + (outDx / outLen) * r, point[1] + (outDy / outLen) * r];
      d += " L " + start[0] + " " + start[1];
      d += " Q " + point[0] + " " + point[1] + " " + finish[0] + " " + finish[1];
    }
    return d;
  }

  var app = Vue.createApp({
    data: function () {
      return {
        modules: MODULES,
        relations: RELATIONS,
        totals: DATA.totals || {},
        generatedAt: DATA.generated_at || "",
        commit: DATA.commit || "",
        activeModule: "",
        depTab: "graph",
        trendLabels: ["本次", "最近一次", "最近两次"],
        theme: VizCharts.tokens()
      };
    },
    computed: {
      hasData: function () {
        return this.modules.length > 0;
      },
      subtitle: function () {
        return (
          this.totals.modules + " 个模块 · " + this.totals.units + " 个单元 · " +
          fmt(this.totals.files) + " 个文件 · " + fmt(this.totals.loc) + " 行 · 生成于 " + this.generatedAt
        );
      },
      commitTitle: function () {
        return this.commit ? "git " + this.commit : "无 git 信息";
      },
      rows: function () {
        var theme = this.theme;
        return this.modules.map(function (module, index) {
          var colorKey = MODULE_COLOR_KEY[module.key] || "engine";
          var color = (theme.colors || {})[colorKey] || (theme.palette || [])[index % 7];
          var shade = shadePair(color);
          return {
            key: module.key,
            label: module.label,
            color: color,
            deep: shade.deep,
            light: shade.light,
            units: module.units || [],
            unitCount: module.totals.units,
            files: module.totals.files,
            loc: module.totals.loc,
            trend: (module.totalTrend || [null, null, null]).slice(0, 3),
            wide: (module.units || []).length > 10,
            height: (module.units || []).length > 8 ? "360px" : "300px",
            chart: BoardOptions.unitTrendColumn(module.units || [], theme, color)
          };
        });
      },
      pieOption: function () {
        return BoardOptions.modulePie(this.rows, this.theme);
      },
      graphOption: function () {
        var nodes = this.rows.map(function (row) {
          return { key: row.key, label: row.key, color: row.color, loc: row.loc, modules: row.unitCount };
        });
        return BoardOptions.depGraph(nodes, this.relations, this.theme, { labelPosition: "bottom" });
      },
      diagram: function () {
        var nodes = this.rows.map(function (row) {
          var layout = DIAGRAM_LAYOUT[row.key] || { x: 0, y: 0, w: 220, h: 54, tilt: 0 };
          return {
            key: row.key,
            title: row.key,
            color: row.color,
            x: layout.x,
            y: layout.y,
            w: layout.w,
            h: layout.h,
            tilt: layout.tilt,
            cx: layout.x + layout.w / 2,
            cy: layout.y + layout.h / 2,
            top: layout.y,
            bottom: layout.y + layout.h,
            left: layout.x,
            right: layout.x + layout.w
          };
        });
        var byKey = {};
        nodes.forEach(function (node) {
          byKey[node.key] = node;
        });
        var edges = [];
        DIAGRAM_EDGES.forEach(function (edge, index) {
          var from = byKey[edge.from];
          var to = byKey[edge.to];
          if (!from || !to) return;
          var points = [[from.right, from.cy], [to.left, to.cy]];
          edges.push({
            key: edge.from + "->" + edge.to + "-" + index,
            from: edge.from,
            to: edge.to,
            label: edge.label,
            labelX: (from.right + to.left) / 2,
            labelY: (from.cy + to.cy) / 2 - 10,
            labelAnchor: "middle",
            d: orthPath(points)
          });
        });
        return { nodes: nodes, edges: edges, width: 1180, height: 480 };
      }
    },
    methods: {
      fmt: fmt,
      isNodeActive: function (node) {
        return this.activeModule === node.key;
      },
      isEdgeActive: function (edge) {
        if (!this.activeModule) return false;
        return edge.from === this.activeModule || edge.to === this.activeModule;
      },
      trendText: function (values, index) {
        var value = (values || [])[index];
        return value === null || value === undefined ? "待记录" : fmt(value) + " 行";
      },
      trendClass: function (values, index) {
        var value = (values || [])[index];
        return value === null || value === undefined ? "is-pending" : "";
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
