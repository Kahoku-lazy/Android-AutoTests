/**
 * workflow 模块常量 — 工作流工作台
 *
 * 提取自 index.vue 和各 store，避免魔法值散落。
 */

// ── 节点类型 ──
export const NODE_TYPES = {
  FOLDER: 'folder',
  PAGE_FLOW: 'page_flow',
  TEST_CASE: 'test_case',
}

// ── 节点类型中文标签 ──
export const NODE_TYPE_LABELS = {
  [NODE_TYPES.PAGE_FLOW]: '页面流',
  [NODE_TYPES.TEST_CASE]: '测试用例',
}

// ── 默认名称 ──
export const DEFAULT_NAMES = {
  FOLDER: '默认目录',
  ROOT_FOLDER: '新建目录',
  CHILD_FOLDER: '新建子目录',
  PAGE_FLOW: '未命名页面流',
  TEST_CASE: '未命名用例',
  PACKAGE_NAME: 'com.example.app',
}

// ── 步骤类型 ──
export const STEP_TYPES = {
  CLICK: 'click',
  WAIT: 'wait',
}

// ── 超时默认值 (秒) ──
export const TIMEOUT_DEFAULTS = {
  WAIT: 10,
  DEFAULT: 5,
}

// ── 表单限制 ──
export const MAX_FOLDER_NAME_LENGTH = 80

// ── 消息 ──
export const MESSAGES = {
  EDITOR_CLOSED: '已关闭编辑',
  IMPORT_JSON_FAILED: 'JSON 解析失败',
  NO_ELEMENT_ON_PORT: '该端口没有关联元素',
  ENTER_FOLDER_NAME: '请输入目录名称',
  ROOT_HINT: '将创建在资源树根级',
  CHILD_HINT: (name) => `将创建为子目录：${name}`,
  PARENT_HINT: (name) => `父目录：${name}`,
  SAVED: (name, parent, id) => `已保存「${name}」→ ${parent} · ${id}`,
  FLOW_CREATED: (id) => `已创建页面流（${id}）`,
  CASE_CREATED: (id) => `已创建测试用例（${id}）`,
  IMPORTED_COUNT: (n) => `已从用例库导入 ${n} 条`,
  EXPORTED: (id) => `已导出 ${id}`,
  STEP_ADDED: (name) => `已添加步骤「${name}」`,
  CASE_FROM_PORT: (name) => `用例-${name}`,
}

// ── 面包屑 ──
export const BREADCRUMB = {
  PREFIX: '资源 / ',
  ALL: '资源 / 全部',
  ROOT: '根目录',
  EDITING: '编辑',
  ELLIPSIS: '…',
}

// ── UI 按钮标签 ──
export const UI_LABELS = {
  IMPORT_JSON: '导入 JSON',
  OVERWRITE: '同 ID 覆盖',
  CLOSE_EDITOR: '关闭编辑',
  EXPORT_JSON: '导出 JSON',
  SAVE: '保存',
  FOLDER_NAME: '目录名称',
  CANCEL: '取消',
  CONFIRM: '确定',
}

// ── 默认导出 MIME ──
export const EXPORT_MIME = 'application/json'
export const IMPORT_ACCEPT = '.json'
