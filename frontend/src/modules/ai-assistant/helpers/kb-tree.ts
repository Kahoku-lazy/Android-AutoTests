/** kb-tree — 知识库文档按 data/rag_datas 相对路径构建折叠树 */

// ── 类型 ──

export interface KbDoc {
  id: string
  source?: string
  type?: string
  size?: number
  [key: string]: unknown
}

export interface KbTreeNode {
  /** 唯一键：目录 dir:相对路径；文件 doc id */
  key: string
  label: string
  type: 'dir' | 'file' | 'group'
  /** dir → 相对路径；file → source */
  path: string
  children?: KbTreeNode[]
  doc?: KbDoc
}

export type KbTreeSelectKey = string

// ── 树构建 ──

export function isDirKey(key: string): boolean {
  return key.startsWith('dir:')
}

export function dirKeyToPath(key: string): string {
  return key.replace(/^dir:/, '')
}

const _sortNodes = (nodes: KbTreeNode[]) => {
  const order = { group: 0, dir: 1, file: 2 } as const
  nodes.sort((a, b) => {
    if (order[a.type] !== order[b.type]) return order[a.type] - order[b.type]
    return (a.label || '').localeCompare(b.label || '', 'zh')
  })
  for (const n of nodes) {
    if (n.children) _sortNodes(n.children)
  }
}

/** 平铺文档列表 → 按相对路径的目录折叠树 */
export function buildKbTree(docs: KbDoc[]): KbTreeNode[] {
  const roots: KbTreeNode[] = []
  const dirMap = new Map<string, KbTreeNode>()

  for (const doc of [...docs].sort((a, b) => (a.source || '').localeCompare(b.source || '', 'zh'))) {
    const src = String(doc.source || doc.id || '').replace(/\\/g, '/')
    const parts = src.split('/').filter(Boolean)
    if (!parts.length) continue
    let parentChildren = roots
    let currentPath = ''
    for (let i = 0; i < parts.length - 1; i++) {
      currentPath = currentPath ? `${currentPath}/${parts[i]}` : parts[i]
      let node = dirMap.get(currentPath)
      if (!node) {
        node = {
          key: `dir:${currentPath}`,
          label: parts[i],
          type: 'dir',
          path: currentPath,
          children: [],
        }
        dirMap.set(currentPath, node)
        parentChildren.push(node)
      }
      parentChildren = node.children as KbTreeNode[]
    }
    parentChildren.push({
      key: String(doc.id),
      label: parts[parts.length - 1],
      type: 'file',
      path: src,
      doc,
    })
  }

  _sortNodes(roots)
  return roots
}

/** 收集节点下全部文件键（doc id） */
export function collectFileKeys(nodes: KbTreeNode[]): string[] {
  const keys: string[] = []
  const walk = (list: KbTreeNode[]) => {
    for (const n of list) {
      if (n.type === 'file') keys.push(n.key)
      else if (n.children) walk(n.children)
    }
  }
  walk(nodes)
  return keys
}
