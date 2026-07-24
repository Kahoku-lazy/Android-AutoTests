<script setup>
import { ref } from 'vue'
import { IconPlus } from '@/shared/icons/index.js'
import AgentMcpDialog from './AgentMcpDialog.vue'

const props = defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
  memoryModes: { type: Array, default: () => [] },
  ltmModes: { type: Array, default: () => [] },
  availablePlatformTools: { type: Array, default: () => [] },
  loadingPlatformTools: { type: Boolean, default: false },
  selectedPlatformTools: { type: Set, default: () => new Set() },
  availableSkills: { type: Array, default: () => [] },
  loadingSkills: { type: Boolean, default: false },
  enabledSkills: { type: Set, default: () => new Set() },
  knowledgeDocs: { type: Array, default: () => [] },
  loadingDocs: { type: Boolean, default: false },
  enabledDocIds: { type: Set, default: () => new Set() },
  sopPhases: { type: Array, default: () => [] },
  phaseToolConfigEnabled: { type: Boolean, default: false },
  mcpTools: { type: Array, default: () => [] },
  skills: { type: Array, default: () => [] },
  mcpTestResults: { type: Object, default: () => ({}) },
  mcpTestingId: { type: String, default: '' },
  mcpCount: { type: Number, default: 0 },
  customSkillCount: { type: Number, default: 0 },
  wsSkillEnabledCount: { type: Number, default: 0 },
  platformToolSelectedCount: { type: Number, default: 0 },
  kbDocSelectedCount: { type: Number, default: 0 },
  skillUploading: { type: Boolean, default: false },
  mcpDialogVisible: { type: Boolean, default: false },
  mcpDialogMode: { type: String, default: 'add' },
  mcpForm: { type: Object, required: true },
  mcpJsonError: { type: String, default: '' },
  configPreview: { type: String, default: '' },
})

const emit = defineEmits([
  'toggle-platform-tool', 'toggle-skill', 'toggle-doc', 'select-all-skills', 'deselect-all-skills',
  'select-all-docs', 'deselect-all-docs', 'select-all-phase', 'deselect-all-phase',
  'open-mcp-dialog', 'save-mcp-tool', 'close-mcp-dialog', 'test-mcp', 'toggle-mcp',
  'remove-mcp-api', 'remove-mcp-local', 'trigger-skill-upload', 'skill-folder-change',
  'remove-skill', 'update:phase-tool-config-enabled', 'update:mcp-dialog-visible',
])

const memoryToolActive = ref(['memory', 'platform'])

