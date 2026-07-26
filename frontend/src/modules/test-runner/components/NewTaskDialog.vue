<script setup>
import { watch } from "vue";

defineProps({
  modelValue: { type: Boolean, default: false },
  newForm: { type: Object, required: true },
  devices: { type: Array, default: () => [] },
  availableCases: { type: Array, default: () => [] },
  deviceLabel: { type: Function, default: (d) => d.serial || d.model || "" },
});

const emit = defineEmits(["update:modelValue", "create"]);

function onClose() {
  emit("update:modelValue", false);
}
</script>

<template>
  <el-dialog
    :model-value="modelValue"
    title="新建测试任务"
    width="520px"
    :close-on-click-modal="false"
    @close="onClose"
  >
    <div class="new-task-form">
      <el-form label-width="88px" label-position="right">
        <el-form-item label="任务名称" required>
          <el-input
            :model-value="newForm.name"
            placeholder="如：稳定性测试"
            maxlength="30"
            clearable
            @update:model-value="newForm.name = $event"
          />
        </el-form-item>
        <el-form-item label="任务类型" required>
          <el-select :model-value="newForm.taskType" style="width: 100%" @update:model-value="newForm.taskType = $event">
            <el-option label="📱 Android UI 自动化测试" value="ui_automation" />
            <el-option label="🌍 Web 自动化测试" value="web_automation" />
            <el-option label="🌐 API 测试" value="api_testing" />
          </el-select>
        </el-form-item>
        <el-form-item v-if="newForm.taskType === 'ui_automation'" label="设备" required>
          <el-select
            :model-value="newForm.deviceSerial"
            placeholder="选择在线设备"
            style="width: 100%"
            :disabled="!devices.length"
            @update:model-value="newForm.deviceSerial = $event"
          >
            <el-option
              v-for="d in devices"
              :key="d.serial"
              :label="deviceLabel(d)"
              :value="d.serial"
            />
          </el-select>
          <p v-if="!devices.length" class="field-hint">
            暂无在线设备，请先在「设备管理」中连接
          </p>
        </el-form-item>
        <el-form-item label="用例" required>
          <el-select
            :model-value="newForm.caseIds"
            multiple
            collapse-tags
            collapse-tags-tooltip
            :placeholder="newForm.taskType === 'api_testing' ? '选择 API 用例（可多选）' : '选择 UI 用例（可多选）'"
            style="width: 100%"
            :disabled="!availableCases.length"
            @update:model-value="newForm.caseIds = $event"
          >
            <el-option
              v-for="c in availableCases"
              :key="c.id"
              :label="c.title"
              :value="c.id"
            />
          </el-select>
          <p v-if="!availableCases.length" class="field-hint">
            {{ newForm.taskType === 'api_testing' ? '暂无 API 用例，请先在「测试用例 > API 接口用例」中创建' : '暂无 UI 用例，请先在「测试用例 > UI 自动化用例」中创建' }}
          </p>
        </el-form-item>
        <el-form-item label="循环次数">
          <el-input-number
            :model-value="newForm.loopCount"
            :min="1"
            :max="10000"
            style="width: 160px"
            @update:model-value="newForm.loopCount = $event"
          />
        </el-form-item>
        <el-form-item label="轮间间隔">
          <el-input-number
            :model-value="newForm.intervalSeconds"
            :min="5"
            :max="300"
            style="width: 160px"
            @update:model-value="newForm.intervalSeconds = $event"
          />
          <span style="margin-left: 8px; font-size: var(--app-size-sm); color: #999">秒（最小 5s）</span>
        </el-form-item>
        <el-form-item label="执行方式">
          <el-radio-group :model-value="newForm.mode" @update:model-value="newForm.mode = $event">
            <el-radio value="now">立即执行</el-radio>
            <el-radio value="scheduled">定时执行</el-radio>
          </el-radio-group>
        </el-form-item>
        <template v-if="newForm.mode === 'scheduled'">
          <el-form-item label="开始时间">
            <el-date-picker
              :model-value="newForm.startAt"
              type="datetime"
              placeholder="开始时间"
              style="width: 100%"
              @update:model-value="newForm.startAt = $event"
            />
          </el-form-item>
          <el-form-item label="结束时间">
            <el-date-picker
              :model-value="newForm.endAt"
              type="datetime"
              placeholder="结束时间（可选）"
              style="width: 100%"
              @update:model-value="newForm.endAt = $event"
            />
          </el-form-item>
        </template>
      </el-form>
    </div>
    <template #footer>
      <el-button class="wb-btn" @click="onClose">取消</el-button>
      <el-button
        class="wb-btn"
        type="primary"
        :disabled="!newForm.caseIds.length || (newForm.taskType === 'ui_automation' && !newForm.deviceSerial)"
        @click="emit('create')"
      >创建并执行</el-button>
    </template>
  </el-dialog>
</template>
