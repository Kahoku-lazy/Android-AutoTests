<script setup lang="ts">
import AppTable from "@/shared/components/AppTable.vue"
import DeviceIdentityCell from "./components/DeviceIdentityCell.vue"
import DeviceStatusCell from "./components/DeviceStatusCell.vue"
import DeviceActionsCell from "./components/DeviceActionsCell.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import DisconnectDialog from "./components/DisconnectDialog.vue"
import NetworkConnectDialog from "./components/NetworkConnectDialog.vue"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import { IconWifi, IconRefresh, IconSearch } from "@/shared/icons/index"
import { useDevicePoolView } from "./DevicePoolView.logic"

const {
  scanning,
  loading,
  error,
  devMockEnabled,
  toggleDevMock,
  activeFilter,
  searchKey,
  hasNarrowing,
  filteredDevices,
  pagedDevices,
  pageSize,
  currentPage,
  totalPages,
  disconnectDialog,
  networkDialog,
  currentUser,
  handleRefresh,
  openNetworkDialog,
  handleNetworkConnect,
  cancelNetworkDialog,
  handleRowClick,
  handleLockClick,
  handleRelease,
  openDisconnectDialog,
  handleDisconnectConfirm,
  cancelDisconnectDialog,
  isRowSelected,
  rowClassName,
  formatDateTime,
  formatRelativeTime,
  PAGE_HEADER,
  filterTabs,
  COLUMNS,
  EMPTY_TEXT,
  SEARCH_PLACEHOLDER,
  tableMinHeightPx,
  tableMinWidthPx,
  tableWrapRef,
  onTablePointerDown,
  goPage,
} = useDevicePoolView()
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell device-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    />

    <ErrorState v-if="error" :message="error" @retry="handleRefresh" />

    <div v-else class="doc-body">
      <section class="device-section--list">
        <div class="device-toolbar">
          <div class="device-toolbar__right">
            <div class="dev-mock-toggle" title="开发调试：注入 60 条模拟设备">
              <span class="dev-mock-toggle__label">开发调试</span>
              <el-switch :model-value="devMockEnabled" size="small" @change="toggleDevMock" />
            </div>
            <el-button
              class="action-bar-btn action-bar-btn--network"
              size="small"
              @click="openNetworkDialog"
            >
              <IconWifi :size="14" /> 局域网
            </el-button>
            <el-button
              class="action-bar-btn action-bar-btn--primary"
              size="small"
              :loading="scanning || loading"
              @click="handleRefresh"
            >
              <IconRefresh :size="14" /> 刷新
            </el-button>
          </div>
        </div>

        <div class="list-controls">
          <span class="page-info"
            >第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredDevices.length }} 台</span
          >
          <el-select v-model="activeFilter" class="filter-select" size="small">
            <el-option
              v-for="tab in filterTabs"
              :key="tab.key"
              :value="tab.key"
              :label="`${tab.label} · ${tab.count}`"
            />
          </el-select>
          <el-input
            v-model="searchKey"
            class="device-search"
            size="small"
            clearable
            :placeholder="SEARCH_PLACEHOLDER"
          >
            <template #prefix>
              <IconSearch :size="14" />
            </template>
          </el-input>
          <div class="page-nav">
            <el-button
              class="wb-btn"
              size="small"
              :disabled="currentPage <= 1"
              @click="goPage(currentPage - 1)"
              >上一页</el-button
            >
            <el-button
              class="wb-btn"
              size="small"
              :disabled="currentPage >= totalPages"
              @click="goPage(currentPage + 1)"
              >下一页</el-button
            >
          </div>
        </div>

        <div
          ref="tableWrapRef"
          class="device-table-wrapper"
          :style="{
            'minHeight': `${tableMinHeightPx}px`,
            '--device-table-body-rows': String(pageSize),
            '--device-table-min-width': `${tableMinWidthPx}px`,
          }"
          @pointerdown="onTablePointerDown"
        >
          <AppTable
            :columns="COLUMNS"
            :data-source="pagedDevices"
            row-key="serial"
            :striped="true"
            :loading="loading"
            table-layout="fixed"
            empty-text="还没有可用设备"
            accent="var(--c-device)"
            :row-class-name="rowClassName"
            @row-click="handleRowClick"
          >
            <template
              v-for="col in COLUMNS"
              :key="`head-${col.dataIndex}`"
              v-slot:[`header-${col.dataIndex}`]
            >
              <span class="th-ico" aria-hidden="true">{{ col.icon }}</span>{{ col.title }}
            </template>
            <template #cell-device="{ record }">
              <DeviceIdentityCell :device="record" :selected="isRowSelected(record)" />
            </template>
            <template #cell-status="{ record }">
              <DeviceStatusCell :device="record" />
            </template>
            <template #cell-connection_type="{ record }">
              <span
                class="conn-chip"
                :class="record.connection_type === 'WIFI' ? 'conn-chip--wifi' : 'conn-chip--usb'"
                >{{ record.connection_type === "WIFI" ? "Wi‑Fi" : "USB" }}</span
              >
            </template>
            <template #cell-lock_status="{ record }">
              <span
                v-if="record.locked_by"
                class="vis-chip vis-chip--locked"
                :title="`锁定者: ${record.locked_by}`"
                >🔒 {{ record.locked_by }}</span
              >
              <span v-else class="vis-chip vis-chip--open">公开</span>
            </template>
            <template #cell-screen="{ record }">
              <span v-if="record.screen" class="screen-cell">{{ record.screen }}</span>
              <span v-else class="text-muted">—</span>
            </template>
            <template #cell-last_seen="{ record }">
              <div class="time-cell">
                <span class="time-rel">{{ formatRelativeTime(record.last_seen) }}</span>
                <span class="time-abs">接入 {{ formatDateTime(record.connected_at) }}</span>
              </div>
            </template>
            <template #cell-actions="{ record }">
              <DeviceActionsCell
                :device="record"
                :current-user="currentUser"
                @lock="handleLockClick"
                @release="(d) => handleRelease(d.serial)"
                @disconnect="(d) => openDisconnectDialog(d.serial)"
              />
            </template>
            <template #empty>
              <EmptyState
                icon="📱"
                :text="hasNarrowing ? EMPTY_TEXT.noMatch : EMPTY_TEXT.noDevices"
                :hint="hasNarrowing ? EMPTY_TEXT.hintClearSearch : EMPTY_TEXT.hintRefresh"
              />
            </template>
          </AppTable>
        </div>
      </section>
    </div>

    <DisconnectDialog
      v-bind="disconnectDialog"
      @confirm="handleDisconnectConfirm"
      @cancel="cancelDisconnectDialog"
    />
    <NetworkConnectDialog
      :visible="networkDialog.visible"
      :loading="networkDialog.loading"
      @confirm="handleNetworkConnect"
      @cancel="cancelNetworkDialog"
    />
  </div>
</template>

<style src="./DevicePoolView.style.css" scoped></style>
