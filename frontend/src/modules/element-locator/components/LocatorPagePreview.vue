<script setup lang="ts">
/**
 * 页面元素只读预览（工作台右栏专用）。
 *
 * 定位：右栏是**概览位**，回答「这一页有哪些元素」。因此只呈现三列
 * （缩略图 / 元素名称 / 序号），并通过共享分页让该页全部元素都可浏览；
 * 只消费 usePageElements 的读状态——不导入任何写函数
 * （apiUpdateElement / createPageElement / batchDeleteElements），
 * 也不渲染勾选框、新增行、批量删除与测试点开关。
 * 「文本 / 主定位 / 交互标注 / 测试点」四列与全部编辑能力只在文件详情页
 * （/elements/projects/:code/files/:fileId）提供，本组件给一个进入那里的入口。
 */
import { ref } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { mediaUrl } from "@/shared/helpers/mediaUrl"
import { usePageElements, type PageElementRow } from "../composables/usePageElements"
import type { LocatorFileNode } from "../types"

/** 只读预览列：只给「有哪些元素」需要的三列；名称列吃剩余宽度 */
const PREVIEW_COLUMNS = [
  { dataIndex: "thumbnail_path", width: 66, label: "缩略图", showOverflowTooltip: false },
  { dataIndex: "alias", minWidth: 200, label: "元素名称", showOverflowTooltip: false },
  { dataIndex: "seq", width: 64, align: "center", label: "序号", showOverflowTooltip: false },
]

const props = defineProps<{ file: LocatorFileNode }>()

const emit = defineEmits<{ open: [fileId: number] }>()

/** 分页走共享 usePagination（每页固定 10 行，边界自动夹取页码） */
const { loading, error, rows, total, currentPage, totalPages, pagedItems, goPage, load } =
  usePageElements(() => props.file.id)

/** 加载失败的缩略图（按行 id 记，避免浏览器破图） */
const brokenThumbs = ref(new Set<number>())

function markThumbBroken(row: PageElementRow) {
  brokenThumbs.value = new Set(brokenThumbs.value).add(row.id)
}
</script>

<template>
  <section class="page-preview">
    <header class="page-preview__head">
      <div class="page-preview__title-block">
        <h3 class="page-preview__title">{{ file.name }}</h3>
        <span class="page-preview__meta">共 {{ total }} 个元素 · 只读预览</span>
      </div>
      <el-button type="primary" @click="emit('open', file.id)">进入页面编辑 ›</el-button>
    </header>

    <div class="page-preview__body">
      <SkeletonCard v-if="loading" variant="list" :lines="6" />
      <ErrorState v-else-if="error" :message="error" @retry="load" />

      <EmptyState
        v-else-if="!rows.length"
        icon="📋"
        text="该页面暂无元素"
        hint="可从设备检查器导入快照，或进入页面手写一条"
      >
        <el-button type="primary" @click="emit('open', file.id)">进入页面编辑 ›</el-button>
      </EmptyState>

      <template v-else>
        <div class="page-preview__sheet">
          <AppTable
            :columns="PREVIEW_COLUMNS"
            :data-source="pagedItems"
            accent="var(--c-element)"
            border
            :striped="true"
            height="100%"
            class="page-elements-table"
            row-key="id"
            empty-text="暂无元素"
          >
            <template #cell-thumbnail_path="{ row }">
              <img
                v-if="row.thumbnail_path && !brokenThumbs.has(row.id)"
                :src="mediaUrl(row.thumbnail_path)"
                class="page-preview__thumb"
                alt=""
                @error="markThumbBroken(row)"
              />
              <span v-else class="page-preview__empty">—</span>
            </template>
            <template #cell-alias="{ row }">
              <span class="page-preview__text">{{ row.alias || "未命名" }}</span>
            </template>
            <template #cell-seq="{ row }">
              <span class="page-preview__text">{{ row.seq || "—" }}</span>
            </template>
          </AppTable>
        </div>

        <footer class="page-preview__foot">
          <div class="page-preview__pager">
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
        </footer>
      </template>
    </div>
  </section>
</template>

<style scoped>
/* 只读预览：概览位。列宽与详情页同源，宽度不足由表纸自身横向滚动（不删列） */
.page-preview {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: var(--app-space-md) var(--app-space-lg) var(--app-space-lg);
  gap: var(--app-space-md);
}
.page-preview__head {
  display: flex;
  align-items: center;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
}
.page-preview__title-block {
  min-width: 0;
  flex: 1 1 auto;
}
.page-preview__title {
  font-size: var(--app-size-lg);
  font-weight: 800;
  color: var(--ink);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.page-preview__meta {
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  font-weight: 700;
}
.page-preview__body {
  flex: 1 1 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}
.page-preview__sheet {
  flex: 1 1 0;
  min-height: 0;
}
.page-elements-table {
  height: 100%;
}
.page-preview__foot {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: var(--app-space-md);
  flex-wrap: wrap;
  flex-shrink: 0;
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.page-preview__pager {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}
.page-preview__thumb {
  display: block;
  width: 46px;
  height: 34px;
  object-fit: contain;
  border: 1px solid var(--ink);
  background: var(--app-bg-input);
}
.page-preview__text {
  color: var(--ink);
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.page-preview__empty {
  color: var(--app-text-secondary);
}
</style>
