/**
 * Android-AutoTests 登录页 HTML 原型（Web 桌面）— 交互逻辑（纯 Mock，无真实 API）
 * 对齐 01-登录页.md：校验 / 记住账号 / 模式切换 / Overlay / 跳转高亮
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
    });
  });

  /* ── Flow board highlight ── */
  const FLOW_MAP = {
    guard: { edges: ["e-guard"], nodes: ["n-protected", "n-login"] },
    success: { edges: ["e-success"], nodes: ["n-login", "n-dash"] },
    switch: { edges: ["e-switch"], nodes: ["n-login", "n-register"] },
    expire: { edges: ["e-expire"], nodes: ["n-dash", "n-login"] },
    error: { edges: ["e-error", "e-error-close"], nodes: ["n-login", "n-error"] },
  };

  function clearFlowHighlight() {
    document.querySelectorAll(".flow-edge, .flow-edge-label, .flow-node").forEach((el) => {
      el.classList.remove("is-hl");
      if (el.classList.contains("flow-node")) el.setAttribute("stroke-width", "2");
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

  /* Jump from board "演示此跳转" note buttons */
  document.querySelectorAll("[data-jump-flow]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelector('.tab-btn[data-tab="flow"]').click();
      highlightFlow(btn.dataset.jumpFlow);
      document.getElementById("panel-flow").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });

  document.querySelectorAll("[data-open-demo]").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelector('.tab-btn[data-tab="demo"]').click();
      const mode = btn.dataset.openDemo;
      if (mode === "register") setMode("register");
      else setMode("login");
    });
  });

  /* ── Interactive login / register mock ── */
  const state = {
    mode: "login", // login | register
    remember: false,
    loading: false,
    serverError: "",
    savedUsername: localStorage.getItem("proto_saved_username") || "",
  };

  const els = {
    meetingTitle: document.getElementById("meeting-title"),
    formLogin: document.getElementById("form-login"),
    formRegister: document.getElementById("form-register"),
    loginUser: document.getElementById("login-username"),
    loginPass: document.getElementById("login-password"),
    regUser: document.getElementById("register-username"),
    regEmail: document.getElementById("register-email"),
    regPass: document.getElementById("register-password"),
    regPass2: document.getElementById("register-password2"),
    loginSubmit: document.getElementById("login-submit"),
    regSubmit: document.getElementById("register-submit"),
    rememberSwitch: document.getElementById("remember-switch"),
    errLoginUser: document.getElementById("err-login-username"),
    errLoginPass: document.getElementById("err-login-password"),
    errRegUser: document.getElementById("err-register-username"),
    errRegEmail: document.getElementById("err-register-email"),
    errRegPass: document.getElementById("err-register-password"),
    errRegPass2: document.getElementById("err-register-password2"),
    toast: document.getElementById("live-toast"),
    overlay: document.getElementById("live-overlay"),
    overlayMsg: document.getElementById("live-overlay-msg"),
    statusPill: document.getElementById("proto-status"),
    ctaLogin: document.getElementById("cta-login"),
    ctaRegister: document.getElementById("cta-register"),
  };

  function setStatus(text, kind) {
    if (!els.statusPill) return;
    els.statusPill.textContent = text;
    els.statusPill.className = "status-pill" + (kind ? " " + kind : "");
  }

  function setMode(mode) {
    if (state.loading) return; // 可选增强：loading 锁定切换
    state.mode = mode;
    state.serverError = "";
    hideOverlay();
    els.meetingTitle.textContent = mode === "login" ? "登录" : "注册";
    els.formLogin.hidden = mode !== "login";
    els.formRegister.hidden = mode !== "register";
    els.ctaLogin.classList.toggle("is-active", mode === "login");
    els.ctaLogin.classList.toggle("is-ghost", mode !== "login");
    els.ctaRegister.classList.toggle("is-active", mode === "register");
    els.ctaRegister.classList.toggle("is-ghost", mode !== "register");

    if (mode === "register") {
      els.regUser.value = "";
      els.regEmail.value = "";
      els.regPass.value = "";
      els.regPass2.value = "";
      clearRegErrors();
      validateRegister();
    } else {
      els.loginPass.value = "";
      clearLoginErrors();
      if (state.savedUsername) {
        els.loginUser.value = state.savedUsername;
        state.remember = true;
        els.rememberSwitch.classList.add("on");
      }
      validateLogin();
    }
    setStatus(mode === "login" ? "空闲（登录）" : "空闲（注册）", "");
  }

  function clearLoginErrors() {
    els.errLoginUser.textContent = "";
    els.errLoginPass.textContent = "";
    els.loginUser.classList.remove("is-error");
    els.loginPass.classList.remove("is-error");
  }
  function clearRegErrors() {
    [els.errRegUser, els.errRegEmail, els.errRegPass, els.errRegPass2].forEach((e) => (e.textContent = ""));
    [els.regUser, els.regEmail, els.regPass, els.regPass2].forEach((e) => e.classList.remove("is-error"));
  }

  function validateLogin() {
    const u = els.loginUser.value;
    const p = els.loginPass.value;
    let uErr = "";
    let pErr = "";
    if (!u) uErr = "请输入用户名";
    else if (!u.trim()) uErr = "用户名不能为空白";
    else if (u.length > 150) uErr = "用户名过长，最多150个字符";
    if (!p) pErr = "请输入密码";
    els.errLoginUser.textContent = uErr;
    els.errLoginPass.textContent = pErr;
    els.loginUser.classList.toggle("is-error", !!uErr && u.length > 0);
    els.loginPass.classList.toggle("is-error", !!pErr && p.length > 0);
    // show errors when touched or non-empty
    if (!u && !p) {
      els.errLoginUser.textContent = "";
      els.errLoginPass.textContent = "";
      els.loginUser.classList.remove("is-error");
      els.loginPass.classList.remove("is-error");
    } else {
      if (uErr) {
        els.errLoginUser.textContent = uErr;
        els.loginUser.classList.add("is-error");
      }
      if (pErr) {
        els.errLoginPass.textContent = pErr;
        els.loginPass.classList.add("is-error");
      }
    }
    const ok = !uErr && !pErr;
    els.loginSubmit.disabled = !ok || state.loading;
    return ok;
  }

  function validateRegister() {
    const username = els.regUser.value.trim();
    const email = els.regEmail.value.trim();
    const password = els.regPass.value.trim();
    const password2 = els.regPass2.value.trim();
    const raw = {
      u: els.regUser.value,
      e: els.regEmail.value,
      p: els.regPass.value,
      p2: els.regPass2.value,
    };
    let uErr = "", eErr = "", pErr = "", p2Err = "";
    if (!username) uErr = "请输入用户名";
    else if (username.length < 3) uErr = "用户名至少 3 个字符";
    else if (username.length > 20) uErr = "用户名最多 20 个字符";
    if (!email) eErr = "请输入邮箱";
    else if (!email.includes("@")) eErr = "邮箱格式不正确";
    if (!password) pErr = "请输入密码";
    else if (password.length < 6) pErr = "密码至少 6 位";
    if (!password2) p2Err = "请再次输入密码";
    else if (password !== password2) p2Err = "两次密码不一致";

    const touched = raw.u || raw.e || raw.p || raw.p2;
    els.errRegUser.textContent = touched && uErr ? uErr : "";
    els.errRegEmail.textContent = touched && eErr ? eErr : "";
    els.errRegPass.textContent = touched && pErr ? pErr : "";
    els.errRegPass2.textContent = touched && p2Err ? p2Err : "";
    els.regUser.classList.toggle("is-error", !!(touched && uErr));
    els.regEmail.classList.toggle("is-error", !!(touched && eErr));
    els.regPass.classList.toggle("is-error", !!(touched && pErr));
    els.regPass2.classList.toggle("is-error", !!(touched && p2Err));

    const ok = !uErr && !eErr && !pErr && !p2Err;
    els.regSubmit.disabled = !ok || state.loading;
    return ok;
  }

  function showToast(msg) {
    els.toast.textContent = msg;
    els.toast.classList.add("show");
    setTimeout(() => els.toast.classList.remove("show"), 2200);
  }
  function showOverlay(msg) {
    state.serverError = msg;
    els.overlayMsg.textContent = msg;
    els.overlay.classList.add("show");
    setStatus("失败（Overlay）", "err");
  }
  function hideOverlay() {
    els.overlay.classList.remove("show");
    state.serverError = "";
  }

  function mockSubmit(kind) {
    if (state.loading) return;
    const ok = kind === "login" ? validateLogin() : validateRegister();
    if (!ok) {
      showToast("请完善表单");
      return;
    }
    state.loading = true;
    setStatus("提交中…", "load");
    if (kind === "login") {
      els.loginSubmit.disabled = true;
      els.loginSubmit.classList.add("is-loading");
      els.loginSubmit.textContent = "登录中";
    } else {
      els.regSubmit.disabled = true;
      els.regSubmit.classList.add("is-loading");
      els.regSubmit.textContent = "提交中";
    }

    const username = kind === "login" ? els.loginUser.value.trim() : els.regUser.value.trim();
    const password = kind === "login" ? els.loginPass.value : els.regPass.value.trim();

    // Mock scenarios by special usernames
    setTimeout(() => {
      state.loading = false;
      els.loginSubmit.classList.remove("is-loading");
      els.regSubmit.classList.remove("is-loading");
      els.loginSubmit.textContent = "登录";
      els.regSubmit.textContent = "完成注册 →";

      if (username === "fail" || password === "wrong") {
        showOverlay("用户名或密码错误");
        validateLogin();
        validateRegister();
        return;
      }
      if (username === "exists") {
        showOverlay("用户名已存在");
        validateRegister();
        return;
      }
      if (username === "network") {
        showOverlay("网络连接失败，请稍后重试");
        validateLogin();
        validateRegister();
        return;
      }
      if (username === "down") {
        showOverlay("后端服务未就绪，请稍后重试");
        validateLogin();
        validateRegister();
        return;
      }

      // success
      if (kind === "login" && state.remember) {
        localStorage.setItem("proto_saved_username", username);
        state.savedUsername = username;
      } else if (kind === "login" && !state.remember) {
        localStorage.removeItem("proto_saved_username");
        state.savedUsername = "";
      }
      // mock session
      sessionStorage.setItem("proto_access_token", "mock-access");
      sessionStorage.setItem("proto_refresh_token", "mock-refresh");
      sessionStorage.setItem("proto_username", username);

      showToast(kind === "login" ? "登录成功，正在跳转..." : "注册成功，正在跳转...");
      setStatus("成功 → /dashboard", "ok");
      setTimeout(() => {
        showDashboardMock();
      }, 900);
      validateLogin();
      validateRegister();
    }, 900);
  }

  function setDemoUrl(path) {
    const el = document.getElementById("demo-url");
    if (el) el.textContent = "http://localhost:5173" + path;
  }

  function showDashboardMock() {
    const dash = document.getElementById("dash-mock");
    const hero = document.getElementById("proto-hero");
    if (dash && hero) {
      hero.hidden = true;
      dash.hidden = false;
      setDemoUrl("/dashboard");
      setStatus("已进入工作台（Mock）", "ok");
    }
  }

  function resetToLogin() {
    const dash = document.getElementById("dash-mock");
    const hero = document.getElementById("proto-hero");
    if (dash && hero) {
      dash.hidden = true;
      hero.hidden = false;
    }
    sessionStorage.removeItem("proto_access_token");
    setDemoUrl("/login");
    setMode("login");
  }

  /* Wire events */
  els.ctaLogin.addEventListener("click", () => setMode("login"));
  els.ctaRegister.addEventListener("click", () => setMode("register"));
  document.getElementById("link-to-register").addEventListener("click", () => setMode("register"));
  document.getElementById("link-to-login").addEventListener("click", () => setMode("login"));

  document.getElementById("remember-row").addEventListener("click", () => {
    state.remember = !state.remember;
    els.rememberSwitch.classList.toggle("on", state.remember);
  });

  ["input", "change"].forEach((ev) => {
    els.loginUser.addEventListener(ev, validateLogin);
    els.loginPass.addEventListener(ev, validateLogin);
    els.regUser.addEventListener(ev, validateRegister);
    els.regEmail.addEventListener(ev, validateRegister);
    els.regPass.addEventListener(ev, validateRegister);
    els.regPass2.addEventListener(ev, validateRegister);
  });

  els.formLogin.addEventListener("submit", (e) => {
    e.preventDefault();
    mockSubmit("login");
  });
  els.formRegister.addEventListener("submit", (e) => {
    e.preventDefault();
    mockSubmit("register");
  });

  document.getElementById("overlay-dismiss").addEventListener("click", () => {
    hideOverlay();
    setStatus(state.mode === "login" ? "空闲（登录）" : "空闲（注册）", "");
  });
  els.overlay.addEventListener("click", (e) => {
    if (e.target === els.overlay) {
      hideOverlay();
      setStatus(state.mode === "login" ? "空闲（登录）" : "空闲（注册）", "");
    }
  });

  document.getElementById("btn-back-login").addEventListener("click", resetToLogin);

  /* Scenario demo buttons */
  document.getElementById("demo-fail").addEventListener("click", () => {
    setMode("login");
    els.loginUser.value = "fail";
    els.loginPass.value = "wrong";
    validateLogin();
    mockSubmit("login");
  });
  document.getElementById("demo-network").addEventListener("click", () => {
    setMode("login");
    els.loginUser.value = "network";
    els.loginPass.value = "any123";
    validateLogin();
    mockSubmit("login");
  });
  document.getElementById("demo-success").addEventListener("click", () => {
    setMode("login");
    els.loginUser.value = "demo";
    els.loginPass.value = "secret1";
    state.remember = true;
    els.rememberSwitch.classList.add("on");
    validateLogin();
    mockSubmit("login");
  });
  document.getElementById("demo-register").addEventListener("click", () => {
    setMode("register");
    els.regUser.value = "newuser";
    els.regEmail.value = "a@b.com";
    els.regPass.value = "secret1";
    els.regPass2.value = "secret1";
    validateRegister();
    mockSubmit("register");
  });
  document.getElementById("demo-exists").addEventListener("click", () => {
    setMode("register");
    els.regUser.value = "exists";
    els.regEmail.value = "a@b.com";
    els.regPass.value = "secret1";
    els.regPass2.value = "secret1";
    validateRegister();
    mockSubmit("register");
  });
  document.getElementById("demo-expire").addEventListener("click", () => {
    sessionStorage.clear();
    resetToLogin();
    showToast("登录已过期，请重新登录");
    setStatus("Token 过期 → /login", "err");
    document.querySelector('.tab-btn[data-tab="flow"]').click();
    highlightFlow("expire");
  });

  // init
  if (state.savedUsername) {
    els.loginUser.value = state.savedUsername;
    state.remember = true;
    els.rememberSwitch.classList.add("on");
  }
  setMode("login");
  validateLogin();
})();
