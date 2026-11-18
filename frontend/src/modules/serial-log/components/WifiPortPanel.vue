<template>
  <div class="sl-cat-head">
    <div>
      <h3 class="sl-cat-title">{{ PORTS_PANEL_TITLE }}</h3>
      <p class="sl-cat-sub">
        {{ PORTS_PANEL_DESC }} · 配置端口来自平台登记（只读）；自定义端口可新增 / 编辑 / 删除
      </p>
    </div>
    <div class="sl-cat-actions">
      <DoodleBtn v-if="props.canManage" tone="yellow" @click="openAdd">
        {{ PORTS_ADD_LABEL }}
      </DoodleBtn>
      <button type="button" class="sl-btn" :disabled="loading" @click="loadPorts">
        {{ loading ? "刷新中…" : "刷新" }}
      </button>
    </div>
  </div>

  <div class="sl-cat-body sketch-kit">
    <div class="lp-ipbar">
      <span class="lp-ip-ico" aria-hidden="true">📡</span>
      <span class="lp-ip-label">{{ PORTS_IP_LABEL }}</span>
      <strong v-if="listenIp" class="lp-ip-value">{{ listenIp }}</strong>
      <span v-else class="lp-ip-empty">{{ PORTS_IP_EMPTY }}</span>
      <DoodleBtn v-if="listenIp" tone="paper" @click="copyIp">{{ PORTS_IP_COPY_LABEL }}</DoodleBtn>
      <span class="lp-ip-hint">{{ PORTS_IP_HINT }}</span>
    </div>
    <ErrorState v-if="loadError" :message="loadError" @retry="loadPorts" />
    <SkeletonCard v-else-if="loading && !ports.length" variant="list" :lines="3" />
    <EmptyState
      v-else-if="!ports.length"
      icon="🔌"
      text="平台未登记日志端口"
      hint="在平台配置里登记日志来源后，这里会列出端口、SKU 与波特率"
    />
    <template v-else>
      <div class="lp-bar">
        <DoodleBtn tone="paper" :disabled="false" @click="toggleOnlyListening">
          {{ onlyListening ? "显示全部端口" : PORTS_ONLY_LISTENING_LABEL }}
        </DoodleBtn>
        <span class="lp-count">
          命中 {{ filteredPorts.length }} / 共 {{ ports.length }} 个端口
        </span>
      </div>

      <AppTable
        :columns="COLUMNS"
        :data-source="pagedPorts"
        row-key="port"
        accent="var(--c-device)"
        table-layout="fixed"
        empty-text="平台未登记日志端口"
      >
        <template
          v-for="col in COLUMNS"
          :key="`h-${col.dataIndex}`"
          v-slot:[`header-${col.dataIndex}`]
        >
          <span class="th-ico" aria-hidden="true">{{ col.icon }}</span
          >{{ col.title }}
        </template>
        <template #cell-port="{ record }">
          <div class="lp-id">
            <span class="lp-badge">🔌</span>
            <div>
              <strong class="lp-port-no">
                {{ record.port }}
                <span
                  class="lp-origin"
                  :class="record.origin === 'custom' ? 'is-custom' : 'is-config'"
                >
                  {{ PORTS_ORIGIN_LABELS[record.origin] || record.origin }}
                </span>
              </strong>
              <span class="lp-port-sub">
                {{ record.sku }} · {{ record.address || PORTS_ADDRESS_FALLBACK }}
              </span>
            </div>
          </div>
        </template>
        <template #cell-sku="{ record }">
          <span class="lp-mono">{{ record.sku }}</span>
        </template>
        <template #cell-baud="{ record }">
          <span class="lp-mono">{{ record.baud || "—" }}</span>
        </template>
        <template #cell-enabled="{ record }">
          <span class="lp-switch">
            <el-switch
              :model-value="record.enabled"
              :disabled="!props.canManage || togglingPort === record.port"
              @update:model-value="setEnabled(record, $event as boolean)"
            />
            <span class="lp-st" :class="statusTone(record)">{{ listeningText(record) }}</span>
          </span>
        </template>
        <template #cell-actions="{ record }">
          <div class="lp-actions">
            <DoodleBtn tone="paper" @click="openLog(record)">日志查看</DoodleBtn>
            <DoodleBtn
              v-if="record.enabled && !record.listening"
              tone="teal"
              :disabled="togglingPort === record.port"
              @click="setEnabled(record, true)"
            >
              {{ PORTS_RETRY_LABEL }}
            </DoodleBtn>
            <template v-if="props.canManage && record.origin === 'custom'">
              <DoodleBtn tone="paper" @click="openEdit(record)">{{ PORTS_EDIT_LABEL }}</DoodleBtn>
              <DoodleBtn tone="danger" @click="remove(record)">{{ PORTS_DELETE_LABEL }}</DoodleBtn>
            </template>
          </div>
        </template>
      </AppTable>

      <div class="lp-pager">
        <span class="lp-count">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <DoodleBtn tone="paper" :disabled="currentPage <= 1" @click="goPage(currentPage - 1)">
          上一页
        </DoodleBtn>
        <DoodleBtn
          tone="paper"
          :disabled="currentPage >= totalPages"
          @click="goPage(currentPage + 1)"
        >
          下一页
        </DoodleBtn>
      </div>

      <div class="lp-hintbar">
        <span aria-hidden="true">ℹ️</span>
        <span>
          {{ LOG_DISABLE_WARNING }}；波特率是无线串口盒串口侧的参数，只作展示，不参与采集（日志走
          TCP 监听）。删除自定义端口会保留历史日志文件。
          <b v-if="!props.canManage">{{ SERIAL_LOG_READONLY_HINT }}</b>
        </span>
      </div>
      <p v-for="row in portsWithNote" :key="row.port" class="lp-warn">{{ row.note }}</p>
    </template>
  </div>

  <el-drawer v-model="drawerVisible" :title="drawerTitle" size="760px" @close="closeLog">
    <div class="lp-log">
      <div class="lp-log-bar sketch-kit">
        <span class="lp-tail">
          读取行数
          <el-select :model-value="tail" class="lp-tail-select" @change="onTailChange">
            <el-option
              v-for="num in LOG_TAIL_OPTIONS"
              :key="num"
              :label="`${num} 行`"
              :value="num"
            />
          </el-select>
        </span>
        <DoodleBtn tone="paper" :disabled="linesLoading" @click="refreshLines">
          {{ linesLoading ? "读取中…" : "刷新" }}
        </DoodleBtn>
        <span class="lp-auto">
          自动刷新
          <el-switch
            :model-value="autoRefresh"
            @update:model-value="onAutoRefreshChange($event as boolean)"
          />
        </span>
        <span class="lp-count">{{ logCountText(lineCount, rawLineCount) }}</span>
      </div>

      <p v-if="note" class="lp-note">{{ note }}</p>

      <div v-loading="linesLoading" class="lp-log-body">
        <EmptyState v-if="!lines.length && !linesLoading" icon="📄" :text="emptyText" />
        <ol v-else class="lp-lines">
          <li v-for="item in decorated" :key="item.key" class="lp-line">
            <span class="lp-text">{{ item.text }}</span>
          </li>
        </ol>
      </div>
    </div>
  </el-drawer>

  <PortFormDialog
    :visible="dialogVisible"
    :edit-row="editRow"
    :existing-ports="ports.map((row) => row.port)"
    :saving="saving"
    :error="formError"
    @close="closeDialog"
    @submit="submit"
  />
