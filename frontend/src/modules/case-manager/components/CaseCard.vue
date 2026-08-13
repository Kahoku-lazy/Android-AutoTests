<script setup>
import { ref } from "vue";
// Button → el-button, AppCard → AppCard
import AppCard from "@/shared/components/AppCard.vue";
import { ElMessage, ElTag } from "element-plus";
import ConfirmButton from "@/shared/components/patterns/ConfirmButton.vue";
import { getActive } from "@/shared/auth/token-storage";
import { caseLock, caseUnlock } from "../api";

const props = defineProps({
  item: { type: Object, required: true },
});

const emit = defineEmits(["edit", "delete", "select", "refresh"]);

const currentUser = getActive();
const isCreator = !!(currentUser && props.item.created_by === currentUser);
const isEditing = !!(props.item.editing_by && props.item.editing_by !== currentUser);
const locking = ref(false);

function stepCount() {
  const cfg = props.item.config_json;
  if (cfg && typeof cfg === "object") {
    // Single format API: count cases
    if (Array.isArray(cfg.cases)) return cfg.cases.length;
    // Multi format API: count steps
    if (Array.isArray(cfg.steps)) return cfg.steps.length;
  }
  // UI/Web: derive from steps_data
  try {
    const data = props.item.steps_data;
    if (Array.isArray(data)) return data.length;
  } catch (e) { console.error(e); }
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
    ElMessage.error(e?.response?.data?.message || e?.message || "锁定操作失败");
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
  transition: transform var(--app-duration-slow) var(--app-ease);
}

.case-card:hover {
  transform: translateY(var(--app-card-hover-lift));
}

.case-card__body {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
}

.case-card__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.case-card__header-left {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
}

.case-card__id {
  font-family: var(--app-font-mono);
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-text-secondary);
  background: var(--case-bg-dragover);
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-sm);
}

.case-card__priority {
  font-size: var(--app-size-xs);
  font-weight: 700;
  padding: 1px 6px;
  border-radius: var(--app-radius-md);
  letter-spacing: 0.02em;
}

.case-card__priority--p0 {
  background: var(--case-badge-danger-bg);
  color: var(--case-badge-danger-text);
}

.case-card__priority--p1 {
  background: var(--case-badge-warn-bg);
  color: var(--case-badge-warn-text);
}

.case-card__priority--p2 {
  background: var(--case-bg-dragover);
  color: var(--app-text-secondary);
}

.case-card__title {
  font-family: var(--app-font, 'Nunito', 'PingFang SC', sans-serif);
  font-weight: 700;
  font-size: var(--app-size-md);
  color: var(--ink);
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
  font-size: var(--app-size-xs);
  font-weight: 600;
  color: var(--app-text-secondary);
  background: var(--case-bg-code);
  padding: 2px var(--app-space-sm);
  border-radius: var(--app-radius-md);
}

.meta-tag--dir {
  color: var(--c-workflow);
  background: var(--case-bg-code-hover);
}

.meta-tag--steps {
  color: var(--app-text-secondary);
}

.meta-tag--user {
  color: var(--case-purple-text);
  background: var(--case-purple-bg);
}

/* Editing status badge */
.case-card__editing-badge {
  font-size: var(--app-size-xs);
  font-weight: 700;
  color: var(--case-badge-editing-text);
  background: var(--case-badge-editing-bg);
  padding: var(--app-space-xs) 10px;
  border-radius: var(--app-radius-md);
}

.case-card__actions {
  display: flex;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-sm);
  padding-top: 12px;
  border-top: 1px dashed var(--case-border-divider);
}
</style>
