/**
 * 总览页（仓库一级目录）：平台架构 + 实际代码依赖 + 依赖/代码量 + 单元代码量。
 *
 * 两套本体，别混：
 *   1.1 平台架构 = 运行时组件与调用链，数据来自 data/architecture.js（源头是
 *       dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json，**人工语义**，不是 AST）。
 *   1.2 实际代码依赖 = 目录怎么切、谁 import 谁多少次，数据来自 data/board.js
 *       的 projectModules（gen_board_data.py 生成，AST 静态解析）。
 *
 * 口径见 tools/gen_board_data.py 的 collect_project_modules() 与 tools/gen_arch_data.py。
 */
(function () {
  "use strict";

  var DATA = (window.__BOARD__ || {}).projectModules || {};
  var MODULES = DATA.modules || [];
  var RELATIONS = DATA.relations || [];

  /* ── 1.2 实际代码依赖：目录层 ───────────────────────────────────────── */

  /* 分层架构图（viewBox 1180×540）：三行 = 三层，左槽写层名。
     行 y 固定 50 / 210 / 370，节点统一 240×88；列 x=200（左）/ 760（右），底座居中 480。
     坐标是排过的，不跑布局算法；改任何一个节点都要重新看一遍走廊（行间 72px）。
     口径：层（入口 / 服务 / 底座）按依赖方向**人工划分**，不是算出来的。 */
  var NODE_W = 240;
  var NODE_H = 88;
  var LAYOUT = {
    frontend: { x: 200, y: 50, tilt: 0.3 },
    tests: { x: 760, y: 50, tilt: -0.5 },
    backend: { x: 200, y: 210, tilt: -0.3 },
    engines: { x: 760, y: 210, tilt: 0.2 },
    utils: { x: 480, y: 370, tilt: -0.2 }
  };

  var LAYERS = [
    { key: "entry", label: "入口层", y: 50 },
    { key: "service", label: "服务层", y: 210 },
    { key: "base", label: "底座", y: 370 }
  ];

  /* 区域边界表达的是纪律，不是分组。已核实 engines/** 无 import django、无 backend.apps.*；
     框上只写「零 django 依赖」（短，避免被 tests→engines 的竖线穿过），
     apps.* 那半句在下方图例里写全。 */
  var BOUNDARY = { key: "engines", pad: 22, label: "engines/ · 零 django 依赖" };

  /* ── 1.1 平台架构：运行时组件 ───────────────────────────────────────── */

  /* 数据来自 data/architecture.js（window.__ARCH__），源头是已评审的
     dev_docs/ARCH_PRD/ARCH-平台架构图.spec.json —— **人工语义**，不是 AST 解析。
     页面只做「摆位置 + 画线」，不改写组件、连线、标签的任何内容。 */
  var ARCH = window.__ARCH__ || {};
  var ARCH_COMPONENTS = ARCH.components || [];
  var ARCH_CONNECTIONS = ARCH.connections || [];
  var ARCH_BOUNDARIES = ARCH.boundaries || [];
  var ARCH_CARDS = ARCH.cards || [];
  var ARCH_KIND_COUNTS = ARCH.kindCounts || {};

  var ARCH_W = 224;
  var ARCH_H = 88;
  var ARCH_CANVAS = { w: 1560, h: 600 };

  /* 三行：接入 / 服务与执行 / 外部；列 28/348/668/988/1308（节点 224 宽、间隙 96），行 60/260/460。
     间隙 96 是量出来的：最宽的行内标签 "axios · /api" / "create_agent" 各 84px，留 12px 呼吸。
     竖线靠同列对齐：api 与 runner、harness 与 llm、support 与 hardware 各在同一列。 */
  var ARCH_LAYOUT = {
    users: { x: 28, y: 60 },
    spa: { x: 348, y: 60 },
    asgi: { x: 668, y: 60 },
    api: { x: 988, y: 60 },
    db: { x: 1308, y: 60 },
    support: { x: 28, y: 260 },
    harness: { x: 348, y: 260 },
    bridge: { x: 668, y: 260 },
    runner: { x: 988, y: 260 },
    hardware: { x: 28, y: 460 },
    llm: { x: 348, y: 460 }
  };

  /* 语义类型 → 平台令牌（与 1.2 的模块色是两套，图例里写清楚） */
  var ARCH_KIND = {
    frontend: { label: "前端", color: "var(--c-element)" },
    backend: { label: "后端", color: "var(--c-device)" },
    database: { label: "数据库", color: "var(--c-tool)" },
    security: { label: "安全", color: "var(--c-runner)" },
    external: { label: "外部系统", color: "var(--app-text-secondary)" }
  };
  var ARCH_KIND_ORDER = ["frontend", "backend", "database", "security", "external"];

  /* 手绘微倾：只为不呆板，不承载信息 */
  var ARCH_TILT = {
    users: -0.3, spa: 0.2, asgi: -0.2, api: 0.3, db: -0.3,
    support: 0.2, harness: -0.3, bridge: 0.2, runner: -0.2,
    hardware: 0.3, llm: -0.2
  };

  /* ── 布线（1.2 用）：四种走法，端点只从节点边中点出入，拐角 8px 圆角 ── */

  /* 同列直上直下 */
  function routeVertical(from, to, spec) {
    var x = from.cx + (spec.dx || 0);
    return {
      points: [[x, from.bottom], [x, to.top]],
      label: {
        x: x + (spec.lx || 12),
        y: (from.bottom + to.top) / 2 + 4,
        anchor: spec.anchor || "start"
      }
    };
  }

  /* 出底边 → 行间走廊横走 → 落到目标顶边 */
  function routeHdrop(from, to, spec) {
    var sx = from.cx + (spec.sx || 0);
    var tx = to.cx + (spec.tx || 0);
    var laneY = from.bottom + (spec.lane || 32);
    /* 标签默认落在走廊线上方；走廊上方被边界框压住时用 labelBelow 翻到下方 */
    var labelY = spec.labelBelow ? laneY + 14 : laneY - 8;
    return {
      points: [[sx, from.bottom], [sx, laneY], [tx, laneY], [tx, to.top]],
      label: { x: (sx + tx) / 2, y: labelY, anchor: "middle" }
    };
  }

  /* 同层左右直连 */
  function routeZlr(from, to) {
    var y = from.cy;
    return {
      points: [[from.right, y], [to.left, y]],
      label: { x: (from.right + to.left) / 2, y: y - 8, anchor: "middle" }
    };
  }

  /* 从右侧出 → 走侧向走廊 → 从目标右边进（跨两层、不穿中间节点） */
  function routeSideWrap(from, to, spec) {
    var corridor = spec.corridor || to.right + 60;
    return {
      points: [
        [from.right, from.cy],
        [corridor, from.cy],
        [corridor, to.cy],
        [to.right, to.cy]
      ],
      label: { x: (to.right + corridor) / 2, y: to.cy - 8, anchor: "middle" }
    };
  }

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
        httpByApp: DATA.http ? DATA.http.byApp || [] : [],
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
            /* 1.2 节点卡第 2/3 行：全部来自本模块自己的快照数字，不跨页取数 */
            sub: (module.label ? module.label + " · " : "") + module.totals.units + " 个单元",
            meta: fmt(module.totals.files) + " 个 .py · " + fmt(module.totals.loc) + " 行",
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
            to: rel.shared ? "共享层" : rel.to,
            kind: rel.kind || "import",
            kindLabel: rel.kind === "http" ? "HTTP 调用" : "import",
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
        /* 用架构图的同一套分层坐标：circular 在 5 个节点时会排歪 */
        var positions = {};
        this.rows.forEach(function (row) {
          var layout = LAYOUT[row.key];
          if (layout) positions[row.key] = [layout.x + NODE_W / 2, layout.y + NODE_H / 2];
        });
        var links = this.relations.map(function (rel) {
          /* 数据流方向：被调用方 → 调用方 */
          return { from: rel.to, to: rel.from, count: rel.count };
        });
        return BoardOptions.depGraph(nodes, links, this.theme, {
          labelPosition: "bottom",
          positions: positions
        });
      },
      /* 1.2 层名槽：层是人工划分的结构，写在图左侧 */
      layers: function () {
        return LAYERS.map(function (layer) {
          return { key: layer.key, label: layer.label, cy: layer.y + NODE_H / 2 };
        });
      },
      /* 1.2 区域边界：包住目标节点，pad 22 */
      boundary: function () {
        var layout = LAYOUT[BOUNDARY.key];
        var exists = this.rows.some(function (row) {
          return row.key === BOUNDARY.key;
        });
        if (!layout || !exists) return null;
        return {
          x: layout.x - BOUNDARY.pad,
          y: layout.y - BOUNDARY.pad,
          w: NODE_W + BOUNDARY.pad * 2,
          h: NODE_H + BOUNDARY.pad * 2,
          label: BOUNDARY.label
        };
      },
      /* 1.1 平台架构：摆位置 + 直连（同行横线、跨行竖线），不自造折线 */
      platform: function () {
        var nodes = ARCH_COMPONENTS.map(function (comp) {
          var layout = ARCH_LAYOUT[comp.id] || { x: 0, y: 0 };
          var kind = ARCH_KIND[comp.type] || ARCH_KIND.external;
          return {
            id: comp.id,
            title: comp.label,
            sub: comp.sublabel,
            tag: comp.tag,
            kind: comp.type,
            color: kind.color,
            x: layout.x,
            y: layout.y,
            w: ARCH_W,
            h: ARCH_H,
            tilt: ARCH_TILT[comp.id] || 0,
            cx: layout.x + ARCH_W / 2,
            cy: layout.y + ARCH_H / 2,
            top: layout.y,
            bottom: layout.y + ARCH_H,
            left: layout.x,
            right: layout.x + ARCH_W
          };
        });
        var byId = {};
        nodes.forEach(function (node) {
          byId[node.id] = node;
        });

        var edges = [];
        ARCH_CONNECTIONS.forEach(function (conn, index) {
          var from = byId[conn.from];
          var to = byId[conn.to];
          if (!from || !to) return;
          var points;
          var label;
          if (from.cy === to.cy) {
            /* 同一行：右出左进 / 左出右进 */
            var rightward = to.cx > from.cx;
            points = [
              [rightward ? from.right : from.left, from.cy],
              [rightward ? to.left : to.right, from.cy]
            ];
            label = { x: (points[0][0] + points[1][0]) / 2, y: from.cy - 8, anchor: "middle" };
          } else {
            /* 跨行：从底边落到顶边（或反向） */
            var down = to.cy > from.cy;
            points = [
              [from.cx, down ? from.bottom : from.top],
              [to.cx, down ? to.top : to.bottom]
            ];
            label = { x: from.cx + 12, y: (points[0][1] + points[1][1]) / 2 + 4, anchor: "start" };
          }
          edges.push({
            key: conn.id + "-" + index,
            from: conn.from,
            to: conn.to,
            label: conn.label,
            labelX: label.x,
            labelY: label.y,
            labelAnchor: label.anchor,
            d: "M " + points[0][0] + " " + points[0][1] + " L " + points[1][0] + " " + points[1][1]
          });
        });

        /* 边界 = 成员的 padding 盒（spec 只给 wraps，坐标由成员算出来） */
        var boundaries = [];
        ARCH_BOUNDARIES.forEach(function (box) {
          var members = box.wraps
            .map(function (id) {
              return byId[id];
            })
            .filter(Boolean);
          if (!members.length) return;
          var left = Math.min.apply(null, members.map(function (m) { return m.left; }));
          var top = Math.min.apply(null, members.map(function (m) { return m.top; }));
          var right = Math.max.apply(null, members.map(function (m) { return m.right; }));
          var bottom = Math.max.apply(null, members.map(function (m) { return m.bottom; }));
          boundaries.push({
            key: box.label + "-" + top,
            label: box.label,
            x: left - box.pad,
            y: top - box.pad,
            w: right - left + box.pad * 2,
            h: bottom - top + box.pad * 2
          });
        });

        return {
          nodes: nodes,
          edges: edges,
          boundaries: boundaries,
          width: ARCH_CANVAS.w,
          height: ARCH_CANVAS.h
        };
      },
      platformLegend: function () {
        return ARCH_KIND_ORDER.filter(function (key) {
          return ARCH_KIND_COUNTS[key];
        }).map(function (key) {
          return {
            key: key,
            label: ARCH_KIND[key].label,
            count: ARCH_KIND_COUNTS[key],
            color: ARCH_KIND[key].color
          };
        });
      },
      platformCards: function () {
        return ARCH_CARDS;
      },
      /* 1.2 实际代码依赖图 */
      diagram: function () {
        var nodes = this.rows.map(function (row) {
          var layout = LAYOUT[row.key] || { x: 0, y: 0, tilt: 0 };
          return {
            key: row.key,
            title: row.key,
            sub: row.sub,
            meta: row.meta,
            color: row.color,
            x: layout.x,
            y: layout.y,
            w: NODE_W,
            h: NODE_H,
            tilt: layout.tilt,
            cx: layout.x + NODE_W / 2,
            cy: layout.y + NODE_H / 2,
            top: layout.y,
            bottom: layout.y + NODE_H,
            left: layout.x,
            right: layout.x + NODE_W
          };
        });
        var byKey = {};
        nodes.forEach(function (node) {
          byKey[node.key] = node;
        });

        /* 双向引用合并成一条边，标签写两个次数；HTTP 是另一类关系，不并进 import 合并 */
        var merged = {};
        this.relations.forEach(function (rel) {
          var pair = rel.kind === "http"
            ? "http:" + rel.from + "->" + rel.to
            : [rel.from, rel.to].sort().join("|");
          if (!merged[pair]) {
            merged[pair] = { from: rel.from, to: rel.to, count: rel.count, reverse: null, kind: rel.kind || "import" };
          } else if (merged[pair].from === rel.to) {
            merged[pair].reverse = rel.count;
          } else {
            merged[pair].count += rel.count;
          }
        });

        /* 每条边的走法（表驱动）：端点只从节点边中点出入，偏移量相对节点中心算 */
        var ROUTES = {
          "frontend->backend": { route: routeVertical, dx: -40, lx: -12, anchor: "end" },
          "tests->backend": { route: routeHdrop, sx: -60, tx: 40, lane: 40 },
          "tests->engines": { route: routeVertical, dx: 60 },
          "backend->engines": { route: routeZlr },
          "backend->utils": { route: routeHdrop, sx: 40, tx: -60, lane: 42 },
          "engines->utils": { route: routeHdrop, sx: 0, tx: 60, lane: 42, labelBelow: true },
          "tests->utils": { route: routeSideWrap, corridor: 1060 }
        };

        var edges = [];
        Object.keys(merged).forEach(function (pair, index) {
          var rel = merged[pair];
          var from = byKey[rel.from];
          var to = byKey[rel.to];
          if (!from || !to) return;
          var spec = ROUTES[rel.from + "->" + rel.to] || { route: routeHdrop, sx: 0, tx: 0, lane: 32 };
          var routed = spec.route(from, to, spec);
          edges.push({
            key: pair + "-" + index,
            from: rel.from,
            to: rel.to,
            kind: rel.kind || "import",
            label: rel.reverse
              ? rel.count + " / " + rel.reverse + " 次"
              : rel.count + (rel.kind === "http" ? " 处" : " 次"),
            labelX: routed.label.x,
            labelY: routed.label.y,
            labelAnchor: routed.label.anchor,
            d: orthPath(routed.points)
          });
        });

        return { nodes: nodes, edges: edges, width: 1180, height: 540 };
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
