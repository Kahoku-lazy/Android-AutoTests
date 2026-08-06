/**
 * useDirtyGuard — 未保存修改的离开保护
 * Extracted from CaseEditor.vue
 */
import { ref, computed } from "vue";
import { useRouter, onBeforeRouteLeave } from "vue-router";
import { ElMessageBox } from "element-plus";

export function useDirtyGuard(form, isDirty) {
  const router = useRouter();
  const skipGuard = ref(false);

  function onBeforeUnload(e) {
    if (isDirty.value) { e.preventDefault(); e.returnValue = ""; }
  }

  function setup() {
    window.addEventListener("beforeunload", onBeforeUnload);
    onBeforeRouteLeave((_to, _from, next) => {
      if (!isDirty.value || skipGuard.value) return next();
      ElMessageBox.confirm(
        "当前用例有未保存的修改，离开后数据将会丢失。是否继续？",
        "未保存的修改",
        { confirmButtonText: "不保存，直接离开", cancelButtonText: "取消", type: "warning" },
      ).then(() => next()).catch(() => next(false));
    });
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

  async function goToElementLocator(saveFn) {
    if (isDirty.value) {
      try {
        await ElMessageBox.confirm(
          "当前用例有未保存的修改，是否保存后跳转到元素定位页面？",
          "保存并跳转",
          { confirmButtonText: "保存并跳转", cancelButtonText: "取消", type: "warning" },
        );
      } catch { return; }
    }
    const ok = await saveFn();
    if (!ok) return;
    router.push("/elements");
  }

  return { skipGuard, setup, teardown, exitPage, goToElementLocator };
}
