<script setup lang="ts">
/** 运营后台 · 用户管理：服务端分页列表 + 右侧抽屉动作。 */
import { computed, onMounted, ref } from "vue"
import { ElMessage, ElMessageBox } from "element-plus"
import WorkbenchHeader from "@/shared/components/WorkbenchHeader.vue"
import FilterTabs from "@/shared/components/FilterTabs.vue"
import AppTable from "@/shared/components/AppTable.vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import SkeletonCard from "@/shared/components/patterns/SkeletonCard.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import ErrorState from "@/shared/components/patterns/ErrorState.vue"
import { formatApiError } from "@/shared/api-client"
import { useAuthUser } from "@/shared/composables/useAuthUser"
import OpsUserDrawer from "./components/OpsUserDrawer.vue"
import OpsUserIdentityCell from "./components/OpsUserIdentityCell.vue"
import {
  disableOpsUsers,
  purgeOpsUsers,
  resetOpsUserPassword,
  setOpsUserActive,
  setOpsUserOperator,
} from "./api"
import { useOpsUsers } from "./composables/useOpsUsers"
import { formatDateTime, formatRelativeTime } from "./helpers/datetime"
import {
  identityClass,
  OPS_BATCH_DISABLE_HINT,
  OPS_BATCH_OUTCOME_LABELS,
  OPS_DISABLE_HINT,
  OPS_EMPTY_TEXT,
  OPS_GRANT_HINT,
  OPS_FILTER_TABS,
  OPS_IDENTITY_LABELS,
  OPS_KEYWORD_PLACEHOLDER,
  OPS_PAGE_ICON,
  OPS_PAGE_ICON_GRADIENT,
  OPS_PAGE_SUBTITLE,
  OPS_PAGE_TITLE,
  OPS_PURGE_CONFIRM_PREFIX,
  OPS_PURGE_HINT,
  OPS_RESET_HINT,
  OPS_REVOKE_HINT,
  OPS_TABLE_COLUMNS,
} from "./constants"
import type { OpsUser } from "./types"

const {
  users,
  total,
  page,
  keyword,
  status,
  loading,
  loaded,
  error,
  totalPages,
  showEmpty,
  load,
  setStatus,
  goPage,
  selectedIds,
  toggleSelected,
  setSelected,
} = useOpsUsers()

const { isSuperuser } = useAuthUser()
const columns = OPS_TABLE_COLUMNS
/** 勾选列的表头是复选框本身，不参与「图标 + 列名」渲染 */
const headerColumns = OPS_TABLE_COLUMNS.filter((column) => column.prop !== "_select")

// 首次进入拉第一页：组合式只提供状态与流程，生命周期归页面
onMounted(load)

const drawerOpen = ref(false)
const selected = ref<OpsUser | null>(null)
const busy = ref(false)
const oneTimePassword = ref("")

/** 超级管理员与运营都不能被停用或注销；只有普通用户可勾选。 */
function canManage(user: OpsUser): boolean {
  return user.identity === "user"
}

const selectedManageable = computed(() => (selected.value ? canManage(selected.value) : false))
const selectedCount = computed(() => selectedIds.value.length)
const manageableIds = computed(() => users.value.filter(canManage).map((item) => item.id))
const allPageSelected = computed(
  () =>
    manageableIds.value.length > 0 &&
    manageableIds.value.every((id) => selectedIds.value.includes(id)),
)

function togglePage(checked: boolean): void {
  setSelected(checked ? manageableIds.value : [])
}

function purgePhrase(count: number): string {
  return `${OPS_PURGE_CONFIRM_PREFIX} ${count} 个账号`
}

function openDrawer(row: OpsUser): void {
  selected.value = row
  oneTimePassword.value = ""
  drawerOpen.value = true
}

/** 用接口回带的最新行替换列表与抽屉里的同一行。 */
function applyRow(next: OpsUser): void {
  users.value = users.value.map((item) => (item.id === next.id ? next : item))
  if (selected.value?.id === next.id) selected.value = next
}

async function confirm(action: string, hint: string): Promise<boolean> {
  try {
    await ElMessageBox.confirm(hint ? `${action}\n${hint}` : action, "请确认", {
      confirmButtonText: "确认",
      cancelButtonText: "取消",
      type: "warning",
    })
    return true
  } catch {
    return false
  }
}

