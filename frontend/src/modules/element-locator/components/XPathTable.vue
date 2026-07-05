<script setup>
import { ref } from 'vue'
import { Modal, Button as AnimalButton } from 'animal-island-vue'

const props = defineProps({ element: { type: Object, default: null } })
const emit = defineEmits(['add-step', 'do-action'])

const inputVisible = ref(false)
const inputText = ref('')

function centerOf(el) {
  return {
    x: el.x + Math.round(el.width / 2),
    y: el.y + Math.round(el.height / 2),
  }
}

function doClick() {
  if (!props.element) return
  const c = centerOf(props.element)
  emit('do-action', 'click', c.x, c.y)
}

function doLongClick() {
  if (!props.element) return
  const c = centerOf(props.element)
  // long-click: hold for 800ms via u2
  emit('do-action', 'longclick', c.x, c.y)
}

function openInput() {
  if (!props.element) return
  inputText.value = ''
  inputVisible.value = true
}

function doInput() {
  if (!props.element || !inputText.value.trim()) return
  const c = centerOf(props.element)
  emit('do-action', 'input', c.x, c.y, inputText.value.trim())
  inputVisible.value = false
}
</script>

<template>
  <div class="panel">
    <h3>XPath 候选</h3>

    <!-- Element detail + action buttons -->
    <div v-if="element" class="el-info">
      <div class="el-meta">
        <p><strong>Class:</strong> {{ element.class_name }}</p>
        <p v-if="element.text"><strong>Text:</strong> {{ element.text }}</p>
        <p v-if="element.resource_id"><strong>ID:</strong> {{ element.resource_id }}</p>
        <p><strong>Bounds:</strong> {{ element.bounds }}</p>
      </div>

      <!-- Action bar -->
      <div class="action-bar">
        <el-button size="small" type="primary" :disabled="!element" @click="doClick">
          👆 点击
        </el-button>
        <el-button size="small" type="warning" :disabled="!element" @click="openInput">
          ⌨ 输入
        </el-button>
        <el-button size="small" type="danger" :disabled="!element" @click="doLongClick">
          ⏱ 长按
        </el-button>
      </div>

      <!-- Input dialog -->
      <Modal v-model:open="inputVisible" title="输入文本" width="340px" :maskClosable="false" showFooter @close="inputVisible = false" @ok="doInput">
        <el-input v-model="inputText" placeholder="输入要发送的文本" maxlength="500" />
        <template #footer>
          <AnimalButton @click="inputVisible = false">取消</AnimalButton>
          <AnimalButton type="primary" @click="doInput">发送</AnimalButton>
        </template>
      </Modal>

      <!-- XPath table -->
      <el-table :data="element.xpaths || []" size="small" max-height="340" style="margin-top:10px">
        <el-table-column prop="type" label="策略" width="130" />
        <el-table-column prop="xpath" label="XPath" show-overflow-tooltip />
        <el-table-column prop="count" label="匹配" width="55" />
        <el-table-column label="" width="50">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="emit('add-step', row)">
              +
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div v-else class="empty">点击截图中元素查看 XPath</div>
  </div>
</template>

<style scoped>
.panel {
  background: var(--glass-bg); backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-radius: 20px; border: 1px solid var(--glass-border);
  padding: 16px; box-shadow: var(--shadow); overflow-y: auto;
  display: flex; flex-direction: column;
}
h3 { font-size: 14px; color: var(--text-primary); margin-bottom: 10px; flex-shrink: 0; }
.empty { color: var(--text-secondary); font-size: 13px; padding: 40px 0; text-align: center; }
.el-info { font-size: 12px; flex: 1; display: flex; flex-direction: column; min-height: 0; }
.el-meta { flex-shrink: 0; }
.el-meta p { margin-bottom: 3px; color: var(--text-secondary); }

.action-bar {
  display: flex; gap: 6px; margin: 10px 0;
  padding: 8px; background: rgba(255,255,255,0.03);
  border-radius: 8px; border: 1px solid var(--glass-border);
}
</style>
