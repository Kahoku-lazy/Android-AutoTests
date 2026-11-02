/**
 * Android-AutoTests 仪表盘模式页 HTML 原型（Web 桌面）— 交互逻辑（纯 Mock）
 * 对齐 02-仪表盘模式页.md：KPI 跳转 / 刷新 / 空态 / ErrorState / 流程高亮
 */
(function () {
  "use strict";

  /* ── Tabs ── */
  const tabs = document.querySelectorAll(".tab-btn");
  const panels = document.querySelectorAll(".panel");
  tabs.forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.tab;
      tabs.forEach((b) => b.classList.toggle("is-active", b === btn));
      panels.forEach((p) => p.classList.toggle("is-active", p.id === "panel-" + id));
      if (id === "flow") clearFlowHighlight();
      if (id === "demo") renderDemo();
    });
  });

  /* ── Toast ── */
  const toastEl = document.getElementById("toast");
  let toastTimer = null;
  function toast(msg) {
    toastEl.textContent = msg;
    toastEl.classList.add("is-show");
    clearTimeout(toastTimer);
    toastTimer = setTimeout(() => toastEl.classList.remove("is-show"), 2200);
  }

  /* ── Flow highlight ── */
  const FLOW_MAP = {
    enter: { edges: ["e-enter", "e-api"], nodes: ["n-login", "n-dash", "n-api"] },
    kpi: { edges: ["e-kpi"], nodes: ["n-dash", "n-mod"] },
    refresh: { edges: ["e-refresh", "e-refresh2", "e-api"], nodes: ["n-dash", "n-api"] },
    silent: { edges: ["e-silent"], nodes: ["n-dash", "n-silent"] },
    error: { edges: ["e-error", "e-retry"], nodes: ["n-dash", "n-err"] },
    logout: { edges: ["e-logout"], nodes: ["n-dash", "n-login"] },
  };

  function clearFlowHighlight() {
    document.querySelectorAll(".flow-edge, .flow-edge-label, .flow-node").forEach((el) => {
      el.classList.remove("is-hl");
      if (el.classList.contains("flow-node")) {
        el.setAttribute("stroke-width", "2");
        el.setAttribute("stroke", "#1e1e24");
      }
    });
    document.querySelectorAll(".flow-actions button").forEach((b) => b.classList.remove("is-on"));
  }

  function highlightFlow(key) {
    clearFlowHighlight();
    const cfg = FLOW_MAP[key];
    if (!cfg) return;
    const btn = document.querySelector('.flow-actions button[data-flow="' + key + '"]');
    if (btn) btn.classList.add("is-on");
    cfg.edges.forEach((id) => {
      const e = document.getElementById(id);
      const l = document.getElementById(id + "-label");
      if (e) e.classList.add("is-hl");
      if (l) l.classList.add("is-hl");
    });
    // refresh uses e-refresh-label
    if (key === "refresh") {
      const l = document.getElementById("e-refresh-label");
      if (l) l.classList.add("is-hl");
    }
    cfg.nodes.forEach((id) => {
      const n = document.getElementById(id);
      if (n) {
        n.classList.add("is-hl");
        n.setAttribute("stroke-width", "3.5");
        n.setAttribute("stroke", "#f56b6a");
      }
    });
  }

  document.querySelectorAll(".flow-actions button").forEach((btn) => {
    btn.addEventListener("click", () => highlightFlow(btn.dataset.flow));
  });

  document.querySelectorAll("[data-jump-flow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelector('.tab-btn[data-tab="flow"]').click();
      highlightFlow(btn.dataset.jumpFlow);
      document.getElementById("panel-flow").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  document.querySelectorAll("[data-open-demo]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const scene = btn.dataset.openDemo || "normal";
      document.querySelector('.tab-btn[data-tab="demo"]').click();
      setScene(scene === "login" ? "normal" : scene);
    });
  });

  /* ── Demo state ── */
  const state = {
    scene: "normal", // normal | empty | error | live | silent
    refreshing: false,
    lastUpdated: formatNow(),
    systemStatus: "normal",
    silentNote: "",
  };

  function formatNow() {
    const d = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    return (
      d.getFullYear() +
      "-" +
      pad(d.getMonth() + 1) +
      "-" +
      pad(d.getDate()) +
      " " +
      pad(d.getHours()) +
      ":" +
      pad(d.getMinutes()) +
      ":" +
      pad(d.getSeconds())
    );
  }

  const MOCK = {
    devicesOnline: 12,
    agentsActive: 3,
    runsActive: 0,
    tasksTotal: 48,
    tasksToday: 5,
    workflow: 7,
    tokenTotalM: "12.40",
    tokenTodayM: "0.86",
    cacheHit: "41.2",
    costTotal: "128",
    costToday: "3.52",
    casesTotal: 126,
    projects: [
      { name: "Smoke", total: 42, path: "/cases/projects/1" },
      { name: "回归包", total: 84, path: "/cases/projects/2" },
    ],
    agent: {
      name: "agent-qa",
      cache: "120,400",
      input: "890,200",
      output: "210,050",
      cost: "36.8",
    },
    tasks: [
      { title: "登录回归", ok: true },
      { title: "支付冒烟", ok: false },
      { title: "设备巡检", ok: true },
    ],
    activities: [
      { text: "demo 触发任务「登录回归」", time: "10:12" },
      { text: "agent-qa 更新智能体配置", time: "09:40" },
      { text: "设备 Pixel-6 上线", time: "09:05" },
    ],
  };

  function setScene(scene) {
    state.scene = scene;
    state.silentNote = "";
    if (scene === "live") {
      /* keep */
    } else if (scene === "silent") {
      state.lastUpdated = formatNow();
      state.silentNote = "已模拟静默刷新（保留原数据）";
      state.scene = "normal";
      toast("静默刷新完成 · 未打断 UI");
    }
    document.querySelectorAll("[data-scene]").forEach((b) => {
      b.classList.toggle("is-on", b.dataset.scene === scene || (scene === "silent" && b.dataset.scene === "silent"));
    });
    if (scene === "silent") {
      document.querySelectorAll("[data-scene]").forEach((b) => b.classList.toggle("is-on", b.dataset.scene === "silent"));
    }
    const labels = {
      normal: "正常数据",
      empty: "无用例空态",
      error: "加载失败",
      live: "运行中 live",
      silent: "模拟静默刷新",
    };
    const status = document.getElementById("demo-status");
    if (status) {
      status.textContent =
        "场景：" +
        (labels[scene] || scene) +
        (state.silentNote ? " · " + state.silentNote : "");
    }
    renderDemo();
  }

  document.querySelectorAll("[data-scene]").forEach((btn) => {
    btn.addEventListener("click", () => setScene(btn.dataset.scene));
  });

  function kpi(cls, label, value, desc, path, live) {
    return (
      '<button type="button" class="kpi ' +
      cls +
      (live ? " is-live" : "") +
      '" data-path="' +
      (path || "") +
      '">' +
      '<div class="kpi__label">' +
      label +
      "</div>" +
      '<div class="kpi__value">' +
      value +
      "</div>" +
      (desc ? '<div class="kpi__desc">' + desc + "</div>" : "") +
      "</button>"
    );
  }

  function renderDemo() {
    const root = document.getElementById("demo-root");
    if (!root) return;

    const live = state.scene === "live";
    const empty = state.scene === "empty";
    const err = state.scene === "error";
    const runs = live ? 2 : MOCK.runsActive;
    const sys = live || MOCK.devicesOnline > 0 ? "normal" : "offline";
    state.systemStatus = sys;

    if (err) {
      root.innerHTML =
        '<div class="wb">' +
        sidebarHtml() +
        '<div class="wb-main">' +
        headerHtml(false) +
        '<div class="error-box"><p>统计数据加载失败，请检查网络连接</p>' +
        '<button type="button" id="btn-retry">重试</button></div>' +
        "</div></div>";
      bindShell(root);
      const retry = root.querySelector("#btn-retry");
      if (retry) {
        retry.addEventListener("click", () => {
          toast("重新 loadData…");
          setScene("normal");
        });
      }
      return;
    }

    const projectsHtml = empty
      ? '<div class="empty-box"><p>暂无用例项目</p>' +
        '<button type="button" class="linkish" data-path="/cases">前往用例管理 →</button></div>'
      : '<div class="kpi-grid">' +
        MOCK.projects
          .map(function (p, i) {
            return kpi(i === 0 ? "kpi--deep" : "kpi--sage", p.name, String(p.total), "→ 项目", p.path, false);
          })
          .join("") +
        "</div>";

    const casesTotal = empty ? 0 : MOCK.casesTotal;

    root.innerHTML =
      '<div class="wb">' +
      sidebarHtml() +
      '<div class="wb-main">' +
      headerHtml(state.refreshing) +
      '<div class="wb-body">' +
      // ops
      '<section class="ch ch--ops">' +
      chHead("监", "Platform Ops", "平台运营", "核心入口指标 · 实时状态可点进模块") +
      '<div class="kpi-grid">' +
      kpi("kpi--sage", "在线设备", String(MOCK.devicesOnline), "→ /devices", "/devices") +
      kpi("kpi--gray", "活跃智能体", String(MOCK.agentsActive), "→ /ai-assistant", "/ai-assistant") +
      kpi("kpi--rose", "运行中任务", String(runs), "→ /reports", "/reports", runs > 0) +
      kpi("kpi--gray", "任务数量", String(MOCK.tasksTotal), "今日 " + MOCK.tasksToday, "/tasks") +
      kpi("kpi--pale", "工作流", String(MOCK.workflow), "→ /workflow", "/workflow") +
      "</div></section>" +
      // ai
      '<section class="ch ch--ai">' +
      chHead("AI", "AI Usage", "AI 用量", "Token · 缓存 · DeepSeek 费用") +
      '<div class="kpi-grid">' +
      kpi("kpi--sage", "累计用量", MOCK.tokenTotalM + "<small>M</small>", "DeepSeek") +
      kpi("kpi--cream", "当天用量", MOCK.tokenTodayM + "<small>M</small>", "DeepSeek") +
      kpi("kpi--deep", "缓存命中率", MOCK.cacheHit + "<small>%</small>", "DeepSeek") +
      kpi("kpi--dust", "总费用", MOCK.costTotal + "<small> 元</small>", "DeepSeek") +
      kpi("kpi--dust", "当天费用", MOCK.costToday + "<small> 元</small>", "DeepSeek") +
      "</div>" +
      '<div class="agent-row"><div class="agent-card"><h4 class="agent-card__name">' +
      MOCK.agent.name +
      '</h4><ul class="agent-card__stats">' +
      "<li><span>缓存命中</span><b>" +
      MOCK.agent.cache +
      "</b></li>" +
      "<li><span>输入</span><b>" +
      MOCK.agent.input +
      "</b></li>" +
      "<li><span>输出</span><b>" +
      MOCK.agent.output +
      "</b></li>" +
      "<li><span>总费用</span><b>" +
      MOCK.agent.cost +
      " 元</b></li>" +
      "</ul></div></div></section>" +
      // asset
      '<section class="ch ch--asset">' +
      '<header class="ch-head"><div class="ch-head__left"><div class="ch-mark">库</div><div>' +
      '<div class="ch-eyebrow">Test Assets</div><h3 class="ch-title"><span class="marker">测试资产</span></h3>' +
      '<p class="ch-desc">用例库 + 元素库 · 同一存量视角</p></div></div>' +
      '<span class="chip chip--teal">用例 <b>' +
      casesTotal +
      "</b></span></header>" +
      projectsHtml +
      "</section>" +
      // trend
      '<section class="ch ch--trend">' +
      chHead("势", "Trends & Activity", "趋势与动态", "近 7 日任务卡 · Token · 费用 · 今日进度 · 活动流") +
      '<div class="trends"><div class="chart-card"><div class="chart-card__title">助手任务卡</div>' +
      '<div class="fake-chart fake-chart--dual">' +
      '<span style="height:40%"></span><span style="height:18%"></span>' +
      '<span style="height:72%"></span><span style="height:22%"></span>' +
      '<span style="height:58%"></span><span style="height:12%"></span>' +
      '<span style="height:84%"></span><span style="height:8%"></span>' +
      "</div></div>" +
      '<div class="chart-card"><div class="chart-card__title">任务执行结果</div><ul class="task-list">' +
      MOCK.tasks
        .map(function (t) {
          return (
            "<li><span>" +
            t.title +
            '</span><span class="' +
            (t.ok ? "ok" : "bad") +
            '">' +
            (t.ok ? "通过" : "失败") +
            "</span></li>"
          );
        })
        .join("") +
      "</ul></div></div>" +
      '<div class="trends"><div class="chart-card"><div class="chart-card__title">每日 Token 用量</div>' +
      '<div class="fake-chart"><span style="height:30%;background:#4ECDC4"></span>' +
      '<span style="height:45%;background:#4ECDC4"></span><span style="height:60%;background:#4ECDC4"></span>' +
      '<span style="height:40%;background:#A78BFA"></span><span style="height:55%;background:#A78BFA"></span>' +
      '<span style="height:70%;background:#4ECDC4"></span><span style="height:50%;background:#4ECDC4"></span></div></div>' +
      '<div class="chart-card"><div class="chart-card__title">每日 DeepSeek 费用（元）</div>' +
      '<div class="fake-chart"><span style="height:25%;background:#F7C948"></span>' +
      '<span style="height:40%;background:#F7C948"></span><span style="height:35%;background:#F7C948"></span>' +
      '<span style="height:55%;background:#F7C948"></span><span style="height:48%;background:#F7C948"></span>' +
      '<span style="height:62%;background:#F7C948"></span><span style="height:44%;background:#F7C948"></span></div></div></div>' +
      '<div class="trends trends--single"><div class="chart-card"><div class="chart-card__title">今日 Token 与费用（逐小时）</div>' +
      '<div class="line-chart"><svg viewBox="0 0 200 60" preserveAspectRatio="none" aria-hidden="true">' +
      '<polyline fill="none" stroke="#4ECDC4" stroke-width="2" points="0,50 20,48 40,40 60,42 80,30 100,28 120,22 140,18 160,20 180,12 200,10"/>' +
      '<polyline fill="none" stroke="#F7C948" stroke-width="2" points="0,55 20,54 40,50 60,51 80,45 100,44 120,40 140,38 160,36 180,32 200,30"/>' +
      "</svg></div></div></div>" +
      '<div class="trends trends--single"><div class="chart-card"><div class="chart-card__title">Voice 来源 Token 消耗</div>' +
      '<div class="fake-chart"><span style="height:35%;background:#4ECDC4"></span>' +
      '<span style="height:55%;background:#F7C948"></span><span style="height:25%;background:#4ECDC4"></span>' +
      '<span style="height:40%;background:#F7C948"></span><span style="height:20%;background:#4ECDC4"></span></div></div></div>' +
      '<div class="ch-desc" style="opacity:1;margin:4px 0">最近动态 <span style="opacity:.5">Activity</span></div>' +
      '<ul class="timeline">' +
      MOCK.activities
        .map(function (a) {
          return "<li>" + a.text + " <time>" + a.time + "</time></li>";
        })
        .join("") +
      "</ul></section>" +
      '<footer class="wb-footer">' +
      "<div>🕒 最近更新: " +
      state.lastUpdated +
      "</div>" +
      "<div>⚠ 系统状态: " +
      (state.systemStatus === "normal" ? "正常运行" : "无设备连接") +
      "</div>" +
      (state.silentNote ? "<div>" + state.silentNote + "</div>" : "") +
      "</footer>" +
      "</div></div></div>";

    bindShell(root);
  }

  function chHead(mark, eye, title, desc) {
    return (
      '<header class="ch-head"><div class="ch-head__left"><div class="ch-mark">' +
      mark +
      "</div><div>" +
      '<div class="ch-eyebrow">' +
      eye +
      '</div><h3 class="ch-title"><span class="marker">' +
      title +
      '</span></h3><p class="ch-desc">' +
      desc +
      "</p></div></div></header>"
    );
  }

  function sidebarHtml() {
    return (
      '<aside class="wb-side">' +
      '<div class="wb-side__brand">自动化测试平台</div>' +
      '<button type="button" class="wb-nav is-active" data-nav="/dashboard">仪表盘</button>' +
      '<div class="wb-side__group-label">AI 功能</div>' +
      '<button type="button" class="wb-nav" data-nav="/ai-assistant">AI 助手</button>' +
      '<button type="button" class="wb-nav" data-nav="/knowledge-assistant">知识库助手</button>' +
      '<div class="wb-side__group-label">数据</div>' +
      '<button type="button" class="wb-nav" data-nav="/devices">设备管理</button>' +
      '<button type="button" class="wb-nav" data-nav="/workflow">页面流</button>' +
      '<button type="button" class="wb-nav" data-nav="/serial-log">串口日志</button>' +
      '<div class="wb-side__group-label">AI任务</div>' +
      '<button type="button" class="wb-nav" data-nav="/tasks">任务清单</button>' +
      '<button type="button" class="wb-nav" data-nav="/cases">用例管理</button>' +
      '<button type="button" class="wb-nav" data-nav="/reports">测试报告</button>' +
      '<button type="button" class="wb-nav" data-nav="/bugs">BUG单管理</button>' +
      '<div class="wb-side__foot">demo · 已登录</div></aside>'
    );
  }

  function headerHtml(loading) {
    return (
      '<header class="wb-header"><div class="wb-header__left">' +
      '<div class="wb-header__icon" aria-hidden="true">▣</div><div>' +
      '<h2 class="wb-header__title">仪表盘</h2>' +
      '<p class="wb-header__sub">自动化测试平台 · 实时监控设备状态、用例执行、AI Agent 与测试报告</p>' +
      '</div></div><button type="button" class="wb-btn' +
      (loading ? " is-loading" : "") +
      '" id="btn-refresh">刷新</button></header>'
    );
  }

  function bindShell(root) {
    root.querySelectorAll("[data-path]").forEach((el) => {
      el.addEventListener("click", () => {
        const p = el.getAttribute("data-path");
        if (!p) return;
        toast("原型：将跳转 " + p);
        const url = document.getElementById("demo-url");
        if (url) url.textContent = "http://localhost:5173" + p + "  (Mock)";
      });
    });
    root.querySelectorAll("[data-nav]").forEach((el) => {
      el.addEventListener("click", () => {
        const p = el.getAttribute("data-nav");
        if (p === "/dashboard") {
          toast("已在仪表盘");
          return;
        }
        toast("原型：侧栏将跳转 " + p);
      });
    });
    const refresh = root.querySelector("#btn-refresh");
    if (refresh) {
      refresh.addEventListener("click", () => {
        if (state.refreshing) return;
        state.refreshing = true;
        renderDemo();
        toast("刷新中…");
        setTimeout(() => {
          state.refreshing = false;
          state.lastUpdated = formatNow();
          toast("刷新完成");
          renderDemo();
        }, 900);
      });
    }
  }

  // initial demo render if panel might be shown later — also warm
  renderDemo();
})();
