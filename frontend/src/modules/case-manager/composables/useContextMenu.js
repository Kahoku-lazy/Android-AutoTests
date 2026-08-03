/**
 * useContextMenu — 目录树右键菜单状态与操作
 * Extracted from DirectoryTree.vue
 */
import { ref, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { formatApiError } from "@/shared/api-client.js";
import {
  deleteDirectory,
  deleteDefinition,
  deleteStorageDefinition,
  deleteApiDefinition,
  deleteWebDefinition,
} from "../api.js";

const DELETE_API = {
  ui_automation: deleteDefinition,
  web_automation: deleteWebDefinition,
  storage: deleteStorageDefinition,
  api_testing: deleteApiDefinition,
};

const ROUTE_CREATE = {
  ui_automation: "/cases/new",
  web_automation: "/cases/web/new",
  storage: "/cases/storage/new",
  api_testing: "/cases/api/new",
};

const ROUTE_EDIT_PREFIX = {
  ui_automation: "/cases",
  web_automation: "/cases/web",
  storage: "/cases/storage",
  api_testing: "/cases/api",
};

export function useContextMenu(caseType, emit) {
  const router = useRouter();

  const menuVisible = ref(false);
  const menuX = ref(0);
  const menuY = ref(0);
  const menuNode = ref(null);

  function handleContextMenu(event, data) {
    event.preventDefault();
    menuNode.value = data;
    menuX.value = event.clientX;
    menuY.value = event.clientY;
    menuVisible.value = true;
  }

  function closeMenu() {
    menuVisible.value = false;
    menuNode.value = null;
  }

  // ── Dialog triggers ──
  function openCreateSub() {
    return {
      mode: "create",
      name: "",
      parentId: menuNode.value ? menuNode.value.id : null,
      nodeId: null,
    };
  }

  function openRename() {
    if (!menuNode.value) return null;
    closeMenu();
    return {
      mode: "rename",
      name: menuNode.value.name,
      parentId: null,
      nodeId: menuNode.value.id,
    };
  }

  // ── Navigation ──
  function goCreateCase() {
    if (!menuNode.value) return;
    const dirId = menuNode.value.id;
    closeMenu();
    const path = ROUTE_CREATE[caseType.value] || "/cases/new";
    router.push({ path, query: { directory_id: dirId } });
  }

  function goEditCase() {
    if (!menuNode.value) return;
    const caseId = menuNode.value.case_id;
    closeMenu();
    const prefix = ROUTE_EDIT_PREFIX[caseType.value] || "/cases";
    router.push(`${prefix}/${caseId}/edit`);
  }

  // ── Delete actions ──
  async function handleDelete() {
    if (!menuNode.value) return;
    const node = menuNode.value;
    closeMenu();
    try {
      await ElMessageBox.confirm(
        `确定删除目录「${node.name}」？${node.children?.length > 0 ? "注意：该目录下存在子目录或用例，需先清空。" : ""}`,
        "确认删除",
        { confirmButtonText: "删除", cancelButtonText: "取消", type: "warning" },
      );
      const { data } = await deleteDirectory(node.id);
      if (data.ok) {
        ElMessage.success("已删除");
        emit("refresh");
      } else {
        ElMessage.error(data.error || "删除失败");
      }
    } catch (e) {
      if (e !== "cancel") ElMessage.error(formatApiError(e, "删除失败"));
    }
  }

  async function handleDeleteCase() {
    if (!menuNode.value) return;
    const node = menuNode.value;
    closeMenu();
    try {
      await ElMessageBox.confirm(`确定删除用例「${node.name}」？`, "确认删除", {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning",
      });
      const deleteFn = DELETE_API[caseType.value] || deleteDefinition;
      const { data } = await deleteFn(node.case_id);
      if (data.ok) {
        ElMessage.success("已删除");
        emit("refresh");
      } else {
        ElMessage.error(data.error || "删除失败");
      }
    } catch (e) {
      if (e !== "cancel" && e?.message !== "cancel")
        ElMessage.error(formatApiError(e, "删除失败"));
    }
  }

  // ── Outside-click listener ──
  function onDocumentClick() {
    if (menuVisible.value) closeMenu();
  }

  if (typeof window !== "undefined") {
    window.addEventListener("click", onDocumentClick);
  }
  onUnmounted(() => {
    window.removeEventListener("click", onDocumentClick);
  });

  return {
    menuVisible, menuX, menuY, menuNode,
    handleContextMenu, closeMenu,
    openCreateSub, openRename,
    goCreateCase, goEditCase,
    handleDelete, handleDeleteCase,
  };
}