function isPlatformToolSelected(name) { return props.selectedPlatformTools.has(name) }
function isSkillEnabled(name) { return props.enabledSkills.has(name) }
function isDocEnabled(id) { return props.enabledDocIds.has(id) }
function phaseToolEnabled(phase, toolName) {
  const cfg = props.form.phase_tool_config || {}
  const pt = cfg[phase]
  if (!pt || !pt.length) return true
  return pt.includes(toolName)
}
function togglePlatformTool(name) { emit('toggle-platform-tool', name) }
function toggleSkill(name) { emit('toggle-skill', name) }
function toggleDoc(id) { emit('toggle-doc', id) }
function togglePhaseTool(phase, name) { emit('toggle-phase-tool', { phase, name }) }
function formatSkillSize(bytes) {
  if (!bytes) return '0 B'
  return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes/1024).toFixed(1)} KB` : `${(bytes/1048576).toFixed(1)} MB`
}
</script>

<template>
  <div v-if="!isNew || step === 4" class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">4</span>
      <span>记忆与工具</span>
    </div>

    <el-collapse v-model="memoryToolActive" class="memory-tools-collapse">

      <!-- 记忆与能力 -->
      <el-collapse-item name="memory">
        <template #title>
          <div class="collapse-title-row"><span class="collapse-title-text">记忆与能力</span></div>
        </template>
        <el-form label-width="120px" class="agent-form">
          <el-form-item label="记忆模式">
            <el-select v-model="form.memory_mode" style="width:100%">
              <el-option v-for="m in memoryModes" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </el-form-item>
          <template v-if="form.memory_mode === 'longterm'">
            <el-form-item label="长期记忆模式">
              <el-select v-model="form.long_term_memory_mode" style="width:100%">
                <el-option v-for="m in ltmModes" :key="m.value" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>
          </template>
          <el-form-item label="元工具">
            <el-switch v-model="form.enable_meta_tool" />
            <span class="form-hint">允许智能体动态管理自己的工具集</span>
          </el-form-item>
          <el-form-item label="重写查询">
            <el-switch v-model="form.enable_rewrite_query" />
            <span class="form-hint">LLM 检索前重写用户查询</span>
          </el-form-item>
          <el-form-item label="知识库检索">
            <el-switch v-model="form.enable_knowledge_base" />
            <span class="form-hint">开启后对话将自动搜索项目文档（ChromaDB RAG）作为上下文</span>
          </el-form-item>
        </el-form>
      </el-collapse-item>

      <!-- 平台业务工具 -->
      <el-collapse-item name="platform">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">平台业务工具</span>
            <span class="collapse-badge">{{ platformToolSelectedCount }} 已选</span>
          </div>
        </template>
        <div v-if="loadingPlatformTools" class="empty-state">加载工具列表中...</div>
        <div v-else-if="!availablePlatformTools.length" class="empty-state">暂无可用工具</div>
        <div v-else class="platform-tools-grid">
          <div v-for="tool in availablePlatformTools" :key="tool.name" class="platform-tool-item"
               :class="{ selected: isPlatformToolSelected(tool.name) }" @click="togglePlatformTool(tool.name)">
            <el-checkbox :model-value="isPlatformToolSelected(tool.name)" />
            <div class="platform-tool-info">
              <span class="platform-tool-name">{{ tool.name }}</span>
              <span class="platform-tool-desc">{{ tool.description?.slice(0,80) }}{{ (tool.description?.length||0)>80?'...':'' }}</span>
            </div>
          </div>
        </div>

        <div class="phase-tool-toggle">
          <el-switch :model-value="phaseToolConfigEnabled"
            @update:model-value="emit('update:phase-tool-config-enabled', $event)"
            active-text="按 SOP 阶段分配工具" inactive-text="全量注入（默认）" size="small" />
          <span class="form-hint phase-tool-hint">每个 SOP 阶段只注入勾选的工具，可节省 ~78% Token</span>
        </div>
        <div v-if="phaseToolConfigEnabled" class="phase-tool-list">
          <div v-for="ph in sopPhases" :key="ph.key" class="phase-tool-card">
            <div class="phase-tool-card-head">
              <span>{{ ph.icon }}</span><span class="phase-tool-card-label">{{ ph.label }}</span>
              <el-button size="small" text type="primary" @click="emit('select-all-phase', ph.key)">全选</el-button>
              <el-button size="small" text type="primary" @click="emit('deselect-all-phase', ph.key)">全部取消</el-button>
              <span class="phase-tool-card-count">{{ (form.phase_tool_config||{})[ph.key] ? (form.phase_tool_config||{})[ph.key].length+' 个工具' : '全部工具' }}</span>
            </div>
            <div class="phase-tool-checks">
              <el-checkbox v-for="tool in availablePlatformTools" :key="ph.key+'_'+tool.name"
                :model-value="phaseToolEnabled(ph.key, tool.name)" size="small"
                @change="togglePhaseTool(ph.key, tool.name)">{{ tool.name }}</el-checkbox>
            </div>
          </div>
        </div>
      </el-collapse-item>

      <!-- 工作区 Skills -->
      <el-collapse-item name="ws_skills">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">工作区 Skills</span>
            <span class="collapse-badge">{{ wsSkillEnabledCount }} 已启用</span>
          </div>
        </template>
        <div v-if="loadingSkills" class="empty-state">加载 Skills 列表中...</div>
        <div v-else-if="!availableSkills.length" class="empty-state">暂无可用 Skills</div>
        <div v-else>
          <div class="select-all-row">
            <el-button size="small" text type="primary" @click="emit('select-all-skills')">全选</el-button>
            <el-button size="small" text type="primary" @click="emit('deselect-all-skills')">全部取消</el-button>
          </div>
          <div class="platform-tools-grid">
            <div v-for="skill in availableSkills" :key="skill.name" class="platform-tool-item"
                 :class="{ selected: isSkillEnabled(skill.name) }" @click="toggleSkill(skill.name)">
              <el-checkbox :model-value="isSkillEnabled(skill.name)" />
              <div class="platform-tool-info">
                <span class="platform-tool-name">{{ skill.name }}</span>
                <span class="platform-tool-desc">{{ skill.description?.slice(0,80) }}{{ (skill.description?.length||0)>80?'...':'' }}</span>
              </div>
            </div>
          </div>
        </div>
        <div class="form-hint collapse-footer-hint">工作区 Skills（Bash/Read/Write 等）默认全部启用。关闭的 Skill 将不会出现在工具列表中。</div>
      </el-collapse-item>

      <!-- 知识库文档范围 -->
      <el-collapse-item name="kb_docs">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">知识库文档范围</span>
            <span v-if="!form.enable_knowledge_base" class="collapse-badge collapse-badge--muted">未启用</span>
            <span v-else class="collapse-badge">{{ kbDocSelectedCount }} 已选</span>
          </div>
        </template>
        <div v-if="loadingDocs" class="empty-state">加载文档列表中...</div>
        <div v-else-if="!knowledgeDocs.length" class="empty-state">知识库暂无文档</div>
        <div v-else>
          <div class="select-all-row">
            <el-button size="small" text type="primary" @click="emit('select-all-docs')">全选</el-button>
            <el-button size="small" text type="primary" @click="emit('deselect-all-docs')">全部取消</el-button>
          </div>
          <div class="form-hint collapse-footer-hint" style="margin-bottom:8px">
            AI 调用 <code>search_knowledge_base</code> 时只检索勾选的文档。未勾选 = 不检索。全部勾选状态 = 检索全部。
          </div>
          <div class="platform-tools-grid">
            <div v-for="doc in knowledgeDocs" :key="doc.id" class="platform-tool-item"
                 :class="{ selected: isDocEnabled(doc.id) }" @click="toggleDoc(doc.id)">
              <el-checkbox :model-value="isDocEnabled(doc.id)" />
              <div class="platform-tool-info">
                <span class="platform-tool-name">{{ doc.source }}</span>
                <span class="platform-tool-desc">{{ doc.type }} · {{ (doc.size/1024).toFixed(1) }} KB</span>
              </div>
            </div>
          </div>
        </div>
      </el-collapse-item>

      <!-- MCP 服务器 -->
      <el-collapse-item name="mcp">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">MCP 服务器</span>
            <span class="collapse-badge">{{ mcpCount }}</span>
          </div>
        </template>
        <button class="add-tool-btn" @click="emit('open-mcp-dialog','add')">
          <IconPlus :size="16" /><span>添加 MCP 服务器</span>
        </button>

        <template v-if="!isNew">
          <div v-for="(t,i) in mcpTools" :key="t.id" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">{{ t.name }}</span>
              <span class="mcp-card-transport">{{ t.config?.transport||'stdio' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status" :class="mcpTestResults[t.name].connected?'connected':'failed'">
                {{ mcpTestResults[t.name].connected?'已连通':'未连通' }}</span>
              <el-switch v-model="t.enabled" size="small" @change="emit('toggle-mcp',i)" />
            </div>
            <div class="mcp-card-body"><code>{{ t.config?.command||t.config?.url||'(未配置)' }}</code></div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId===t.name" @click="emit('test-mcp',i)">测试连通</el-button>
              <el-button size="small" @click="emit('open-mcp-dialog','edit',i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="emit('remove-mcp-api',i)">删除</el-button>
            </div>
          </div>
        </template>

        <template v-if="isNew">
          <div v-for="(t,i) in form.tools" :key="i" class="mcp-card">
            <div class="mcp-card-head">
              <span class="mcp-card-name">{{ t.name||'(未命名)' }}</span>
              <span v-if="mcpTestResults[t.name]" class="mcp-card-status" :class="mcpTestResults[t.name].connected?'connected':'failed'">
                {{ mcpTestResults[t.name].connected?'已连通':'未连通' }}</span>
              <el-switch v-model="t.enabled" size="small" />
            </div>
            <div class="mcp-card-body"><code>{{ (typeof t.config_json==='string'?JSON.parse(t.config_json):t.config_json)?.command||'(未配置)' }}</code></div>
            <div class="mcp-card-actions">
              <el-button size="small" :loading="mcpTestingId===t.name" @click="emit('test-mcp',i)">测试连通</el-button>
              <el-button size="small" @click="emit('open-mcp-dialog','edit',i)">编辑</el-button>
              <el-button size="small" type="danger" plain @click="emit('remove-mcp-local',i)">删除</el-button>
            </div>
          </div>
        </template>

        <div v-if="mcpCount===0" class="empty-state">暂未添加 MCP 服务器，点击上方按钮添加</div>
      </el-collapse-item>

      <!-- 自定义 Skills -->
      <el-collapse-item name="skills">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">Skills</span>
            <span class="collapse-badge">{{ customSkillCount }}</span>
          </div>
        </template>
        <template v-if="!isNew">
          <button class="add-tool-btn add-skill-btn" @click="emit('trigger-skill-upload')" :disabled="skillUploading">
            <IconPlus :size="16" /><span>{{ skillUploading?'上传中...':'上传 Skill 文件夹' }}</span>
          </button>
          <div v-if="skillUploading" style="padding:12px 0">
            <el-progress :percentage="100" :indeterminate="true" :duration="2" />
          </div>

          <div v-for="(s,i) in skills" :key="s.id" class="skill-card">
            <div class="skill-card-head">
              <span class="skill-card-name">{{ s.name }}</span>
              <span class="skill-card-count">{{ s.config?.file_count||0 }} 个文件</span>
            </div>
            <div class="skill-card-body">
              <div class="skill-card-features">{{ s.config?.features||'无功能描述' }}</div>
              <div class="skill-card-meta">
                <span>{{ formatSkillSize(s.config?.size_bytes) }}</span><span>·</span>
                <span>{{ s.config?.uploaded_at||s.created_at }}</span>
              </div>
            </div>
            <div class="skill-card-actions">
              <el-button size="small" type="danger" plain @click="emit('remove-skill',i)">删除</el-button>
            </div>
          </div>

          <div v-if="!skills.length&&!skillUploading" class="empty-state">暂未上传 Skill，点击上方按钮选择文件夹上传</div>
        </template>
        <div v-else class="empty-state">Skills 管理在创建智能体后可用。请先保存智能体，再进入编辑模式上传 Skill。</div>
      </el-collapse-item>
    </el-collapse>

    <!-- MCP 编辑弹窗 -->
    <AgentMcpDialog
      :visible="mcpDialogVisible"
      :mode="mcpDialogMode"
      :mcp-form="mcpForm"
      :mcp-json-error="mcpJsonError"
      :config-preview="configPreview"
      @close="emit('close-mcp-dialog')"
      @save="emit('save-mcp-tool')"
    />
  </div>
</template>

<style scoped>
.add-tool-btn { display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border:2px dashed #c4b89e;border-radius:10px;background:#faf9f4;color:#8a7b66;font-size:var(--app-size-sm);font-weight:600;font-family:inherit;cursor:pointer;transition:all .2s ease;margin-bottom:14px; }
.add-tool-btn:hover { border-color:#19c8b9;background:#e6f9f6;color:#158a80; }
.tool-empty { padding:24px;text-align:center;color:#a0936e;font-size:var(--app-size-sm); }
.collapse-empty { padding:16px 0;text-align:center;color:#a0936e;font-size:var(--app-size-sm); }
.collapse-footer-hint { font-size:var(--app-size-xs);color:#a0936e;padding-top:8px; }
.select-all-row { display:flex;gap:8px;padding-bottom:8px; }
.memory-tools-collapse { --el-collapse-border-color:transparent; }
.memory-tools-collapse :deep(.el-collapse-item) { background:#fff;border:2px solid #e8e2d6;border-radius:12px;margin-bottom:8px;overflow:hidden; }
.memory-tools-collapse :deep(.el-collapse-item__header) { padding:14px 18px;font-size:var(--app-size-md);font-weight:700;color:var(--ink);background:#faf9f4;border-bottom:1px solid #f0ebe0; }
.memory-tools-collapse :deep(.el-collapse-item__content) { padding:18px; }
.collapse-title-row { display:flex;align-items:center;gap:10px;width:100%; }
.collapse-badge { font-size:var(--app-size-xs);font-weight:600;color:#19c8b9;background:#e6f9f6;padding:2px 10px;border-radius:20px; }
.collapse-badge--muted { color:#a0936e;background:#f0ede8; }
.platform-tools-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px; }
.platform-tool-item { display:flex;align-items:center;gap:10px;padding:10px 14px;border:1.5px solid #e8e2d6;border-radius:10px;cursor:pointer;transition:all .15s ease;background:#fff; }
.platform-tool-item:hover { border-color:#19c8b9;background:#e6f9f6; }
.platform-tool-item.selected { border-color:#19c8b9;background:#e6f9f6; }
.platform-tool-info { display:flex;flex-direction:column;gap:2px;min-width:0; }
.platform-tool-name { font-weight:600;font-size:var(--app-size-sm);color:var(--ink); }
.platform-tool-desc { font-size:var(--app-size-xs);color:#a0936e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.phase-tool-toggle { display:flex;align-items:center;gap:12px;padding:14px 0 8px; }
.phase-tool-list { display:flex;flex-direction:column;gap:10px; }
.phase-tool-card { border:1.5px solid #e8e2d6;border-radius:10px;padding:12px 16px;background:#faf9f4; }
.phase-tool-card-head { display:flex;align-items:center;gap:8px;margin-bottom:8px; }
.phase-tool-card-label { font-weight:600;font-size:var(--app-size-sm);color:var(--ink); }
.phase-tool-card-count { font-size:var(--app-size-xs);color:#a0936e;margin-left:auto; }
.phase-tool-checks { display:flex;flex-wrap:wrap;gap:6px; }
.mcp-card { background:#faf9f4;border:1.5px solid #e8e2d6;border-radius:12px;padding:16px;margin-bottom:12px; }
.mcp-card-head { display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px; }
.mcp-card-name { font-weight:700;font-size:var(--app-size-sm);color:var(--ink); }
.mcp-card-transport { font-size:var(--app-size-xs);color:#a0936e;background:#f0ede8;padding:2px 8px;border-radius:6px; }
.mcp-card-status { font-size:var(--app-size-xs);font-weight:600;padding:2px 8px;border-radius:6px; }
.mcp-card-status.connected { color:#2d7a2d;background:#C8F5D0; }
.mcp-card-status.failed { color:#a03030;background:#FFE0DB; }
.mcp-card-body { margin-bottom:10px; }
.mcp-card-body code { font-size:var(--app-size-sm);color:#8a7b66;background:#fff;padding:4px 10px;border-radius:6px; }
.mcp-card-actions { display:flex;gap:8px; }
.skill-card { background:#faf9f4;border:1.5px solid #e8e2d6;border-radius:12px;padding:16px;margin-bottom:12px; }
.skill-card-head { display:flex;align-items:center;gap:10px;margin-bottom:8px; }
.skill-card-name { font-weight:700;font-size:var(--app-size-sm);color:var(--ink); }
.skill-card-count { font-size:var(--app-size-xs);color:#a0936e; }
.skill-card-body { margin-bottom:10px; }
.skill-card-features { font-size:var(--app-size-sm);color:#8a7b66; }
.skill-card-meta { display:flex;gap:6px;font-size:var(--app-size-xs);color:#a0936e;margin-top:4px; }
.skill-card-actions { display:flex;gap:8px; }
.phase-tool-hint { font-size:var(--app-size-xs); }
</style>
