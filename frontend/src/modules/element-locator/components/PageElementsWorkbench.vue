<script setup lang="ts">
/**
 * 页面元素工作台：每页 10 行的元素定位信息表。
 *
 * 呈现列与可编辑字段按收敛口径：列 = 缩略图 / 元素名称 / 序号 / 文本 / 主定位 / 交互标注 / 测试点；
 * 只有元素名称、文本、主定位与测试点可改（校验见 helpers/elementRowValidation.ts）；
 * 支持新增一行与勾选多行批量删除；状态与编排见 composables/usePageElements.ts。
 */
import { computed, ref } from "vue"
import { ElMessageBox } from "element-plus"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { mediaUrl } from "@/shared/helpers/mediaUrl"
import EditableCell from "./EditableCell.vue"
import PageElementFormDialog from "./PageElementFormDialog.vue"
import type { PageElementFields } from "../api"
import {
  usePageElements,
  type EditableField,
  type PageElementRow,
} from "../composables/usePageElements"
import {
  validateAliasCell,
  validatePrimaryXPath,
  validateText,
  type TextField,
} from "../helpers/elementRowValidation"
import { interactionLabels } from "../helpers/elementPresentation"

const props = defineProps<{ pageId: number }>()

const {
  loading,
  error,
  rows,
  total,
  truncated,
  currentPage,
  totalPages,
  pagedItems,
  goPage,
  selectedIds,
  allSelectedOnPage,
  isSelected,
  toggleRow,
  toggleAllOnPage,
  load,
  updateField,
  createRow,
  removeSelected,
} = usePageElements(() => props.pageId)

const formVisible = ref(false)
const selectedCount = computed(() => selectedIds.value.length)
/** 加载失败的缩略图（按行 id 记，避免浏览器破图） */
const brokenThumbs = ref(new Set<number>())

/** 列定义：收敛后的七列（顺序即展示顺序） */
const ELEMENT_COLUMNS = [
  { key: "_select", width: 44, align: "center", label: "", showOverflowTooltip: false },
  { dataIndex: "thumbnail_path", width: 66, label: "缩略图", showOverflowTooltip: false },
  { dataIndex: "alias", minWidth: 120, label: "元素名称", showOverflowTooltip: false },
  { dataIndex: "seq", width: 64, align: "center", label: "序号", showOverflowTooltip: false },
  { dataIndex: "text_val", minWidth: 120, label: "文本", showOverflowTooltip: false },
  { dataIndex: "primary_xpath", minWidth: 220, label: "主定位", showOverflowTooltip: false },
  { dataIndex: "flags", minWidth: 200, label: "交互标注", showOverflowTooltip: false },
  {
    dataIndex: "is_test_point",
    width: 88,
    align: "center",
    label: "测试点",
    showOverflowTooltip: false,
  },
]

/** 行内可编辑的文本列（元素名称 / 文本 / 主定位） */
const TEXT_FIELDS: Array<[string, TextField]> = [
  ["alias", "alias"],
  ["text_val", "text_val"],
  ["primary_xpath", "primary_xpath"],
]

/** 每列的校验函数；返回 undefined 表示该列不做前端校验 */
function validateFor(field: string): ((value: string) => string | null) | undefined {
  if (field === "alias") return validateAliasCell
  if (field === "primary_xpath") return validatePrimaryXPath
  const entry = TEXT_FIELDS.find(([key]) => key === field)
  return entry ? (value: string) => validateText(entry[1], value) : undefined
}

function markThumbBroken(row: PageElementRow) {
  brokenThumbs.value = new Set(brokenThumbs.value).add(row.id)
}

function onEdit(row: PageElementRow, field: EditableField, value: string) {
  void updateField(row, field, value)
}

function onTestPointChange(row: PageElementRow, value: string | number | boolean) {
  void updateField(row, "is_test_point", Boolean(value))
}

function onToggleAll(value: string | number | boolean) {
  toggleAllOnPage(Boolean(value))
}

async function onCreate(fields: PageElementFields) {
  const ok = await createRow(fields)
  if (ok) formVisible.value = false
}

async function onRemoveSelected() {
  if (!selectedCount.value) return
  try {
    await ElMessageBox.confirm(`确认删除选中的 ${selectedCount.value} 行元素？`, "确认批量删除", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning",
    })
  } catch {
    return
  }
  await removeSelected()
}

function rowClassName({ row }: { row: PageElementRow }) {
  return isSelected(row.id) ? "is-selected" : ""
}

defineExpose({ reload: load })
</script>

