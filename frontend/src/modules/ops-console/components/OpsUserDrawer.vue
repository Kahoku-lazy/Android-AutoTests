<script setup lang="ts">
import { computed } from "vue"
import DoodleBtn from "@/shared/components/DoodleBtn.vue"
import EmptyState from "@/shared/components/patterns/EmptyState.vue"
import { identityClass, OPS_DISABLE_HINT, OPS_IDENTITY_LABELS, OPS_RESET_HINT } from "../constants"
import type { OpsUser } from "../types"

const props = defineProps<{
  modelValue: boolean
  user: OpsUser | null
  busy: boolean

  canManage: boolean

  canGrant: boolean

  oneTimePassword: string
}>()

const emit = defineEmits<{
  "update:modelValue": [value: boolean]
  "toggle": [user: OpsUser]
  "reset": [user: OpsUser]
  "grant": [user: OpsUser, enabled: boolean]
}>()

const roleHint = computed(() => {
  if (!props.user) return ""
  if (props.canManage) return ""
  if (props.user.identity === "superuser") return "超级管理员账号不能被停用或注销。"
  return "运营账号不能被停用或注销。"
})
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    title="账号详情"
    size="min(460px, 92vw)"
    class="ops-drawer"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <EmptyState v-if="!user" icon="👤" text="没有选中账号" hint="请在列表里点一行" />

    <div v-else class="ops-detail">
      <div class="ops-detail__head">
        <h2 class="ops-detail__name">{{ user.username }}</h2>
        <span :class="identityClass(user.identity)">{{ OPS_IDENTITY_LABELS[user.identity] }}</span>
        <span class="ops-state" :class="user.is_active ? 'ops-state--on' : 'ops-state--off'">
          {{ user.is_active ? "启用中" : "已停用" }}
        </span>
      </div>

      <dl class="ops-meta">
        <dt>邮箱</dt>
        <dd>{{ user.email || "—" }}</dd>
        <dt>注册时间</dt>
        <dd>{{ user.date_joined || "—" }}</dd>
        <dt>最后登录</dt>
        <dd>{{ user.last_login || "从未登录" }}</dd>
      </dl>

      <div v-if="oneTimePassword" class="ops-secret" role="status">
        <p class="ops-secret__title">一次性新密码</p>
        <code class="ops-secret__value">{{ oneTimePassword }}</code>
        <p class="ops-secret__hint">{{ OPS_RESET_HINT }}</p>
      </div>

      <p v-if="roleHint" class="ops-hint">{{ roleHint }}</p>

      <div class="ops-actions">
        <DoodleBtn
          v-if="user.is_active"
          tone="danger"
          :disabled="!canManage || busy"
          @click="emit('toggle', user)"
        >
          停用账号
        </DoodleBtn>
        <DoodleBtn v-else tone="teal" :disabled="!canManage || busy" @click="emit('toggle', user)">
          恢复启用
        </DoodleBtn>
        <DoodleBtn tone="paper" :disabled="!canManage || busy" @click="emit('reset', user)">
          重置密码
        </DoodleBtn>
        <DoodleBtn
          v-if="canGrant && user.identity === 'user'"
          tone="yellow"
          :disabled="busy"
          @click="emit('grant', user, true)"
        >
          设为运营
        </DoodleBtn>
        <DoodleBtn
          v-if="canGrant && user.identity === 'operator'"
          tone="paper"
          :disabled="busy"
          @click="emit('grant', user, false)"
        >
          取消运营
        </DoodleBtn>
      </div>

      <p class="ops-hint">{{ OPS_DISABLE_HINT }}</p>
    </div>
  </el-drawer>
</template>

<style scoped>
.ops-detail {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
}

.ops-detail__head {
  display: flex;
  align-items: center;
  gap: var(--app-space-xs);
  flex-wrap: wrap;
}

.ops-detail__name {
  margin: 0;
  font-size: var(--app-size-lg);
  color: var(--app-text-primary);
}

.ops-meta {
  display: grid;
  grid-template-columns: 84px 1fr;
  gap: var(--app-space-xs) var(--app-space-sm);
  margin: 0;
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1px solid var(--app-border-light);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-subtle);
}

.ops-meta dt {
  color: var(--app-text-secondary);
  font-size: var(--app-size-xs);
}

.ops-meta dd {
  margin: 0;
  color: var(--app-text-primary);
  font-size: var(--app-size-xs);
  word-break: break-all;
}

.ops-secret {
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1px solid var(--ink);
  border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
  box-shadow: var(--app-shadow-sm);
}

.ops-secret__title {
  margin: 0 0 var(--app-space-xs);
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ops-secret__value {
  display: block;
  font-family: var(--app-font-mono);
  font-size: var(--app-size-md);
  color: var(--app-text-primary);
  letter-spacing: 1px;
}

.ops-secret__hint {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
}

.ops-hint {
  margin: 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  line-height: 1.6;
}

.ops-actions {
  display: flex;
  gap: var(--app-space-sm);
  flex-wrap: wrap;
}

.ops-identity {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  border-radius: var(--app-radius-sm);
  border: 1.5px solid var(--ink);
  background: color-mix(in srgb, var(--paper) 55%, var(--app-bg-card));
  color: var(--app-text-primary);
}

.ops-identity--superuser {
  background: color-mix(in srgb, var(--c-element) 32%, var(--app-bg-card));
}

.ops-identity--operator {
  background: color-mix(in srgb, var(--c-ops) 30%, var(--app-bg-card));
}

.ops-identity--user {
  border-color: var(--app-border-strong);
  font-weight: var(--app-font-weight-bold);
}

.ops-state {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  font-size: var(--app-size-sm);
  font-weight: var(--app-font-weight-heavy);
  border-radius: var(--app-radius-sm);
  border: 1.5px solid var(--ink);
}

.ops-state--on {
  color: var(--app-status-success-text);
  background: color-mix(in srgb, var(--c-device) 32%, var(--app-bg-card));
}

.ops-state--off {
  color: var(--app-status-danger-text);
  background: color-mix(in srgb, var(--c-runner) 45%, var(--app-bg-card));
}
</style>
