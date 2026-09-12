<script setup lang="ts">
/** Device Pool — 单页工作台（无独立 Overview，数量挂筛选 Tab） */
import AppTable from '@/shared/components/AppTable.vue'
import FilterTabs from '@/shared/components/FilterTabs.vue'
import DeviceCard from './components/DeviceCard.vue'
import DeviceStatusCell from './components/DeviceStatusCell.vue'
import DeviceActionsCell from './components/DeviceActionsCell.vue'
import ErrorState from '@/shared/components/patterns/ErrorState.vue'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import DisconnectDialog from './components/DisconnectDialog.vue'
import NetworkConnectDialog from './components/NetworkConnectDialog.vue'
import WorkbenchHeader from '@/shared/components/WorkbenchHeader.vue'
import { IconWifi, IconRefresh } from '@/shared/icons/index'
import { useDevicePoolView } from './DevicePoolView.logic'

const {
  scanning,
  loading,
  error,
  devMockEnabled,
  toggleDevMock,
  activeFilter,
  viewMode,
  switchViewMode,
  filteredDevices,
  pagedDevices,
  pageSize,
  currentPage,
  totalPages,
  PAGE_SIZE_OPTIONS,
  groupedDevices,
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
  deviceRowClassName,
  displayModel,
  deviceAddress,
  formatDateTime,
  formatRelativeTime,
  PAGE_HEADER,
  filterTabs,
  COLUMNS,
  CARD_GROUPS,
  EMPTY_TEXT,
  tableMinHeightPx,
  tableMinWidthPx,
  tableWrapRef,
  onTablePointerDown,
  setPageSize,
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
          <FilterTabs :tabs="filterTabs" v-model="activeFilter" />
          <div class="device-toolbar__right">
            <div class="view-toggle">
              <button
                type="button"
                class="view-btn"
                :class="{ active: viewMode === 'table' }"
                @click="switchViewMode('table')"
              >表格</button>
              <button
                type="button"
                class="view-btn"
                :class="{ active: viewMode === 'cards' }"
                @click="switchViewMode('cards')"
              >卡片</button>
            </div>
            <span class="filter-count">{{ filteredDevices.length }} 台</span>
            <div class="dev-mock-toggle" title="开发调试：注入 60 条模拟设备">
              <span class="dev-mock-toggle__label">开发调试</span>
              <el-switch
                :model-value="devMockEnabled"
                size="small"
                @change="toggleDevMock"
              />
            </div>
            <el-button class="action-bar-btn" size="small" @click="openNetworkDialog">
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

        <template v-if="viewMode === 'table'">
          <div class="table-toolbar">
            <div class="page-size-control">
              <span class="toolbar-label">显示行数</span>
              <div class="page-size-btns">
                <button
                  v-for="n in PAGE_SIZE_OPTIONS"
                  :key="n"
                  type="button"
                  class="page-size-btn"
                  :class="{ active: pageSize === n }"
                  @click="setPageSize(n)"
                >{{ n }}</button>
              </div>
            </div>
            <div v-if="filteredDevices.length > 0" class="table-toolbar-right">
              <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页 · 共 {{ filteredDevices.length }} 台</span>
              <div v-if="totalPages > 1" class="page-nav">
                <el-button class="wb-btn" size="small" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">上一页</el-button>
                <el-button class="wb-btn" size="small" :disabled="currentPage >= totalPages" @click="goPage(currentPage + 1)">下一页</el-button>
              </div>
            </div>
          </div>

          <el-card class="table-card" shadow="never">
            <div
              ref="tableWrapRef"
              class="device-table-wrapper"
              :style="{
                minHeight: `${tableMinHeightPx}px`,
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
                :row-class-name="deviceRowClassName"
                @row-click="handleRowClick"
              >
                <template #cell-device="{ record }">
                  <div class="dev-id" :class="{ 'is-selected': isRowSelected(record) }">
                    <p class="dev-model">{{ displayModel(record) }}</p>
                    <div class="dev-meta">
                      <code :title="record.serial">{{ record.serial }}</code>
                      <span :title="deviceAddress(record)">{{ deviceAddress(record) }}</span>
                    </div>
                  </div>
                </template>
                <template #cell-status="{ record }">
                  <DeviceStatusCell :device="record" />
                </template>
                <template #cell-connection_type="{ record }">
                  <span
                    class="conn-chip"
                    :class="record.connection_type === 'WIFI' ? 'conn-chip--wifi' : 'conn-chip--usb'"
                  >{{ record.connection_type === 'WIFI' ? 'Wi‑Fi' : 'USB' }}</span>
                </template>
                <template #cell-lock_status="{ record }">
                  <span
                    v-if="record.locked_by"
                    class="vis-chip vis-chip--locked"
                    :title="`锁定者: ${record.locked_by}`"
                  >🔒 {{ record.locked_by }}</span>
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
                    :text="activeFilter === 'all' ? EMPTY_TEXT.noDevices : EMPTY_TEXT.noMatch"
                    :hint="activeFilter === 'all' ? EMPTY_TEXT.hintRefresh : '尝试切换筛选条件'"
                  />
                </template>
              </AppTable>
            </div>
          </el-card>
        </template>

        <div v-if="viewMode === 'cards'" class="card-grid-grouped">
          <div v-for="group in CARD_GROUPS" :key="group.key" class="card-group">
            <template v-if="groupedDevices[group.key].length">
              <div class="card-group-title">
                {{ group.label }}
                <span class="card-group-count">{{ groupedDevices[group.key].length }}</span>
              </div>
              <div class="card-group-grid">
                <DeviceCard
                  v-for="dev in groupedDevices[group.key]"
                  :key="dev.serial"
                  :device="dev"
                  :current-user="currentUser"
                  @click="handleRowClick"
                  @lock="handleLockClick"
                  @release="(d) => handleRelease(d.serial)"
                  @disconnect="(d) => openDisconnectDialog(d.serial)"
                />
              </div>
            </template>
          </div>
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
