/**
 * useStepFields — 步骤字段工具函数集
 * Extracted from StepEditor.vue
 */
import { STEP_FIELDS, FIELD_LABELS, APP_LIFECYCLE_TYPES } from '@/shared/constants/steps.js';

// ── 旧名 → 新名归一化（过渡期兼容）──
const _ALIAS = { start_app: 'adb_start_app', kill_app: 'adb_kill_app', wait_toast: 'adb_wait_toast',
  perf_element_time: 'adb_perf_element_time', poll_text: 'adb_poll_text',
  if_element_appear: 'adb_if_appear', if_element_disappear: 'adb_if_disappear',
  loop_n: 'adb_loop_n', loop_elements: 'adb_loop_elements',
  web_click: 'click', web_screenshot: 'screenshot' };
const canonical = (t) => _ALIAS[t] || t;

const CONTAINER_TYPES = ['adb_if_appear', 'adb_if_disappear', 'adb_loop_n', 'adb_loop_elements'];
const PKG_NAME_TYPES = ['adb_start_app', 'adb_kill_app'];

export function useStepFields(getPackageName) {
  function defaultStep(type = 'click') {
    const pkg = getPackageName ? getPackageName() : '';
    const xpath = APP_LIFECYCLE_TYPES.includes(type) ? pkg : '';
    return {
      type, xpath, xpath2: '', timeout: 10, expected_text: '',
      index: 0, description: '', direction: 'up', distance: 500,
    };
  }

  function visibleFields(step) {
    const info = STEP_FIELDS[canonical(step.type)] || STEP_FIELDS[step.type] || { required: [], optional: [] };
    return [...info.required, ...(info.optional || [])];
  }

  function isFieldRequired(step, field) {
    return (STEP_FIELDS[canonical(step.type)]?.required || STEP_FIELDS[step.type]?.required || []).includes(field);
  }

  function isContainer(type) {
    return CONTAINER_TYPES.includes(canonical(type));
  }

  function fieldLabel(step, field) {
    const t = canonical(step.type);
    if (field === 'xpath' && PKG_NAME_TYPES.includes(t)) return '包名';
    if (field === 'timeout' && step.type === 'long_click') return '长按秒数';
    if (field === 'timeout' && step.type === 'sleep') return '等待秒数';
    return FIELD_LABELS[field] || field;
  }

  function fieldHint(step, field) {
    if (field === 'direction') return '滑动方向';
    if (field === 'distance') return '滑动的像素距离';
    return '';
  }

  function useElementPicker(step) {
    const t = canonical(step.type);
    return !PKG_NAME_TYPES.includes(t) && t !== 'swipe';
  }

  return { defaultStep, visibleFields, isFieldRequired, isContainer, fieldLabel, fieldHint, useElementPicker };
}
