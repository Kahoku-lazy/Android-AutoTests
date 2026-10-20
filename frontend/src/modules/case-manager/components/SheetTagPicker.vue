<script setup lang="ts">
/**
 * SheetTagPicker — 用例表格内的枚举标签下拉。
 *
 * 只负责「点开 → 选项 → 回传值」，不持有业务状态：选中后的落库与脏标记由父级处理。
 * 标签色由 ``toneOf`` 决定，色值集中在 ``SheetTagPicker.style.css``（子组件内部样式
 * 不受父级 scoped 样式影响）。
 */
import { onMounted, onUnmounted, ref } from "vue"
import type { EnumOption } from "../types"

const props = defineProps<{
  options: EnumOption[]
  value: string
  toneOf: (value: string) => string
}>()

const emit = defineEmits<{ pick: [value: string] }>()

const open = ref(false)
const root = ref<HTMLElement | null>(null)

function currentLabel(): string {
  return props.options.find((option) => option.value === props.value)?.label || props.value
}

function toggle() {
  open.value = !open.value
}

function choose(option: EnumOption) {
  emit("pick", option.value)
  open.value = false
}

function onDocClick(event: MouseEvent) {
  if (!open.value) return
  const target = event.target as Node | null
  if (root.value && target && root.value.contains(target)) return
  open.value = false
}

onMounted(() => document.addEventListener("click", onDocClick))
onUnmounted(() => document.removeEventListener("click", onDocClick))
</script>

<template>
  <div ref="root" class="sheet-tag-wrap">
    <button
      type="button"
      class="sheet-tag"
      :class="`sheet-tag--${toneOf(value)}`"
      @click.stop="toggle"
    >
      {{ currentLabel() }}
      <span class="sheet-tag__caret">▾</span>
    </button>
    <div v-if="open" class="sheet-tag-menu">
      <button
        v-for="option in options"
        :key="option.value"
        type="button"
        class="sheet-tag-menu__item"
        @click.stop="choose(option)"
      >
        <span class="sheet-tag sheet-tag--sm" :class="`sheet-tag--${toneOf(option.value)}`">
          {{ option.label }}
        </span>
        <span v-if="option.note" class="sheet-tag-menu__note">{{ option.note }}</span>
      </button>
    </div>
  </div>
</template>

<style src="./SheetTagPicker.style.css" scoped></style>
