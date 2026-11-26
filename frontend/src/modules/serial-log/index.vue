<script setup lang="ts">
import { ref } from "vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import SerialLogTabs from "./components/SerialLogTabs.vue"
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
        <div class="serial-log-section__head">
          <SerialLogTabs
            :items="SERIAL_LOG_TABS"
            :model-value="activeTab"
            @update:model-value="activeTab = $event"
          />
        </div>
        <div class="serial-log-section__body">
          <WifiPortPanel v-if="activeTab === 'ports'" :can-manage="isSuperuser" />
          <LogKeywordPanel v-else :can-manage="isSuperuser" />
        </div>
      </section>
    </div>
  </div>
</template>

<style src="./index.style.css" scoped></style>