async function toggleActive(user: OpsUser): Promise<void> {
  const verb = user.is_active ? "停用" : "恢复启用"
  const ok = await confirm(`${verb}账号「${user.username}」？`, OPS_DISABLE_HINT)
  if (!ok) return
  busy.value = true
  try {
    const { data } = await setOpsUserActive(user.id, !user.is_active)
    if (!data.status || !data.data) throw data
    applyRow(data.data.user)
    ElMessage.success(`已${verb}「${user.username}」`)
  } catch (e) {
    ElMessage.error(formatApiError(e as never, `${verb}失败`))
  } finally {
    busy.value = false
  }
}

async function grantOperator(user: OpsUser, enabled: boolean): Promise<void> {
  const verb = enabled ? "设为运营" : "取消运营"
  const ok = await confirm(
    `将「${user.username}」${verb}？`,
    enabled ? OPS_GRANT_HINT : OPS_REVOKE_HINT,
  )
  if (!ok) return
  busy.value = true
  try {
    const { data } = await setOpsUserOperator(user.id, enabled)
    if (!data.status || !data.data) throw data
    applyRow(data.data.user)
    ElMessage.success(`已将「${user.username}」${verb}`)
  } catch (e) {
    ElMessage.error(formatApiError(e as never, `${verb}失败`))
  } finally {
    busy.value = false
  }
}

async function batchDisable(): Promise<void> {
  const ids = [...selectedIds.value]
  if (!ids.length) return
  const ok = await confirm(`停用已勾选的 ${ids.length} 个账号？`, OPS_BATCH_DISABLE_HINT)
  if (!ok) return
  busy.value = true
  try {
    const { data } = await disableOpsUsers(ids)
    if (!data.status || !data.data) throw data
    const { counts } = data.data
    ElMessage.success(
      `${OPS_BATCH_OUTCOME_LABELS.disabled} ${counts.disabled}，${OPS_BATCH_OUTCOME_LABELS.skipped} ${counts.skipped}，${OPS_BATCH_OUTCOME_LABELS.rejected} ${counts.rejected}`,
    )
    await load()
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "批量停用失败"))
  } finally {
    busy.value = false
  }
}

async function batchPurge(): Promise<void> {
  const ids = [...selectedIds.value]
  if (!ids.length) return
  const phrase = purgePhrase(ids.length)
  try {
    const { value } = await ElMessageBox.prompt(
      `${OPS_PURGE_HINT}\n请输入「${phrase}」以确认。`,
      "注销账号",
      {
        confirmButtonText: "注销",
        cancelButtonText: "取消",
        inputPlaceholder: phrase,
        inputValidator: (input) => input === phrase || `请原样输入「${phrase}」`,
      },
    )
    if (value !== phrase) return
  } catch {
    return
  }
  busy.value = true
  try {
    const { data } = await purgeOpsUsers(ids)
    if (!data.status || !data.data) throw data
    ElMessage.success(`已注销 ${data.data.deleted.length} 个账号`)
    await load()
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "批量注销失败"))
  } finally {
    busy.value = false
  }
}

