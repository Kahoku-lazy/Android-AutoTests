/** useMarkdown — Markdown 渲染 + Mermaid 图表支持 */
import { nextTick } from 'vue'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import mermaid from 'mermaid'

mermaid.initialize({
  startOnLoad: false,
  theme: 'base',
  securityLevel: 'strict',
  themeVariables: {
    primaryColor: '#19c8b9',
    primaryTextColor: '#4A3A28',
    lineColor: '#8a7b66',
    fontSize: '14px',
  },
})

let mermaidId = 0
const pendingMermaidBlocks: { id: string; code: string }[] = []

// Custom renderer: intercept mermaid code blocks, replace with placeholder divs
const mermaidRenderer = {
  code(code: string | { text?: string }, lang?: string): string {
    const codeStr = typeof code === 'string' ? code : code?.text || String(code || '')
    if (lang === 'mermaid') {
      const id = `mm-${++mermaidId}`
      const escaped = codeStr
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
      pendingMermaidBlocks.push({ id, code: codeStr })
      return `<div class="mermaid-placeholder" data-mm-id="${id}"><pre><code class="language-mermaid">${escaped}</code></pre></div>`
    }
    const escaped = codeStr
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
    return `<pre><code class="language-${lang || ''}">${escaped}</code></pre>`
  },
}

marked.use({ renderer: mermaidRenderer })

export function renderMarkdown(text: string): string {
  if (!text) return ''
  pendingMermaidBlocks.length = 0
  const raw = marked.parse(String(text), { breaks: true, gfm: true }) as string
  return DOMPurify.sanitize(raw, { ADD_ATTR: ['data-mm-id', 'target', 'href'] })
}

/** Lightweight markdown → HTML, no sanitization. For streaming only. */
export function renderMarkdownLight(text: string): string {
  if (!text) return ''
  return marked.parse(String(text), { breaks: true, gfm: true }) as string
}

export function sanitizeHtml(html: string): string {
  if (!html) return ''
  return DOMPurify.sanitize(html)
}

export async function renderMermaidBlocks(): Promise<void> {
  if (!pendingMermaidBlocks.length) return
  const jobs = pendingMermaidBlocks.splice(0)
  await nextTick()
  await new Promise(r => requestAnimationFrame(r))
  for (const { id, code } of jobs) {
    const placeholder = document.querySelector(`[data-mm-id="${id}"]`) as HTMLElement | null
    if (!placeholder) continue
    try {
      const { svg } = await mermaid.render(id, code)
      const wrapper = document.createElement('div')
      wrapper.className = 'mermaid-diagram'
      wrapper.innerHTML = svg
      placeholder.replaceWith(wrapper)
    } catch {
      placeholder.classList.remove('mermaid-placeholder')
      placeholder.removeAttribute('data-mm-id')
    }
  }
}
