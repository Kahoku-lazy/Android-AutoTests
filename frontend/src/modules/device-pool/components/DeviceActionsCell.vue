<script setup lang="ts">
import { computed } from "vue"
import type { DeviceRecord } from "@/shared/types/device"
import { isRunnerOccupied } from "@/shared/helpers/deviceOccupancy"

const props = defineProps<{
  device: DeviceRecord
  currentUser?: string
}>()
const emit = defineEmits<{
  lock: [device: DeviceRecord]
  release: [device: DeviceRecord]
  disconnect: [device: DeviceRecord]
}>()

const runnerOccupied = computed(() => isRunnerOccupied(props.device.occupied_by))
const isWifi = computed(() => props.device.connection_type === "WIFI")

const canRelease = computed(() => Boolean(props.device.occupied_by) && !runnerOccupied.value)
const hasSecondary = computed(() => canRelease.value || isWifi.value)

const hasPrimary = computed(() => isWifi.value)

function onCommand(command: string) {
  if (command === "release") emit("release", props.device)
  else if (command === "disconnect") emit("disconnect", props.device)
}
</script>

<template>
  <!-- 点操作区不冒泡到行：避免顺手改掉行选中（行点击本身仍由父级处理） -->
  <div v-if="hasPrimary || hasSecondary" class="action-bar" @click.stop>
    <button
      v-if="hasPrimary"
      type="button"
      class="act-pill"
      :class="device.locked ? 'act-pill--locked' : 'act-pill--open'"
      @click="emit('lock', device)"
    >
      {{ device.locked ? "已锁定" : "公开" }}
    </button>
    <el-dropdown v-if="hasSecondary" trigger="click" placement="bottom-end" @command="onCommand">
      <button type="button" class="act-more" aria-label="更多操作" title="更多操作">⋯</button>
      <template #dropdown>
        <el-dropdown-menu>
          <el-dropdown-item v-if="canRelease" command="release">强制释放</el-dropdown-item>
          <el-dropdown-item v-if="isWifi" command="disconnect" :disabled="device.status === 'BUSY'">
            删除
          </el-dropdown-item>
        </el-dropdown-menu>
      </template>
    </el-dropdown>
  </div>
  <span v-else class="act-empty">—</span>
</template>

<style scoped>
.action-bar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.act-pill {
  border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm);
  padding: 4px 12px;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  line-height: var(--app-line-height-tight);
  color: var(--app-text-primary);
  white-space: nowrap;
  box-shadow: 2px 2px 0 0 var(--ink);
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

.act-pill:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--ink);
}

.act-pill--locked {
  background: var(--app-status-purple-bg);
}

.act-pill--open {
  background: var(--app-status-success-bg);
}

.act-more {
  width: 26px;
  height: 26px;
  padding: 0;
  display: grid;
  place-items: center;
  border: 2px solid var(--ink);
  border-radius: 50%;
  background: var(--app-bg-card);
  color: var(--app-text-primary);
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-bold);
  line-height: 1;
  box-shadow: 2px 2px 0 0 var(--ink);
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

.act-more:hover {
  transform: translate(-1px, -1px);
  box-shadow: 3px 3px 0 0 var(--ink);
}

.act-empty {
  color: var(--app-text-secondary);
  opacity: 0.5;
  font-size: var(--app-size-sm);
}

@media (prefers-reduced-motion: reduce) {
  .act-pill,
  .act-more {
    transition: none;
  }

  .act-pill:hover,
  .act-more:hover {
    transform: none;
    box-shadow: 2px 2px 0 0 var(--ink);
  }
}
</style>