</template>

<script setup lang="ts">
/** WifiPortPanel — 串口日志页「无线端口」Tab：本机 IP 条 + 五列表格 + 自定义端口增删改
 *  + 只看监听中筛选 + 分页 + 原始日志抽屉；监听失败红色胶囊与重试。 */
import { computed, onMounted, ref } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { usePagination } from "@/shared/composables/usePagination"
import { useLogPorts } from "../composables/useLogPorts"
import { useCustomPorts } from "../composables/useCustomPorts"
import PortFormDialog from "./PortFormDialog.vue"
import {
  PORTS_ADD_LABEL,
  PORTS_ADDRESS_FALLBACK,
  PORTS_DELETE_LABEL,
  PORTS_EDIT_LABEL,
  PORTS_IP_COPY_LABEL,
  PORTS_IP_EMPTY,
  PORTS_IP_HINT,
  PORTS_IP_LABEL,
  PORTS_LISTEN_FAIL_LABEL,
  PORTS_ONLY_LISTENING_LABEL,
  PORTS_ORIGIN_LABELS,
  PORTS_PAGE_SIZE,
  PORTS_PAGE_SIZE_OPTIONS,
  PORTS_PANEL_DESC,
  PORTS_PANEL_TITLE,
  PORTS_RETRY_LABEL,
  SERIAL_LOG_READONLY_HINT,
} from "../constants"
import {
  LOG_DISABLE_WARNING,
  LOG_TAIL_OPTIONS,
  decorateLogLines,
  logConclusionText,
  logCountText,
} from "../helpers/log-port-lines"
import type { LogPortRow } from "../api"

