<script setup>
import { useElementStore } from "../store"
import { IconZap } from "@/shared/icons"

const store = useElementStore()
const emit = defineEmits(["capture"])

/** 未选设备时按键为灰（不可用）：不发请求、只提示原因；
 *  请求进行中仍用原生 disabled 表达忙碌态（区别于「未选设备」） */
function onCaptureClick() {
  if (!store.captureSerial) {
    store.notifyKeyUnavailable()
    return
  }
  emit("capture")
}
</script>

<template>
  <div class="cap-form">
    <el-select
      v-model="store.captureSerial"
      placeholder="选择设备"
      size="small"
      class="cap-device"
      popper-class="cap-device-popper"
      data-testid="capture-device-select"
    >
      <el-option
        v-for="d in store.availableDevices"
        :key="d.serial"
        :value="d.serial"
        :label="`${d.model || d.brand || ''} (${d.serial}) · ${d.status === 'BUSY' ? '使用中' : '在线'}`"
      />
    </el-select>
    <button
      class="action-btn"
      :class="{ 'action-btn--unavailable': !store.captureSerial }"
      :aria-disabled="!store.captureSerial"
      :disabled="store.captLoading"
      @click="onCaptureClick"
      data-testid="capture-btn"
    >
      <IconZap :size="14" />{{ store.captLoading ? "获取中..." : "获取" }}
    </button>
  </div>
</template>

<style scoped>
.cap-form {
  display: flex;
  align-items: center;
  gap: var(--insp-gap-row);
  flex-wrap: wrap;
}
.cap-device {
  width: 280px;
}
/* .action-btn 的布局、底色与灰键状态，以及 .cap-device 触发键的白底无阴影皮肤，
   均由页面作用域（.inspector-workbench）统一承担，本组件不再声明，避免同一几何在两处重复维护 */
</style>
