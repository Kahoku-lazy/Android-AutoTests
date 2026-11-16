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
import { resetOpsUserPassword, setOpsUserActive, setOpsUserOperator } from "./api"
import { useOpsUsers } from "./composables/useOpsUsers"
import {
  identityClass,
  OPS_DISABLE_HINT,
  OPS_EMPTY_TEXT,
  OPS_GRANT_HINT,
  OPS_FILTER_TABS,
  OPS_IDENTITY_LABELS,
  OPS_KEYWORD_PLACEHOLDER,
  OPS_PAGE_ICON,
  OPS_PAGE_ICON_GRADIENT,
  OPS_PAGE_SIZE_OPTIONS,
  OPS_PAGE_SUBTITLE,
  OPS_PAGE_TITLE,
  OPS_RESET_HINT,
  OPS_REVOKE_HINT,
  OPS_TABLE_COLUMNS,
} from "./constants"
import type { OpsUser } from "./types"

const {
  users,
  total,
  page,
  pageSize,
  keyword,
  status,
  loading,
  loaded,
  error,
  totalPages,
  showEmpty,
  load,
  setStatus,
  setPageSize,
  goPage,
} = useOpsUsers()

const { isSuperuser } = useAuthUser()
const columns = OPS_TABLE_COLUMNS

// 首次进入拉第一页：组合式只提供状态与流程，生命周期归页面
onMounted(load)

const drawerOpen = ref(false)
const selected = ref<OpsUser | null>(null)
const busy = ref(false)
const oneTimePassword = ref("")

/** 超管行谁都不能动；运营行只有超管能动；普通用户行运营可动。 */
function canManage(user: OpsUser): boolean {
  if (user.identity === "superuser") return false
  if (user.identity === "operator") return isSuperuser.value
  return true
}

const selectedManageable = computed(() => (selected.value ? canManage(selected.value) : false))

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
      <section class="doc-section ops-section" data-testid="ops-users-page">
        <div class="doc-section__header ops-section__header">
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
          />
          <span class="ops-count">共 {{ total }} 个账号</span>
        </div>

        <ErrorState v-if="error && !loaded" :message="error" @retry="load" />
        <SkeletonCard v-else-if="loading && !loaded" variant="list" :lines="6" />

        <template v-else>
          <div class="ops-toolbar">
            <span class="ops-toolbar__label">显示行数</span>
            <div class="ops-size-btns">
              <button
                v-for="size in OPS_PAGE_SIZE_OPTIONS"
                :key="size"
                type="button"
                class="ops-size-btn"
                :class="{ active: pageSize === size }"
                @click="setPageSize(size)"
              >
                {{ size }}
              </button>
            </div>
            <span v-if="total" class="ops-page-info">
              第 {{ page }} / {{ totalPages }} 页 · 共 {{ total }} 条
            </span>
            <div v-if="totalPages > 1" class="ops-page-nav">
              <DoodleBtn tone="paper" :disabled="page <= 1" @click="goPage(page - 1)">
                上一页
              </DoodleBtn>
              <DoodleBtn tone="paper" :disabled="page >= totalPages" @click="goPage(page + 1)">
                下一页
              </DoodleBtn>
            </div>
          </div>

          <ErrorState v-if="error" :message="error" @retry="load" />

          <AppTable
            :columns="columns"
            :data-source="users"
            row-key="id"
            :border="true"
            :loading="loading"
            :empty-text="OPS_EMPTY_TEXT.noData"
            accent="var(--c-ops)"
            class="ops-table"
            @row-click="openDrawer"
          >
            <template #cell-username="{ record }">
              <code class="ops-account">{{ record.username }}</code>
            </template>

            <template #cell-email="{ record }">
              <span class="ops-email">{{ record.email || "—" }}</span>
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

            <template #cell-actions="{ record }">
              <DoodleBtn tone="paper" @click.stop="openDrawer(record)">管理</DoodleBtn>
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

<style src="./index.style.css" scoped></style>