const props = defineProps<{ canManage?: boolean }>()

/** 五列：前三列只读展示，后两列是操作（开关 / 日志查看）；列头带图标 */
const COLUMNS = [
  { dataIndex: "port", title: "端口", icon: "🔌", minWidth: 200 },
  { dataIndex: "sku", title: "SKU名称", icon: "▣", minWidth: 160 },
  { dataIndex: "baud", title: "波特率", icon: "⏱", width: 140, align: "center" },
  { dataIndex: "enabled", title: "监听状态", icon: "🟢", width: 240, align: "center" },
  { dataIndex: "actions", title: "操作", icon: "💬", width: 140, align: "center" },
]

const {
  ports,
  listenIp,
  loading,
  loadError,
  togglingPort,
  loadPorts,
  setEnabled,
  copyIp,
  drawerVisible,
  activePort,
  lines,
  linesLoading,
  conclusion,
  note,
  lineCount,
  rawLineCount,
  tail,
  autoRefresh,
  openLog,
  closeLog,
  refreshLines,
  onAutoRefreshChange,
} = useLogPorts()

/** 自定义端口增删改：弹窗开合 / 校验兜底 / CRUD 编排都在 composable */
const {
  dialogVisible,
  editRow,
  saving,
  formError,
  openAdd,
  openEdit,
  closeDialog,
  submit,
  remove,
} = useCustomPorts(ports, loadPorts)

/** 只看监听中：本地筛选，不发请求 */
const onlyListening = ref(false)
const filteredPorts = computed(() =>
  onlyListening.value ? ports.value.filter((row) => row.enabled) : ports.value,
)

const {
  currentPage,
  totalPages,
  pagedItems: pagedPorts,
  goPage,
} = usePagination(filteredPorts, {
  pageSize: PORTS_PAGE_SIZE,
  options: PORTS_PAGE_SIZE_OPTIONS,
})

function toggleOnlyListening(): void {
  onlyListening.value = !onlyListening.value
  goPage(1)
}

/** 服务端已按「同毫秒合并、最新在上」排好：这里只做装饰，不再排序 */
const decorated = computed(() => decorateLogLines(lines.value))

const portsWithNote = computed(() => ports.value.filter((row) => Boolean(row.note)))

const drawerTitle = computed(() => {
  const row = activePort.value
  if (!row) return "原始日志"
  return `${row.sku} · 端口 ${row.port} · ${row.log_file}`
})

const emptyText = computed(
  () => logConclusionText(conclusion.value, activePort.value?.port || 0) || "当前日志文件暂无内容",
)

/** 状态胶囊色相：监听中绿 / 监听失败红 / 已停止灰 */
function statusTone(row: LogPortRow): string {
  if (!row.enabled) return "is-off"
  return row.listening ? "is-on" : "is-fail"
}

function listeningText(row: LogPortRow): string {
  if (!row.enabled) return "已停止监听"
  return row.listening ? "监听中" : PORTS_LISTEN_FAIL_LABEL
}

function onTailChange(value: unknown): void {
  tail.value = Number(value) || tail.value
  void refreshLines()
}

onMounted(() => {
  void loadPorts()
})
</script>

<style src="./WifiPortPanel.style.css" scoped></style>
