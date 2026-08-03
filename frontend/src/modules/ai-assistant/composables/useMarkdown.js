import { nextTick } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";
import mermaid from "mermaid";

mermaid.initialize({
  startOnLoad: false,
  theme: "base",
  securityLevel: "strict",
  themeVariables: {
    primaryColor: "#19c8b9",
    primaryTextColor: "#4A3A28",
    lineColor: "#8a7b66",
    fontSize: "14px",
  },
});

let mermaidId = 0;
let pendingMermaidBlocks = [];

const mermaidRenderer = {
  code(code, lang) {
    // marked v5+ passes a token object; normalize to string
    const codeStr = typeof code === "string" ? code : code?.text || String(code || "");
    if (lang === "mermaid") {
      const id = `mm-${++mermaidId}`;
      const escaped = codeStr
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
      pendingMermaidBlocks.push({ id, code: codeStr });
      return `<div class="mermaid-placeholder" data-mm-id="${id}"><pre><code class="language-mermaid">${escaped}</code></pre></div>`;
    }
    const escaped = codeStr
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
    return `<pre><code class="language-${lang || ""}">${escaped}</code></pre>`;
  },
};
marked.use({ renderer: mermaidRenderer });

export function renderMarkdown(text) {
  if (!text) return "";
  pendingMermaidBlocks = [];
  const raw = marked.parse(String(text), { breaks: true, gfm: true });
  return DOMPurify.sanitize(raw);
}

/** Lightweight markdown → HTML, no sanitization. For streaming only. */
export function renderMarkdownLight(text) {
  if (!text) return "";
  return marked.parse(String(text), { breaks: true, gfm: true });
}

export function sanitizeHtml(html) {
  if (!html) return "";
  return DOMPurify.sanitize(html);
}

export async function renderMermaidBlocks() {
  if (!pendingMermaidBlocks.length) return;
  const jobs = pendingMermaidBlocks.splice(0);
  await nextTick();
  await new Promise((r) => requestAnimationFrame(r));
  for (const { id, code } of jobs) {
    const placeholder = document.querySelector(`[data-mm-id="${id}"]`);
    if (!placeholder) continue;
    try {
      const { svg } = await mermaid.render(id, code);
      const wrapper = document.createElement("div");
      wrapper.className = "mermaid-diagram";
      wrapper.innerHTML = svg;
      placeholder.replaceWith(wrapper);
    } catch {
      placeholder.classList.remove("mermaid-placeholder");
      placeholder.removeAttribute("data-mm-id");
    }
  }
}
