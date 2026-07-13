const LIFECYCLE_STAGES = STAGES.filter(s => s.id !== 'x' && s.id !== 'a' && s.id !== 't');
let chartInstances = [];
let chartsInited = false;

function stageDocs(stage) {
  if (stage.sections && stage.sections.length) {
    const md = [], html = [];
    const collect = (sec) => {
      (sec.md || []).forEach(d => md.push(d));
      (sec.html || []).forEach(d => html.push(d));
      (sec.subsections || []).forEach(collect);
    };
    stage.sections.forEach(collect);
    return { md, html };
  }
  return { md: stage.md || [], html: stage.html || [] };
}

function countDocs() {
  let md = 0, html = 0;
  STAGES.forEach(s => { const d = stageDocs(s); md += d.md.length; html += d.html.length; });
  return { md, html, total: md + html };
}

function stageCompleteness(s) {
  const d = stageDocs(s);
  if (s.sections && s.sections.length) {
    let units = 0, filled = 0;
    s.sections.forEach(sec => {
      if (sec.subsections && sec.subsections.length) {
        sec.subsections.forEach(sub => {
          units += 1;
          if ((sub.md && sub.md.length) || (sub.html && sub.html.length)) filled += 1;
        });
      } else {
        units += 1;
        if ((sec.md && sec.md.length) || (sec.html && sec.html.length)) filled += 1;
      }
    });
    return units ? Math.round((filled / units) * 100) : 0;
  }
  const hasMd = d.md.length > 0, hasHtml = d.html.length > 0;
  if (hasMd && hasHtml) return 100;
  if (hasMd || hasHtml) return (!hasMd && s.mdEmpty) || (!hasHtml && s.htmlEmpty) ? 50 : 80;
  if (s.mdEmpty && s.htmlEmpty) return 0;
  return 30;
}

// ── Sidebar ──
function renderSidebar() {
  const nav = document.getElementById('sidebar-nav');
  let html = `<div class="nav-section">总览</div>
    <button class="nav-item nav-dash" data-hash="dashboard">
      <span class="nav-num">📊</span>
      <span class="nav-label">仪表盘<span class="sub">ECharts 可视化</span></span>
    </button>
    <button class="nav-item nav-dash" data-hash="ai-workflow">
      <span class="nav-num" style="background:var(--pm-dark);font-size:12px">AI</span>
      <span class="nav-label">AI工作流<span class="sub">Stage-Gate · Agent · 用法</span></span>
    </button>
    <button class="nav-item nav-dash" data-hash="stage-t">
      <span class="nav-num" style="background:var(--stb);font-size:14px">🧪</span>
      <span class="nav-label">测试报告<span class="sub">一览平台测试报告</span></span>
    </button>
    <div class="nav-section">Stage-Gate 六阶段</div>`;

  STAGES.forEach(s => {
    if (s.id === 't') return;
    const colors = STAGE_COLORS[s.id];
    const num = s.id === 'x' ? '⊕' : (s.id === 'a' ? '◈' : s.id);
    const d = stageDocs(s);
    const cnt = d.md.length + d.html.length;
    if (s.id === 'x') html += '<div class="nav-section">管理员</div>';
    html += `<button class="nav-item" data-hash="${s.hash}">
      <span class="nav-num" style="background:${colors.border}">${num}</span>
      <span class="nav-label">${s.short}<span class="sub">${s.title}</span></span>
      <span class="nav-cnt">${cnt}</span>
    </button>`;
  });
  nav.innerHTML = html;
}

function renderStats() {
  const c = countDocs();
  const blanks = STAGES.filter(s => {
    if (s.sections) return s.sections.some(sec => sec.empty && !(sec.md && sec.md.length) && !(sec.html && sec.html.length));
    return (s.md.length === 0 && s.mdEmpty) || (s.html.length === 0 && s.htmlEmpty);
  }).length;
  document.getElementById('stats-bar').innerHTML = `
    <span class="stat">索引 <strong>${c.total}</strong> 份</span>
    <span class="stat">MD <strong>${c.md}</strong> · HTML <strong>${c.html}</strong></span>
    <span class="stat">Gate <strong>3</strong> 道</span>
    <span class="stat">待产出 <strong>${blanks}</strong> 处</span>`;
}

