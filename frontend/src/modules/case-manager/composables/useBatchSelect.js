/**
 * useBatchSelect — 目录树批量选择 + 批量移动
 * Used by DirectoryTree.vue
 */
import { ref, nextTick } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatApiError } from "@/shared/api-client.js";
import { batchMoveItems } from "../api.js";

export function useBatchSelect(treeData, treeRef, allCheckableIds, findNodeById, emit) {
  const selectMode = ref(false);
  const checkedIds = ref(new Set());
  const selectAll = ref(false);
  const moveDialogVisible = ref(false);
  const moveTargetDirId = ref(null);

  const checkedCount = ref(0);

  function toggleSelectMode() {
    selectMode.value = !selectMode.value;
    if (!selectMode.value) {
      checkedIds.value = new Set();
      selectAll.value = false;
      checkedCount.value = 0;
    }
  }

  function handleCheck() {
    nextTick(() => {
      if (treeRef.value) {
        const keys = treeRef.value.getCheckedKeys().map(String);
        checkedIds.value = new Set(keys);
        selectAll.value = keys.length === allCheckableIds.value.length;
        checkedCount.value = keys.length;
      }
    });
  }

  function handleSelectAll() {
    if (selectAll.value) {
      checkedIds.value = new Set();
      selectAll.value = false;
      checkedCount.value = 0;
      if (treeRef.value) treeRef.value.setCheckedKeys([]);
    } else {
      const allIds = allCheckableIds.value;
      checkedIds.value = new Set(allIds);
      selectAll.value = true;
      checkedCount.value = allIds.length;
      if (treeRef.value) treeRef.value.setCheckedKeys(allIds);
    }
  }

  function openBatchMoveDialog() {
    if (checkedIds.value.size === 0) {
      ElMessage.warning("请先选择要移动的用例或目录");
      return;
    }
    moveTargetDirId.value = null;
    moveDialogVisible.value = true;
  }

  async function confirmBatchMove() {
    if (!moveTargetDirId.value) {
      ElMessage.warning("请选择目标目录");
      return;
    }
    const items = [];
    for (const id of checkedIds.value) {
      const node = findNodeById(treeData.value, id);
      if (node) {
        items.push({
          type: node.node_type === "case" ? "case" : "directory",
          id: node.node_type === "case" ? node.case_id : node.id,
        });
      }
    }
    if (items.length === 0) return;
    try {
      await ElMessageBox.confirm(`确认将 ${items.length} 项移动到目标位置？`, "批量移动", {
        confirmButtonText: "确认移动", cancelButtonText: "取消", type: "warning",
      });
    } catch {
      return;
    }
    try {
      const { data } = await batchMoveItems(items, Number(moveTargetDirId.value));
      if (data.ok) {
        if (data.errors?.length) data.errors.forEach((e) => ElMessage.error(`${e.id}: ${e.reason}`));
        if (data.moved > 0) ElMessage.success(`已移动 ${data.moved} 项`);
        emit("refresh");
      } else {
        ElMessage.error(data.error || "批量移动失败");
      }
    } catch (e) {
      ElMessage.error(formatApiError(e, "批量移动失败"));
    } finally {
      moveDialogVisible.value = false;
      checkedIds.value = new Set();
      selectAll.value = false;
      checkedCount.value = 0;
    }
  }

  return {
    selectMode, checkedIds, selectAll, moveDialogVisible, moveTargetDirId, checkedCount,
    toggleSelectMode, handleCheck, handleSelectAll, openBatchMoveDialog, confirmBatchMove,
  };
}
