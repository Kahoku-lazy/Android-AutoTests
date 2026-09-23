<script setup lang="ts">
import { computed } from "vue"
import { useRoute } from "vue-router"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WorkbenchCrumbs from "@/shared/components/WorkbenchCrumbs.vue"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import { useToolDebug } from "./composables/useToolDebug"

const route = useRoute()
const toolName = computed(() => String(route.params.toolName || ""))
const { isSuperuser } = useAuthUser()
const canExecuteWrite = computed(() => isSuperuser.value === true)

const {
  schema,
  form,
  loading,
  invoking,
  error,
  invokeError,
  result,
  resultText,
  screenshot,
  canExecute,
  loadSchema,
  runInvoke,
} = useToolDebug(toolName, canExecuteWrite)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ai-workbench tool-debug-page">
    <WorkbenchHeader
      :title="toolName || '工具调试'"
      subtitle="输入参数并查看平台工具真实返回"
      icon="wrench"
      icon-gradient="linear-gradient(135deg, var(--c-ai), var(--color-violet-75))"
    />

    <div class="doc-body">
      <WorkbenchCrumbs
        back-to="/ai-assistant/toolbox"
        back-label="返回工具箱"
        :items="[
          { label: 'AI工具箱', to: '/ai-assistant/toolbox' },
          { label: toolName || '工具调试' },
        ]"
      />

      <ErrorState v-if="error" :message="error" @retry="loadSchema" />

      <div v-else v-loading="loading" class="td-page">
        <EmptyState v-if="!loading && !schema" icon="🔧" text="未找到该平台工具" />

        <template v-else-if="schema">
          <aside class="td-form panel">
            <div class="td-form-head">
              <h3 class="td-title">{{ schema.name }}</h3>
              <span class="td-badge" :class="schema.read_only ? 'ro' : 'wr'">
                {{ schema.read_only ? "只读" : "写" }}
              </span>
            </div>
            <p class="td-summary">{{ schema.summary }}</p>
            <p v-if="!schema.read_only && !canExecute" class="td-hint">
              写工具仅超级管理员可执行；你可查看说明与表单。
            </p>

            <div class="td-fields">
              <EmptyState
                v-if="!schema.parameters.length"
                icon="∅"
                text="无需额外参数，可直接执行"
              />
              <label v-for="p in schema.parameters" :key="p.name" class="td-field">
                <span class="td-field-label">
                  {{ p.name }}
                  <em v-if="p.required">必填</em>
                  <em v-else>可选</em>
                  <span class="td-type">{{ p.type }}</span>
                </span>
                <el-select
                  v-if="p.options"
                  v-model="form[p.name]"
                  class="td-select"
                  filterable
                  allow-create
                  default-first-option
                  placeholder="选择或输入"
                >
                  <el-option
                    v-for="opt in p.options"
                    :key="opt.value"
                    :label="opt.label"
                    :value="opt.value"
                  />
                </el-select>
                <input
                  v-else-if="p.type !== 'bool'"
                  v-model="form[p.name]"
                  class="td-input"
                  :type="p.type === 'int' || p.type === 'float' ? 'number' : 'text'"
                  :step="p.type === 'float' ? 'any' : undefined"
                />
                <input v-else v-model="form[p.name]" class="td-check" type="checkbox" />
                <em v-if="p.options && !p.options.length" class="td-field-note">
                  当前没有在线且未被占用的设备，可手动填写
                </em>
              </label>
            </div>

            <div class="td-actions">
              <button
                type="button"
                class="td-run"
                :disabled="!canExecute || invoking"
                @click="runInvoke"
              >
                {{ invoking ? "执行中…" : "执行" }}
              </button>
            </div>
          </aside>

          <section class="td-result panel">
            <div class="td-result-head">
              <h3 class="td-title">返回结果</h3>
            </div>
            <ErrorState v-if="invokeError" :message="invokeError" @retry="runInvoke" />
            <EmptyState
              v-else-if="result == null && !invoking"
              icon="📦"
              text="执行后在此查看返回数据"
            />
            <div v-else-if="result != null" class="td-result-body">
              <figure v-if="screenshot" class="td-shot">
                <img :src="screenshot.dataUrl" alt="工具截图预览" />
                <figcaption>截图预览（编码已折叠，下方为 summary）</figcaption>
              </figure>
              <pre class="td-json">{{ resultText }}</pre>
            </div>
          </section>
        </template>
      </div>
    </div>
  </div>
</template>

<style src="./ToolDebugPage.style.css" scoped></style>
