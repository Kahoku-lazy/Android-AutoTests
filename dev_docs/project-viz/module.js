/**
 * 前端模块详情页（每个业务模块一个页面）。
 *
 * 口径见 tools/gen_board_data.py 的 collect_frontend_modules()：
 * 模块 = frontend/src/modules/<key>；单元 = 模块下的直接子目录（整目录算一个）或直接 .vue/.ts；
 * 单元间 import 由 tools/count_frontend.mjs 的 TS AST 采集（只算模块内、不算跨模块/共享层）。
 *
 * 三节与主页面一致：① 单元关系图（自绘 SVG，环形布局，点节点高亮）② 单元依赖（图/表 tab）+ 代码量饼图
 * ③ 单元代码量最近三次对比。
 */
(function () {
  "use strict";

  var KEY = String(window.__MODULE_KEY__ || "");
  var SCOPE = String(window.__MODULE_SCOPE__ || "frontend");
  var BOARD = window.__BOARD__ || {};
  var SECTION = (SCOPE === "backend" ? BOARD.backendModules : BOARD.frontendModules) || {};
  var MODULES = SECTION.modules || [];
  var ROOT_LABEL = SCOPE === "backend" ? "backend/apps/" : "frontend/src/modules/";

  var NODE_H = 44;
  var NODE_W = 150;

  function fmt(value) {
    return Number(value || 0).toLocaleString("en-US");
  }

  /* 同一色相的深/中/浅三档 */
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
      mid: toHex(h, Math.min(100, s), 52),
      light: toHex(h, Math.max(20, s * 0.85), 78)
    };
  }

  /* 椭圆布局：n 个单元沿椭圆均匀分布（节点数不定，手写坐标不可维护；
     用椭圆而不是圆，是因为画布宽扁，圆环放不下 11 个 150px 宽的节点会互相压） */
  function ringLayout(names, width, height) {
    var cx = width / 2;
    var cy = height / 2;
    var rx = Math.min(width / 2 - NODE_W / 2 - 16, 470);
    var ry = Math.min(height / 2 - NODE_H / 2 - 16, 200);
    /* 节点多时收窄：21 个单元按 150px 会在椭圆上叠起来 */
    var nodeW = names.length > 16 ? 92 : (names.length > 12 ? 112 : NODE_W);
    ringLayout.nodeW = nodeW;
    return names.map(function (name, index) {
      var angle = -Math.PI / 2 + (index / names.length) * Math.PI * 2;
      var x = cx + rx * Math.cos(angle);
      var y = cy + ry * Math.sin(angle);
      return {
        key: name,
        cx: x,
        cy: y,
        x: x - nodeW / 2,
        y: y - NODE_H / 2,
        left: x - nodeW / 2,
        right: x + nodeW / 2,
        top: y - NODE_H / 2,
        bottom: y + NODE_H / 2
      };
    });
  }

  var app = Vue.createApp({
    data: function () {
      return {
        key: KEY,
        modules: MODULES,
        activeUnit: "",
        depTab: "graph",
        generatedAt: BOARD.generated_at || "",
        commit: BOARD.commit || "",
        vueVersion: Vue.version,
        trendLabels: ["本次", "最近一次", "最近两次"],
        theme: VizCharts.tokens()
      };
    },
    computed: {
      module: function () {
        var key = this.key;
        for (var i = 0; i < this.modules.length; i += 1) {
          if (this.modules[i].key === key) return this.modules[i];
        }
        return null;
      },
      hasModule: function () {
        return !!this.module;
      },
      units: function () {
        return (this.module && this.module.units) || [];
      },
      relations: function () {
        return (this.module && this.module.edges) || [];
      },
      color: function () {
        var index = 0;
        for (var i = 0; i < this.modules.length; i += 1) {
          if (this.modules[i].key === this.key) index = i;
        }
        var pool = [
          this.theme.colors.frontend, this.theme.colors.backend, this.theme.colors.engine,
          this.theme.colors.agents, this.theme.colors.tools, this.theme.colors.assistant,
          this.theme.colors.workflow, this.theme.colors.event, this.theme.colors.middleware,
          this.theme.colors.utils
        ].filter(Boolean);
        return pool[index % pool.length] || this.theme.colors.engine;
      },
      subtitle: function () {
        if (!this.module) return "没有找到模块 " + this.key;
        var m = this.module;
        return (
          ROOT_LABEL + m.key + " · " + m.totals.units + " 个单元 · " +
          fmt(m.totals.files) + " 个文件 · " + fmt(m.totals.loc) + " 行 · " +
          this.relations.length + " 条单元间引用 · 生成于 " + this.generatedAt
        );
      },
      /* 第 1 节：环形布局的单元关系图 */
      diagram: function () {
        var self = this;
        var names = this.units.map(function (unit) {
          return unit.name;
        });
        var nodes = ringLayout(names, 1180, 560).map(function (node) {
          var unit = null;
          self.units.forEach(function (item) {
            if (item.name === node.key) unit = item;
          });
          return {
            key: node.key,
            title: node.key,
            color: self.color,
            x: node.x,
            y: node.y,
            cx: node.cx,
            cy: node.cy,
            left: node.left,
            right: node.right,
            top: node.top,
            bottom: node.bottom,
            loc: unit ? unit.loc : 0
          };
        });
        var byKey = {};
        nodes.forEach(function (node) {
          byKey[node.key] = node;
        });
        var edges = [];
        this.relations.forEach(function (rel, index) {
          var from = byKey[rel.from];
          var to = byKey[rel.to];
          if (!from || !to) return;
          /* 二次贝塞尔：控制点沿法线交替偏移，避免所有线穿圆心挤成一团 */
          var mx = (from.cx + to.cx) / 2;
          var my = (from.cy + to.cy) / 2;
          var dx = to.cx - from.cx;
          var dy = to.cy - from.cy;
          var len = Math.sqrt(dx * dx + dy * dy) || 1;
          var bend = (index % 2 === 0 ? 1 : -1) * Math.min(46, len * 0.14);
          var qx = mx - (dy / len) * bend;
          var qy = my + (dx / len) * bend;
          var d = "M " + from.cx + " " + from.cy + " Q " + qx + " " + qy + " " + to.cx + " " + to.cy;
          /* 标签放在 t=0.22（贴着起点）：放中点会全挤到圆心 */
          var tt = 0.16 + (index % 4) * 0.11;
          var one = 1 - tt;
          var labelX = one * one * from.cx + 2 * one * tt * qx + tt * tt * to.cx;
          var labelY = one * one * from.cy + 2 * one * tt * qy + tt * tt * to.cy - 4;
          edges.push({
            key: rel.from + "->" + rel.to + "-" + index,
            from: rel.from,
            to: rel.to,
            label: String(rel.count),
            labelX: labelX,
            labelY: labelY,
            d: d
          });
        });
        var nodeW = ringLayout.nodeW || NODE_W;
        return {
          nodes: nodes, edges: edges, width: 1180, height: 560,
          nodeW: nodeW, nodeH: NODE_H,
          nodeFont: nodeW < 110 ? 9 : 11
        };
      },
      /* 第 2 节左栏：单元依赖图（ECharts，复用环形坐标） */
      graphOption: function () {
        var positions = {};
        this.diagram.nodes.forEach(function (node) {
          positions[node.key] = [node.cx, node.cy];
        });
        var nodes = this.units.map(function (unit) {
          return { key: unit.name, label: unit.name, color: null, loc: unit.loc, modules: 1 };
        });
        return BoardOptions.depGraph(nodes, this.relations, this.theme, {
          labelPosition: "bottom",
          positions: positions
        });
      },
      /* 第 2 节右栏：单元代码量占比 */
      pieOption: function () {
        var palette = ["#a78bfa", "#4ecdc4", "#6bcb77", "#f4a261", "#89cff0", "#ffd166", "#ffb5a7", "#c9a7ff"];
        return BoardOptions.modulePie(
          this.units.map(function (unit, index) {
            return { key: unit.name, loc: unit.loc, color: palette[index % palette.length] };
          }),
          this.theme
        );
      },
      /* 第 3 节：单元代码量三次对比 */
      trendOption: function () {
        return BoardOptions.unitTrendColumn(this.units, this.theme, this.color);
      },
      chartHeight: function () {
        return this.units.length > 10 ? "380px" : "320px";
      }
    },
    methods: {
      fmt: fmt,
      share: function (value, total) {
        if (!total) return "—";
        return ((Number(value || 0) / Number(total)) * 100).toFixed(1) + "%";
      },
      toggleUnit: function (name) {
        this.activeUnit = this.activeUnit === name ? "" : name;
      },
      isNodeActive: function (node) {
        return this.activeUnit === node.key;
      },
      isEdgeActive: function (edge) {
        if (!this.activeUnit) return false;
        return edge.from === this.activeUnit || edge.to === this.activeUnit;
      },
      trendText: function (unit, index) {
        var value = (unit.trend || [])[index];
        return value === null || value === undefined ? "待记录" : fmt(value) + " 行";
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
