/** kb-tree — 知识库文档按 dev_docs/ 本地目录层级构建折叠树 */

// ── 类型 ──

export interface KbDoc {
  id: string
  source?: string
  type?: string
  size?: number
  [key: string]: unknown
}

export interface KbTreeNode {
  /** 唯一键：目录 dir:相对路径；文件 doc id；兜底组 group:xxx */
  key: string
  label: string
  type: 'dir' | 'file' | 'group'
  /** dir → 相对路径；file → source；group → 组名 */
  path: string
  children?: KbTreeNode[]
  doc?: KbDoc
}

export type KbTreeSelectKey = string

// ── 树构建 ──

/** 文档 source 是否位于某个目录引用（dir:）范围内 */
export function isDirKey(key: string): boolean {
  return key.startsWith('dir:')
}

/** dir 键 → 相对路径（去掉前缀） */
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

/** 平铺文档列表 → 目录折叠树（非 dev_docs 来源归入「其他/参考」兜底组） */
export function buildKbTree(docs: KbDoc[]): KbTreeNode[] {
  const roots: KbTreeNode[] = []
  const dirMap = new Map<string, KbTreeNode>()
  const otherGroup: KbTreeNode = {
    key: 'group:other',
    label: '其他/参考',
    type: 'group',
    path: '其他/参考',
    children: [],
  }

  for (const doc of [...docs].sort((a, b) => (a.source || '').localeCompare(b.source || '', 'zh'))) {
    const src = doc.source || doc.id || ''
    const parts = src.split('/')
    if (doc.type === 'project_doc' && parts.length > 1) {
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
        key: doc.id,
        label: parts[parts.length - 1],
        type: 'file',
        path: src,
        doc,
      })
    } else if (doc.type === 'project_doc') {
      // dev_docs 根目录直属文件
      roots.push({ key: doc.id, label: src, type: 'file', path: src, doc })
    } else {
      otherGroup.children?.push({ key: doc.id, label: src || doc.id, type: 'file', path: src || doc.id, doc })
    }
  }

  if (otherGroup.children?.length) roots.push(otherGroup)
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
