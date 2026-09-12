<script setup lang="ts">
/**
 * 文件详情面板（独立页使用）。
 * 页面：左表右截图联动；Web/API：简易表单编辑。
 */
import { computed, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import { formatApiError } from '@/shared/api-client'
import {
  apiGetApiEndpoint,
  apiGetWebElement,
  apiUpdateApiEndpoint,
  apiUpdateWebElement,
} from '../api'
import {
  API_METHODS,
  FILE_KIND_LABELS,
  WEB_LOCATOR_TYPES,
  type ApiEndpointDetail,
  type LocatorFileKind,
  type LocatorFileNode,
  type WebElementDetail,
} from '../types'
import PageElementsWorkbench from './PageElementsWorkbench.vue'

const props = defineProps<{
  file: LocatorFileNode
  /** 外层已有标题时隐藏 kind/名称，只保留操作 */
  hideIdentity?: boolean
}>()

const emit = defineEmits<{
  deleteFile: [payload: { fileId: number; kind: LocatorFileKind }]
  back: []
}>()

const loading = ref(false)
const saving = ref(false)
const error = ref('')

const webForm = ref<WebElementDetail>({
  id: 0,
  name: '',
  locator_type: 'css_selector',
  locator_value: '',
})
const apiForm = ref<ApiEndpointDetail>({
  id: 0,
  name: '',
  method: 'GET',
  url: '',
})

const kindLabel = computed(() => FILE_KIND_LABELS[props.file.kind])

function unwrapDetail<T>(payload: unknown): T | null {
  if (!payload || typeof payload !== 'object') return null
  const body = payload as { status?: boolean; data?: T; id?: number }
  if (body.status && body.data && typeof body.data === 'object') {
    return body.data
  }
  if (body.status && body.id != null) {
    return payload as T
  }
  return null
}

async function loadDetail() {
  if (props.file.kind === 'page') {
    error.value = ''
    loading.value = false
    return
  }
  loading.value = true
  error.value = ''
  try {
    if (props.file.kind === 'web_element') {
      const { data } = await apiGetWebElement(props.file.id)
      const detail = unwrapDetail<WebElementDetail>(data)
      if (detail) {
        webForm.value = {
          id: Number(detail.id),
          name: String(detail.name || props.file.name),
          locator_type: String(detail.locator_type || 'css_selector'),
          locator_value: String(detail.locator_value || ''),
        }
      } else {
        error.value = (data as { message?: string }).message || 'Web 元素加载失败'
      }
      return
    }

    const { data } = await apiGetApiEndpoint(props.file.id)
    const detail = unwrapDetail<ApiEndpointDetail>(data)
    if (detail) {
      apiForm.value = {
        id: Number(detail.id),
        name: String(detail.name || props.file.name),
        method: String(detail.method || 'GET'),
        url: String(detail.url || ''),
      }
    } else {
      error.value = (data as { message?: string }).message || '接口加载失败'
    }
  } catch (e: unknown) {
    error.value = formatApiError(e as never, '加载失败')
  } finally {
    loading.value = false
  }
}

watch(
  () => [props.file.id, props.file.kind] as const,
  () => {
    void loadDetail()
  },
  { immediate: true },
)

async function saveWeb() {
  const name = webForm.value.name.trim()
  const locatorValue = webForm.value.locator_value.trim()
  if (!name || !locatorValue) {
    ElMessage.warning('请填写名称和定位值')
    return
  }
  saving.value = true
  try {
    const { data } = await apiUpdateWebElement(props.file.id, {
      name,
      locator_type: webForm.value.locator_type,
      locator_value: locatorValue,
    })
    if ((data as { status?: boolean }).status) {
      ElMessage.success('已保存')
    } else {
      ElMessage.error((data as { message?: string }).message || '保存失败')
    }
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e as never, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function saveApi() {
  const name = apiForm.value.name.trim()
  const url = apiForm.value.url.trim()
  if (!name || !url) {
    ElMessage.warning('请填写名称和 URL')
    return
  }
  saving.value = true
  try {
    const { data } = await apiUpdateApiEndpoint(props.file.id, {
      name,
      method: apiForm.value.method,
      url,
    })
    if ((data as { status?: boolean }).status) {
      ElMessage.success('已保存')
    } else {
      ElMessage.error((data as { message?: string }).message || '保存失败')
    }
  } catch (e: unknown) {
    ElMessage.error(formatApiError(e as never, '保存失败'))
  } finally {
    saving.value = false
  }
}

async function confirmDelete() {
  try {
    await ElMessageBox.confirm(`确认删除「${props.file.name}」？`, '确认删除', {
      confirmButtonText: '删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  emit('deleteFile', { fileId: props.file.id, kind: props.file.kind })
}
</script>

<template>
  <section class="file-panel">
    <header class="file-panel__head">
      <div v-if="!hideIdentity">
        <p class="file-panel__kind">{{ kindLabel }}</p>
        <h2 class="file-panel__title">{{ file.name }}</h2>
      </div>
      <div v-else class="file-panel__spacer" />
      <el-button type="danger" plain @click="confirmDelete">删除</el-button>
    </header>

    <div v-if="file.kind === 'page'" class="file-panel__body file-panel__body--page">
      <PageElementsWorkbench :page-id="file.id" />
    </div>

    <div v-else-if="loading" class="file-panel__body">
      <el-skeleton :rows="5" animated />
    </div>
    <ErrorState v-else-if="error" :message="error" @retry="loadDetail" />

    <div v-else class="file-panel__body">
      <el-form
        v-if="file.kind === 'web_element'"
        label-position="top"
        class="file-panel__form"
      >
        <el-form-item label="名称" required>
          <el-input v-model="webForm.name" maxlength="200" />
        </el-form-item>
        <el-form-item label="定位方式">
          <el-select v-model="webForm.locator_type">
            <el-option
              v-for="item in WEB_LOCATOR_TYPES"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="定位值" required>
          <el-input v-model="webForm.locator_value" type="textarea" :rows="3" />
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="saveWeb">保存</el-button>
      </el-form>

      <el-form v-else label-position="top" class="file-panel__form">
        <el-form-item label="名称" required>
          <el-input v-model="apiForm.name" maxlength="200" />
        </el-form-item>
        <el-form-item label="方法">
          <el-select v-model="apiForm.method">
            <el-option
              v-for="method in API_METHODS"
              :key="method"
              :label="method"
              :value="method"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="URL" required>
          <el-input v-model="apiForm.url" />
        </el-form-item>
        <el-button type="primary" :loading="saving" @click="saveApi">保存</el-button>
      </el-form>
    </div>
  </section>
</template>

<style scoped>
.file-panel {
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  padding: var(--app-space-lg);
}
.file-panel__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--app-space-md);
  margin-bottom: var(--app-space-md);
  flex-shrink: 0;
}
.file-panel__spacer {
  flex: 1;
}
.file-panel__kind {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--c-element);
}
.file-panel__title {
  margin: 0;
  font-size: var(--app-size-lg);
  color: var(--ink);
}
.file-panel__body {
  flex: 1 1 0;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}
.file-panel__body--page {
  overflow: hidden;
}
.file-panel__form {
  max-width: 640px;
  overflow-y: auto;
}
</style>
