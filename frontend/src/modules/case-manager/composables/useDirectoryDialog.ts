/**
 * useDirectoryDialog — 目录创建/重命名对话框状态与 API 调用
 * Extracted from DirectoryTree.vue
 */
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { formatApiError } from "@/shared/api-client";
import { createDirectory, updateDirectory } from "../api";

export function useDirectoryDialog(caseType, emit) {
  const dialogVisible = ref(false);
  const dialogMode = ref("create"); // "create" | "rename"
  const dialogName = ref("");
  const dialogParentId = ref(null);
  const dialogNodeId = ref(null);

  function openCreateRoot() {
    dialogMode.value = "create";
    dialogName.value = "";
    dialogParentId.value = null;
    dialogNodeId.value = null;
    dialogVisible.value = true;
  }

  function applyCreateSub(info) {
    if (!info) return;
    dialogMode.value = info.mode;
    dialogName.value = info.name;
    dialogParentId.value = info.parentId;
    dialogNodeId.value = info.nodeId;
    dialogVisible.value = true;
  }

  function applyRename(info) {
    if (!info) return;
    dialogMode.value = info.mode;
    dialogName.value = info.name;
    dialogParentId.value = info.parentId;
    dialogNodeId.value = info.nodeId;
    dialogVisible.value = true;
  }

  async function handleDialogConfirm() {
    if (!dialogName.value.trim()) {
      ElMessage.warning("请输入目录名称");
      return;
    }
    try {
      if (dialogMode.value === "create") {
        const { data } = await createDirectory(
          dialogName.value.trim(),
          dialogParentId.value,
          caseType.value,
        );
        if (data.status) {
          ElMessage.success("目录已创建");
        } else {
          ElMessage.error(data.message || "创建失败");
          return;
        }
      } else {
        const { data } = await updateDirectory(dialogNodeId.value, {
          name: dialogName.value.trim(),
        });
        if (data.status) {
          ElMessage.success("目录已更新");
        } else {
          ElMessage.error(data.message || "更新失败");
          return;
        }
      }
      dialogVisible.value = false;
      emit("refresh");
    } catch (e) {
      ElMessage.error(formatApiError(e, "操作失败"));
    }
  }

  return {
    dialogVisible, dialogMode, dialogName, dialogParentId, dialogNodeId,
    openCreateRoot, applyCreateSub, applyRename, handleDialogConfirm,
  };
}