async function resetPassword(user: OpsUser): Promise<void> {
  const ok = await confirm(`重置「${user.username}」的密码？`, OPS_RESET_HINT)
  if (!ok) return
  busy.value = true
  try {
    const { data } = await resetOpsUserPassword(user.id)
    if (!data.status || !data.data) throw data
    oneTimePassword.value = data.data.password
    ElMessage.success("已生成一次性密码")
  } catch (e) {
    ElMessage.error(formatApiError(e as never, "重置密码失败"))
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <div class="doc-page doc-page--fixed wb-shell ops-workbench">
    <WorkbenchHeader
      :title="OPS_PAGE_TITLE"
      :subtitle="OPS_PAGE_SUBTITLE"
      :icon="OPS_PAGE_ICON"
      :icon-gradient="OPS_PAGE_ICON_GRADIENT"
    />

    <div class="doc-body">
      <section class="ops-section" data-testid="ops-users-page">
        <!-- 行 1：批量动作在左（账号计数已下线："共 N 个账号" 与第二行的总条数重复） -->
        <div class="ops-toolbar">
          <DoodleBtn
            tone="paper"
            data-testid="ops-batch-disable"
            :disabled="!selectedCount || busy"
            @click="batchDisable"
          >
            批量停用{{ selectedCount ? `（${selectedCount}）` : "" }}
          </DoodleBtn>
          <DoodleBtn
            v-if="isSuperuser"
            tone="danger"
            data-testid="ops-batch-purge"
            :disabled="!selectedCount || busy"
            @click="batchPurge"
          >
            批量注销{{ selectedCount ? `（${selectedCount}）` : "" }}
          </DoodleBtn>
        </div>

        <!-- 行 2：页码文案 + 状态筛选 + 搜索 + 翻页（常驻，与设备页同序） -->
        <div class="ops-controls">
          <span class="ops-page-info">第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条</span>
          <FilterTabs
            :tabs="OPS_FILTER_TABS"
            :model-value="status"
            @update:model-value="setStatus"
          />
          <el-input
            v-model="keyword"
            :placeholder="OPS_KEYWORD_PLACEHOLDER"
            clearable
            class="ops-search"
            size="small"
          />
          <div class="ops-page-nav">
            <DoodleBtn tone="paper" :disabled="page <= 1" @click="goPage(page - 1)">
              上一页
            </DoodleBtn>
            <DoodleBtn tone="paper" :disabled="page >= totalPages" @click="goPage(page + 1)">
              下一页
            </DoodleBtn>
          </div>
        </div>

        <ErrorState v-if="error && !loaded" :message="error" @retry="load" />
        <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="6" />

        <template v-else>
          <ErrorState v-if="error" :message="error" @retry="load" />

          <AppTable
            :columns="columns"
            :data-source="users"
            row-key="id"
            :loading="loading"
            :empty-text="OPS_EMPTY_TEXT.noData"
            table-layout="fixed"
            accent="var(--c-ops)"
            class="ops-table"
            @row-click="openDrawer"
          >
            <!-- 勾选列：表头是全选复选框本身 -->
            <template #header-_select>
              <input
                type="checkbox"
                class="ops-check"
                data-testid="ops-page-check"
                :checked="allPageSelected"
                :disabled="!manageableIds.length"
                @click.stop
                @change="togglePage(($event.target as HTMLInputElement).checked)"
              />
            </template>

            <!-- 其余列：图标与列名同源（COLUMNS[].icon / .label），只做扫读加速 -->
            <template
              v-for="col in headerColumns"
              :key="`head-${col.prop}`"
              v-slot:[`header-${col.prop}`]
            >
              <span class="th-ico" aria-hidden="true">{{ col.icon }}</span
              >{{ col.label }}
            </template>

            <template #cell-_select="{ record }">
              <input
                type="checkbox"
                class="ops-check"
                data-testid="ops-row-check"
                :checked="selectedIds.includes(record.id)"
                :disabled="!canManage(record)"
                @click.stop
                @change="toggleSelected(record.id, ($event.target as HTMLInputElement).checked)"
              />
            </template>

            <template #cell-user="{ record }">
              <OpsUserIdentityCell :user="record" />
            </template>

            <template #cell-identity="{ record }">
              <span :class="identityClass(record.identity)">
                {{ OPS_IDENTITY_LABELS[record.identity as OpsUser["identity"]] }}
              </span>
            </template>

            <template #cell-is_active="{ record }">
              <span
                class="ops-state"
                :class="record.is_active ? 'ops-state--on' : 'ops-state--off'"
              >
                {{ record.is_active ? "启用" : "停用" }}
              </span>
            </template>

            <template #cell-date_joined="{ record }">
              <div class="ops-time">
                <span class="ops-time__rel">{{ formatRelativeTime(record.date_joined) }}</span>
                <span class="ops-time__abs">{{ formatDateTime(record.date_joined) }}</span>
              </div>
            </template>

            <template #cell-last_login="{ record }">
              <div v-if="record.last_login" class="ops-time">
                <span class="ops-time__rel">{{ formatRelativeTime(record.last_login) }}</span>
                <span class="ops-time__abs">{{ formatDateTime(record.last_login) }}</span>
              </div>
              <span v-else class="ops-time__abs">从未登录</span>
            </template>

            <template #cell-actions="{ record }">
              <div class="ops-row-actions">
                <button type="button" class="ops-action-pill" @click.stop="openDrawer(record)">
                  管理
                </button>
              </div>
            </template>

            <template #empty>
              <EmptyState
                v-if="showEmpty"
                icon="👤"
                :text="OPS_EMPTY_TEXT.noData"
                :hint="OPS_EMPTY_TEXT.hint"
              />
            </template>
          </AppTable>
        </template>
      </section>
    </div>

    <OpsUserDrawer
      v-model="drawerOpen"
      :user="selected"
      :busy="busy"
      :can-manage="selectedManageable"
      :can-grant="isSuperuser"
      :one-time-password="oneTimePassword"
      @toggle="toggleActive"
      @reset="resetPassword"
      @grant="grantOperator"
    />
  </div>
</template>

<style src="./table.style.css" scoped></style>
<style src="./index.style.css" scoped></style>
