<script setup lang="ts">
/** Device Pool v2 — 设备管理主页面 per PRD-02 */
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
import KpiCard from '@/shared/components/KpiCard.vue'
import { IconWifi, IconRefresh } from '@/shared/icons/index'
import { useDevicePoolView } from './DevicePoolView.logic'

const {
  scanning,
  loading,
  error,
  activeFilter,
  kpiStats,
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
  displayModel,
  connectionLabel,
  deviceAddress,
  formatDateTime,
  formatRelativeTime,
  statusTag,
  PAGE_HEADER,
  FILTER_TABS,
  COLUMNS,
  CARD_GROUPS,
  EMPTY_TEXT,
  setPageSize,
  goPage,
} = useDevicePoolView()
</script>

<template>
  <div class="doc-page wb-shell device-workbench">
    <WorkbenchHeader
      :title="PAGE_HEADER.title"
      :subtitle="PAGE_HEADER.subtitle"
      :icon="PAGE_HEADER.icon"
      :icon-gradient="PAGE_HEADER.iconGradient"
    >
    </WorkbenchHeader>

    <ErrorState v-if="error" :message="error" @retry="handleRefresh" />

    <div class="doc-body" v-else>
      <!-- 统计概览 -->
      <section class="doc-section device-section">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            统计概览
            <span class="doc-tag">Overview</span>
          </h3>
          <span class="doc-section__label">设备在线状态与平台接入总览</span>
        </div>
        <div class="kpi-row">
          <KpiCard :value="kpiStats.online" label="在线" color="var(--c-device)" shape="diamond" />
          <KpiCard :value="kpiStats.busy" label="使用中" color="var(--c-runner)" shape="triangle" />
          <KpiCard :value="kpiStats.total" label="总计" color="var(--ink)" shape="circle" />
        </div>
      </section>

      <!-- 设备列表 -->
      <section class="doc-section device-section--list">
        <div class="doc-section__header">
          <h3 class="doc-section__title">
            设备列表
            <span class="doc-tag">Devices</span>
          </h3>
          <span class="doc-section__label">管理所有已连接的 Android 设备</span>
        </div>
        <div class="device-toolbar">
          <FilterTabs :tabs="FILTER_TABS" v-model="activeFilter" />
          <div class="device-toolbar__right">
            <div class="view-toggle">
              <button class="view-btn" :class="{ active: viewMode === 'table' }" @click="switchViewMode('table')">📋 表格</button>
              <button class="view-btn" :class="{ active: viewMode === 'cards' }" @click="switchViewMode('cards')">📷 卡片</button>
            </div>
            <span class="filter-count">{{ filteredDevices.length }} 台</span>
            <el-button class="action-bar-btn" size="small" @click="openNetworkDialog">
              <IconWifi :size="14" /> 局域网
            </el-button>
            <el-button class="action-bar-btn" size="small" :loading="scanning || loading" @click="handleRefresh">
              <IconRefresh :size="14" /> 刷新
            </el-button>
          </div>
        </div>

        <!-- 表视图 -->
        <template v-if="viewMode === 'table'">
          <div class="table-toolbar">
            <div class="page-size-control">
              <span class="toolbar-label">显示行数</span>
              <div class="page-size-btns">
                <button v-for="n in PAGE_SIZE_OPTIONS" :key="n" type="button" class="page-size-btn" :class="{ active: pageSize === n }" @click="setPageSize(n)">{{ n }}</button>
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
          <div class="device-table-wrapper">
            <AppTable
              :columns="COLUMNS"
              :data-source="pagedDevices"
              row-key="serial"
              :striped="true"
              :loading="loading"
              empty-text="暂无设备，点击「刷新设备」扫描并连接设备"
              @row-click="handleRowClick"
            >
                    <template #cell-adb_addr="{ record }">
                      <span class="mono-text" :title="deviceAddress(record)">{{ deviceAddress(record) }}</span>
                    </template>
                    <template #cell-serial="{ record }">
                      <span v-if="isRowSelected(record)" class="row-dot">●</span>
                      <span class="mono-text" :title="record.serial">{{ record.serial }}</span>
                    </template>
                    <template #cell-model="{ record }">
                      <span>{{ displayModel(record) }}</span>
                    </template>
                    <template #cell-screen="{ record }">
                      <span v-if="record.screen">{{ record.screen }}</span>
                      <span v-else class="text-muted">—</span>
                    </template>
                    <template #cell-status="{ record }">
                      <DeviceStatusCell :device="record" />
                    </template>
                    <template #cell-connection_type="{ record }">
                      <span class="connection-text">{{ connectionLabel(record) }}</span>
                    </template>
                    <template #cell-lock_status="{ record }">
                      <span v-if="record.locked_by" class="lock-badge lock-badge--locked" :title="`锁定者: ${record.locked_by}`">{{ record.locked_by }}</span>
                      <span v-else class="lock-badge lock-badge--shared">公开</span>
                    </template>
                    <template #cell-connected_at="{ record }">
                      <span class="last-seen-text">{{ formatDateTime(record.connected_at) }}</span>
                    </template>
                    <template #cell-last_seen="{ record }">
                      <span class="last-seen-text">{{ formatRelativeTime(record.last_seen) }}</span>
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
                      <EmptyState icon="📱"
                        :text="activeFilter === 'all' ? EMPTY_TEXT.noDevices : EMPTY_TEXT.noMatch"
                        :hint="activeFilter === 'all' ? EMPTY_TEXT.hintRefresh : '尝试切换筛选条件'" />
                    </template>
              </AppTable>
          </div>
        </el-card>
        </template>

        <!-- 卡片视图：按状态分组 -->
        <div class="card-grid-grouped" v-if="viewMode === 'cards'">
          <div class="card-group" v-for="group in CARD_GROUPS" :key="group.key">
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

    <!-- Dialogs -->
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
