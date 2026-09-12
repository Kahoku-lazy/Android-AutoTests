/** skill-markdown — Markdown 渲染（DOMPurify 清洗） */
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import type { SkillTreeNode } from '../api/toolbox'

marked.setOptions({ gfm: true })

export function renderSkillMarkdown(src: string): string {
  const html = marked.parse(src, { async: false }) as string
  return DOMPurify.sanitize(html)
}

export function firstSkillFilePath(nodes: SkillTreeNode[]): string {
  for (const node of nodes) {
    if (!node.is_dir && node.name.toLowerCase() === 'skill.md') return node.path
  }
  for (const node of nodes) {
    if (node.is_dir) {
      const found = firstSkillFilePath(node.children || [])
      if (found) return found
    }
  }
  for (const node of nodes) {
    if (!node.is_dir) return node.path
  }
  return ''
}
