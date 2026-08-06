/**
 * useStepRunner — 步骤在设备上执行（单步/批量/从当前位置）
 * Extracted from StepEditor.vue
 */
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { runStep as apiRunStep } from "../api/uiAutomation";

export function useStepRunner(debugDevice, steps) {
  const runningStep = ref(null);
  const runningBatch = ref(false);
  const runningFromIdx = ref(null);
  const stepResults = ref({});

  async function runStep(idx, step) {
    if (!debugDevice.value) {
      ElMessage.warning("请先在顶部选择调试设备");
      return;
    }
    runningStep.value = idx;
    stepResults.value[idx] = null;
    try {
      const { data } = await apiRunStep({
        device_serial: debugDevice.value,
        type: step.type,
        xpath: step.xpath || "",
        xpath2: step.xpath2 || "",
        timeout: step.timeout || 10,
        expected_text: step.expected_text || "",
        index: step.index ?? 0,
        direction: step.direction || "",
        distance: step.distance || 500,
        description: step.description || "",
      });
      stepResults.value[idx] = data.status
        ? { ok: true, message: data.message || "执行成功" }
        : { ok: false, message: data.message || "执行失败" };
    } catch (e) {
      stepResults.value[idx] = { ok: false, message: e.response?.data?.message || e.message || "请求失败" };
    }
    runningStep.value = null;
  }

  async function runStepsRange(fromIdx) {
    runningBatch.value = true;
    runningFromIdx.value = fromIdx;
    const stepsToRun = steps.value.slice(fromIdx);
    for (let i = 0; i < stepsToRun.length; i++) {
      const realIdx = fromIdx + i;
      runningStep.value = realIdx;
      stepResults.value[realIdx] = null;
      try {
        const s = stepsToRun[i];
        const { data } = await apiRunStep({
          device_serial: debugDevice.value,
          type: s.type, xpath: s.xpath || "", xpath2: s.xpath2 || "",
          timeout: s.timeout || 10, expected_text: s.expected_text || "",
          index: s.index ?? 0, direction: s.direction || "",
          distance: s.distance || 500, description: s.description || "",
        });
        stepResults.value[realIdx] = data.status
          ? { ok: true, message: data.message || "执行成功" }
          : { ok: false, message: data.message || "执行失败" };
        if (!data.status) {
          try {
            await ElMessageBox.confirm("上一步执行失败，是否继续？", "步骤失败", {
              confirmButtonText: "继续", cancelButtonText: "停止", type: "warning",
            });
          } catch { break; }
        }
      } catch (e) {
        stepResults.value[realIdx] = { ok: false, message: e.message || "请求失败" };
        break;
      }
    }
    runningStep.value = null;
    runningBatch.value = false;
    runningFromIdx.value = null;
  }

  function runAllSteps() { stepResults.value = {}; runStepsRange(0); }
  function runFromCurrent(idx) { runStepsRange(idx); }

  return { runningStep, runningBatch, runningFromIdx, stepResults, runStep, runStepsRange, runAllSteps, runFromCurrent };
}