<template>
  <div class="page-workbench">
    <div class="page-workbench__toolbar">
      <span class="page-workbench__count">共 {{ total }} 个元素</span>
      <el-button size="small" @click="formVisible = true">+ 新增一行</el-button>
      <el-button size="small" type="danger" :disabled="!selectedCount" @click="onRemoveSelected">
        删除选中{{ selectedCount ? `（${selectedCount}）` : "" }}
      </el-button>
      <span v-if="truncated" class="page-workbench__hint">
        接口一次最多取回 {{ rows.length }} 条，当前仅显示这些（共 {{ total }} 条）
      </span>
    </div>

    <div v-if="loading" class="page-workbench__state">
      <SkeletonCard variant="list" :lines="6" />
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="load" />

    <section v-else class="page-workbench__table">
      <EmptyState
        v-if="!rows.length"
        icon="📋"
        text="该页面暂无元素"
        hint="可从设备检查器导入快照，或点「+ 新增一行」手写一条"
      />
      <div v-else class="page-workbench__grid">
        <AppTable
          :columns="ELEMENT_COLUMNS"
          :data-source="pagedItems"
          accent="var(--c-element)"
          border
          :striped="true"
          height="100%"
          class="page-elements-table"
          row-key="id"
          :row-class-name="rowClassName"
          empty-text="暂无元素"
        >
          <template #header-_select>
            <el-checkbox :model-value="allSelectedOnPage" @change="onToggleAll" />
          </template>
          <template #cell-_select="{ row }">
            <el-checkbox
              :model-value="isSelected(row.id)"
              @click.stop
              @change="() => toggleRow(row.id)"
            />
          </template>
          <template #cell-thumbnail_path="{ row }">
            <img
              v-if="row.thumbnail_path && !brokenThumbs.has(row.id)"
              :src="mediaUrl(row.thumbnail_path)"
              class="page-elements-thumb"
              alt=""
              @error="markThumbBroken(row)"
            />
            <span v-else class="page-elements-empty">—</span>
          </template>
          <template #cell-alias="{ row }">
            <EditableCell
              :value="row.alias"
              :validate="validateFor('alias')"
              placeholder="未命名"
              @commit="(v: string) => onEdit(row, 'alias', v)"
            />
          </template>
          <template #cell-seq="{ row }">
            <span class="page-elements-seq">{{ row.seq || "—" }}</span>
          </template>
          <template #cell-text_val="{ row }">
            <EditableCell
              :value="row.text_val"
              :validate="validateFor('text_val')"
              @commit="(v: string) => onEdit(row, 'text_val', v)"
            />
          </template>
          <template #cell-primary_xpath="{ row }">
            <EditableCell
              :value="row.primary_xpath"
              :validate="validateFor('primary_xpath')"
              placeholder="主定位表达式"
              @commit="(v: string) => onEdit(row, 'primary_xpath', v)"
            />
          </template>
          <template #cell-flags="{ row }">
            <div class="page-elements-flags">
              <template v-if="interactionLabels(row).length">
                <span
                  v-for="label in interactionLabels(row)"
                  :key="label"
                  class="page-elements-flag"
                  >{{ label }}</span
                >
              </template>
              <span v-else class="page-elements-empty">—</span>
            </div>
          </template>
          <template #cell-is_test_point="{ row }">
            <el-switch
              :model-value="row.is_test_point"
              @click.stop
              @change="(v: string | number | boolean) => onTestPointChange(row, v)"
            />
          </template>
        </AppTable>
      </div>
      <div class="page-workbench__pager">
        <span>第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
        <el-button size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">
          上一页
        </el-button>
        <el-button
          size="small"
          :disabled="currentPage >= totalPages"
          @click="goPage(currentPage + 1)"
        >
          下一页
        </el-button>
      </div>
    </section>

    <PageElementFormDialog v-model="formVisible" @confirm="onCreate" />
  </div>
</template>

<style scoped>
.page-workbench {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  gap: var(--app-space-md);
}
.page-workbench__toolbar {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.page-workbench__count {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.page-workbench__hint {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}
.page-workbench__state {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
.page-workbench__table {
  flex: 1 1 0;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  overflow: hidden;
}
.page-workbench__grid {
  flex: 1 1 0;
  min-height: 0;
}
.page-workbench__pager {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-space-sm);
  flex-shrink: 0;
  font-size: var(--app-size-sm);
  color: var(--ink);
}
.page-elements-table {
  height: 100%;
}
/* 缩略图格：固定尺寸（同检查器口径），失效或无图都落占位，不出现破图 */
.page-elements-thumb {
  display: block;
  width: 46px;
  height: 34px;
  object-fit: contain;
  border: 1px solid var(--ink);
  background: var(--app-bg-input);
}
.page-elements-seq {
  color: var(--ink);
}
.page-elements-flags {
  display: flex;
  flex-wrap: wrap;
  gap: var(--app-space-xs);
}
.page-elements-flag {
  border: 1px solid var(--ink);
  border-radius: 2px;
  padding: 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--ink);
  background: var(--app-bg-input);
}
.page-elements-empty {
  color: var(--app-text-secondary);
}
</style>
