/**
 * useStepFields — 步骤字段工具函数集
 * Extracted from StepEditor.vue
 */
import { STEP_FIELDS, FIELD_LABELS, APP_LIFECYCLE_TYPES } from '@/shared/constants/steps.js';

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
    const info = STEP_FIELDS[step.type] || { required: [], optional: [] };
    return [...info.required, ...(info.optional || [])];
  }

  function isFieldRequired(step, field) {
    return (STEP_FIELDS[step.type]?.required || []).includes(field);
  }

  function isContainer(type) {
    return ['if_element_appear', 'if_element_disappear', 'loop_n', 'loop_elements'].includes(type);
  }

  function fieldLabel(step, field) {
    if (field === 'xpath' && ['start_app', 'kill_app'].includes(step.type)) return '包名';
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
    return !['start_app', 'kill_app', 'swipe'].includes(step.type);
  }

  return { defaultStep, visibleFields, isFieldRequired, isContainer, fieldLabel, fieldHint, useElementPicker };
}
