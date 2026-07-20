<script setup>
import { ref } from "vue";
// Button → el-button, AppCard → AppCard
import AppCard from "@/shared/components/AppCard.vue";
import { ElTag } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import { caseLock, caseUnlock } from "../api.js";

const props = defineProps({
  item: { type: Object, required: true },
});

const emit = defineEmits(["edit", "delete", "select", "refresh"]);

function resolveCurrentUser() {
  const active = sessionStorage.getItem("auth_active") || ""
  if (active) return active
  try {
    const pool = JSON.parse(localStorage.getItem("auth_accounts") || "{}")
    return Object.keys(pool)[0] || ""
  } catch { return "" }
}
const currentUser = resolveCurrentUser();
const isCreator = currentUser && props.item.created_by === currentUser;
const isEditing = props.item.editing_by && props.item.editing_by !== currentUser;
const locking = ref(false);

function stepCount() {
  try {
    const data = props.item.steps_data;
    if (Array.isArray(data)) return data.length;
  } catch (_) {}
  return 0;
}

function formatDate(val) {
  if (!val) return "";
  const d = new Date(val);
  if (isNaN(d.getTime())) return val.slice(0, 10);
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const dd = String(d.getDate()).padStart(2, "0");
  const hh = String(d.getHours()).padStart(2, "0");
  const mi = String(d.getMinutes()).padStart(2, "0");
  return `${mm}-${dd} ${hh}:${mi}`;
}

async function toggleLock() {
  locking.value = true;
  try {
    if (props.item.locked) {
      await caseUnlock(props.item.id);
    } else {
      await caseLock(props.item.id);
    }
    emit("refresh");
  } catch (e) {
    // silently fail, parent refreshes
  } finally {
    locking.value = false;
  }
}
</script>

<template>
  <AppCard
    class="case-card"
    @click="$emit('select', item)"
  >
    <div class="case-card__body">
      <div class="case-card__header">
        <div class="case-card__header-left">
          <span class="case-card__id">{{ item.id }}</span>
          <span
            class="case-card__priority"
            :class="
              'case-card__priority--' + (item.priority || 'P1').toLowerCase()
            "
            >{{ item.priority }}</span
          >
          <span v-if="item.locked" class="case-card__lock-icon" title="已锁定">🔒</span>
          <span v-if="item.visibility !== 'public'" class="case-card__vis-icon" :title="'可见性: ' + item.visibility">👁️‍🗨️</span>
        </div>
        <el-tag
          :type="item.enabled ? 'success' : 'info'"
          effect="dark"
          size="small"
          round
        >
          {{ item.enabled ? "启用" : "停用" }}
        </el-tag>
      </div>
      <h4 class="case-card__title">{{ item.title || "未命名用例" }}</h4>
      <!-- Editing status -->
      <div v-if="isEditing" class="case-card__editing-badge">
        ✏️ {{ props.item.editing_by }} 正在编辑
      </div>
      <div class="case-card__meta">
        <span v-if="item.category" class="meta-tag">{{ item.category }}</span>
        <span v-if="item.directory_name" class="meta-tag meta-tag--dir">{{
          item.directory_name
        }}</span>
        <span class="meta-tag meta-tag--steps">{{ stepCount() }} 步骤</span>
        <span v-if="item.created_by" class="meta-tag meta-tag--user"
          >创建: {{ item.created_by }} · {{ formatDate(item.created_at) }}</span
        >
        <span v-if="item.updated_by" class="meta-tag meta-tag--user"
          >修改: {{ item.updated_by }} · {{ formatDate(item.updated_at) }}</span
        >
      </div>
    </div>
    <div class="case-card__actions" @click.stop>
      <el-button
        size="small"
        type="primary"
        :disabled="isEditing"
        @click="$emit('edit', item)"
        >编辑</el-button
      >
      <!-- Lock toggle (creator only) -->
      <el-button
        v-if="isCreator"
        size="small"
        :type="item.locked ? 'primary' : 'default'"
        :danger="item.locked"
        :loading="locking"
        @click="toggleLock"
        >{{ item.locked ? '🔒' : '🔓' }}</el-button
      >
      <ConfirmButton
        size="small"
        type="primary"
        danger
        plain
        :message="`删除用例「${item.title}」？`"
        title="确认删除"
        confirm-text="删除"
        @confirm="$emit('delete', item)"
        >删除</ConfirmButton
      >
    </div>
  </AppCard>
</template>

<style scoped>
.case-card {
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.case-card:hover {
  transform: translateY(-2px);
}

.case-card__body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.case-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.case-card__header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.case-card__id {
  font-family: "SF Mono", "Fira Code", Consolas, monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--app-text-secondary);
  background: rgba(162,210,255,0.14);
  padding: 2px 8px;
  border-radius: 6px;
}

.case-card__priority {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  border-radius: 8px;
  letter-spacing: 0.02em;
}

.case-card__priority--p0 {
  background: rgba(224, 90, 90, 0.12);
  color: #c0392b;
}

.case-card__priority--p1 {
  background: rgba(245, 195, 28, 0.15);
  color: #8b6914;
}

.case-card__priority--p2 {
  background: rgba(162,210,255,0.14);
  color: var(--app-text-secondary);
}

.case-card__title {
  font-family: Nunito, "Noto Sans SC", sans-serif;
  font-weight: 700;
  font-size: 15px;
  color: var(--app-text);
  margin: 0;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.case-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.meta-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--app-text-secondary);
  background: rgba(162,210,255,0.12);
  padding: 2px 8px;
  border-radius: 8px;
}

.meta-tag--dir {
  color: var(--app-green-deep);
  background: rgba(162,210,255,0.16);
}

.meta-tag--steps {
  color: var(--app-text-secondary);
}

.meta-tag--user {
  color: #889df0;
  background: rgba(136, 157, 240, 0.08);
}

/* Editing status badge */
.case-card__editing-badge {
  font-size: 11px;
  font-weight: 700;
  color: #9a6a1f;
  background: rgba(255,214,165,0.28);
  padding: 4px 10px;
  border-radius: 8px;
}

.case-card__actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px dashed rgba(162,210,255,0.38);
}
</style>
