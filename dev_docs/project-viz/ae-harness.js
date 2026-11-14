/*
 * ae_harness 页：六个模块（根目录文件夹）的架构、代码量、依赖与逐文件对比。
 *
 * 数据来源：window.__BOARD__.ae_harness（生成器产出）
 *   1. 架构：模块关系（人工定义，见 DIAGRAM_EDGES）
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

  /* 模块 = ae_harness 根目录的六个文件夹，顺序固定（与页面第 2/3 节一致） */
  var MODULE_ORDER = ["agents", "tools", "assistant", "workflow", "event", "middleware"];

  /* 架构图坐标（viewBox 1180×580）
     布局目标：创建链路顺流不交叉 —— 左上 agents、左中 tools，左下 assistant，右上 workflow，底部 event */
  var DIAGRAM_LAYOUT = {
    /* 节点位置固定（viewBox 1180×600）：上 agents、左中 tools、左下 assistant、右中 workflow、
       底部 event 与 middleware 并排（两者都是"被调用的支撑件"） */
    agents: { x: 620, y: 60, w: 240, h: 54, tilt: -0.5 },
    tools: { x: 90, y: 215, w: 240, h: 54, tilt: 0.5 },
    assistant: { x: 300, y: 380, w: 240, h: 54, tilt: -0.3 },
    workflow: { x: 830, y: 180, w: 240, h: 54, tilt: 0.4 },
    event: { x: 620, y: 500, w: 240, h: 54, tilt: -0.4 },
    middleware: { x: 300, y: 500, w: 240, h: 54, tilt: -0.2 }
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

  /* 正交布线（参考 archify 的自动路由原则）：
     一条主路径、直角折线、端口从节点边中点出、标签贴线段、跨线处画 6px 跳桥。
     points = 折线拐点（绝对坐标）；bridge = {seg: 第几段, at: 交叉坐标轴向位置} */
  var DIAGRAM_EDGES = [
    /* 创建 assistant：tools 从左边进、agents 从右边进 */
    { id: "tools->assistant", from: "tools", to: "assistant", label: "build_adb_tools()",
      points: [[210, 269], [210, 330], [390, 330], [390, 380]], labelAt: [300, 316] },
    { id: "agents->assistant", from: "agents", to: "assistant", label: "create_agent()",
      points: [[620, 87], [470, 87], [470, 380]], labelAt: [545, 73] },
    /* assistant 组装成工作流 */
    { id: "assistant->workflow", from: "assistant", to: "workflow", label: "run_sop() + _bootstrap",
      points: [[540, 407], [780, 407], [780, 207], [830, 207]], labelAt: [768, 300], labelAnchor: "end" },
    /* workflow 自己也用 agents / tools：各走一条上弧 */
    { id: "agents->workflow", from: "agents", to: "workflow", label: "create_agent() ×2",
      points: [[740, 60], [740, 40], [950, 40], [950, 180]], labelAt: [850, 26], secondary: true },
    { id: "tools->workflow", from: "tools", to: "workflow", label: "build_*_tools()",
      points: [[210, 215], [210, 150], [830, 150], [830, 197]],
      labelAt: [520, 136], bridge: { seg: 1, axis: "x", at: 470 }, secondary: true },
    /* 观测中间件：assistant / workflow 各注入一次（只读观测） */
    { id: "assistant->middleware", from: "assistant", to: "middleware", label: "ObservationMiddleware",
      points: [[360, 434], [360, 500]], labelAt: [372, 476], labelAnchor: "start" },
    { id: "workflow->middleware", from: "workflow", to: "middleware", label: "ObservationMiddleware",
      points: [[950, 234], [950, 480], [570, 480], [570, 500]], labelAt: [760, 466], secondary: true },
    /* 运行阶段：向下汇到 event */
    { id: "assistant->event", from: "assistant", to: "event", label: "AgentEventRecorder",
      points: [[480, 434], [480, 460], [700, 460], [700, 500]], labelAt: [600, 446], runtime: true },
    { id: "workflow->event", from: "workflow", to: "event", label: "HtmlReportRenderer",
      points: [[860, 234], [860, 440], [760, 440], [760, 500]], labelAt: [812, 426], runtime: true }
  ];

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
      /* 按固定顺序排列的六个模块（含颜色、三次总量、逐文件趋势、柱状图 option） */
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
          /* 六个模块的固定色，与架构图同色（tokens 里已登记） */
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
      /* 架构图：节点 = 六个模块；边 = 正交折线（谁在用谁） */
      diagram: function () {
        var modules = this.modules;
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
            bottom: layout.y + layout.h
          };
        });

        var edges = DIAGRAM_EDGES.map(function (edge) {
          return {
            id: edge.id,
            key: edge.id,
            from: edge.from,
            to: edge.to,
            label: edge.label,
            runtime: Boolean(edge.runtime),
            secondary: Boolean(edge.secondary),
            labelX: edge.labelAt[0],
            labelY: edge.labelAt[1],
            labelAnchor: edge.labelAnchor || "middle",
            d: orthPath(edge.points, edge.bridge)
          };
        });

        return { nodes: nodes, edges: edges, width: 1180, height: 600 };
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
          /* 模块只有六个文件夹；根目录 __init__.py 不属于任何模块，别混进表里 */
          if (edge.from === "(根)" || edge.to === "(根)") return;
          rows.push({ from: edge.from, to: edge.to, count: edge.count });
        });
        rows.sort(function (a, b) {
          return b.count - a.count;
        });
        return rows;
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
