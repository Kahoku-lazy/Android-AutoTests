<script setup>
/**
 * GroupTreePanel — 共享分组树面板
 * WebElementManager 与 ApiEndpointManager 的树面板、右键菜单、创建/重命名/批量移动弹窗的共用实现
 */
defineProps({
  // Display config
  panelTitle: { type: String, default: '项目分组' },
  metaLabel: { type: String, default: '元素' },
  metaCountKey: { type: String, default: 'element_count' },
  // Tree state
  groups: { type: Array, default: () => [] },
  selectedGroup: { type: Object, default: null },
  loading: { type: Boolean, default: false },
  selectMode: { type: Boolean, default: false },
  selectedGroupIds: { type: Set, default: () => new Set() },
  dragEnabled: { type: Boolean, default: false },
  groupTree: { type: Array, default: () => [] },
  // Context menu
  menuVisible: { type: Boolean, default: false },
  menuX: { type: Number, default: 0 },
  menuY: { type: Number, default: 0 },
  menuNode: { type: Object, default: null },
  // Create/Rename dialogs
  showCreateGroup: { type: Boolean, default: false },
  createIsFolder: { type: Boolean, default: true },
  newGroupForm: { type: Object, default: () => ({ name: '' }) },
  showRenameDialog: { type: Boolean, default: false },
  renameTarget: { type: Object, default: null },
  renameLabel: { type: String, default: '' },
  // Batch move
  moveDialogVisible: { type: Boolean, default: false },
  moveTargetDirId: { type: [String, Number], default: null },
  folderList: { type: Array, default: () => [] },
  // Tree rendering
  nodeClass: { type: Function, default: () => ({}) },
  nodeIcon: { type: Function, default: () => '📄' },
  nodeName: { type: Function, default: (d) => d?.name || '' },
});

const emit = defineEmits([
  'select-group', 'tree-node-click', 'tree-contextmenu', 'tree-check', 'tree-node-drop',
  'create-group', 'rename-group', 'delete-group', 'batch-move',
  'update:showCreateGroup', 'update:showRenameDialog', 'update:moveDialogVisible',
  'update:moveTargetDirId', 'update:selectMode', 'update:selectedGroupIds',
  'node-mousedown', 'node-mouseup', 'node-mouseleave',
  'toggle-select-mode', 'handle-select-all', 'open-batch-move', 'confirm-batch-move',
  'do-create-group', 'do-rename',
]);
</script>