function renderKPIs() {
  const c = countDocs();
  const avgComplete = Math.round(LIFECYCLE_STAGES.reduce((a, s) => a + stageCompleteness(s), 0) / LIFECYCLE_STAGES.length);
  const richest = LIFECYCLE_STAGES.reduce((best, s) => {
    const a = stageDocs(s).md.length + stageDocs(s).html.length;
    const b = stageDocs(best).md.length + stageDocs(best).html.length;
    return a > b ? s : best;
  });
  document.getElementById('kpi-row').innerHTML = `
    <div class="kpi"><div class="kpi-val">${c.total}</div><div class="kpi-label">文档总数</div></div>
    <div class="kpi"><div class="kpi-val">${avgComplete}%</div><div class="kpi-label">平均完备度</div></div>
    <div class="kpi"><div class="kpi-val">${richest.short}</div><div class="kpi-label">最丰富阶段</div></div>
    <div class="kpi"><div class="kpi-val">6+3</div><div class="kpi-label">阶段 + Gate</div></div>`;
}

// ── Card colour mapping ──
function cardTopClass(doc) {
  const b = (doc.badge || '').toString();
  if (/主/.test(b)) return 't-main';
  if (/原型|导航/.test(b)) return 't-proto';
  if (/参考|对标|流程图/.test(b)) return 't-ref';
  if (/快照|指标|对比/.test(b)) return 't-snap';
  if (/交付/.test(b)) return 't-deliver';
  if (/规划/.test(b)) return 't-plan';
  if (/分析/.test(b)) return 't-analysis';
  if (/最新/.test(b)) return 't-latest';
  if (/审查/.test(b)) return 't-review';
  if (/质量/.test(b)) return 't-quality';
  if (/前端/.test(b)) return 't-frontend';
  if (/工作流/.test(b)) return 't-workflow';
  if (/统计/.test(b)) return 't-stats';
  if (/趋势/.test(b)) return 't-trend';
  if (/需求/.test(b)) return 't-require';
  return 't-md';
}

// ── Kanban-style doc card ──
function renderDocCard(doc, fmt) {
  const icon = fmt === 'md' ? '📄' : '📊';
  const fmtBadge = fmt === 'md' ? '<span class="badge b-md">MD</span>' : '<span class="badge b-html">HTML</span>';
  const extraBadge = doc.extra ? `<span class="badge ${doc.extra}">${doc.badge}</span>` : (doc.badge ? `<span class="badge ${doc._badgeClass || ''}">${doc.badge}</span>` : '');
  const grade = doc.grade ? `<span class="grade ${doc.grade}">${doc.badge}</span>` : '';
  const badgeHtml = grade || extraBadge || fmtBadge;
  const topCls = cardTopClass(doc);
  const emp = doc.emphasis ? ' card-emphasis' : '';

  return `<a class="doc-card ${topCls}${emp}" href="${doc.path}">
    <div class="card-top">
      <span class="card-icon">${icon}</span>
      <div class="card-info">
        <div class="card-title">${doc.title}</div>
        <div class="card-desc">${doc.desc}</div>
      </div>
    </div>
    <hr class="card-divider">
    <div class="card-foot">
      <span class="card-path">${doc.path}</span>
      <span class="card-badges">${badgeHtml}</span>
      <span class="card-arrow">→</span>
    </div>
  </a>`;
}

function renderPlaceholder(text) {
  return `<div class="doc-card placeholder" style="pointer-events:none"><div class="card-top">
    <span class="card-icon">📝</span>
    <div class="card-info">
      <div class="card-title placeholder-text">待 Agent 产出</div>
      <div class="card-desc placeholder-text">${text}</div>
    </div>
  </div></div>`;
}

// ── Smart layout: auto-kanban or grid ──
function renderDocList(sec) {
  const docs = [...(sec.md || []).map(d => ({ ...d, _fmt: 'md' })), ...(sec.html || []).map(d => ({ ...d, _fmt: 'html' }))];
  if (!docs.length) {
    if (sec.empty) return renderPlaceholder(sec.empty);
    return '';
  }
  // Decide layout
  const useKanban = sec.layout === 'kanban' || (docs.length >= 4 && !sec.layout);
  if (useKanban) {
    return `<div class="kanban-grid">${docs.map(d => renderDocCard(d, d._fmt)).join('')}</div>`;
  }
  // Standard grid for >1 doc, else single
  if (docs.length > 1) {
    return `<div class="kanban-grid" style="grid-template-columns:repeat(auto-fill,minmax(300px,1fr))">${docs.map(d => renderDocCard(d, d._fmt)).join('')}</div>`;
  }
  return renderDocCard(docs[0], docs[0]._fmt);
}

