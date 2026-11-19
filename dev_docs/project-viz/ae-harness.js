/*
 * ae_harness 页：七个原语模块（根目录文件夹）的架构、代码量、依赖与逐文件对比。
 *
 * 数据来源：window.__BOARD__.ae_harness（生成器产出）
 *   1. 架构：模块关系（节点顺序固定，边的两端与次数来自生成器：包内 relations + 包外 external）
 *   2. 模块代码量：每组 .py 的行数合计
 *   3. 目录依赖：AST import（只证明"引用了谁"）
 *   4. 逐文件代码量：每个文件三个值（本次 / 最近一次 / 最近两次）
 */
(function () {
  "use strict";

  var EMPTY = {
    groups: [],
    relations: [],
    imports: { edges: [], internal: {}, pairs: [] },
    comparison: { at: [], groups: {}, files: {}, scope: 3 },
    totals: {}
  };
  var BOARD = window.__BOARD__ || {};
  var DATA = BOARD.ae_harness || EMPTY;

  var renderMarkdown = window.SimpleMarkdown.render;

  /* 模块色 → 同色系深浅两档（保色相、调 HSL 亮度，给大数字做深→浅渐变） */
  function hexParts(hex) {
    var value = String(hex || "#888888").trim();
    if (value.charAt(0) !== "#") return [136, 136, 136];
    if (value.length === 4) {
      value = "#" + value[1] + value[1] + value[2] + value[2] + value[3] + value[3];
    }
    return [
      parseInt(value.slice(1, 3), 16),
      parseInt(value.slice(3, 5), 16),
      parseInt(value.slice(5, 7), 16)
    ];
  }

  function rgbToHsl(r, g, b) {
    r /= 255;
    g /= 255;
    b /= 255;
    var max = Math.max(r, g, b);
    var min = Math.min(r, g, b);
    var l = (max + min) / 2;
    var s = 0;
    var h = 0;
    if (max !== min) {
      var d = max - min;
      s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
      if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
      else if (max === g) h = ((b - r) / d + 2) / 6;
      else h = ((r - g) / d + 4) / 6;
    }
    return [h * 360, s * 100, l * 100];
  }

  function hslToHex(h, s, l) {
    s /= 100;
    l /= 100;
    var c = (1 - Math.abs(2 * l - 1)) * s;
    var hp = (h % 360) / 60;
    var x = c * (1 - Math.abs((hp % 2) - 1));
    var rgb = [0, 0, 0];
    if (hp < 1) rgb = [c, x, 0];
    else if (hp < 2) rgb = [x, c, 0];
    else if (hp < 3) rgb = [0, c, x];
    else if (hp < 4) rgb = [0, x, c];
    else if (hp < 5) rgb = [x, 0, c];
    else rgb = [c, 0, x];
    var m = l - c / 2;
    var toHex = function (value) {
      var v = Math.round((value + m) * 255);
      return ("0" + Math.max(0, Math.min(255, v)).toString(16)).slice(-2);
    };
    return "#" + toHex(rgb[0]) + toHex(rgb[1]) + toHex(rgb[2]);
  }

  /* 深端压亮度、提饱和；浅端提亮度、略降饱和 —— 同一色相内做深浅 */
  function shadePair(hex) {
    var parts = hexParts(hex);
    var hsl = rgbToHsl(parts[0], parts[1], parts[2]);
    return {
      deep: hslToHex(hsl[0], Math.min(100, hsl[1] * 1.05), 36),
      light: hslToHex(hsl[0], Math.max(20, hsl[1] * 0.85), 78)
    };
  }

  /* 模块 = ae_harness 根目录的七个文件夹，顺序固定（与页面第 2/3 节一致） */
  var MODULE_ORDER = ["agents", "tools", "knowledge", "assistant", "workflow", "event", "middleware"];

  /* 架构图坐标（viewBox 1180×460）：
     顶部一条是「外部装配方」（backend_bridge / backend/apps）——本包只出原语，装配在包外；
     第一行四个模块、第二行三个模块，第二行的竖线走第一行之间的空档，不穿节点。 */
  var DIAGRAM_LAYOUT = {
    external: { x: 60, y: 40, w: 1060, h: 54, tilt: 0 },
    agents: { x: 40, y: 180, w: 200, h: 54, tilt: -0.4 },
    tools: { x: 330, y: 180, w: 200, h: 54, tilt: 0.4 },
    knowledge: { x: 620, y: 180, w: 200, h: 54, tilt: -0.3 },
    assistant: { x: 910, y: 180, w: 200, h: 54, tilt: 0.3 },
    workflow: { x: 185, y: 340, w: 200, h: 54, tilt: -0.3 },
    event: { x: 475, y: 340, w: 200, h: 54, tilt: 0.4 },
    middleware: { x: 765, y: 340, w: 200, h: 54, tilt: -0.4 }
  };

  /* 折线 → path：直角折线 + 拐角 8px 圆角；可选在某一段插 10px 跳桥（跨过另一条线） */
  function orthPath(points, bridge) {
    var radius = 8;
    var gap = 10;
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
      var isBridge = bridge && bridge.seg === i - 1 && bridge.axis === "x" && inDy === 0;
      if (isBridge) {
        d += " L " + (bridge.at - gap) + " " + prev[1];
        d += " A " + gap + " " + gap + " 0 0 1 " + (bridge.at + gap) + " " + prev[1];
        d += " L " + start[0] + " " + start[1];
      } else {
        d += " L " + start[0] + " " + start[1];
      }
      d += " Q " + point[0] + " " + point[1] + " " + finish[0] + " " + finish[1];
    }
    return d;
  }

  /* 一条边的走线：同一行 → 横线；外部装配方 → 落到目标顶边中点；其余走中缝的直角折线。
     边全部来自生成器统计（包内 relations + 包外 external），不在这里手写。 */
  function routeEdge(from, to) {
    if (Math.abs(to.cy - from.cy) < 12) {
      return {
        points: [[from.right, from.cy], [to.left, to.cy]],
        labelAt: [(from.right + to.left) / 2, from.cy - 9],
        anchor: "middle"
      };
    }
    if (from.key === "external") {
      return {
        points: [[to.cx, from.bottom], [to.cx, to.top]],
        labelAt: [to.cx + 6, to.top - 9]
      };
    }
    var goingDown = to.cy > from.cy;
    var startY = goingDown ? from.bottom : from.top;
    var endY = goingDown ? to.top : to.bottom;
    var midY = (startY + endY) / 2;
    return {
      points: [[from.cx, startY], [from.cx, midY], [to.cx, midY], [to.cx, endY]],
      labelAt: [from.cx + 6, midY - 9]
    };
  }

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
        hasData: Boolean((DATA.groups || []).length),
        groups: DATA.groups || [],
        relations: DATA.relations || [],
        imports: DATA.imports || EMPTY.imports,
        comparison: DATA.comparison || EMPTY.comparison,
        totals: DATA.totals || {},
        activeModule: "",
        depTab: "graph",
        docModule: "",
        theme: VizCharts.tokens()
      };
    },
    computed: {
      commitTitle: function () {
        var parts = [];
        if (this.commit) parts.push("commit " + this.commit);
        parts.push(this.dirty ? "工作区有未提交改动" : "工作区干净");
        return parts.join(" · ");
      },
      /* 按固定顺序排列的七个模块（含颜色、三次总量、逐文件趋势、柱状图 option） */
      modules: function () {
        var theme = this.theme;
        var comparison = this.comparison;
        var maxLoc = Math.max.apply(
          null,
          this.groups.map(function (group) {
            return Number(group.totals.loc || 0);
          }).concat([1])
        );
        var self = this;
        return MODULE_ORDER.map(function (key, index) {
          var group = null;
          self.groups.forEach(function (item) {
            if (item.key === key) group = item;
          });
          if (!group) return null;
          /* 七个模块的固定色，与架构图同色（tokens 里已登记） */
          var color = (theme.colors || {})[key] || (theme.palette || [])[index % 7];
          var values = (comparison.groups || {})[key] || [group.totals.loc, null, null];
          var files = group.files.map(function (file) {
            return {
              name: file.name,
              loc: file.loc,
              values: (file.trend || [file.loc, null, null]).concat([null, null]).slice(0, 3)
            };
          });
          return {
            key: key,
            label: group.label,
            note: group.note,
            color: color,
            /* 大数字渐变：深 → 浅两档（color-mix 在 background-clip:text 下绘制不稳，改成 hex） */
            agentsDoc: group.agentsDoc || "",
            deep: shadePair(color).deep,
            light: shadePair(color).light,
            loc: group.totals.loc,
            fileCount: group.totals.files,
            pct: Math.round((Number(group.totals.loc || 0) / maxLoc) * 100),
            values: values.concat([null, null]).slice(0, 3),
            files: files,
            chart: BoardOptions.fileTrendBar(files, theme, color, {
              labelOf: function (name) {
                return String(name || "").replace(/\.py$/, "");
              }
            }),
            height: "260px"
          };
        }).filter(Boolean);
      },
      comparisonAts: function () {
        return (this.comparison.at || []).filter(function (at) {
          return at;
        });
      },
      /* 架构图：节点 = 七个原语模块 + 一条「外部装配方」；边 = 生成器统计的 import（内外都算） */
      diagram: function () {
        var modules = this.modules;
        var theme = this.theme || {};
        var external = DATA.external || {};
        var nodes = modules.map(function (module) {
          var layout = DIAGRAM_LAYOUT[module.key] || { x: 0, y: 0, w: 240, h: 54, tilt: 0 };
          return {
            key: module.key,
            title: module.key + "：" + module.label,
            doc: Boolean(module.agentsDoc),
            color: module.color,
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

        /* 外部装配方：不在本包内，用虚线框和灰色区分；数字来自 external.total */
        var extLayout = DIAGRAM_LAYOUT.external;
        var extLayers = (external.layers || []).map(function (layer) {
          return layer.name;
        });
        nodes.push({
          key: "external",
          external: true,
          title:
            "外部装配方：" + (extLayers.join(" / ") || "无") + "（" + fmt(external.total || 0) + " 处引用）",
          doc: false,
          color: theme.secondary || "#96918c",
          x: extLayout.x,
          y: extLayout.y,
          w: extLayout.w,
          h: extLayout.h,
          tilt: extLayout.tilt,
          cx: extLayout.x + extLayout.w / 2,
          cy: extLayout.y + extLayout.h / 2,
          top: extLayout.y,
          bottom: extLayout.y + extLayout.h,
          left: extLayout.x,
          right: extLayout.x + extLayout.w
        });

        var byKey = {};
        nodes.forEach(function (node) {
          byKey[node.key] = node;
        });

        var pairs = [];
        (external.edges || []).forEach(function (row) {
          pairs.push({ from: "external", to: row.to, count: row.count });
        });
        (this.relations || []).forEach(function (row) {
          pairs.push({ from: row.from, to: row.to, count: row.count });
        });

        var edges = pairs
          .map(function (pair, index) {
            var from = byKey[pair.from];
            var to = byKey[pair.to];
            if (!from || !to) return null;
            var route = routeEdge(from, to);
            return {
              id: pair.from + "->" + pair.to + "-" + index,
              key: pair.from + "->" + pair.to + "-" + index,
              from: pair.from,
              to: pair.to,
              label: fmt(pair.count) + " 处引用",
              runtime: false,
              secondary: false,
              labelX: route.labelAt[0],
              labelY: route.labelAt[1],
              labelAnchor: route.anchor || "start",
              d: orthPath(route.points)
            };
          })
          .filter(Boolean);

        return { nodes: nodes, edges: edges, width: 1180, height: 460 };
      },
      /* 打开某个模块的 AGENTS.md */
      docGroup: function () {
        var key = this.docModule;
        var found = null;
        this.groups.forEach(function (group) {
          if (group.key === key) found = group;
        });
        return found;
      },
      docHtml: function () {
        var group = this.docGroup;
        return group ? renderMarkdown(group.agentsDoc || "") : "";
      },
      /* 点模块 → 与它相连的调用线全部变绿；再点同一个取消 */
      isEdgeActive: function () {
        var key = this.activeModule;
        return function (edge) {
          if (!key) return false;
          return edge.from === key || edge.to === key;
        };
      },
      /* 第 3 节：目录级依赖（跨模块引用清单） */
      depRows: function () {
        var rows = [];
        (this.imports.edges || []).forEach(function (edge) {
          /* 模块只有七个文件夹；根目录 __init__.py 不属于任何模块，别混进表里 */
          if (edge.from === "(根)" || edge.to === "(根)") return;
          rows.push({ from: edge.from, to: edge.to, count: edge.count });
        });
        rows.sort(function (a, b) {
          return b.count - a.count;
        });
        return rows;
      },
      /* 第 2 节：包外装配方一览（谁在 import 这些原语，带真实符号名） */
      externalRows: function () {
        return ((DATA.external || {}).edges || []).map(function (row) {
          return {
            to: row.to,
            count: row.count,
            symbols: row.label,
            layers: (row.layers || [])
              .map(function (layer) {
                return layer.name + " " + layer.count;
              })
              .join(" · ")
          };
        });
      },
      externalLayers: function () {
        return (DATA.external || {}).layers || [];
      },
      externalTotal: function () {
        return (DATA.external || {}).total || 0;
      },
      graphOption: function () {
        var theme = this.theme;
        var self = this;
        var nodes = this.modules.map(function (module) {
          return {
            key: module.key,
            label: module.key,
            fullLabel: module.key + " · " + module.label,
            modules: Math.max(1, module.fileCount),
            loc: module.loc,
            internal: Number((self.imports.internal || {})[module.key] || 0),
            color: module.color
          };
        });
        return BoardOptions.depGraph(nodes, this.imports.edges || [], theme, { labelPosition: "bottom" });
      }
    },
    mounted: function () {
      /* ESC 关闭文档弹层（弹层本身不可聚焦，监听挂在 window 上） */
      var self = this;
      this.onKeydownEsc = function (event) {
        if (event.key === "Escape" && self.docModule) self.docModule = "";
      };
      window.addEventListener("keydown", this.onKeydownEsc);
    },
    beforeUnmount: function () {
      window.removeEventListener("keydown", this.onKeydownEsc);
    },
    methods: {
      fmt: fmt,
      toggleModule: function (key) {
        this.activeModule = this.activeModule === key ? "" : key;
      },
      openDoc: function (key) {
        this.docModule = key;
      },
      closeDoc: function () {
        this.docModule = "";
      }
    }
  });

  VizCharts.register(app);
  app.mount("#app");
})();