<template>
  <aside class="tree-panel">
    <div v-if="!selectMode" class="tree-header">
      <span class="tree-header__title">{{ panelTitle }}</span>
      <div class="tree-header__actions">
        <el-button size="small" plain @click="$emit('create-group', null, true)">📁 + 项目</el-button>
        <el-button size="small" type="primary" @click="$emit('create-group', null, false)">📄 + 模块</el-button>
        <el-button size="small" plain @click="$emit('toggle-select-mode')">☑ 选择</el-button>
      </div>
    </div>
    <div v-else class="tree-header tree-header--select">
      <span class="tree-header__title">已选 {{ selectedGroupIds.size }} 项</span>
      <div class="tree-header__actions">
        <el-button size="small" plain @click="$emit('handle-select-all')">☑ 全选</el-button>
        <el-button size="small" type="primary" :disabled="selectedGroupIds.size === 0" @click="$emit('open-batch-move')">📂 移动</el-button>
        <el-button size="small" plain @click="$emit('toggle-select-mode')">✕ 退出</el-button>
      </div>
    </div>

    <div class="tree-body" :class="{ 'drag-mode-active': dragEnabled }">
      <div v-if="loading && !groups.length" class="tree-loading">加载中...</div>
      <div v-else-if="!groups.length" class="tree-empty">
        <span class="tree-empty__icon">📁</span>
        <p class="tree-empty__text">暂无分组</p>
        <p class="tree-empty__hint">点击「+ 项目」或「+ 模块」创建</p>
      </div>
      <el-tree
        v-else
        ref="treeRef"
        :data="groupTree"
        :props="{ children: 'children', label: 'name' }"
        node-key="id"
        :indent="16"
        :expand-on-click-node="true"
        :highlight-current="!selectMode"
        :current-node-key="selectedGroup?.id"
        :show-checkbox="selectMode"
        :check-strictly="true"
        :draggable="!selectMode"
        :allow-drag="() => dragEnabled"
        :allow-drop="() => true"
        default-expand-all
        @node-click="emit('tree-node-click', $event)"
        @node-contextmenu="(evt, data) => emit('tree-contextmenu', evt, data)"
        @check="emit('tree-check', $event)"
        @node-drop="emit('tree-node-drop', $event)"
      >
        <template #default="{ data }">
          <span
            class="tree-node"
            :class="nodeClass(data)"
            @mousedown="emit('node-mousedown', $event, data)"
            @mouseup="emit('node-mouseup')"
            @mouseleave="emit('node-mouseleave')"
          >
            <span class="tree-node__icon">{{ nodeIcon(data) }}</span>
            <span class="tree-node__name" :title="data.name">{{ nodeName(data) }}</span>
            <span v-if="data[metaCountKey]" class="tree-node__meta">{{ data[metaCountKey] }} {{ metaLabel }}</span>
            <span v-else-if="data.is_folder && data.child_count" class="tree-node__meta">{{ data.child_count }} 项</span>
          </span>
        </template>
      </el-tree>

      <div
        v-if="groups.length"
        class="tree-node tree-node--page ungrouped-node"
        :class="{ 'tree-node--active': selectedGroup?.id === '__ungrouped__' }"
        @click="$emit('select-group', { id: '__ungrouped__', name: '未分类', is_folder: false })"
      >
        <span class="tree-node__icon">📄</span>
        <span class="tree-node__name">未分类</span>
      </div>
    </div>

    <!-- Context menu -->
    <div v-if="menuVisible && menuNode" class="context-menu" :style="{ left: menuX + 'px', top: menuY + 'px' }" @click.stop>
      <template v-if="menuNode.is_folder">
        <div class="context-menu__item" @click="$emit('create-group', menuNode.id, true); $emit('update:menuVisible', false)">+ 新建子目录</div>
        <div class="context-menu__item" @click="$emit('create-group', menuNode.id, false); $emit('update:menuVisible', false)">+ 新建模块</div>
      </template>
      <div class="context-menu__item" @click="$emit('rename-group', menuNode); $emit('update:menuVisible', false)">✏️ 重命名</div>
      <div class="context-menu__divider" />
      <div class="context-menu__item context-menu__item--danger" @click="$emit('delete-group', menuNode); $emit('update:menuVisible', false)">🗑️ 删除</div>
    </div>
  </aside>

  <!-- Create Group Dialog -->
  <el-dialog
    :model-value="showCreateGroup"
    :title="createIsFolder ? '新建项目' : '新建模块'"
    width="400px"
    @close="$emit('update:showCreateGroup', false)"
  >
    <div class="form-grid">
      <label class="form-label required">
        {{ createIsFolder ? '项目名称' : '模块名称' }}
      </label>
      <el-input v-model="newGroupForm.name" :placeholder="createIsFolder ? '如：登录模块' : '如：登录页'" maxlength="30" @keyup.enter="$emit('do-create-group')" />
    </div>
    <template #footer>
      <el-button class="wb-btn" @click="$emit('update:showCreateGroup', false)">取消</el-button>
      <el-button class="wb-btn" type="primary" :disabled="!newGroupForm.name.trim()" @click="$emit('do-create-group')">{{ createIsFolder ? '创建项目' : '创建模块' }}</el-button>
    </template>
  </el-dialog>

  <!-- Rename Dialog -->
  <el-dialog
    :model-value="showRenameDialog"
    :title="'重命名：' + (renameTarget?.name || '')"
    width="400px"
    @close="$emit('update:showRenameDialog', false)"
  >
    <div class="form-grid">
      <label class="form-label required">新名称</label>
      <el-input :model-value="renameLabel" maxlength="30" @update:model-value="$emit('update:renameLabel', $event)" @keyup.enter="$emit('do-rename')" />
    </div>
    <template #footer>
      <el-button class="wb-btn" @click="$emit('update:showRenameDialog', false)">取消</el-button>
      <el-button class="wb-btn" type="primary" :disabled="!renameLabel.trim()" @click="$emit('do-rename')">确认</el-button>
    </template>
  </el-dialog>

  <!-- Batch Move Dialog -->
  <el-dialog
    :model-value="moveDialogVisible"
    title="移动到..."
    width="400px"
    @close="$emit('update:moveDialogVisible', false)"
  >
    <div class="form-grid">
      <label class="form-label required">目标目录</label>
      <el-select :model-value="moveTargetDirId" placeholder="选择目标目录" style="width: 100%" @update:model-value="(v) => $emit('update:moveTargetDirId', v)">
        <el-option v-for="dir in folderList" :key="dir.value" :label="dir.label" :value="dir.value" />
      </el-select>
    </div>
    <template #footer>
      <el-button class="wb-btn" @click="$emit('update:moveDialogVisible', false)">取消</el-button>
      <el-button class="wb-btn" type="primary" :disabled="!moveTargetDirId" @click="$emit('confirm-batch-move')">确认移动</el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