function renderSubsection(sub) {
  const docsHtml = renderDocList(sub);
  const cnt = (sub.md || []).length + (sub.html || []).length;
  return `<div class="subsection">
    <div class="subsection-head">
      <span class="col-dot" style="background:var(--primary)"></span>
      <span class="sub-title">${sub.title}</span>
      <span class="col-cnt">${cnt} 份</span>
      <span class="sub-path">${sub.dir || ''}</span>
    </div>
    <div class="subsection-body">${docsHtml || '<div class="placeholder-text">本功能暂无文档</div>'}</div>
  </div>`;
}

function renderSectionBlock(sec, idx, tone) {
  const hasSubs = sec.subsections && sec.subsections.length;
  let body = '';
  if (sec.inlineHtml) {
    body = sec.inlineHtml;
  } else if (hasSubs) {
    body = sec.subsections.map(renderSubsection).join('');
    const topDocs = renderDocList(sec);
    if (topDocs) body = topDocs + body;
  } else {
    body = renderDocList(sec) || `<div class="doc-card placeholder"><div class="card-top"><div class="card-info"><div class="placeholder-text">本栏目暂无文档</div></div></div></div>`;
  }
  if (sec.hint) body = `<p class="role-hint">${sec.hint}</p>` + body;

  const cnt = (() => {
    if (sec.inlineHtml) return '内嵌';
    let n = (sec.md || []).length + (sec.html || []).length;
    (sec.subsections || []).forEach(s => { n += (s.md || []).length + (s.html || []).length; });
    return n;
  })();
  const mdCnt = (sec.md || []).length;
  const htmlCnt = (sec.html || []).length;
  const statHtml = typeof cnt === 'number'
    ? `${mdCnt > 0 ? `<span class="stat-badge md-count">${mdCnt} MD</span>` : ''}${htmlCnt > 0 ? `<span class="stat-badge html-count">${htmlCnt} HTML</span>` : ''}`
    : '';

  const toneClass = tone ? ` tone-${tone}` : '';
  const idAttr = sec.id ? ` id="${sec.id}"` : '';
  return `<div class="section-block${toneClass}"${idAttr}>
    <div class="section-head">
      <span class="sec-num">${idx + 1}</span>
      <span class="sec-title">${sec.title}</span>
      ${statHtml}
      <span class="sec-path">${sec.dir || ''}</span>
    </div>
    <div class="section-body">${body}</div>
  </div>`;
}

function renderStageToc(stage) {
  if (!stage.toc || !stage.toc.length) return '';
  return `<div class="stage-toc">${stage.toc.map(t =>
    `<button type="button" data-scroll="${t.target}">${t.label}</button>`
  ).join('')}</div>`;
}

// ── SVG progress ring ──
function progressRing(pct, color) {
  const r = 20, circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;
  return `<div class="progress-ring-wrap">
    <svg class="progress-ring" width="52" height="52" viewBox="0 0 52 52">
      <circle class="bg" r="${r}" cx="26" cy="26"/>
      <circle class="fill" r="${r}" cx="26" cy="26" stroke="${color}"
        stroke-dasharray="${circ}" stroke-dashoffset="${circ}" data-final="${offset}"/>
    </svg>
    <span class="progress-ring-text">${pct}%</span>
  </div>`;
}

