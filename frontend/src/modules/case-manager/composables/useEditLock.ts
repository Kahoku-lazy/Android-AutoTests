/**
 * useEditLock — 用例编辑锁管理
 * Extracted from CaseEditor.vue
 */
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { getActive } from "@/shared/auth/token-storage";
import { acquireEditLock, releaseEditLock } from "../api";

export function useEditLock() {
  const isReadOnly = ref(false);
  const editingBy = ref("");
  const caseCreatedBy = ref("");
  const hasEditLock = ref(false);

  const currentUser = getActive();

  async function acquireLock(caseId, caseData) {
    if (!currentUser) return;
    // Persistent lock (creator-locked)
    if (caseData.locked && caseData.created_by !== currentUser) {
      isReadOnly.value = true;
      editingBy.value = "创建者（已锁定用例）";
      return;
    }
    // Already holding the lock — refresh it
    if (caseData.editing_by && caseData.editing_by === currentUser) {
      hasEditLock.value = true;
      acquireEditLock(caseId).catch(() => {});
      return;
    }
    // Locked by someone else → read-only
    if (caseData.editing_by && caseData.editing_by !== currentUser) {
      isReadOnly.value = true;
      editingBy.value = caseData.editing_by;
      return;
    }
    // No lock — try to acquire
    try {
      const lockResp = await acquireEditLock(caseId);
      if (lockResp.data.status) hasEditLock.value = true;
    } catch (e) {
      if (e.response?.status === 423) {
        isReadOnly.value = true;
        editingBy.value = e.response.data?.editing_by || "";
      }
    }
  }

  async function forceEdit(caseId) {
    try {
      await releaseEditLock(caseId, true);
      const lockResp = await acquireEditLock(caseId);
      if (lockResp.data.status) {
        isReadOnly.value = false;
        editingBy.value = "";
        hasEditLock.value = true;
        ElMessage.success("已强制获取编辑权限");
      }
    } catch (e) {
      ElMessage.error(e.response?.data?.message || "强制编辑失败");
    }
  }

  function releaseLock(caseId) {
    if (hasEditLock.value && caseId) {
      releaseEditLock(caseId).catch(() => {});
    }
  }

  return { currentUser, isReadOnly, editingBy, caseCreatedBy, hasEditLock, acquireLock, forceEdit, releaseLock };
}
