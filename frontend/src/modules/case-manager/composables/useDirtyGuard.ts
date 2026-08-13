/**
 * useDirtyGuard — 未保存修改的离开保护
 * Extracted from CaseEditor.vue
 */
import { ref } from "vue";
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { ElMessageBox } from "element-plus";

export function useDirtyGuard(form, isDirty) {
  const router = useRouter();
  const skipGuard = ref(false);

  // 必须在 composable 同步执行期间注册（不可放到 onMounted）
  onBeforeRouteLeave((_to, _from, next) => {
    if (!isDirty.value || skipGuard.value) return next();
    ElMessageBox.confirm(
      "当前用例有未保存的修改，离开后数据将会丢失。是否继续？",
      "未保存的修改",
      { confirmButtonText: "不保存，直接离开", cancelButtonText: "取消", type: "warning" },
    ).then(() => next()).catch(() => next(false));
  });

  function onBeforeUnload(e) {
    if (isDirty.value) { e.preventDefault(); e.returnValue = ""; }
  }

  function setup() {
    window.addEventListener("beforeunload", onBeforeUnload);
  }

  function teardown() {
    window.removeEventListener("beforeunload", onBeforeUnload);
  }

  async function exitPage(goToPath = "/cases") {
    if (isDirty.value) {
      try {
        await ElMessageBox.confirm(
          "当前用例有未保存的修改，退出后数据将会丢失。是否继续退出？",
          "未保存的修改",
          { confirmButtonText: "不保存，直接退出", cancelButtonText: "取消", type: "warning" },
        );
      } catch { return; }
    }
    skipGuard.value = true;
    router.push(goToPath);
  }

  async function goToDeviceInspector(saveFn) {
    if (isDirty.value) {
      try {
        await ElMessageBox.confirm(
          "当前用例有未保存的修改，是否保存后跳转到设备检查器？",
          "保存并跳转",
          { confirmButtonText: "保存并跳转", cancelButtonText: "取消", type: "warning" },
        );
      } catch { return; }
    }
    const ok = await saveFn();
    if (!ok) return;
    router.push("/inspector");
  }

  return { skipGuard, setup, teardown, exitPage, goToDeviceInspector };
}