function renderPanel(stage) {
  const colors = STAGE_COLORS[stage.id];
  const numLabel = stage.id === 'x' ? '⊕' : (stage.id === 'a' ? '◈' : stage.id);
  const agentTags = stage.agents.map(a => `<span class="tag-agent">${a}</span>`).join('');
  const skillTags = stage.skills.map(s => `<span class="tag-skill">${s}</span>`).join('');
  const gateHtml = stage.gate ? `<span class="gate-badge">◆ ${stage.gate} ◆</span>` : '';
  const pct = stageCompleteness(stage);
  const ring = progressRing(pct, colors.hex);

  let content = '';
  if (stage.sections && stage.sections.length) {
    const tone = stage.sectionTone || (stage.id === 1 ? 's1' : null);
    content = stage.sections.map((sec, i) => renderSectionBlock(sec, i, tone)).join('');
    if (stage.htmlEmpty && !(stage.html && stage.html.length)) {
      content += `<div class="section-block"><div class="section-head"><span class="sec-num">◆</span><span class="sec-title">Gate 产出</span></div><div class="section-body">${renderPlaceholder(stage.htmlEmpty)}</div></div>`;
    }
  } else {
    let mdSection = stage.md.length ? stage.md.map(d => renderDocCard(d, 'md')).join('')
      : (stage.mdEmpty ? renderPlaceholder(stage.mdEmpty) : '<div class="doc-card placeholder"><div class="card-top"><div class="card-info"><div class="placeholder-text">本阶段暂无 MD 文档</div></div></div></div>');
    let htmlSection = stage.html.length ? stage.html.map(d => renderDocCard(d, 'html')).join('')
      : (stage.htmlEmpty ? renderPlaceholder(stage.htmlEmpty) : '<div class="doc-card placeholder"><div class="card-top"><div class="card-info"><div class="placeholder-text">本阶段暂无 HTML 报告</div></div></div></div>');
    content = `<div class="section-block">
      <div class="section-head"><span class="sec-num">1</span><span class="sec-title">MD 文档</span><span class="stat-badge md-count">${stage.md.length || 0} MD</span></div>
      <div class="section-body">${mdSection}</div></div>
      <div class="section-block">
      <div class="section-head"><span class="sec-num">2</span><span class="sec-title">HTML 报告</span><span class="stat-badge html-count">${stage.html.length || 0} HTML</span></div>
      <div class="section-body">${htmlSection}</div></div>`;
  }

  const toc = renderStageToc(stage);
  const guide = stage.guideHtml || '';

  return `<div class="view-panel stage-panel" data-hash="${stage.hash}">
    <div class="stage-head" style="background:${colors.bg}">
      <div class="row">
        <div class="stage-num" style="background:${colors.border}">${numLabel}</div>
        <div>
          <div class="stage-title">${stage.title}</div>
          <div class="stage-sub">${stage.subtitle}</div>
          ${(agentTags || skillTags) ? `<div class="stage-tags">${agentTags}${skillTags}</div>` : ''}
        </div>
        ${gateHtml}
      </div>
      ${ring}
    </div>
    ${toc}${guide}
    ${content}
  </div>`;
}

function renderPanels() {
  document.getElementById('panels').innerHTML = STAGES.map(renderPanel).join('');
}

function updateHeader(hash) {
  const header = document.getElementById('main-header');
  if (hash === 'dashboard') {
    header.innerHTML = `<h1>文档仪表盘</h1><p class="meta">Stage-Gate 全生命周期文档分布与完备度可视化</p>`;
    return;
  }
  if (hash === 'ai-workflow') {
    header.innerHTML = `<h1>AI 工作流</h1><p class="meta">总览视图 · Stage-Gate 设计思路 · Agent 配置关联 · 用 AI 做产品 · 附录案例</p>`;
    return;
  }
  const stage = STAGES.find(s => s.hash === hash);
  if (stage) {
    header.innerHTML = `<h1>${stage.title}</h1><p class="meta">${stage.subtitle}${stage.gate ? ' · ' + stage.gate : ''}</p>`;
  }
}

