<template>
  <div class="tb-cat-head">
    <div>
      <h3 class="tb-cat-title">{{ source.name }}</h3>
      <p class="tb-cat-sub">{{ source.desc }} · 端口 / SKU名称 / 波特率来自平台配置登记（只读）</p>
    </div>
    <div class="tb-cat-actions">
      <button type="button" class="tb-btn" :disabled="loading" @click="loadPorts">
        {{ loading ? "刷新中…" : "刷新" }}
      </button>
    </div>
  </div>

  <div class="tb-cat-body">
    <ErrorState v-if="loadError" :message="loadError" @retry="loadPorts" />
    <SkeletonCard v-else-if="loading && !ports.length" variant="list" :lines="3" />
    <EmptyState
      v-else-if="!ports.length"
      icon="🔌"
      text="平台未登记日志端口"
      hint="在平台配置里登记日志来源后，这里会列出端口、SKU 与波特率"
    />
    <template v-else>
      <AppTable
        :columns="COLUMNS"
        :data-source="ports"
        row-key="port"
        accent="var(--c-ai)"
        empty-text="平台未登记日志端口"
      >
        <template #cell-port="{ record }">
          <span class="lp-port">
            <span class="lp-dot" :class="record.listening ? 'on' : 'off'" />
            {{ record.port }}
          </span>
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
            <span class="lp-switch-text" :class="record.enabled ? 'on' : 'off'">
              {{ listeningText(record) }}
            </span>
          </span>
        </template>
        <template #cell-actions="{ record }">
          <button type="button" class="tb-btn" @click="openLog(record)">日志查看</button>
        </template>
      </AppTable>

      <p class="lp-hint">
        {{ LOG_DISABLE_WARNING }}
        <span class="lp-hint-dim">
          · 波特率是无线串口盒串口侧的参数，只作展示，不参与采集（日志走 TCP 监听）
        </span>
      </p>
      <p v-if="!props.canManage" class="lp-hint-dim">仅超级管理员可以开关监听</p>
      <p v-for="row in portsWithNote" :key="row.port" class="lp-warn">{{ row.note }}</p>
    </template>
  </div>

  <el-drawer v-model="drawerVisible" :title="drawerTitle" size="760px" @close="closeLog">
    <div class="lp-log">
      <div class="lp-log-bar">
        <span class="lp-tail">
          读取行数
          <el-select :model-value="tail" size="small" class="lp-tail-select" @change="onTailChange">
            <el-option
              v-for="num in LOG_TAIL_OPTIONS"
              :key="num"
              :label="`${num} 行`"
              :value="num"
            />
          </el-select>
        </span>
        <button type="button" class="tb-btn" :disabled="linesLoading" @click="refreshLines">
          {{ linesLoading ? "读取中…" : "刷新" }}
        </button>
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
            <span class="lp-time">{{ item.clock }}</span>
            <span class="lp-src" :class="`lp-src--${item.source}`">{{ item.source }}</span>
            <span class="lp-text">{{ item.text }}</span>
          </li>
        </ol>
      </div>
    </div>
  </el-drawer>
</template>

<script setup lang="ts">
/** WifiPortPanel — 无线端口来源区：五列表格（端口 / SKU名称 / 波特率 / 监听开关 / 日志查看）+ 原始日志抽屉 */
import { computed, onMounted } from "vue"
import AppTable from "@/shared/components/AppTable.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import { useLogPorts } from "../composables/useLogPorts"
import { sourceDef } from "../helpers/toolbox-assembly"
import {
  LOG_DISABLE_WARNING,
  LOG_TAIL_OPTIONS,
  decorateLogLines,
  logConclusionText,
  logCountText,
} from "../helpers/log-port-lines"
import type { LogPortRow } from "../api/toolbox"

const props = defineProps<{ canManage?: boolean }>()

const source = sourceDef("port")

/** 五列：前三列只读展示，后两列是操作（开关 / 日志查看） */
const COLUMNS = [
  { dataIndex: "port", label: "端口", width: 120 },
  { dataIndex: "sku", label: "SKU名称", minWidth: 140 },
  { dataIndex: "baud", label: "波特率", width: 140 },
  { dataIndex: "enabled", label: "监听开关", width: 190 },
  { key: "actions", label: "日志查看", width: 140 },
]

const {
  ports,
  loading,
  loadError,
  togglingPort,
  loadPorts,
  setEnabled,
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

function listeningText(row: LogPortRow): string {
  if (!row.enabled) return "已停止监听"
  return row.listening ? "监听中" : "未监听"
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