/* ── Tree Panel ── */
.tree-panel {
  width: 260px; min-width: 220px;
  background: var(--app-bg-card); border: 3px solid var(--ink);
  border-radius: var(--app-radius-md); display: flex; flex-direction: column;
  overflow: hidden;
}
.tree-header {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding: var(--app-space-sm) var(--app-space-md);
  border-bottom: 2px solid var(--ink);
  background: var(--app-bg-card);
  border-radius: 6px 10px 0 0;
  flex-shrink: 0;
}
.tree-header--select { background: var(--app-highlight); }
.tree-header__title { font-weight: 700; font-size: 13px; color: var(--ink); }
.tree-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: center;
}
.tree-header__actions :deep(.el-button) {
  font-size: var(--app-size-xs);
  padding: 4px 8px;
}
.tree-body { flex: 1 1 0; min-height: 0; overflow-y: auto; padding: 6px 0; }
.tree-body.drag-mode-active { background: rgba(255,224,102,0.15); }
.tree-loading { text-align: center; padding: 20px; color: var(--app-text-secondary); font-size: var(--app-size-sm); }
.tree-empty { text-align: center; padding: 30px 16px; }
.tree-empty__icon { font-size: 32px; display: block; margin-bottom: 8px; }
.tree-empty__text { color: var(--app-text-secondary); font-size: var(--app-size-sm); margin: 0; }
.tree-empty__hint { color: #bbb; font-size: var(--app-size-xs); margin: 4px 0 0; }

/* ── Tree Node ── */
.tree-node {
  display: flex; align-items: center; gap: 4px; padding: 3px 8px;
  font-size: 13px; cursor: pointer; border-radius: 4px;
  transition: background var(--app-duration-fast) var(--app-ease);
}
.tree-node:hover { background: var(--app-highlight); }
.tree-node--active { background: var(--app-highlight); font-weight: 700; }
.tree-node--folder { font-weight: 600; }
.tree-node__icon { font-size: 14px; flex-shrink: 0; }
.tree-node__name { flex: 1; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tree-node__meta { font-size: var(--app-size-xs); color: var(--app-text-secondary); flex-shrink: 0; padding-left: 4px; }

.ungrouped-node { border-top: 1px dashed var(--app-border-lighter); margin-top: 4px; padding-top: 7px; }
.ungrouped-node:hover { background: var(--app-highlight); }
.ungrouped-node.tree-node--active { background: var(--app-highlight); }

/* ── Context Menu ── */
.context-menu {
  /* z-index 70 = 弹窗层（.agents/skills/android-autotests-rules/references/frontend.md z-index 层级） */
  position: fixed; z-index: 70; background: var(--app-bg-card);
  border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  box-shadow: var(--app-shadow-lg); min-width: 160px; padding: var(--app-space-xs) 0;
}
.context-menu__item {
  padding: 8px 14px; font-size: 13px; cursor: pointer;
  transition: background var(--app-duration-fast) var(--app-ease);
}
.context-menu__item:hover { background: var(--app-highlight); }
.context-menu__item--danger { color: var(--app-status-danger-text); }
.context-menu__item--danger:hover { background: var(--app-status-danger-bg); }
.context-menu__divider { height: 1px; background: var(--app-border-lighter); margin: 4px 0; }

/* ── Form Grid ── */
.form-grid { display: flex; flex-direction: column; gap: 8px; }
.form-label { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); }
.form-label.required::after { content: ' *'; color: var(--app-status-danger); }
</style>
