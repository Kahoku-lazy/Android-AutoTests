/*
 * 项目看板的图表配置（纯函数：给数据 → 返回 ECharts option，不碰 DOM、不建实例）
 *
 * 这样拆分的原因：option 能单测、能被别的页面复用；实例生命周期统一交给
 * charts/chart-framework.js 的 <viz-chart>，本文件不出现 echarts.init。
 *
 * 三个图各司其职：
 *   totalsBar()  总量信息（6 项指标，对数横轴 —— 量级差太大，线性轴会把小值压成一条线）
 *   donut()      代码行占比（按分类；筛选时高亮选中，不隐藏）
 *   bar()        分层明细（每个模块一条，受分类筛选影响）
 */
(function () {
  "use strict";

  var METRICS = [
    { key: "features", label: "功能" },
    { key: "files", label: "文件" },
    { key: "classes", label: "类" },
    { key: "methods", label: "方法" },
    { key: "loc", label: "代码行" }
  ];

  /* 总量卡片用的指标：多一个"模块"（分类下的模块个数） */
  var TOTALS_METRICS = [
    { key: "modules", label: "模块" },
    { key: "features", label: "功能" },
    { key: "files", label: "文件" },
    { key: "classes", label: "类" },
    { key: "methods", label: "方法" },
    { key: "loc", label: "代码行" }
  ];

  function fmt(value) {
    return Number(value || 0).toLocaleString("zh-CN");
  }

  /* 坐标轴放不下长名：截断显示，完整名走 tooltip */
  function shortName(name) {
    var text = String(name || "");
    return text.length > 16 ? text.slice(0, 15) + "…" : text;
  }

  function visibleCategories(board, active) {
    var all = board.categories || [];
    if (!active || active === "all") return all;
    return all.filter(function (category) {
      return category.key === active;
    });
  }

  /** 当前筛选范围的合计：全部分类相加，或单个分类自己的小计。 */
  function scopeTotals(board, active) {
    var categories = visibleCategories(board, active);
    var totals = { modules: 0, features: 0, files: 0, classes: 0, methods: 0, loc: 0 };
    categories.forEach(function (category) {
      totals.modules += category.modules.length;
      Object.keys(category.totals || {}).forEach(function (key) {
        totals[key] += Number(category.totals[key] || 0);
      });
    });
    return totals;
  }

  function scopeLabel(board, active) {
    var categories = visibleCategories(board, active);
    if (!active || active === "all") return "全仓合计";
    return categories.length ? categories[0].label : active;
  }

  /** 总量信息：6 项指标横向条形，对数刻度（量级差大），标签给真实值。 */
  function totalsBar(board, theme, active) {
    var totals = scopeTotals(board, active);
    var rows = TOTALS_METRICS.map(function (metric) {
      return { label: metric.label, value: Number(totals[metric.key] || 0) };
    }).reverse(); /* 反序：模块排在最上面 */

    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          return scopeLabel(board, active) + " · " + param.name + "：" + fmt(param.value);
        }
      },
      xAxis: {
        type: "log",
        logBase: 10,
        min: 1,
        axisLine: { show: false },
        axisTick: { show: false },
        minorSplitLine: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.18 } },
        axisLabel: {
          color: theme.secondary,
          fontFamily: theme.font,
          fontSize: theme.fontSize,
          formatter: function (value) {
            return fmt(value);
          }
        }
      },
      yAxis: {
        type: "category",
        data: rows.map(function (row) {
          return row.label;
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 16,
          emphasis: { focus: "none" },
          label: {
            show: true,
            position: "right",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: theme.fontSize,
            formatter: function (param) {
              return fmt(param.value);
            }
          },
          itemStyle: {
            color: theme.accent,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [0, 2, 2, 0]
          },
          data: rows.map(function (row) {
            return { value: row.value, name: row.label };
          })
        }
      ]
    };
  }

  /** 五张明细图共用的行顺序：按代码行降序，同值再按方法数、最后按名字。 */
  function moduleOrder(board, active) {
    var rows = [];
    visibleCategories(board, active).forEach(function (category) {
      category.modules.forEach(function (module) {
        rows.push({
          name: module.name,
          loc: Number(module.loc || 0),
          methods: Number(module.methods || 0)
        });
      });
    });
    rows.sort(function (a, b) {
      if (b.loc !== a.loc) return b.loc - a.loc;
      if (b.methods !== a.methods) return b.methods - a.methods;
      return a.name < b.name ? -1 : a.name > b.name ? 1 : 0;
    });
    return rows.map(function (row) {
      return row.name;
    });
  }

  /** 引擎/agents 的模块分布：按目录（tools / workflow / …）的代码行，附模块数与功能条目数。 */
  function agentsBar(agents, theme) {
    var groups = (agents && agents.groups) || [];
    var rows = groups.slice(); /* 生成器已按代码行降序、根级放最后 */
    /* 这份图只有 9 行且整行宽，标签可以给长一点 */
    var axisName = function (label) {
      var text = String(label || "");
      return text.length > 26 ? text.slice(0, 25) + "…" : text;
    };
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 64, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          var data = param.data || {};
          return [
            (data.fullLabel || param.name).replace(/\n/g, " "),
            "模块 " + fmt(data.modules) + " 个 · 功能条目 " + fmt(data.features) + " 条",
            "代码行 " + fmt(param.value)
          ].join("\n");
        }
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.18 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rows.map(function (group) {
          return axisName(group.label);
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 16,
          emphasis: { focus: "none" },
          label: {
            show: true,
            position: "right",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: theme.fontSize,
            formatter: function (param) {
              return fmt(param.value) + " 行 / " + fmt(param.data.modules) + " 模块";
            }
          },
          itemStyle: {
            color: theme.colors.engine,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [0, 2, 2, 0]
          },
          data: rows.map(function (group) {
            return {
              value: Number((group.totals || {}).loc || 0),
              name: axisName(group.label),
              fullLabel: group.label,
              modules: Number((group.totals || {}).modules || 0),
              features: Number((group.totals || {}).features || 0)
            };
          })
        }
      ]
    };
  }

  /** 引擎/agents 的目录级依赖图：节点=目录，边=跨目录 import 次数（环形布局，避免力导向抖动）。 */
  /** 引擎/agents 的目录级依赖图（复用通用 depGraph）。 */
  function agentsGraph(agents, theme) {
    var groups = (agents && agents.groups) || [];
    var imports = (agents && agents.imports) || {};
    var internal = imports.internal || {};
    var nodes = groups.map(function (group) {
      var shortLabel = String(group.label).split(" · ")[0].split("（")[0];
      return {
        key: group.key,
        label: shortLabel,
        fullLabel: group.label,
        modules: Number((group.totals || {}).modules || 0),
        loc: Number((group.totals || {}).loc || 0),
        internal: Number(internal[group.key] || 0),
        color: theme.colors.engine
      };
    });
    return depGraph(nodes, imports.edges || [], theme);
  }

  /** 历史趋势：agents 模块量的折线（只有 ≥2 个快照才有意义）。 */
  /** 历史趋势：某一层（frontend / backend / engine / agents）的代码行折线。 */
  function historyLine(history, catKey, theme) {
    var rows = (history || [])
      .map(function (entry) {
        var slice = entry[catKey] || {};
        return {
          at: entry.at,
          modules: Number(slice.modules || 0),
          features: Number(slice.features || 0),
          classes: Number(slice.classes || 0),
          methods: Number(slice.methods || 0),
          tests: Number(slice.tests || 0),
          loc: Number(slice.loc || 0)
        };
      })
      .filter(function (row) {
        return row.at;
      });
    return {
      animation: !theme.reduceMotion,
      animationDuration: 200,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 24, top: 24, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "axis",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (params) {
          var row = rows[params[0].dataIndex] || {};
          return [
            row.at,
            "代码行 " + fmt(row.loc),
            "模块 " + fmt(row.modules) + " · 功能 " + fmt(row.features),
            "类 " + fmt(row.classes) + " · 方法 " + fmt(row.methods)
          ].join("\\n");
        }
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: rows.map(function (row) {
          return row.at;
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.18 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      series: [
        {
          type: "line",
          name: "代码行",
          smooth: false,
          symbolSize: 8,
          data: rows.map(function (row) {
            return row.loc;
          }),
          itemStyle: { color: theme.accent, borderColor: theme.ink, borderWidth: 1 },
          lineStyle: { color: theme.accent, width: 2.5 },
          areaStyle: { color: theme.accent, opacity: 0.12 },
          label: {
            show: true,
            position: "top",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: theme.fontSize,
            formatter: function (param) {
              return fmt(param.value);
            }
          }
        }
      ]
    };
  }

  /** 引擎页历史趋势（agents 层）。 */
  function agentsHistory(history, theme) {
    return historyLine(history, "agents", theme);
  }

  /** 通用有向依赖图：节点=模块/目录，边=import 次数（环形布局，避免力导向抖动）。 */
  function depGraph(nodes, edges, theme, opts) {
    var shortOf = {};
    var positions = (opts && opts.positions) || null;
    var data = nodes.map(function (node) {
      shortOf[node.key] = node.label;
      var anchor = positions ? positions[node.key] : null;
      return {
        name: node.label,
        key: node.key,
        fullLabel: node.fullLabel || node.label,
        value: Number(node.modules || 0),
        modules: Number(node.modules || 0),
        loc: Number(node.loc || 0),
        internal: Number(node.internal || 0),
        symbolSize: 22 + Math.min(20, Number(node.modules || 0)),
        x: anchor ? anchor[0] : undefined,
        y: anchor ? anchor[1] : undefined,
        itemStyle: {
          color: node.color || theme.colors.engine,
          borderColor: theme.ink,
          borderWidth: 2
        }
      };
    });

    var links = edges
      .filter(function (edge) {
        return shortOf[edge.from] && shortOf[edge.to];
      })
      .map(function (edge) {
        return {
          source: shortOf[edge.from],
          target: shortOf[edge.to],
          value: Number(edge.count || 0),
          lineStyle: {
            width: Math.min(4, 0.8 + Number(edge.count || 0) * 0.12),
            color: theme.ink,
            opacity: 0.45,
            curveness: 0.12
          }
        };
      });

    return {
      animation: !theme.reduceMotion,
      animationDuration: 200,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      tooltip: {
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          if (param.dataType === "edge") {
            return (
              param.data.source + " → " + param.data.target +
              "：跨层 import " + fmt(param.data.value) + " 次"
            );
          }
          var node = param.data || {};
          return [
            node.fullLabel || param.name,
            "模块 " + fmt(node.modules) + " 个 · 代码行 " + fmt(node.loc),
            "内部互相 import " + fmt(node.internal) + " 次"
          ].join("\n");
        }
      },
      series: [
        {
          type: "graph",
          layout: positions ? "none" : "circular",
          roam: true,
          symbol: "roundRect",
          label: {
            show: true,
            position: (opts && opts.labelPosition) || "right",
            distance: 10,
            color: theme.ink,
            fontFamily: theme.font,
            fontSize: theme.fontSize
          },
          edgeSymbol: ["none", "arrow"],
          edgeSymbolSize: [0, 8],
          emphasis: { focus: "adjacency" },
          data: data,
          links: links
        }
      ]
    };
  }

  /**
   * 单层（前端模块 / 后端 App / ae_harness 文件）总览：按代码行的横向条形。
   *
   * @param rows 每行 {name, loc, files, features, classes, methods}
   * @param theme VizCharts.tokens()
   * @param colorKey theme.colors 里的名字，未给 colorOf 时整组同色
   * @param colorOf 可选 (row) => 颜色串；给了就逐条着色（用于按模块分组上色）
   */
  function moduleBar(rows, theme, colorKey, colorOf) {
    var list = rows.slice().sort(function (a, b) {
      return Number(b.loc || 0) - Number(a.loc || 0);
    });
    var baseColor = theme.colors[colorKey] || theme.accent;
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 72, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          var row = param.data.row || {};
          /* row.meta：调用方自己给的一句话说明（如分组 + 类/方法数），有就优先用 */
          if (row.meta) return row.name + "\n" + row.meta;
          return [
            row.name,
            "代码行 " + fmt(row.loc) + " · 文件 " + fmt(row.files),
            "功能 " + fmt(row.features) + " · 类 " + fmt(row.classes) + " · 方法 " + fmt(row.methods)
          ].join("\n");
        }
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.18 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: list.map(function (row) {
          return shortName(row.name);
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 16,
          emphasis: { focus: "none" },
          label: {
            show: true,
            position: "right",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: theme.fontSize,
            formatter: function (param) {
              return fmt(param.value) + " 行";
            }
          },
          itemStyle: {
            color: baseColor,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [0, 2, 2, 0]
          },
          data: list.map(function (row) {
            var color = colorOf ? colorOf(row) : baseColor;
            return {
              value: Number(row.loc || 0),
              name: shortName(row.name),
              row: row,
              itemStyle: {
                color: color || baseColor,
                borderColor: theme.ink,
                borderWidth: 1,
                borderRadius: [0, 2, 2, 0]
              }
            };
          })
        }
      ]
    };
  }

  /**
   * 迷你三点折线：某个模块最近几次的代码量（点少于 2 个时页面不要画，走空态）。
   *
   * @param points [{label, value}]，value 为 null 的已由调用方过滤
   */
  function miniLine(points, theme, color) {
    var rows = (points || []).filter(function (point) {
      return point.value !== null && point.value !== undefined;
    });
    return {
      animation: !theme.reduceMotion,
      animationDuration: 160,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 4, right: 12, top: 22, bottom: 4, containLabel: true },
      tooltip: {
        trigger: "axis",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (params) {
          var point = rows[params[0].dataIndex] || {};
          return (point.label || "") + "\n代码行 " + fmt(point.value);
        }
      },
      xAxis: {
        type: "category",
        boundaryGap: false,
        data: rows.map(function (point) {
          return point.label;
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1 } },
        axisTick: { show: false },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 10 }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.15 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 10 }
      },
      series: [
        {
          type: "line",
          smooth: false,
          symbolSize: 6,
          data: rows.map(function (point) {
            return point.value;
          }),
          itemStyle: { color: color, borderColor: theme.ink, borderWidth: 1 },
          lineStyle: { color: color, width: 2 },
          areaStyle: { color: color, opacity: 0.14 },
          label: {
            show: true,
            position: "top",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: 10,
            formatter: function (param) {
              return fmt(param.value);
            }
          }
        }
      ]
    };
  }

  /**
   * 迷你柱状图：竖向柱（X 轴水平放类目，Y 轴垂直放数值）。
   *
   * @param items [{label, value}]
   * @param opts  {rotateLabels: number} 类目名较长时倾斜角度
   */
  function miniBar(items, theme, color, opts) {
    var rows = items || [];
    var rotate = opts && opts.rotateLabels ? opts.rotateLabels : 0;
    return {
      animation: !theme.reduceMotion,
      animationDuration: 160,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 4, right: 18, top: 24, bottom: rotate ? 8 : 4, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          var row = rows[param.dataIndex] || {};
          return (row.label || "") + "\n代码行 " + fmt(row.value);
        }
      },
      xAxis: {
        type: "category",
        data: rows.map(function (row) {
          return row.label;
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1 } },
        axisTick: { show: false },
        axisLabel: {
          color: theme.secondary,
          fontFamily: theme.font,
          fontSize: 10,
          rotate: rotate,
          interval: 0
        }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.15 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 10 }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 44,
          itemStyle: { color: color, borderColor: theme.ink, borderWidth: 1, borderRadius: [2, 2, 0, 0] },
          label: {
            show: true,
            position: "top",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: 10,
            formatter: function (param) {
              return fmt(param.value);
            }
          },
          data: rows.map(function (row) {
            return row.value;
          })
        }
      ]
    };
  }

  /**
   * 文件级三次代码量：一个文件一组柱（本次 / 最近一次 / 最近两次）。
   *
   * @param items [{name, values: [n1, n2, n3]}]，缺的值为 null（不补 0，图上就不画那根）
   */
  /**
   * 模块内一层单元（子目录 / 单文件）的代码行数：横向条形，单元多时也能读。
   *
   * @param units  [{ name, kind, loc }]
   * @param theme  令牌
   * @param color  该模块的主色
   */
  /**
   * 模块内一层单元（子目录 / 单文件）的代码行数：竖柱状，与 ae_harness 页一致。
   *
   * @param units  [{ name, kind, loc }]
   * @param theme  令牌
   * @param color  该模块的主色
   */
  /**
   * 模块内一层单元的「最近三次」代码行数：三组竖柱（本次 / 最近一次 / 最近两次）。
   *
   * @param units  [{ name, trend: [n, n-1, n-2] }]
   * @param theme  令牌
   * @param color  该模块的主色
   */
  /**
   * 模块代码量占比：环形饼图 + 右侧图例。
   *
   * @param rows  [{ key, loc, color }]
   * @param theme 令牌
   */
  function modulePie(rows, theme) {
    var items = (rows || []).filter(function (row) {
      return Number(row.loc || 0) > 0;
    });
    var total = items.reduce(function (sum, row) {
      return sum + Number(row.loc || 0);
    }, 0);
    return {
      animation: !theme.reduceMotion,
      animationDuration: 220,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          var pct = total ? ((param.value / total) * 100).toFixed(1) : "0";
          return param.name + "：" + fmt(param.value) + " 行（" + pct + "%）";
        }
      },
      legend: {
        type: "scroll",
        orient: "vertical",
        right: 0,
        top: "middle",
        itemWidth: 10,
        itemHeight: 10,
        itemGap: 8,
        textStyle: { color: theme.stat, fontFamily: theme.font, fontSize: 11 },
        formatter: function (name) {
          var row = null;
          items.forEach(function (item) {
            if (item.key === name) row = item;
          });
          return row ? name + "  " + fmt(row.loc) : name;
        }
      },
      series: [
        {
          type: "pie",
          radius: ["20.4%", "68%"],
          center: ["34%", "50%"],
          avoidLabelOverlap: true,
          label: { show: false },
          labelLine: { show: false },
          itemStyle: { borderColor: theme.ink, borderWidth: 1.5 },
          emphasis: { scale: true, scaleSize: 6 },
          data: items.map(function (row) {
            return { name: row.key, value: Number(row.loc || 0), itemStyle: { color: row.color } };
          })
        }
      ]
    };
  }

  function unitTrendColumn(units, theme, color) {
    var rows = (units || []).slice();
    var seriesNames = ["本次", "最近一次", "最近两次"];
    var alphas = ["", "99", "4D"];
    var active = seriesNames
      .map(function (name, index) {
        return { name: name, index: index };
      })
      .filter(function (item) {
        return rows.some(function (row) {
          var value = (row.trend || [])[item.index];
          return value !== null && value !== undefined;
        });
      });
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 12, top: 36, bottom: 6, containLabel: true },
      legend: {
        top: 0,
        right: 0,
        itemWidth: 12,
        itemHeight: 10,
        textStyle: { color: theme.stat, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (params) {
          var lines = [params[0].name];
          params.forEach(function (item) {
            if (item.value === null || item.value === undefined) return;
            lines.push(item.seriesName + "：" + fmt(item.value) + " 行");
          });
          return lines.join("\n");
        }
      },
      xAxis: {
        type: "category",
        data: rows.map(function (row) {
          return String(row.name || "").replace(/\/$/, "");
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: {
          color: theme.secondary,
          fontFamily: theme.font,
          fontSize: 9,
          rotate: 45,
          interval: 0,
          width: 88,
          overflow: "truncate"
        }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.16 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 11 }
      },
      series: active.map(function (item) {
        return {
          name: item.name,
          type: "bar",
          barMaxWidth: 16,
          itemStyle: {
            color: color + alphas[item.index],
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [2, 2, 0, 0]
          },
          emphasis: { focus: "none" },
          data: rows.map(function (row) {
            var value = (row.trend || [])[item.index];
            return value === null || value === undefined ? null : Number(value);
          })
        };
      })
    };
  }

  function unitColumn(units, theme, color) {
    var rows = (units || []).slice();
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 12, top: 28, bottom: 6, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          return param.name + "：" + fmt(param.value) + " 行";
        }
      },
      xAxis: {
        type: "category",
        data: rows.map(function (row) {
          return String(row.name || "").replace(/\/$/, "");
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: {
          color: theme.secondary,
          fontFamily: theme.font,
          fontSize: 9,
          rotate: 45,
          interval: 0,
          width: 88,
          overflow: "truncate"
        }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.16 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 11 }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 22,
          itemStyle: {
            color: color,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [2, 2, 0, 0]
          },
          emphasis: { focus: "none" },
          /* 单元多时柱顶数字会互相压，超过 10 个就只留 tooltip */
          label: {
            show: rows.length <= 10,
            position: "top",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: 9,
            formatter: function (param) {
              return fmt(param.value);
            }
          },
          data: rows.map(function (row) {
            return Number(row.loc || 0);
          })
        }
      ]
    };
  }

  function unitBar(units, theme, color) {
    var rows = (units || []).slice();
    var maxLoc = Math.max.apply(
      null,
      rows.map(function (row) {
        return Number(row.loc || 0);
      }).concat([1])
    );
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 56, top: 8, bottom: 8, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          return param.name + "：" + fmt(param.value) + " 行";
        }
      },
      xAxis: {
        type: "value",
        max: maxLoc,
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.14 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 11 }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rows.map(function (row) {
          return row.name;
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: {
          color: theme.ink,
          fontFamily: theme.font,
          fontSize: 11,
          width: 150,
          overflow: "truncate"
        }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 14,
          itemStyle: {
            color: color,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [0, 2, 2, 0]
          },
          emphasis: { focus: "none" },
          label: {
            show: true,
            position: "right",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: 11,
            formatter: function (param) {
              return fmt(param.value);
            }
          },
          data: rows.map(function (row) {
            return Number(row.loc || 0);
          })
        }
      ]
    };
  }

  function fileTrendBar(items, theme, color, opts) {
    var rows = items || [];
    var seriesNames = ["本次", "最近一次", "最近两次"];
    /* 三次用同色不同透明度：越早越淡，一眼能分清先后 */
    var alphas = ["", "99", "4D"];
    /* 整列都没有数据的 series 不渲染（否则图例里会出现一个空系列，像有数据却没画） */
    var active = seriesNames
      .map(function (name, index) {
        return { name: name, index: index };
      })
      .filter(function (item) {
        return rows.some(function (row) {
          var value = (row.values || [])[item.index];
          return value !== null && value !== undefined;
        });
      });
    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 16, top: 36, bottom: 8, containLabel: true },
      legend: {
        top: 0,
        right: 0,
        itemWidth: 12,
        itemHeight: 10,
        textStyle: { color: theme.stat, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      tooltip: {
        trigger: "axis",
        axisPointer: { type: "shadow" },
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (params) {
          var lines = [params[0].name];
          params.forEach(function (item) {
            if (item.value === null || item.value === undefined) return;
            lines.push(item.seriesName + "：" + fmt(item.value) + " 行");
          });
          return lines.join("\n");
        }
      },
      xAxis: {
        type: "category",
        data: rows.map(function (row) {
          /* caller-supplied labels keep long file names readable */
          return opts && typeof opts.labelOf === "function" ? opts.labelOf(row.name) : shortName(row.name);
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 10, rotate: 26, interval: 0 }
      },
      yAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.16 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: 12 }
      },
      series: active.map(function (item) {
        return {
          name: item.name,
          type: "bar",
          barMaxWidth: 18,
          itemStyle: {
            color: color + alphas[item.index],
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [2, 2, 0, 0]
          },
          emphasis: { focus: "series" },
          data: rows.map(function (row) {
            var values = row.values || [];
            return values[item.index] === null || values[item.index] === undefined ? null : values[item.index];
          })
        };
      })
    };
  }

  function flatten(board, metricKey, active, order) {
    var rank = {};
    (order || []).forEach(function (name, index) {
      rank[name] = index;
    });
    var rows = [];
    visibleCategories(board, active).forEach(function (category) {
      category.modules.forEach(function (module) {
        rows.push({
          name: module.name,
          category: category.key,
          categoryLabel: category.label,
          shared: Boolean(module.shared),
          value: Number(module[metricKey] || 0)
        });
      });
    });
    /* 统一顺序：同一模块在五张图里永远同一行；缺 order 时退回按值降序 */
    rows.sort(function (a, b) {
      var rankA = rank[a.name];
      var rankB = rank[b.name];
      if (rankA === undefined || rankB === undefined) return b.value - a.value;
      if (rankA !== rankB) return rankA - rankB;
      return b.value - a.value;
    });
    return rows;
  }

  /** 分层明细：横向条形，一行一个模块；顺序由 moduleOrder 统一，受筛选影响。 */
  function bar(board, metricKey, theme, active, order) {
    var rows = flatten(board, metricKey, active, order);
    var label = "";
    METRICS.forEach(function (metric) {
      if (metric.key === metricKey) label = metric.label;
    });

    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      grid: { left: 8, right: 64, top: 16, bottom: 12, containLabel: true },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          var data = param.data || {};
          var lines = [
            data.fullName || param.name,
            data.categoryLabel + " · " + label + "：" + fmt(param.value)
          ];
          if (data.shared) lines.push("（共享层 / 基础设施，不属于单个业务模块）");
          return lines.join("\n");
        }
      },
      xAxis: {
        type: "value",
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { lineStyle: { color: theme.ink, type: "dashed", opacity: 0.18 } },
        axisLabel: { color: theme.secondary, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      yAxis: {
        type: "category",
        inverse: true,
        data: rows.map(function (row) {
          return shortName(row.name);
        }),
        axisLine: { lineStyle: { color: theme.ink, width: 1.5 } },
        axisTick: { show: false },
        axisLabel: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize }
      },
      series: [
        {
          type: "bar",
          barMaxWidth: 14,
          emphasis: { focus: "none" },
          label: {
            show: true,
            position: "right",
            color: theme.stat,
            fontFamily: theme.font,
            fontSize: theme.fontSize,
            formatter: function (param) {
              return fmt(param.value);
            }
          },
          data: rows.map(function (row) {
            return {
              value: row.value,
              name: shortName(row.name),
              fullName: row.name,
              categoryLabel: row.categoryLabel,
              shared: row.shared,
              itemStyle: {
                color: theme.colors[row.category] || theme.subtle,
                borderColor: theme.ink,
                borderWidth: 1,
                borderRadius: [0, 2, 2, 0]
              }
            };
          })
        }
      ]
    };
  }

  /** 代码行占比：环形，按分类；筛选时选中项实色、其余降透明度（不隐藏，保留对比）。 */
  function donut(board, theme, active) {
    var focused = Boolean(active) && active !== "all";
    var slices = (board.categories || []).map(function (category) {
      var dim = focused && category.key !== active;
      return {
        key: category.key,
        name: category.label,
        value: Number((category.totals || {}).loc || 0),
        itemStyle: {
          color: theme.colors[category.key] || theme.subtle,
          opacity: dim ? 0.28 : 1
        }
      };
    });
    var total = slices.reduce(function (sum, slice) {
      return sum + slice.value;
    }, 0);
    var percentOf = function (name) {
      for (var i = 0; i < slices.length; i += 1) {
        if (slices[i].name === name) {
          return total ? ((slices[i].value / total) * 100).toFixed(1) + "%" : "0%";
        }
      }
      return "";
    };

    return {
      animation: !theme.reduceMotion,
      animationDuration: 180,
      textStyle: { fontFamily: theme.font, fontSize: theme.fontSize, color: theme.stat },
      tooltip: {
        trigger: "item",
        backgroundColor: theme.card,
        borderColor: theme.ink,
        borderWidth: 1,
        textStyle: { color: theme.ink, fontFamily: theme.font, fontSize: theme.fontSize },
        formatter: function (param) {
          return param.name + " · 代码行 " + fmt(param.value) + "（" + param.percent + "%）";
        }
      },
      series: [
        {
          type: "pie",
          radius: ["46%", "70%"],
          center: ["50%", "44%"],
          itemStyle: { borderColor: theme.ink, borderWidth: 2 },
          /* 卡片只有三分之一宽：内置标签会压边，百分比改由底部图例承载 */
          label: { show: false },
          labelLine: { show: false },
          data: slices
        }
      ],
      legend: {
        bottom: 0,
        left: "center",
        itemWidth: 14,
        itemHeight: 14,
        icon: "roundRect",
        itemGap: 12,
        textStyle: {
          color: theme.stat,
          fontFamily: theme.font,
          fontSize: theme.fontSize
        },
        formatter: function (name) {
          return name + " " + percentOf(name);
        }
      }
    };
  }

  window.BoardOptions = {
    metrics: METRICS,
    totalsMetrics: TOTALS_METRICS,
    bar: bar,
    donut: donut,
    totalsBar: totalsBar,
    agentsBar: agentsBar,
    moduleBar: moduleBar,
    miniLine: miniLine,
    miniBar: miniBar,
    fileTrendBar: fileTrendBar,
    unitBar: unitBar,
    unitColumn: unitColumn,
    unitTrendColumn: unitTrendColumn,
    modulePie: modulePie,
    depGraph: depGraph,
    agentsGraph: agentsGraph,
    historyLine: historyLine,
    agentsHistory: agentsHistory,
    moduleOrder: moduleOrder,
    scopeTotals: scopeTotals,
    scopeLabel: scopeLabel,
    fmt: fmt
  };
})();
