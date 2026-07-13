/* ════════════════ MD Viewer — in-browser Markdown + Mermaid renderer ════════════════ */
(function () {
  'use strict';

  /* ── Mermaid init ── */
  if (typeof mermaid !== 'undefined') {
    mermaid.initialize({
      startOnLoad: false,
      theme: 'neutral',
      securityLevel: 'loose',
      fontFamily: "Nunito, 'Noto Sans SC', sans-serif",
    });
  }

  /* ── Build overlay DOM once ── */
  const overlay = document.createElement('div');
  overlay.className = 'md-viewer-overlay';
  overlay.innerHTML = `
    <div class="md-viewer">
      <div class="md-viewer-bar">
        <span class="mdv-icon">📄</span>
        <span class="mdv-path"></span>
        <span class="mdv-badge">Markdown 渲染</span>
        <button class="md-viewer-close" title="关闭 (Esc)">✕</button>
      </div>
      <div class="md-viewer-body"></div>
    </div>`;
  document.body.appendChild(overlay);

  const bodyEl = overlay.querySelector('.md-viewer-body');
  const pathEl = overlay.querySelector('.mdv-path');
  const closeBtn = overlay.querySelector('.md-viewer-close');

  /* ── Close ── */
  function close() {
    overlay.classList.remove('open');
    document.body.style.overflow = '';
  }

  closeBtn.addEventListener('click', close);
  overlay.addEventListener('click', function (e) {
    if (e.target === overlay) close();
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.classList.contains('open')) close();
  });

  /* ── Marked config ── */
  if (typeof marked !== 'undefined') {
    marked.setOptions({
      breaks: false,
      gfm: true,
    });
  }

  /* ── Render mermaid blocks ── */
  async function renderMermaidBlocks(container) {
    if (typeof mermaid === 'undefined') return;
    const wraps = container.querySelectorAll('.mermaid-wrap');
    for (let i = 0; i < wraps.length; i++) {
      const wrap = wraps[i];
      const svgTarget = wrap.querySelector('.mermaid-svg');
      const graphDefinition = wrap.getAttribute('data-mermaid');
      if (!svgTarget || !graphDefinition) continue;
      try {
        const id = 'mermaid-' + Date.now() + '-' + i;
        const { svg } = await mermaid.render(id, graphDefinition);
        svgTarget.innerHTML = svg;
      } catch (err) {
        svgTarget.innerHTML =
          '<div style="color:var(--error);font-size:12px;padding:12px">⚠️ Mermaid 渲染失败: ' +
          (err.message || err) +
          '</div>';
      }
    }
  }

  /* ── Pre-process markdown: extract mermaid blocks before marked ── */
  function preprocessMermaid(md) {
    const mermaidBlocks = [];
    // Match ```mermaid ... ``` blocks (allow optional info string after "mermaid")
    const replaced = md.replace(
      /```mermaid\s*\n([\s\S]*?)```/g,
      function (match, code) {
        const idx = mermaidBlocks.length;
        mermaidBlocks.push(code.trim());
        return '<!--MERMAID_' + idx + '-->';
      }
    );
    return { md: replaced, mermaidBlocks };
  }

  /* ── Restore mermaid placeholders as wrappers ── */
  function restoreMermaidPlaceholders(html, mermaidBlocks) {
    return html.replace(/<!--MERMAID_(\d+)-->/g, function (match, idx) {
      const code = mermaidBlocks[parseInt(idx)] || '';
      const escaped = code
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
      return (
        '<div class="mermaid-wrap" data-mermaid="' +
        escaped +
        '">' +
        '<span class="mermaid-tag">🧜 mermaid</span>' +
        '<div class="mermaid-svg"></div>' +
        '</div>'
      );
    });
  }

  /* ── Add lang labels to regular code blocks ── */
  function addCodeLangLabels(html) {
    return html.replace(
      /<pre><code class="language-(\w+)">/g,
      '<pre data-lang="$1"><code class="language-$1">'
    );
  }

  /* ── Open & render ── */
  async function openMd(path) {
    bodyEl.innerHTML =
      '<div class="md-viewer-loading"><div class="spinner"></div><span>加载中...</span></div>';
    pathEl.textContent = path;
    overlay.classList.add('open');
    document.body.style.overflow = 'hidden';

    try {
      const resp = await fetch(path);
      if (!resp.ok) {
        throw new Error('HTTP ' + resp.status + ' ' + resp.statusText);
      }
      const rawMd = await resp.text();

      // Pre-process: extract mermaid blocks
      const { md: cleanMd, mermaidBlocks } = preprocessMermaid(rawMd);

      // Render markdown → HTML
      let html;
      if (typeof marked !== 'undefined') {
        html = marked.parse(cleanMd);
      } else {
        // Fallback: basic rendering
        html = '<pre>' + escapeHtml(cleanMd) + '</pre>';
      }

      // Restore mermaid placeholders
      html = restoreMermaidPlaceholders(html, mermaidBlocks);

      // Add language labels to code blocks
      html = addCodeLangLabels(html);

      bodyEl.innerHTML = html;

      // Render mermaid diagrams
      await renderMermaidBlocks(bodyEl);

      // Scroll to top
      overlay.scrollTop = 0;
    } catch (err) {
      bodyEl.innerHTML =
        '<div class="md-viewer-error"><div class="err-icon">⚠️</div><div class="err-msg">加载失败: ' +
        (err.message || err) +
        '</div><div style="font-size:11px;color:var(--text-muted);margin-top:8px">路径: ' +
        path +
        '</div></div>';
    }
  }

  function escapeHtml(str) {
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /* ── Intercept clicks on MD doc cards ── */
  document.addEventListener('click', function (e) {
    // Find closest doc-card link
    var card = e.target.closest('.doc-card');
    if (!card) return;

    var href = card.getAttribute('href');
    if (!href) return;

    // Only intercept .md files
    if (!/\.md$/i.test(href)) return;

    e.preventDefault();
    e.stopPropagation();

    // Resolve relative path from index.html location
    openMd(href);
  });

  /* ── Expose for programmatic use ── */
  window.MdViewer = { open: openMd, close: close };
})();