// ── ECharts ──
function initCharts() {
  if (typeof echarts === 'undefined') return;
  chartInstances.forEach(c => c.dispose());
  chartInstances = [];

  const textColor = '#725d42', mutedColor = '#9f927d';
  const fontFamily = "Nunito, 'Noto Sans SC', sans-serif";

  const allStages = STAGES.filter(s => s.id !== 't');
  const stageLabels = allStages.map(s => s.id === 'x' ? '管理员' : s.id === 'a' ? '智能体' : s.short);
  const mdData = allStages.map(s => stageDocs(s).md.length);
  const htmlData = allStages.map(s => stageDocs(s).html.length);

  const bar = echarts.init(document.getElementById('chart-stage-bar'));
  bar.setOption({
    color: ['#11a89b', '#889df0'],
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    legend: { data: ['MD', 'HTML'], bottom: 0, textStyle: { color: textColor, fontFamily } },
    grid: { left: 48, right: 24, top: 24, bottom: 48 },
    xAxis: { type: 'category', data: stageLabels, axisLabel: { color: textColor, fontFamily } },
    yAxis: { type: 'value', minInterval: 1, axisLabel: { color: mutedColor } },
    series: [
      { name: 'MD', type: 'bar', stack: 'total', data: mdData, itemStyle: { borderRadius: [0, 0, 0, 0] } },
      { name: 'HTML', type: 'bar', stack: 'total', data: htmlData, itemStyle: { borderRadius: [6, 6, 0, 0] },
        label: { show: true, position: 'top', formatter: p => { const i = p.dataIndex; return mdData[i] + htmlData[i] || ''; }, color: textColor } },
    ],
  });
  chartInstances.push(bar);

  const c = countDocs();
  const pie = echarts.init(document.getElementById('chart-format-pie'));
  pie.setOption({
    color: ['#11a89b', '#889df0'],
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{ type: 'pie', radius: ['42%', '68%'], center: ['50%', '48%'],
      data: [{ value: c.md, name: 'MD 源文档' }, { value: c.html, name: 'HTML 报告' }],
      label: { color: textColor, fontFamily, fontSize: 11 },
      emphasis: { itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,.12)' } },
    }],
  });
  chartInstances.push(pie);

  const radar = echarts.init(document.getElementById('chart-completeness'));
  radar.setOption({
    tooltip: {},
    radar: {
      indicator: LIFECYCLE_STAGES.map(s => ({ name: s.short, max: 100 })),
      axisName: { color: textColor, fontFamily, fontSize: 11 },
      splitArea: { areaStyle: { color: ['rgba(255,255,255,.4)', 'rgba(255,255,255,.2)'] } },
    },
    series: [{ type: 'radar',
      data: [{ value: LIFECYCLE_STAGES.map(stageCompleteness), name: '完备度',
        areaStyle: { color: 'rgba(25,200,185,.25)' }, lineStyle: { color: '#11a89b', width: 2 }, itemStyle: { color: '#11a89b' },
      }],
    }],
  });
  chartInstances.push(radar);

  const funnel = echarts.init(document.getElementById('chart-funnel'));
  funnel.setOption({
    color: LIFECYCLE_STAGES.map(s => STAGE_COLORS[s.id].hex),
    tooltip: { trigger: 'item', formatter: '{b}: {c} 份' },
    series: [{ type: 'funnel', left: '12%', width: '76%', top: 16, bottom: 16, sort: 'none', gap: 4,
      label: { show: true, position: 'inside', color: '#fff', fontSize: 11, fontWeight: 700 },
      data: LIFECYCLE_STAGES.map(s => ({ name: s.short, value: stageDocs(s).md.length + stageDocs(s).html.length })),
    }],
  });
  chartInstances.push(funnel);

  const gateChart = echarts.init(document.getElementById('chart-gate'));
  gateChart.setOption({
    color: ['#6fba2c', '#f5c31c', '#e05a5a'],
    tooltip: { trigger: 'axis' },
    grid: { left: 100, right: 40, top: 24, bottom: 32 },
    xAxis: { type: 'value', max: 100, axisLabel: { formatter: '{value}%', color: mutedColor } },
    yAxis: { type: 'category',
      data: ['Gate 1 PRD 评审', 'Gate 2 架构就绪', 'Gate 3 上线评审'],
      axisLabel: { color: textColor, fontFamily, fontSize: 11 },
    },
    series: [{ type: 'bar', barWidth: 20,
      data: [
        { value: 70, itemStyle: { color: '#11a89b', borderRadius: [0, 6, 6, 0] }, label: { show: true, position: 'right', formatter: 'PRD 齐全 · 缺 Gate 报告', color: textColor, fontSize: 10 } },
        { value: 85, itemStyle: { color: '#185FA5', borderRadius: [0, 6, 6, 0] }, label: { show: true, position: 'right', formatter: '架构+原型丰富', color: textColor, fontSize: 10 } },
        { value: 15, itemStyle: { color: '#e05a5a', borderRadius: [0, 6, 6, 0] }, label: { show: true, position: 'right', formatter: '完全空白 · 最大短板', color: textColor, fontSize: 10 } },
      ],
    }],
  });
  chartInstances.push(gateChart);
  chartsInited = true;
}

