<script setup>

import AppCard from "@/shared/components/AppCard.vue";
import AppTabs from "@/shared/components/AppTabs.vue";
import AppTable from "@/shared/components/AppTable.vue";
import { ref, computed, nextTick, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { animate, stagger } from 'animejs'
import { apiAddElementToPage, apiUpdateElement } from '../api.js'
import { useElementTree } from '../composables/useElementTree.js'
import { usePagination } from '@/shared/composables/usePagination.js'

const {
  pages, selectedPage, elements, loading, maxDepth, treeRef,
  menuVisible, menuX, menuY, menuNode,
  showCreatePage, createParentId, createIsFolder, newPageForm, createDialogTitle,
  showRenameDialog, renameTarget, renameLabel,
  selectedPageIds, showClearDialog, clearSelectedOnly,
  dragEnabled, selectMode,
  moveDialogVisible, moveTargetDirId,
  pageTree, allCheckableIds, checkedCount, folderList,
  canCreateSubFolder, openCreatePage, openCreateFolder, doCreatePage,
  startEditLabel, doRename,
  selectPage, deletePage, openClearDialog, doClearPages,
  loadPages,
  onNodeMouseDown, onNodeMouseUp, onNodeMouseLeave,
  allowDrag, allowDrop, handleNodeDrop,
  toggleSelectMode, handleSelectAll, openBatchMoveDialog, confirmBatchMove,
  handleContextMenu, closeMenu,
  handleTreeNodeClick, handleTreeCheck, nodeClass, nodeIcon, pageLabel,
} = useElementTree()

// ── "+" button animation ──
const plusFolderRef = ref(null)
const plusPageRef = ref(null)
let plusAnimeInstances = []

function startPlusAnimation() {
  stopPlusAnimation()
  ;[plusFolderRef.value, plusPageRef.value].forEach((el) => {
    if (!el) return
    plusAnimeInstances.push(animate(el, {
      scale: [1, 1.25, 1],
      duration: 1800,
      loop: true,
      ease: 'inOutSine',
    }))
  })
}
function stopPlusAnimation() {
  plusAnimeInstances.forEach(inst => { try { inst.pause() } catch (_) {} })
  plusAnimeInstances = []
}
onMounted(() => { nextTick(() => startPlusAnimation()) })
onUnmounted(() => stopPlusAnimation())

const showAddElement = ref(false)
const newElForm = ref({ alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false })

function openAddElement() {
  newElForm.value = { alias: '', xpath: '', class_name: '', text_val: '', resource_id: '', bounds: '', clickable: false }
  showAddElement.value = true
}

async function doAddElement() {
  if (!newElForm.value.alias.trim()) { ElMessage.warning('请输入元素名称'); return }
  try {
    const { data } = await apiAddElementToPage(selectedPage.value.id, newElForm.value)
    if (data.ok) { showAddElement.value = false; await selectPage(selectedPage.value) }
  } catch (e) { ElMessage.error(e?.response?.data?.error || '添加元素失败，请检查网络连接') }
}

const filterMode = ref('all')
const filterTabs = [
  { key: 'all', label: '全部' },
  { key: 'test_point', label: '测试点' },
]
const filteredElements = computed(() =>
  filterMode.value === 'test_point' ? elements.value.filter((e) => e.is_test_point) : elements.value)

const {
  PAGE_SIZE_OPTIONS, pageSize, currentPage, totalPages, pagedItems: pagedElements, setPageSize, goPage
} = usePagination(filteredElements)

const columns = [
  { title: '别名', dataIndex: 'alias', key: 'alias', minWidth: 160 },
  { title: 'XPath', dataIndex: 'xpath', key: 'xpath', minWidth: 320 },
  { title: '类名', dataIndex: 'class_name', key: 'class_name', minWidth: 160 },
  { title: '文本', dataIndex: 'text_val', key: 'text_val', minWidth: 160 },
  { title: 'Resource ID', dataIndex: 'resource_id', key: 'resource_id', minWidth: 220 },
  { title: '可点击', dataIndex: 'clickable', key: 'clickable', minWidth: 100, align: 'center' },
  { title: '测试点', dataIndex: 'is_test_point', key: 'is_test_point', minWidth: 100, align: 'center' },
]

async function updateEl(record, field, value) {
  try {
    const { data } = await apiUpdateElement(record.id, { [field]: value })
    if (!data.ok) ElMessage.error(data.error || '更新失败')
  } catch (_) { ElMessage.error('更新失败，请检查网络') }
}
</script>
<template>
  <div class="element-manager">
    <div class="main-layout">
        <!-- Left: Page tree -->
        <aside class="page-tree-panel">
          <div v-if="!selectMode" class="tree-header">
            <span class="tree-header__title">页面目录</span>
            <div class="tree-header__actions">
              <el-button size="small" plain @click="openCreateFolder()">
                📁 <span ref="plusFolderRef" class="plus-sign">+</span> 目录
              </el-button>
              <el-button size="small" type="primary" @click="openCreatePage()">
                📄 <span ref="plusPageRef" class="plus-sign">+</span> 页面
              </el-button>
              <el-button size="small" plain @click="toggleSelectMode">☑ 选择</el-button>
              <el-button size="small" type="danger" plain @click="openClearDialog">🗑 清空</el-button>
            </div>
          </div>
          <div v-else class="tree-header tree-header--select">
            <span class="tree-header__title">已选 {{ checkedCount }} 项</span>
            <div class="tree-header__actions">
              <el-button size="small" plain @click="handleSelectAll">
                {{ selectAll ? '☐ 取消全选' : '☑ 全选' }}
              </el-button>
              <el-button
                size="small"
                type="primary"
                :disabled="checkedCount === 0"
                @click="openBatchMoveDialog"
              >📂 移动</el-button>
              <el-button size="small" type="danger" plain :disabled="checkedCount === 0" @click="openClearDialog">
                🗑 删除
              </el-button>
              <el-button size="small" plain @click="toggleSelectMode">✕ 退出</el-button>
            </div>
          </div>
          <div class="tree-body" :class="{ 'drag-mode-active': dragEnabled }">
            <div v-if="loading && !pages.length" class="tree-loading">加载中...</div>
            <div v-else-if="!pages.length" class="tree-empty">
              <span class="tree-empty__icon">📁</span>
              <p class="tree-empty__text">暂无页面</p>
              <p class="tree-empty__hint">点击「+ 目录」或「+ 页面」创建</p>
            </div>
            <el-tree
              v-else
              ref="treeRef"
              :data="pageTree"
              :props="{ children: 'children', label: 'label' }"
              node-key="id"
              :indent="16"
              :expand-on-click-node="true"
              :highlight-current="!selectMode"
              :current-node-key="selectedPage?.id"
              :show-checkbox="selectMode"
              :check-strictly="true"
              :draggable="!selectMode"
              :allow-drag="allowDrag"
              :allow-drop="allowDrop"
              default-expand-all
              @node-click="handleTreeNodeClick"
              @node-contextmenu="handleContextMenu"
              @check="handleTreeCheck"
              @node-drop="handleNodeDrop"
            >
              <template #default="{ data }">
                <span
                  class="tree-node"
                  :class="nodeClass(data)"
                  @mousedown="onNodeMouseDown($event, data)"
                  @mouseup="onNodeMouseUp"
                  @mouseleave="onNodeMouseLeave"
                >
                  <span class="tree-node__icon">{{ nodeIcon(data) }}</span>
                  <span class="tree-node__name" :title="data.label">{{ data.label || `Page #${data.id}` }}</span>
                  <span v-if="!data.is_folder" class="tree-node__meta">{{ data.element_count ?? 0 }} 元素</span>
                  <span v-else-if="data.children?.length" class="tree-node__meta">{{ data.children.length }} 项</span>
                </span>
              </template>
            </el-tree>
          </div>
        </aside>

        <!-- Context menu -->
        <div
          v-if="menuVisible && menuNode"
          class="context-menu"
          :style="{ left: menuX + 'px', top: menuY + 'px' }"
          @click.stop
        >
          <template v-if="menuNode.is_folder">
            <div
              v-if="canCreateSubFolder(menuNode.id)"
              class="context-menu__item"
              @click="openCreateFolder(menuNode.id); closeMenu()"
            >+ 新建子目录</div>
            <div class="context-menu__item" @click="openCreatePage(menuNode.id); closeMenu()">+ 新建页面</div>
          </template>
          <div class="context-menu__item" @click="startEditLabel(menuNode); closeMenu()">✏️ 重命名</div>
          <div class="context-menu__divider" />
          <div class="context-menu__item context-menu__item--danger" @click="deletePage(menuNode); closeMenu()">🗑️ 删除</div>
        </div>

        <!-- Right: Element table -->
        <template v-if="selectedPage">
          <div class="elements-panel">
            <div class="panel-header">
              <h3 class="panel-title">
                {{ pageLabel(selectedPage) }}
                <span class="doc-tag">Elements</span>
              </h3>
              <el-button size="small" type="primary" @click="openAddElement">+ 添加元素</el-button>
            </div>
            <div class="elements-subheader">
              <AppTabs
                class="element-tabs"
                :items="filterTabs"
                v-model="filterMode"
                :leaf-animation="true"
                :shadow="true"
              >
                <template v-for="tab in filterTabs" #[tab.key] :key="tab.key">
                  <div class="table-area">
                    <div class="table-toolbar">
                      <div class="page-size-control">
                        <span class="toolbar-label">显示行数</span>
                        <div class="page-size-btns">
                          <button
                            v-for="n in PAGE_SIZE_OPTIONS"
                            :key="n"
                            type="button"
                            class="page-size-btn"
                            :class="{ active: pageSize === n }"
                            @click="setPageSize(n)"
                          >{{ n }}</button>
                        </div>
                      </div>
                      <div v-if="filteredElements.length > 0" class="table-toolbar-right">
                        <span class="page-info">
                          第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredElements.length }} 条
                        </span>
                        <div v-if="totalPages > 1" class="page-nav">
                          <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                          <el-button size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
                        </div>
                      </div>
                    </div>
                    <AppCard class="table-card">
                      <div class="table-scroll">
                        <AppTable
                        :columns="columns"
                        :data-source="pagedElements"
                        row-key="id"
                        :striped="true"
                        empty-text="暂无元素"
                        class="elements-table"
                      >
                      <!-- Custom cell: alias (inline edit) -->
                      <template #cell-alias="{ record }">
                        <input
                          class="cell-input"
                          :value="record.alias"
                          placeholder="未命名"
                          @blur="(e) => updateEl(record, 'alias', e.target.value)"
                          @keyup.enter="(e) => { updateEl(record, 'alias', e.target.value); e.target.blur() }"
                        />
                      </template>

                      <!-- Custom cell: xpath — pre-parsed in selectPage() for performance -->
                      <template #cell-xpath="{ record }">
                        <span v-if="record._first_xpath"
                          class="cell-code"
                          :title="record._first_xpath">
                          {{ record._first_xpath }}
                        </span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: text_val -->
                      <template #cell-text_val="{ record }">
                        <span v-if="record.text_val" class="cell-text">{{ record.text_val }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: resource_id -->
                      <template #cell-resource_id="{ record }">
                        <span v-if="record.resource_id" class="cell-code" :title="record.resource_id">{{ record.resource_id }}</span>
                        <span v-else class="text-muted">—</span>
                      </template>

                      <!-- Custom cell: clickable -->
                      <template #cell-clickable="{ value }">
                        <span :class="['clickable-badge', value ? 'clickable-yes' : 'clickable-no']">
                          {{ value ? '✓ 可点击' : '—' }}
                        </span>
                      </template>

                      <!-- Custom cell: is_test_point -->
                      <template #cell-is_test_point="{ record }">
                        <el-switch
                          size="small"
                          :model-value="record.is_test_point"
                          @update:model-value="(val) => updateEl(record, 'is_test_point', val)"
                        />
                      </template>

                      <!-- Empty state -->
                      <template #empty>
                        <div class="table-empty">
                          <span>📋</span>
                          <p>暂无元素</p>
                          <el-button size="small" type="primary" @click="openAddElement">添加第一个元素</el-button>
                        </div>
                      </template>
                    </AppTable>
                      </div>
                    </AppCard>
                  </div>
                </template>
              </AppTabs>
              <span class="element-count">共 {{ elements.length }} 个元素</span>
            </div>
          </div>
        </template>
        <AppCard v-else class="empty-card">
          <div class="empty-state">← 选择页面查看元素（目录仅用于分组）</div>
        </AppCard>
    </div>

    <!-- Batch move dialog -->
    <el-dialog
      v-model="moveDialogVisible"
      title="选择目标目录"
      width="420px"
      
      :close-on-click-modal="false"
      @close="moveDialogVisible = false"
    >
      <el-select
        v-model="moveTargetDirId"
        placeholder="选择要移动到的目录"
        filterable
        style="width: 100%"
      >
        <el-option
          v-for="dir in folderList"
          :key="dir.id"
          :label="dir.label"
          :value="dir.id"
        />
      </el-select>
      <template #footer>
        <el-button @click="moveDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="!moveTargetDirId" @click="confirmBatchMove">确认移动</el-button>
      </template>
    </el-dialog>

    <!-- Create Page Dialog -->
    <el-dialog
      v-model="showCreatePage"
      :title="createDialogTitle"
      width="360px"

      :close-on-click-modal="false"
      @close="showCreatePage = false"
    >
      <div class="form-grid">
        <label class="form-label required">{{ createIsFolder ? '目录名称' : '页面名称' }}</label>
        <el-input
          v-model="newPageForm.label"
          :placeholder="createIsFolder ? '如：电商模块、登录流程' : '如：登录页、首页'"
          size="middle"
          @keyup.enter="doCreatePage"
        />
      </div>
      <template #footer>
        <el-button @click="showCreatePage = false">取消</el-button>
        <el-button type="primary" @click="doCreatePage">创建</el-button>
      </template>
    </el-dialog>

    <!-- Rename Dialog -->
    <el-dialog
      v-model="showRenameDialog"
      :title="renameTarget?.is_folder ? '重命名目录' : '重命名页面'"
      width="360px"

      :close-on-click-modal="false"
      @close="showRenameDialog = false"
    >
      <div class="form-grid">
        <label class="form-label required">名称</label>
        <el-input
          v-model="renameLabel"
          placeholder="输入新名称"
          size="middle"
          @keyup.enter="doRename"
        />
      </div>
      <template #footer>
        <el-button @click="showRenameDialog = false">取消</el-button>
        <el-button type="primary" @click="doRename">确定</el-button>
      </template>
    </el-dialog>

    <!-- Clear Pages Confirm Dialog -->
    <el-dialog v-model="showClearDialog" title="清空页面" width="440px"  :close-on-click-modal="false">
      <div class="clear-confirm">
        <p class="clear-warning">⚠️ 此操作将永久删除页面及关联元素，不可恢复。</p>
        <p class="clear-question">
          确定要清空<strong>{{ clearSelectedOnly && selectedPageIds.size > 0 ? `选中的 ${selectedPageIds.size} 个` : '所有' }}</strong>页面吗？
        </p>
        <label class="clear-option" :class="{ disabled: selectedPageIds.size === 0 }">
          <input type="checkbox" v-model="clearSelectedOnly" :disabled="selectedPageIds.size === 0" />
          <span>仅清除选中的页面（已选 {{ selectedPageIds.size }} 个）</span>
        </label>
      </div>
      <template #footer>
        <el-button @click="showClearDialog = false">取消</el-button>
        <el-button type="primary" danger @click="doClearPages">确定清空</el-button>
      </template>
    </el-dialog>

    <!-- Add Element Dialog -->
    <el-dialog
      v-model="showAddElement"
      title="添加元素"
      width="500px"
      
      :close-on-click-modal="false"
      @close="showAddElement = false"
    >
      <div class="form-grid">
        <label class="form-label required">元素名称</label>
        <el-input v-model="newElForm.alias" placeholder="如：登录按钮、用户名输入框" size="middle" />
        <label class="form-label">XPath</label>
        <el-input v-model="newElForm.xpath" placeholder="元素定位 XPath" size="middle" />
        <label class="form-label">类名</label>
        <el-input v-model="newElForm.class_name" placeholder="android.widget.Button" size="middle" />
        <label class="form-label">文本</label>
        <el-input v-model="newElForm.text_val" placeholder="元素文本内容" size="middle" />
        <label class="form-label">Resource ID</label>
        <el-input v-model="newElForm.resource_id" placeholder="com.example:id/btn" size="middle" />
        <label class="form-label">可点击</label>
        <el-switch v-model="newElForm.clickable" size="medium" />
      </div>
      <template #footer>
        <el-button @click="showAddElement = false">取消</el-button>
        <el-button type="primary" @click="doAddElement">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped src="./ElementManager.css"></style>
