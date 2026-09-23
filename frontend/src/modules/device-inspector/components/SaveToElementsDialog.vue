<script setup>
/**
 * 「保存到元素定位」弹窗：目录路径与目标页面都取自元素定位的**项目树**
 * （`el_locator_directories` + `el_pages.directory_id`）。
 *
 * 不能再用 legacy 的 `Page.parent_id` / `is_folder` 过滤：项目化迁移（0013）之后
 * 目录已独立成表，`is_folder` 恒为假、`parent_id` 恒为空，按旧口径过滤会得到空级联。
 */
import { computed, ref, watch } from "vue"
import { ElMessage } from "element-plus"
import { formatApiError } from "@/shared/api-client"
import { getLocatorProjectTree } from "@/modules/element-locator/api"
import { LOCATOR_PROJECT_CODES } from "@/modules/element-locator/types"
import { useElementStore } from "../store"

const store = useElementStore()

/** 元素定位项目树节点：{type:"directory", id, name, children} / {type:"file", kind:"page", id, name} */
const tree = ref([])
const loading = ref(false)

const mode = ref("existing") // 'existing' | 'create'
const folderPath = ref([]) // 级联目录 label 路径（逐层选择）
const selectedPageId = ref(null) // 已有页面
const newPageLabel = ref("")

const saveFormRef = ref(null)
/** 保存目标的必填校验（按 L4 口径走 EP :rules，取代原 Toast 空值守卫） */
const saveRules = {
  selectedPageId: [{ required: true, message: "请选择要保存到的页面", trigger: "change" }],
  newPageLabel: [{ required: true, message: "请填写新页面名称", trigger: "blur" }],
}

/** ── 项目树 → 级联目录 options（只取目录节点，逐层嵌套）──
 *  value 用目录名：保存请求按 `folder_path` 逐段按名字查找或创建（`_resolve_folder`）。
 */
function buildDirOptions(nodes) {
  return (nodes || [])
    .filter((node) => node.type === "directory")
    .map((node) => ({
      value: node.name,
      label: node.name,
      children: buildDirOptions(node.children),
    }))
}
const folderOptions = computed(() => buildDirOptions(tree.value))

/** 按 label 路径在项目树里定位目录节点；越界或不存在时返回 undefined */
function findDirectory(nodes, path, depth = 0) {
  if (depth >= path.length) return undefined
  const node = (nodes || []).find((item) => item.type === "directory" && item.name === path[depth])
  if (!node) return undefined
  if (depth === path.length - 1) return node
  return findDirectory(node.children, path, depth + 1)
}

/** 当前所选目录（末层）下挂的页面；未选目录时列项目根下的页面 */
const selectedFolderPages = computed(() => {
  const nodes = folderPath.value.length
    ? findDirectory(tree.value, folderPath.value)?.children || []
    : tree.value
  return nodes
    .filter((node) => node.type === "file" && node.kind === "page")
    .map((node) => ({ id: node.id, label: node.name }))
})

const folderPathText = computed(() => folderPath.value.join(" / "))

watch(
  () => store.saveDialogVisible,
  async (v) => {
    if (!v) return
    loading.value = true
    mode.value = "existing"
    folderPath.value = []
    selectedPageId.value = null
    newPageLabel.value = store.snapshot?.package || ""
    try {
      const { data } = await getLocatorProjectTree(LOCATOR_PROJECT_CODES[0])
      if (data.status) {
        tree.value = data.data?.tree || []
      } else {
        ElMessage.error(data.message || "目录加载失败")
      }
    } catch (e) {
      ElMessage.error(formatApiError(e, "目录加载失败"))
    } finally {
      loading.value = false
    }
  },
)

async function confirm() {
  try {
    await saveFormRef.value?.validate()
  } catch {
    // 校验失败：EP 的 validate 以 reject 表示，交由字段内联提示（非静默吞错）
    return
  }
  if (mode.value === "existing") {
    store.saveToElements({
      pageId: selectedPageId.value,
      pageLabel: "",
      folderPath: "",
    })
  } else {
    store.saveToElements({
      pageLabel: newPageLabel.value.trim(),
      folderPath: folderPathText.value,
    })
  }
}
</script>

<template>
  <el-dialog
    v-model="store.saveDialogVisible"
    title="保存到元素定位"
    width="520px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="save-dlg">
      <el-form
        ref="saveFormRef"
        :model="{ selectedPageId, newPageLabel }"
        :rules="saveRules"
        label-width="90px"
        @submit.prevent
      >
        <el-form-item label="目录路径">
          <!-- el-cascader 不把 data-* 透传到 DOM，测试钩子必须挂在普通元素上才真实可达 -->
          <div class="save-folder-field" data-testid="save-folder-cascader">
            <el-cascader
              v-model="folderPath"
              :options="folderOptions"
              :props="{ checkStrictly: false }"
              placeholder="逐层选择目录（不选 = 根目录）"
              clearable
            />
          </div>
        </el-form-item>

        <el-form-item label="保存目标">
          <el-radio-group v-model="mode">
            <el-radio-button value="existing">已有页面</el-radio-button>
            <el-radio-button value="create">新建页面</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <el-form-item v-if="mode === 'existing'" label="选择页面" prop="selectedPageId">
          <el-select
            v-model="selectedPageId"
            placeholder="选择该目录下的页面"
            class="save-page-select"
            data-testid="save-page-select"
          >
            <el-option
              v-for="p in selectedFolderPages"
              :key="p.id"
              :value="p.id"
              :label="p.label || `Page #${p.id}`"
            />
          </el-select>
        </el-form-item>

        <el-form-item v-else label="页面名称" prop="newPageLabel">
          <el-input
            v-model="newPageLabel"
            placeholder="新页面名称"
            data-testid="save-label-input"
          />
        </el-form-item>
      </el-form>
    </div>
    <template #footer>
      <el-button @click="store.saveDialogVisible = false">取消</el-button>
      <el-button
        type="primary"
        :loading="store.saving"
        data-testid="save-confirm-btn"
        @click="confirm"
      >
        保存
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.save-dlg {
  min-height: 200px;
}
/* el-cascader 的根节点不携带作用域属性，直接写 .save-folder 打不中；
   包裹层自己撑满，再用 :deep() 把宽度透传到子组件内部 */
.save-folder-field {
  width: 100%;
}
.save-folder-field :deep(.el-cascader),
.save-page-select {
  width: 100%;
}
</style>
