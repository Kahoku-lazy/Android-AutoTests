<script setup lang="ts">
/** Serial Log — 串口日志：无线端口 / 日志关键词两个 Tab。 */
import { ref } from "vue"
import AppTabs from "@/shared/components/AppTabs.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import WifiPortPanel from "./components/WifiPortPanel.vue"
import LogKeywordPanel from "./components/LogKeywordPanel.vue"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import {
  SERIAL_LOG_DEFAULT_TAB,
  SERIAL_LOG_PAGE_ICON,
  SERIAL_LOG_PAGE_SUBTITLE,
  SERIAL_LOG_PAGE_TITLE,
  SERIAL_LOG_TABS,
} from "./constants"

const { isSuperuser } = useAuthUser()

/** Tab 切换不改变任何开关状态：两个面板各自只在被选中时挂载。 */
const activeTab = ref<string>(SERIAL_LOG_DEFAULT_TAB)
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell serial-log-workbench">
    <WorkbenchHeader
      :title="SERIAL_LOG_PAGE_TITLE"
      :subtitle="SERIAL_LOG_PAGE_SUBTITLE"
      :icon="SERIAL_LOG_PAGE_ICON"
      icon-gradient="linear-gradient(135deg,var(--c-device),var(--app-status-purple))"
    />

    <div class="doc-body">
      <section class="serial-log-section" data-testid="serial-log-page">
        <AppTabs v-model="activeTab" :items="SERIAL_LOG_TABS">
          <template #ports>
            <WifiPortPanel v-if="activeTab === 'ports'" :can-manage="isSuperuser" />
          </template>
          <template #keywords>
            <LogKeywordPanel v-if="activeTab === 'keywords'" />
          </template>
        </AppTabs>
      </section>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
