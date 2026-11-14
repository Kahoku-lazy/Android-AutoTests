/**
 * 前端功能模块页（frontend/src/modules）：模块关系、依赖、一层单元代码量。
 *
 * 口径见 tools/gen_board_data.py 的 collect_frontend_modules()：
 * 模块 = modules 下的一个业务目录；单元 = 模块下的直接子目录（整体算一个）或直接 .vue/.ts。
 * 依赖来自 count_frontend.mjs 的 import 统计；指向「共享层」的边在图上用虚线表示。
 */
(function () {
  "use strict";

  var DATA = (window.__BOARD__ || {}).frontendModules || {};
  var MODULES = DATA.modules || [];
  var RELATIONS = DATA.relations || [];
  var SHARED_KEY = "共享层（shared/views/router）";

  /* 架构图布局（viewBox 1180×680）：11 个业务模块三行，共享层单独落底 */
  var DIAGRAM_LAYOUT = {
    workflow: { x: 60, y: 60, w: 200, h: 54, tilt: -0.4 },
    "task-list": { x: 330, y: 60, w: 200, h: 54, tilt: 0.3 },
    "case-manager": { x: 600, y: 60, w: 200, h: 54, tilt: -0.3 },
    dashboard: { x: 870, y: 60, w: 200, h: 54, tilt: 0.4 },
    "device-pool": { x: 60, y: 200, w: 200, h: 54, tilt: 0.4 },
    "knowledge-assistant": { x: 330, y: 200, w: 200, h: 54, tilt: -0.4 },
    "report-generator": { x: 600, y: 200, w: 200, h: 54, tilt: 0.3 },
    "ai-assistant": { x: 870, y: 200, w: 200, h: 54, tilt: -0.3 },
    "serial-log": { x: 60, y: 340, w: 200, h: 54, tilt: -0.3 },
    "bug-manager": { x: 330, y: 340, w: 200, h: 54, tilt: 0.4 },
    "agent-reports": { x: 600, y: 340, w: 200, h: 54, tilt: -0.4 },
    shared: { x: 470, y: 520, w: 240, h: 54, tilt: 0 }
  };

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
    return {
      deep: toHex(h, Math.min(100, s * 1.05), 36),
      mid: toHex(h, Math.min(100, s * 1.0), 52),
      light: toHex(h, Math.max(20, s * 0.85), 78)
    };
  }

  /* 正交折线：直角 + 8px 圆角 */
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
      var board = window.__BOARD__ || {};
      return {
        modules: MODULES,
        relations: RELATIONS,
        totals: DATA.totals || {},
        generatedAt: board.generated_at || "",
        commit: board.commit || "",
        activeModule: "",
        depTab: "graph",
        vueVersion: Vue.version,
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
          "backend/apps · " + this.totals.modules + " 个模块 · " + this.totals.units + " 个单元 · " +
          fmt(this.totals.files) + " 个 .py · " + fmt(this.totals.loc) + " 行 · 生成于 " + this.generatedAt
        );
      },
      commitTitle: function () {
        return this.commit ? "git " + this.commit : "无 git 信息";
      },
      rows: function () {
        var theme = this.theme;
        var c = theme.colors || {};
        var pool = [
          c.frontend, c.backend, c.engine, c.agents, c.tools, c.assistant,
          c.workflow, c.event, c.middleware, c.utils,
          (theme.palette || [])[5], (theme.palette || [])[6]
        ].filter(Boolean);
        return this.modules.map(function (module, index) {
          var color = pool[index % pool.length] || c.engine;
          var shade = shadePair(color);
          return {
            key: module.key,
            label: module.label,
            /* 长模块名放不下中文名，留空避免压字 */
            shortLabel: module.key.length > 14 ? "" : module.label,
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
      /* 关系卡：把两端模块的颜色带上，卡片里三个值各自着色 */
      relRows: function () {
        var c = this.theme.colors || {};
        /* 只留三种颜色：被调用方=蓝、调用方=绿、次数=紫；不再按模块上色 */
        var blue = shadePair(c.backend && c.event ? c.event : "#89cff0");
        var green = shadePair(c.backend || "#6bcb77");
        var purple = shadePair(c.engine || "#a78bfa");
        var gradient = function (pair) {
          /* 文字渐变只走 深→中，避免末端太浅看不清 */
          return "linear-gradient(180deg, " + pair.deep + " 0%, " + pair.mid + " 100%)";
        };
        return this.relations.map(function (rel) {
          return {
            key: rel.from + "->" + rel.to,
            from: rel.from,
            /* 共享层的 key 名太长，卡片上显示短名 */
            to: rel.shared ? "共享层" : rel.to,
            count: rel.count,
            calledGradient: gradient(blue),
            callerGradient: gradient(green),
            countGradient: gradient(purple)
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
        /* 用架构图的同一套分层坐标：circular 在 12 个节点时会挤成一团 */
        var positions = {};
        this.rows.forEach(function (row) {
          var layout = DIAGRAM_LAYOUT[row.key];
          if (layout) positions[row.key] = [layout.x + layout.w / 2, layout.y + layout.h / 2];
        });
        positions.shared = [DIAGRAM_LAYOUT.shared.x + 120, DIAGRAM_LAYOUT.shared.y + 27];
        nodes.push({
          key: "shared",
          label: "shared",
          color: this.theme.secondary || "#999999",
          loc: 0,
          modules: 0
        });
        var links = this.relations.map(function (rel) {
          /* 数据流方向：被调用方 → 调用方 */
          return { from: rel.shared ? "shared" : rel.to, to: rel.from, count: rel.count };
        });
        return BoardOptions.depGraph(nodes, links, this.theme, {
          labelPosition: "bottom",
          positions: positions
        });
      },
      diagram: function () {
        var nodes = this.rows.map(function (row) {
          var layout = DIAGRAM_LAYOUT[row.key] || { x: 0, y: 0, w: 200, h: 54, tilt: 0 };
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

        /* 共享层不是业务模块，但 11 个模块都依赖它——画一个虚框，避免图上出现一堆孤立节点 */
        var sharedLayout = DIAGRAM_LAYOUT.shared;
        nodes.push({
          key: "shared",
          title: "共享层（不计入统计）",
          color: this.theme.secondary || "#999999",
          x: sharedLayout.x,
          y: sharedLayout.y,
          w: sharedLayout.w,
          h: sharedLayout.h,
          tilt: 0,
          cx: sharedLayout.x + sharedLayout.w / 2,
          cy: sharedLayout.y + sharedLayout.h / 2,
          top: sharedLayout.y,
          bottom: sharedLayout.y + sharedLayout.h,
          shared: true
        });

        var byKey = {};
        nodes.forEach(function (node) {
          byKey[node.key] = node;
        });

        var edges = [];
        this.relations.forEach(function (rel, index) {
          var from = byKey[rel.from];
          var to = byKey[rel.shared ? "shared" : rel.to];
          if (!from || !to) return;
          var points;
          var midY;
          if (Math.abs(to.cy - from.cy) < 12) {
            /* 同一行：右出左进，别从节点上方倒着进 */
            midY = from.cy;
            points = [[from.right, from.cy], [to.left, to.cy]];
          } else {
            var goingDown = to.cy > from.cy;
            var startY = goingDown ? from.bottom : from.top;
            var endY = goingDown ? to.top : to.bottom;
            midY = (startY + endY) / 2;
            points = [
              [from.cx, startY],
              [from.cx, midY],
              [to.cx, midY],
              [to.cx, endY]
            ];
          }
          edges.push({
            key: rel.from + "->" + rel.to + "-" + index,
            from: rel.from,
            to: rel.shared ? "shared" : rel.to,
            label: rel.count + " 次",
            labelX: (from.cx + to.cx) / 2,
            labelY: midY - 6,
            labelAnchor: "middle",
            d: orthPath(points)
          });
        });

        return { nodes: nodes, edges: edges, width: 1180, height: 680 };
      },
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
