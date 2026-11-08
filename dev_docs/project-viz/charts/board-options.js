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
  function depGraph(nodes, edges, theme) {
    var shortOf = {};
    var data = nodes.map(function (node) {
      shortOf[node.key] = node.label;
      return {
        name: node.label,
        key: node.key,
        fullLabel: node.fullLabel || node.label,
        value: Number(node.modules || 0),
        modules: Number(node.modules || 0),
        loc: Number(node.loc || 0),
        internal: Number(node.internal || 0),
        symbolSize: 14 + Math.min(26, Number(node.modules || 0) * 2),
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
            width: 0.8 + Number(edge.count || 0),
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
          layout: "circular",
          roam: true,
          symbol: "roundRect",
          label: {
            show: true,
            position: "right",
            distance: 6,
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

  /** 单层（前端模块 / 后端 App）总览：按代码行的横向条形。 */
  function moduleBar(rows, theme, colorKey) {
    var list = rows.slice().sort(function (a, b) {
      return Number(b.loc || 0) - Number(a.loc || 0);
    });
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
            color: theme.colors[colorKey] || theme.accent,
            borderColor: theme.ink,
            borderWidth: 1,
            borderRadius: [0, 2, 2, 0]
          },
          data: list.map(function (row) {
            return { value: Number(row.loc || 0), name: shortName(row.name), row: row };
          })
        }
      ]
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