function resizeCharts() { chartInstances.forEach(c => c.resize()); }

// ── Activation & Animation ──
function activate(hash) {
  const target = hash || 'dashboard';
  const validHashes = ['dashboard', 'ai-workflow', ...STAGES.map(s => s.hash)];
  const h = validHashes.includes(target) ? target : 'dashboard';

  document.querySelectorAll('.nav-item').forEach(el => el.classList.toggle('active', el.dataset.hash === h));
  document.getElementById('dashboard-panel').classList.toggle('active', h === 'dashboard');
  const wf = document.getElementById('workflow-panel');
  if (wf) wf.classList.toggle('active', h === 'ai-workflow');
  document.querySelectorAll('.stage-panel').forEach(el => el.classList.toggle('active', el.dataset.hash === h));
  document.getElementById('stats-bar').style.display = h === 'dashboard' ? 'flex' : 'none';
  updateHeader(h);

  if (h === 'dashboard') {
    if (!chartsInited) initCharts(); else resizeCharts();
    animateDashboard();
  } else {
    animatePanel(h);
  }
}

function animateDashboard() {
  if (typeof anime === 'undefined') return;
  anime({ targets: '.kpi', translateY: [16, 0], opacity: [0, 1], delay: anime.stagger(60), duration: 500, easing: 'easeOutCubic' });
  anime({ targets: '.chart-card', translateY: [20, 0], opacity: [0, 1], delay: anime.stagger(80, { start: 200 }), duration: 600, easing: 'easeOutCubic' });
}

function animatePanel(hash) {
  if (typeof anime === 'undefined') return;
  const panel = document.querySelector(`.stage-panel[data-hash="${hash}"]`);
  if (!panel) return;
  // Stage head
  anime({ targets: panel.querySelector('.stage-head'), opacity: [0, 1], translateY: [-12, 0], duration: 450, easing: 'easeOutCubic' });
  // Progress ring
  const ring = panel.querySelector('.progress-ring .fill');
  if (ring) {
    const final = parseFloat(ring.dataset.final) || 0;
    anime({ targets: ring, strokeDashoffset: [ring.dataset.initial || ring.getAttribute('stroke-dasharray') || 126, final], duration: 1000, easing: 'easeOutCubic', delay: 300 });
  }
  // Section blocks
  anime({ targets: panel.querySelectorAll('.section-block'), opacity: [0, 1], translateY: [16, 0], delay: anime.stagger(60, { start: 150 }), duration: 500, easing: 'easeOutCubic' });
  // Kanban/doc cards
  anime({ targets: panel.querySelectorAll('.doc-card'), opacity: [0, 1], translateY: [10, 0], delay: anime.stagger(25, { start: 350 }), duration: 400, easing: 'easeOutCubic' });
}

// ── Init ──
function init() {
  const wfMount = document.getElementById('workflow-panel');
  if (wfMount && window.WORKFLOW_PANEL_HTML) wfMount.outerHTML = window.WORKFLOW_PANEL_HTML;

  renderSidebar();
  renderStats();
  renderKPIs();
  renderPanels();

  const hash = location.hash.slice(1);
  activate(hash || 'dashboard');

  document.querySelectorAll('.nav-item').forEach(el => {
    el.addEventListener('click', () => { location.hash = el.dataset.hash; activate(el.dataset.hash); });
  });
  window.addEventListener('hashchange', () => { activate(location.hash.slice(1)); });
  window.addEventListener('resize', () => { if (chartsInited) resizeCharts(); });

  document.getElementById('wf-toc')?.querySelectorAll('[data-scroll]').forEach(btn => {
    btn.addEventListener('click', () => { document.getElementById(btn.dataset.scroll)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  });
  document.querySelectorAll('.stage-toc [data-scroll]').forEach(btn => {
    btn.addEventListener('click', () => { document.getElementById(btn.dataset.scroll)?.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
  });
}

init();
