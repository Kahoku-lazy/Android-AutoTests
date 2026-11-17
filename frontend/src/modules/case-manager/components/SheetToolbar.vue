<script setup lang="ts">
/**
 * 用例表控制区：上排视图（分组 / 筛选 / 列显示），下排写操作（新增 / 导入 / 保存）。
 *
 * 控件一律走共享件：FilterTabs + .sketch-kit 表单件 + DoodleBtn + CaseChip，
 * 页面里不再出现原生 select / input / button。
 */
import { ref } from "vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import CaseChip from "./CaseChip.vue"
import SheetColumnMenu from "./SheetColumnMenu.vue"
import { BUSINESS_OPTIONS, GROUP_OPTIONS, PRIORITY_OPTIONS, SHEET_COLUMNS } from "../types"

defineProps<{
  groupBy: string
  priority: string
  businessType: string
  hidden: string[]
  draftTitle: string
  caseCount: number
  caseLimit: number
  dirtyCount: number
  saving: boolean
}>()

const emit = defineEmits<{
  "update:groupBy": [value: string]
  "update:priority": [value: string]
  "update:businessType": [value: string]
  "update:hidden": [value: string[]]
  "update:draftTitle": [value: string]
  "create": []
  "import": [file: File]
  "save": []
}>()

const fileInput = ref<HTMLInputElement | null>(null)

/** 选完文件立刻清空，否则同一个文件第二次选不触发 change */
function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) emit("import", file)
  input.value = ""
}
</script>

<template>
  <div class="sheet-bar sketch-kit">
    <div class="sheet-bar__row">
      <div class="sketch-field sheet-field sheet-field--group">
        <span class="sketch-field__label">分组</span>
        <FilterTabs
          :tabs="GROUP_OPTIONS"
          :model-value="groupBy"
          @update:model-value="emit('update:groupBy', $event)"
        />
      </div>

      <div class="sketch-field sheet-field">
        <span class="sketch-field__label">优先级</span>
        <el-select
          :model-value="priority"
          placeholder="全部优先级"
          clearable
          class="sheet-select"
          @update:model-value="emit('update:priority', $event ?? '')"
        >
          <el-option
            v-for="option in PRIORITY_OPTIONS"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </div>

      <div class="sketch-field sheet-field">
        <span class="sketch-field__label">业务</span>
        <el-select
          :model-value="businessType"
          placeholder="全部业务"
          clearable
          class="sheet-select"
          @update:model-value="emit('update:businessType', $event ?? '')"
        >
          <el-option
            v-for="option in BUSINESS_OPTIONS"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </div>

      <SheetColumnMenu
        :hidden="hidden"
        :columns="SHEET_COLUMNS"
        @update:hidden="emit('update:hidden', $event)"
      />
    </div>

    <div class="sheet-bar__row sheet-bar__row--ops">
      <div class="sketch-field sheet-field sheet-field--grow">
        <span class="sketch-field__label">新增用例</span>
        <el-input
          :model-value="draftTitle"
          placeholder="输入标题，回车即建一行"
          maxlength="200"
          @update:model-value="emit('update:draftTitle', $event)"
          @keyup.enter="emit('create')"
        />
      </div>
      <DoodleBtn tone="teal" @click="emit('create')">新增行</DoodleBtn>
      <DoodleBtn tone="paper" @click="fileInput?.click()">导入 YAML</DoodleBtn>
      <span class="sheet-count">{{ caseCount }} / {{ caseLimit }}</span>
      <span class="sheet-bar__spacer" />
      <CaseChip v-if="dirtyCount" tone="dirty" :text="`未保存 ${dirtyCount} 处`" />
      <DoodleBtn tone="yellow" :disabled="!dirtyCount || saving" @click="emit('save')">
        {{ saving ? "保存中…" : "保存" }}
      </DoodleBtn>
      <input
        ref="fileInput"
        type="file"
        accept=".yaml,.yml"
        hidden
        aria-hidden="true"
        tabindex="-1"
        @change="onFile"
      />
    </div>
  </div>
</template>

<style scoped>
.sheet-bar {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  padding-bottom: var(--app-space-md);
}

.sheet-bar__row {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--app-space-md);
}

.sheet-bar__row--ops {
  gap: var(--app-space-sm);
}

.sheet-field--group {
  min-width: 292px;
}

.sheet-field--grow {
  flex: 1 1 260px;
  min-width: 220px;
}

.sheet-select {
  width: 168px;
}

.sheet-count {
  display: inline-flex;
  align-items: center;
  min-height: 36px;
  padding: 0 var(--app-space-sm);
  border: 1.5px solid var(--ink);
  border-radius: var(--app-radius-sm);
  background: var(--app-bg-card);
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-text-primary);
  white-space: nowrap;
}

.sheet-bar__spacer {
  flex: 1 1 auto;
}
</style>
