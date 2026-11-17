<script setup lang="ts">
/**
 * 设备身份单元 — 首列：图标圆 + 状态点 + 型号 / 「序列号 · 地址」双行
 *
 * 组件只做渲染：型号与地址的格式化仍走 `../helpers` 的纯函数，不在此重复实现。
 */
import { computed } from "vue"
import type { DeviceRecord } from "@/shared/types/device"
import { IconDevice } from "@/shared/icons/index"
import { displayModel, deviceAddress } from "../helpers"

const props = defineProps<{
  device: DeviceRecord
  /** 行是否被选中：只影响图标圆描边，选中底色由共享行规则承担 */
  selected?: boolean
}>()

/** 状态点色调：在线绿 / 使用中黄 / 其余灰 */
const tone = computed(() => {
  if (props.device.status === "ONLINE") return "online"
  if (props.device.status === "BUSY") return "busy"
  return "off"
})

const address = computed(() => deviceAddress(props.device))
</script>

<template>
  <div class="dev-id" :class="{ 'is-selected': selected }">
    <span class="dev-id__badge" :class="`dev-id__badge--${tone}`" aria-hidden="true">
      <IconDevice :size="16" />
      <span class="dev-id__dot"></span>
    </span>
    <div class="dev-id__text">
      <p class="dev-id__model">{{ displayModel(device) }}</p>
      <div class="dev-id__meta">
        <code :title="device.serial">{{ device.serial }}</code>
        <span :title="address">{{ address }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.dev-id {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  padding-left: 2px;
  text-align: left;
}

/* 图标圆：等价于「头像位」，色只做浅底装饰（--c-device 系），不承载状态语义 */
.dev-id__badge {
  position: relative;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: 2px solid var(--ink);
  border-radius: 50%;
  color: var(--app-nav-text);
  background: color-mix(in srgb, var(--c-device) 24%, var(--app-bg-card));
}

/* 选中态只加 0 模糊外环（G12：模糊半径必须为 0） */
.dev-id.is-selected .dev-id__badge {
  box-shadow: 0 0 0 2px var(--c-device);
}

.dev-id__badge--busy {
  background: color-mix(in srgb, var(--c-dashboard) 28%, var(--app-bg-card));
}

.dev-id__badge--off {
  background: var(--app-bg-subtle);
  color: var(--app-text-secondary);
  opacity: 0.8;
}

/* 状态点：与「状态」列同源，只作辅助，不替代状态列 */
.dev-id__dot {
  position: absolute;
  right: -2px;
  bottom: -2px;
  width: 9px;
  height: 9px;
  border-radius: 50%;
  border: 2px solid var(--app-bg-card);
  background: var(--app-status-success);
}

.dev-id__badge--busy .dev-id__dot {
  background: var(--c-dashboard);
}

.dev-id__badge--off .dev-id__dot {
  background: var(--app-text-muted);
}

.dev-id__text {
  min-width: 0;
}

.dev-id__model {
  margin: 0 0 4px;
  font-weight: var(--app-font-weight-heavy);
  font-size: var(--app-size-sm);
  line-height: var(--app-line-height-tight);
  color: var(--app-text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.dev-id__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 10px;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-secondary);
}

.dev-id__meta code {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-nav-text);
  background: var(--app-bg-subtle);
  border: 1px solid var(--app-border-light);
  border-radius: var(--app-radius-sm);
  padding: 1px 6px;
}
</style>
