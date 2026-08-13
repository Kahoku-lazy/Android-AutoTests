/**
 * useEditLock — 用例编辑锁管理
 * Extracted from CaseEditor.vue
 */
import { ref, onUnmounted } from "vue";
import { ElMessage } from "element-plus";
import { getActive } from "@/shared/auth/token-storage";
import { acquireEditLock, releaseEditLock } from "../api";

export function useEditLock() {
  const isReadOnly = ref(false);
  const editingBy = ref("");
  const caseCreatedBy = ref("");
  const hasEditLock = ref(false);
  let heldCaseId = null;

  const currentUser = getActive();

  async function acquireLock(caseId, caseData) {
    if (!currentUser) {
      // 未登录：保守只读，避免无锁协作写
      isReadOnly.value = true;
      editingBy.value = "未登录";
      return;
    }
    // Persistent lock (creator-locked)
    if (caseData.locked && caseData.created_by !== currentUser) {
      isReadOnly.value = true;
      editingBy.value = "创建者（已锁定用例）";
      return;
    }
    // Already holding the lock — refresh it
    if (caseData.editing_by && caseData.editing_by === currentUser) {
      hasEditLock.value = true;
      heldCaseId = caseId;
      acquireEditLock(caseId).catch((e) => console.error("编辑锁刷新失败", e))
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
      if (lockResp.data.status) {
        hasEditLock.value = true;
        heldCaseId = caseId;
      }
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
        heldCaseId = caseId;
        ElMessage.success("已强制获取编辑权限");
      }
    } catch (e) {
      ElMessage.error(e.response?.data?.message || "强制编辑失败");
    }
  }

  function releaseLock(caseId) {
    const id = caseId || heldCaseId;
    if (hasEditLock.value && id) {
      releaseEditLock(id).catch(() => {});
      hasEditLock.value = false;
      heldCaseId = null;
    }
  }

  function onPageHide() {
    releaseLock(heldCaseId);
  }

  if (typeof window !== "undefined") {
    window.addEventListener("pagehide", onPageHide);
  }
  onUnmounted(() => {
    if (typeof window !== "undefined") {
      window.removeEventListener("pagehide", onPageHide);
    }
  });

  return { currentUser, isReadOnly, editingBy, caseCreatedBy, hasEditLock, acquireLock, forceEdit, releaseLock };
}
