/**
 * 智能体功能模块（engines/）页：模块关系、依赖、一层子单元代码量。
 *
 * 口径见 tools/gen_board_data.py 的 collect_engine_modules()：
 * 模块 = engines 下一个顶层目录；单元 = 模块下的直接子目录（整体算一个）或直接文件。
 */
(function () {
  "use strict";

  var DATA = (window.__BOARD__ || {}).engineModules || {};
  var MODULE_COLOR_KEY = {
    ae_harness: "engine",
    backend_bridge: "workflow",
    device: "assistant",
    uart_log: "tools",
    utils: "utils",
    vision: "event"
  };

  var MODULE_ORDER = ["ae_harness", "backend_bridge", "device", "uart_log", "utils", "vision"];

  /* 架构图坐标（viewBox 1180×480）：上层是「原语层 + 平台装配」，下层是四块底座 */
  var DIAGRAM_LAYOUT = {
    backend_bridge: { x: 120, y: 60, w: 240, h: 54, tilt: -0.4 },
    ae_harness: { x: 620, y: 60, w: 240, h: 54, tilt: 0.4 },
    device: { x: 120, y: 250, w: 220, h: 54, tilt: 0.3 },
    vision: { x: 400, y: 250, w: 220, h: 54, tilt: -0.3 },
    uart_log: { x: 680, y: 250, w: 220, h: 54, tilt: 0.4 },
    utils: { x: 960, y: 250, w: 200, h: 54, tilt: -0.2 }
  };

  var renderMarkdown = window.SimpleMarkdown.render;

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
    h *= 360; s *= 100;
    var toHex = function (hh, ss, ll) {
      ss /= 100; ll /= 100;
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
      light: toHex(h, Math.max(20, s * 0.85), 78)
    };
  }

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
        modules: DATA.modules || [],
        relations: DATA.relations || [],
        totals: DATA.totals || {},
        generatedAt: board.generated_at || "",
        comparisonAt: ((board.engineModules || {}).comparison || {}).at || ["", "", ""],
        commit: board.commit || "",
        activeModule: "",
        docModule: "",
        depTab: "graph",
        theme: VizCharts.tokens()
      };
    },
    computed: {
      hasData: function () {
        return this.modules.length > 0;
      },
      /* 模块行：颜色 + 一层单元 + 横向条形 option */
      rows: function () {
        var theme = this.theme;
        return MODULE_ORDER.map(function (key, index) {
          var module = null;
          (DATA.modules || []).forEach(function (item) {
            if (item.key === key) module = item;
          });
          if (!module) return null;
          var colorKey = MODULE_COLOR_KEY[key] || "engine";
          var color = (theme.colors || {})[colorKey] || (theme.palette || [])[index % 7];
          var shade = shadePair(color);
          return {
            key: key,
            label: module.label,
            note: module.note,
            color: color,
            deep: shade.deep,
            light: shade.light,
            doc: Boolean(module.agentsDoc),
            units: module.units || [],
            unitCount: module.totals.units,
            files: module.totals.files,
            loc: module.totals.loc,
            chart: BoardOptions.unitTrendColumn(module.units || [], theme, color),
            height: (module.units || []).length > 8 ? "360px" : "300px",
            wide: (module.units || []).length > 10,
            trend: (module.totalTrend || [null, null, null]).slice(0, 3)
          };
        }).filter(Boolean);
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
        var links = this.relations.map(function (rel) {
          /* 数据流方向：被调用方 → 调用方 */
          return { from: rel.shared ? "shared" : rel.to, to: rel.from, count: rel.count };
        });
        return BoardOptions.depGraph(nodes, links, this.theme, { labelPosition: "bottom" });
      },
      depRows: function () {
        return this.relations.map(function (rel) {
          return { from: rel.from, to: rel.to, count: rel.count };
        });
      },
      /* 打开某个模块的 AGENTS.md */
      docGroup: function () {
        var key = this.docModule;
        var found = null;
        (DATA.modules || []).forEach(function (item) {
          if (item.key === key) found = item;
        });
        return found;
      },
      docHtml: function () {
        var group = this.docGroup;
        return group ? renderMarkdown(group.agentsDoc || "") : "";
      },
      /* 架构图：节点 + 正交折线 */
      diagram: function () {
        var rows = this.rows;
        var nodes = rows.map(function (row) {
          var layout = DIAGRAM_LAYOUT[row.key] || { x: 0, y: 0, w: 220, h: 54, tilt: 0 };
          return {
            key: row.key,
            doc: row.doc,
            title: row.key,
            label: row.label,
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
        /* 边直接来自 AST 统计的 relations（不是手写清单）：图上每条线都能对回代码 */
        this.relations.forEach(function (rel, index) {
          var from = byKey[rel.from];
          var to = byKey[rel.to];
          if (!from || !to) return;
          var points;
          var labelAt;
          if (Math.abs(to.cy - from.cy) < 12) {
            /* 同一行：右出左进 */
            points = [[from.right, from.cy], [to.left, to.cy]];
            labelAt = [(from.right + to.left) / 2, from.cy - 10];
          } else {
            var goingDown = to.cy > from.cy;
            var startY = goingDown ? from.bottom : from.top;
            var endY = goingDown ? to.top : to.bottom;
            var midY = (startY + endY) / 2;
            points = [[from.cx, startY], [from.cx, midY], [to.cx, midY], [to.cx, endY]];
            labelAt = [from.cx + 8, midY - 10];
          }
          edges.push({
            id: rel.from + "->" + rel.to + "-" + index,
            from: rel.from,
            to: rel.to,
            label: rel.count + " 个文件引用",
            labelX: labelAt[0],
            labelY: labelAt[1],
            labelAnchor: "middle",
            d: orthPath(points)
          });
        });

        return { nodes: nodes, edges: edges, width: 1180, height: 480 };
      }
    },
    methods: {
      fmt: fmt,
      trendText: function (values, index) {
        var value = (values || [])[index];
        return value === null || value === undefined ? "待记录" : fmt(value) + " 行";
      },
      trendClass: function (values, index) {
        var value = (values || [])[index];
        return value === null || value === undefined ? "is-pending" : "";
      },
      toggleModule: function (key) {
        this.activeModule = this.activeModule === key ? "" : key;
      },
      openDoc: function (key) {
        this.docModule = key;
      },
      closeDoc: function () {
        this.docModule = "";
      },
      isNodeActive: function (node) {
        return this.activeModule === node.key;
      },
      isEdgeActive: function (edge) {
        if (!this.activeModule) return false;
        return edge.from === this.activeModule || edge.to === this.activeModule;
      }
    }
  });

  app.mixin({
    mounted: function () {
      var self = this;
      this.onKeydownEsc = function (event) {
        if (event.key === "Escape" && self.docModule) self.docModule = "";
      };
      window.addEventListener("keydown", this.onKeydownEsc);
    },
    beforeUnmount: function () {
      window.removeEventListener("keydown", this.onKeydownEsc);
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
