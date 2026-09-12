<script setup lang="ts">
/** NetworkConnectDialog — 局域网连接：已配对/已在 adb devices 可直连；首次选填配对 */
import { computed, ref, watch } from 'vue'
import { validateLanConnect, type LanConnectPayload } from '../helpers'

const props = withDefaults(defineProps<{
  visible?: boolean
  loading?: boolean
}>(), {
  visible: false,
  loading: false,
})

const emit = defineEmits<{
  confirm: [payload: LanConnectPayload]
  cancel: []
}>()

const ip = ref('')
const connectPort = ref('')
const pairPort = ref('')
const pairCode = ref('')
const ipError = ref('')
const connectPortError = ref('')
const pairPortError = ref('')
const pairCodeError = ref('')

const ipWrap = ref<HTMLElement | null>(null)
const connectPortWrap = ref<HTMLElement | null>(null)
const pairPortWrap = ref<HTMLElement | null>(null)
const pairCodeWrap = ref<HTMLElement | null>(null)

const willPair = computed(() => Boolean(pairPort.value.trim() || pairCode.value.trim()))

watch(
  () => props.visible,
  (v) => {
    if (v) {
      ip.value = ''
      connectPort.value = ''
      pairPort.value = ''
      pairCode.value = ''
      ipError.value = ''
      connectPortError.value = ''
      pairPortError.value = ''
      pairCodeError.value = ''
    }
  },
)

function applyErrors(errors: {
  ip: string
  connectPort: string
  pairPort: string
  pairCode: string
}) {
  ipError.value = errors.ip
  connectPortError.value = errors.connectPort
  pairPortError.value = errors.pairPort
  pairCodeError.value = errors.pairCode
}

function focusField(wrap: HTMLElement | null) {
  wrap?.querySelector?.('input')?.focus?.()
}

function handleConfirm() {
  if (props.loading) return
  const result = validateLanConnect({
    ip: ip.value,
    connectPort: connectPort.value,
    pairPort: pairPort.value,
    pairCode: pairCode.value,
  })
  applyErrors(result.errors)
  if (!result.ok) {
    const map = {
      ip: ipWrap.value,
      connectPort: connectPortWrap.value,
      pairPort: pairPortWrap.value,
      pairCode: pairCodeWrap.value,
    }
    if (result.firstError) focusField(map[result.firstError])
    return
  }
  if (result.payload) emit('confirm', result.payload)
}

function handleCancel() {
  if (props.loading) return
  emit('cancel')
}
</script>

<template>
  <el-dialog
    :model-value="visible"
    title="局域网连接设备"
    width="520px"
    :close-on-click-modal="false"
    @close="handleCancel"
  >
    <div class="net-form">
      <p class="net-hint">
        手机打开「开发者选项 → 无线调试」，并与电脑同一局域网。
        若本机 <code>adb devices</code> 已出现 <code>IP:端口</code>
        或 <code>adb-序列号-…._adb-tls-connect._tcp</code>，说明已配对/已发现，只需填连接端口。
      </p>

      <div class="net-form-item">
        <label class="net-label">IP 地址 *</label>
        <div ref="ipWrap" class="net-field" :class="{ 'has-error': ipError }">
          <el-input v-model="ip" placeholder="如 10.162.95.96" :maxlength="15" @keyup.enter="handleConfirm" />
        </div>
        <p v-if="ipError" class="net-error">{{ ipError }}</p>
      </div>

      <div class="net-form-item">
        <label class="net-label">连接端口 *</label>
        <div ref="connectPortWrap" class="net-field" :class="{ 'has-error': connectPortError }">
          <el-input
            v-model="connectPort"
            placeholder="无线调试主页上的端口，如 43523"
            :maxlength="5"
            @keyup.enter="handleConfirm"
          />
        </div>
        <p v-if="connectPortError" class="net-error">{{ connectPortError }}</p>
      </div>

      <p class="net-hint">
        首次连接才需要配对（配对端口 ≠ 连接端口）。已配对可留空下面两项。
      </p>

      <div class="net-form-item">
        <label class="net-label">配对端口（可选）</label>
        <div ref="pairPortWrap" class="net-field" :class="{ 'has-error': pairPortError }">
          <el-input
            v-model="pairPort"
            placeholder="配对弹窗上的端口，如 41395"
            :maxlength="5"
            @keyup.enter="handleConfirm"
          />
        </div>
        <p v-if="pairPortError" class="net-error">{{ pairPortError }}</p>
      </div>

      <div class="net-form-item">
        <label class="net-label">配对码（可选）</label>
        <div ref="pairCodeWrap" class="net-field" :class="{ 'has-error': pairCodeError }">
          <el-input
            v-model="pairCode"
            placeholder="如 387429"
            :maxlength="16"
            @keyup.enter="handleConfirm"
          />
        </div>
        <p v-if="pairCodeError" class="net-error">{{ pairCodeError }}</p>
      </div>
    </div>

    <template #footer>
      <el-button :disabled="loading" @click="handleCancel">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleConfirm">
        {{ willPair ? '配对并连接' : '连接' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<style scoped>
.net-form {
  display: flex;
  flex-direction: column;
  gap: var(--app-space-md);
  padding: var(--app-space-sm) 0;
}

.net-form-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.net-label {
  font-size: var(--app-size-sm);
  font-weight: 700;
  color: var(--ink);
}

.net-field.has-error :deep(input) {
  border-color: var(--app-status-danger);
}

.net-error {
  font-size: var(--app-size-sm);
  color: var(--app-status-danger-text);
  margin: 0;
  line-height: 1.4;
}

.net-hint {
  font-size: var(--app-size-sm);
  color: var(--app-ink-muted);
  margin: 0;
  line-height: 1.5;
}

.net-hint code {
  font-size: var(--app-size-xs);
  padding: 0 var(--app-space-xs);
  border-radius: 3px;
  background: var(--ai-bg-neutral, rgba(0, 0, 0, 0.04));
}
</style>
