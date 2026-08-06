<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { IconPlus } from '@/shared/icons/index'
import AgentMcpDialog from './AgentMcpDialog.vue'
import { fetchSharedTools, importFromToolbox } from '../api/toolbox'

const props = defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
  memoryModes: { type: Array, default: () => [] },
  ltmModes: { type: Array, default: () => [] },
  toolCategories: { type: Array, default: () => [] },
  isCategorySelected: { type: Function, default: () => () => false },
  loadingPlatformTools: { type: Boolean, default: false },
  selectedPlatformTools: { type: Set, default: () => new Set() },
  availableSkills: { type: Array, default: () => [] },
  loadingSkills: { type: Boolean, default: false },
  enabledSkills: { type: Set, default: () => new Set() },
  knowledgeDocs: { type: Array, default: () => [] },
  loadingDocs: { type: Boolean, default: false },
  showImportDialog: { type: Boolean, default: false },
  importedDocIds: { type: Array, default: () => [] },
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
  'toggle-platform-tool', 'toggle-category', 'toggle-skill', 'toggle-doc-enabled', 'select-all-skills', 'deselect-all-skills',
  'open-import-dialog', 'remove-doc',
  'open-mcp-dialog', 'save-mcp-tool', 'close-mcp-dialog', 'test-mcp', 'toggle-mcp',
  'remove-mcp-api', 'remove-mcp-local', 'trigger-skill-upload',
  'remove-skill', 'update:mcp-dialog-visible',
])

// ── AI Toolbox import ──
const toolboxItems = ref([])
const toolboxLoading = ref(false)
const importingIds = ref(new Set())

onMounted(async () => {
  toolboxLoading.value = true
  try {
    const data = await fetchSharedTools()
    if (data.status) toolboxItems.value = data.items || []
  } catch (e) { console.error('Failed to load toolbox:', e) }
  toolboxLoading.value = false
})

async function doImportFromToolbox(item) {
  if (!props.form.id) {
    ElMessage.warning('请先保存智能体，再导入工具箱项目')
    return
  }
  if (importingIds.value.has(item.id)) return
  importingIds.value.add(item.id)
  try {
    const data = await importFromToolbox(props.form.id, item.id)
    if (data.status) {
      ElMessage.success(`已导入: ${item.name}`)
      // Remove from available list after import
      toolboxItems.value = toolboxItems.value.filter((i) => i.id !== item.id)
    } else {
      ElMessage.warning(data.message || '导入失败')
    }
  } catch (e) { ElMessage.error('导入失败') }
  importingIds.value.delete(item.id)
}

const memoryToolActive = ref(['memory', 'platform'])

function isPlatformToolSelected(name) { return props.selectedPlatformTools.has(name) }
function isSkillEnabled(name) {
  const cfg = props.form.skills_config || {}
  return cfg[name] !== false
}
function isDocEnabled(docId) {
  const sources = props.form.knowledge_sources || {}
  return sources[docId] === true
}

function importedDocs() {
  const sources = props.form.knowledge_sources || {}
  const ids = Object.keys(sources)
  return ids.map(id => {
    const doc = props.knowledgeDocs.find(d => d.id === id)
    return doc ? { ...doc, enabled: sources[id] === true } : null
  }).filter(Boolean)
}
function togglePlatformTool(name) { emit('toggle-platform-tool', name) }
function toggleSkill(name) { emit('toggle-skill', name) }
function toggleDocEnabled(id) { emit('toggle-doc-enabled', id) }
function formatSkillSize(bytes) {
  if (!bytes) return '0 B'
  return bytes < 1024 ? `${bytes} B` : bytes < 1048576 ? `${(bytes/1024).toFixed(1)} KB` : `${(bytes/1048576).toFixed(1)} MB`
}
</script>

<template>
  <div class="doc-section step-panel">
    <div class="section-title">
      <span class="section-num">4</span>
      <span>记忆与工具</span>
    </div>

    <el-collapse v-model="memoryToolActive" class="memory-tools-collapse">

      <!-- 能力开关 -->
      <el-collapse-item name="capability">
        <template #title>
          <div class="collapse-title-row"><span class="collapse-title-text">能力开关</span><span class="collapse-badge">控制 AI 可用能力</span></div>
        </template>
        <el-form label-width="140px" class="agent-form">
          <el-form-item>
            <template #label>
              <span class="label-with-help">内置工具 <el-tooltip content="AgentScope 工作区内置工具：Bash/Edit/Glob/Grep/Read/Write。开启后可在下方「工作区 Skills」中选择具体启用项。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_workspace_tools" />
            <span class="form-hint">Bash · Edit · Glob · Grep · Read · Write</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">平台技能 <el-tooltip content="设备管理 / 元素定位 / 用例管理 / 测试执行。开启后可在下方「平台业务工具」中选择具体模块。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_business_tools" />
            <span class="form-hint">设备管理 · 元素定位 · 用例管理 · 测试执行</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">MCP 工具 <el-tooltip content="用户自配的 MCP Server 工具（如 GitHub、Slack）。开启后可在下方「MCP 工具」中配置。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_mcp_tools" />
            <span class="form-hint">{{ mcpCount > 0 ? `已配置 ${mcpCount} 个 MCP` : '暂无 MCP 工具' }}</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">自定义 Skills <el-tooltip content="用户上传的 Skill 文件夹（脚本 + 文档）。开启后可在下方「自定义 Skills」中上传和管理。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_skills" />
            <span class="form-hint">{{ customSkillCount > 0 ? `已上传 ${customSkillCount} 个 Skill` : '暂无自定义 Skill' }}</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">知识库 <el-tooltip content="ChromaDB RAG 检索。开启后 AI 回答问题时自动搜索项目文档作为上下文。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_knowledge_base" />
            <span class="form-hint">{{ kbDocSelectedCount > 0 ? `已索引 ${kbDocSelectedCount} 篇文档` : '暂无知识库文档' }}</span>
          </el-form-item>
        </el-form>
      </el-collapse-item>

      <!-- 记忆与能力 -->
      <el-collapse-item name="memory">
        <template #title>
          <div class="collapse-title-row"><span class="collapse-title-text">记忆与能力</span></div>
        </template>
        <el-form label-width="120px" class="agent-form">
          <el-form-item>
            <template #label>
              <span class="label-with-help">记忆模式 <el-tooltip content="短期记忆=只记当前会话。长期记忆=跨会话保留对话摘要。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-select v-model="form.memory_mode" style="width:100%">
              <el-option v-for="m in memoryModes" :key="m.value" :label="m.label" :value="m.value" />
            </el-select>
          </el-form-item>
          <template v-if="form.memory_mode === 'longterm'">
            <el-form-item>
              <template #label>
                <span class="label-with-help">长期记忆模式 <el-tooltip content="智能体控制=Agent 自己决定何时记忆；静态控制=固定策略；两者结合=推荐。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
              </template>
              <el-select v-model="form.long_term_memory_mode" style="width:100%">
                <el-option v-for="m in ltmModes" :key="m.value" :label="m.label" :value="m.value" />
              </el-select>
            </el-form-item>
          </template>
          <el-form-item>
            <template #label>
              <span class="label-with-help">元工具 <el-tooltip content="允许 Agent 动态管理自己的工具集。高级功能，不建议普通场景开启。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_meta_tool" />
            <span class="form-hint">允许智能体动态管理自己的工具集</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">重写查询 <el-tooltip content="开启后 LLM 在检索知识库前自动重写用户问题，提高检索精度。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_rewrite_query" />
            <span class="form-hint">LLM 检索前重写用户查询</span>
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
        <div v-else-if="!toolCategories.length" class="empty-state">暂无可用工具</div>
        <div v-else>
          <p class="section-desc">勾选模块即可激活该模块下全部工具。</p>
          <div class="module-cards">
            <div v-for="cat in toolCategories" :key="cat.key" class="module-card"
                 :class="{ selected: isCategorySelected(cat) }"
                 :style="{ '--mc-color': cat.color }"
                 @click="emit('toggle-category', cat)">
              <div class="mc-icon">{{ cat.icon }}</div>
              <div class="mc-body">
                <div class="mc-name">{{ cat.key }}</div>
                <div class="mc-count">{{ cat.tools.length }} 个工具</div>
              </div>
              <div class="mc-check">
                <span v-if="isCategorySelected(cat)" class="mc-check-on">✓</span>
              </div>
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
        <div v-else-if="!knowledgeDocs.length" class="empty-state">知识库暂无文档，请先在知识库管理页重建索引</div>
        <div v-else>
          <button class="add-tool-btn add-skill-btn" @click="emit('open-import-dialog')">
            <span>📥</span><span>导入文档</span>
          </button>
          <div v-if="!importedDocs().length" class="empty-state">
            暂未导入文档，点击上方按钮从知识库选取
          </div>
          <div v-else class="kb-imported-list">
            <div class="form-hint collapse-footer-hint" style="margin-bottom:8px">
              AI 调用 <code>search_knowledge_base</code> 时只检索已启用的文档。
            </div>
            <div v-for="doc in importedDocs()" :key="doc.id" class="kb-doc-card">
              <div class="kb-doc-card-left">
                <span class="kb-doc-card-name">📄 {{ doc.source || doc.id }}</span>
                <span class="kb-doc-card-meta">{{ doc.type }} · {{ formatSkillSize(doc.size) }}</span>
              </div>
              <div class="kb-doc-card-right">
                <span :class="['kb-doc-toggle', { on: doc.enabled }]"
                      @click="toggleDocEnabled(doc.id)"
                      :title="doc.enabled ? '已启用索引' : '已禁用索引'">
                  {{ doc.enabled ? '🔛' : '🔘' }}
                </span>
                <button class="kb-doc-remove-btn" @click="emit('remove-doc', doc.id)" title="移除文档">✕</button>
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

      <!-- 从 AI 工具箱选取 -->
      <el-collapse-item name="toolbox">
        <template #title>
          <div class="collapse-title-row">
            <span class="collapse-title-text">从 AI 工具箱选取</span>
            <span class="collapse-title-badge">{{ toolboxItems.length }}</span>
          </div>
        </template>
        <div v-if="toolboxLoading" class="empty-state">加载中...</div>
        <div v-else-if="!toolboxItems.length" class="empty-state">
          工具箱暂无共享项目，请先在
          <strong>AI 工具箱</strong> 标签页中添加
        </div>
        <div v-else class="toolbox-import-list">
          <div v-for="item in toolboxItems" :key="item.id" class="toolbox-import-row">
            <div class="toolbox-import-info">
              <span class="toolbox-import-name">{{ item.name }}</span>
              <span class="tb-card-type" :class="'tb-type-' + item.item_type">
                {{ { mcp: 'MCP', skill: 'Skill', extension: '扩展' }[item.item_type] || item.item_type }}
              </span>
            </div>
            <button
              class="tb-import-btn"
              :disabled="importingIds.has(item.id)"
              @click="doImportFromToolbox(item)"
            >
              {{ importingIds.has(item.id) ? '导入中...' : '导入' }}
            </button>
          </div>
        </div>
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
.add-tool-btn { display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border:2px dashed var(--ai-warm-border);border-radius:10px;background:var(--ai-warm-bg);color:#8a7b66;font-size:var(--app-size-sm);font-weight:600;font-family:inherit;cursor:pointer;transition:all .2s ease;margin-bottom:14px; }
.add-tool-btn:hover { border-color:var(--ai-teal);background:var(--ai-teal-bg);color:var(--ai-teal-text); }
.tool-empty { padding:24px;text-align:center;color:var(--ai-ink-muted);font-size:var(--app-size-sm); }
.collapse-empty { padding:16px 0;text-align:center;color:var(--ai-ink-muted);font-size:var(--app-size-sm); }
.collapse-footer-hint { font-size:var(--app-size-xs);color:var(--ai-ink-muted);padding-top:8px; }
.select-all-row { display:flex;gap:8px;padding-bottom:8px; }
.memory-tools-collapse { --el-collapse-border-color:transparent; }
.memory-tools-collapse :deep(.el-collapse-item) { background:#fff;border:2px solid var(--ai-warm-border);border-radius:12px;margin-bottom:8px;overflow:hidden; }
.memory-tools-collapse :deep(.el-collapse-item__header) { padding:14px 18px;font-size:var(--app-size-md);font-weight:700;color:var(--ink);background:var(--ai-warm-bg);border-bottom:1px solid var(--ai-bg-subtle); }
.memory-tools-collapse :deep(.el-collapse-item__content) { padding:18px; }
.collapse-title-row { display:flex;align-items:center;gap:10px;width:100%; }
.collapse-badge { font-size:var(--app-size-xs);font-weight:600;color:var(--ai-teal);background:var(--ai-teal-bg);padding:2px 10px;border-radius:20px; }
.collapse-badge--muted { color:var(--ai-ink-muted);background:#f0ede8; }
.platform-tools-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px; }
.platform-tool-item { display:flex;align-items:center;gap:10px;padding:10px 14px;border:1.5px solid var(--ai-warm-border);border-radius:10px;cursor:pointer;transition:all .15s ease;background:#fff; }
.platform-tool-item:hover { border-color:var(--ai-teal);background:var(--ai-teal-bg); }
.platform-tool-item.selected { border-color:var(--ai-teal);background:var(--ai-teal-bg); }
.platform-tool-info { display:flex;flex-direction:column;gap:2px;min-width:0; }
.platform-tool-name { font-weight:600;font-size:var(--app-size-sm);color:var(--ink); }
.platform-tool-desc { font-size:var(--app-size-xs);color:var(--ai-ink-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.mcp-card { background:var(--ai-warm-bg);border:1.5px solid var(--ai-warm-border);border-radius:12px;padding:16px;margin-bottom:12px; }
.mcp-card-head { display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px; }
.mcp-card-name { font-weight:700;font-size:var(--app-size-sm);color:var(--ink); }
.mcp-card-transport { font-size:var(--app-size-xs);color:var(--ai-ink-muted);background:#f0ede8;padding:2px 8px;border-radius:6px; }
.mcp-card-status { font-size:var(--app-size-xs);font-weight:600;padding:2px 8px;border-radius:6px; }
.mcp-card-status.connected { color:var(--app-status-success-text);background:var(--app-status-success-bg); }
.mcp-card-status.failed { color:var(--app-status-danger-text);background:var(--app-status-danger-bg); }
.mcp-card-body { margin-bottom:10px; }
.mcp-card-body code { font-size:var(--app-size-sm);color:#8a7b66;background:#fff;padding:4px 10px;border-radius:6px; }
.mcp-card-actions { display:flex;gap:8px; }
.skill-card { background:var(--ai-warm-bg);border:1.5px solid var(--ai-warm-border);border-radius:12px;padding:16px;margin-bottom:12px; }
.skill-card-head { display:flex;align-items:center;gap:10px;margin-bottom:8px; }
.skill-card-name { font-weight:700;font-size:var(--app-size-sm);color:var(--ink); }
.skill-card-count { font-size:var(--app-size-xs);color:var(--ai-ink-muted); }
.skill-card-body { margin-bottom:10px; }
.skill-card-features { font-size:var(--app-size-sm);color:#8a7b66; }
.skill-card-meta { display:flex;gap:6px;font-size:var(--app-size-xs);color:var(--ai-ink-muted);margin-top:4px; }
.skill-card-actions { display:flex;gap:8px; }
.label-with-help { display: inline-flex; align-items: center; gap: 4px; }
.help-icon {
  display: inline-flex; align-items: center; justify-content: center;
  width: 16px; height: 16px; border-radius: 50%;
  background: var(--ai-ink-muted); color: #fff;
  font-size: 11px; font-weight: 700; cursor: help;
  opacity: 0.5; transition: opacity 0.15s;
}
.help-icon:hover { opacity: 1; background: var(--app-accent-purple, #b39ef3); }

/* ── Module cards ── */
.section-desc { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-bottom: 12px; }
.module-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.module-card {
  display: flex; align-items: center; gap: 12px; padding: 16px;
  border: 2px solid var(--ai-warm-border); border-radius: 14px;
  background: #fff; cursor: pointer; transition: all 0.15s;
  position: relative; overflow: hidden;
}
.module-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: var(--mc-color, #ccc); opacity: 0; transition: opacity 0.15s;
}
.module-card:hover { border-color: var(--mc-color, var(--ai-teal)); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.module-card.selected { border-color: var(--mc-color, var(--ai-teal)); }
.module-card.selected::before { opacity: 0.08; }
.mc-icon { font-size: 28px; flex-shrink: 0; position: relative; z-index: 1; }
.mc-body { flex: 1; min-width: 0; position: relative; z-index: 1; }
.mc-name { font-weight: 700; font-size: var(--app-size-sm); color: var(--ink); }
.mc-count { font-size: var(--app-size-xs); color: var(--ai-ink-muted); margin-top: 2px; }
.mc-check { flex-shrink: 0; position: relative; z-index: 1; }
.mc-check-on {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--mc-color, var(--ai-teal)); color: #fff;
  font-size: 14px; font-weight: 700;
}

/* ── KB imported doc cards ── */
.kb-imported-list { display: flex; flex-direction: column; gap: 8px; }
.kb-doc-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border: 1.5px solid var(--ai-warm-border);
  border-radius: 12px; background: #fff; transition: border-color .15s;
}
.kb-doc-card:hover { border-color: var(--ai-teal); }
.kb-doc-card-left { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.kb-doc-card-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); }
.kb-doc-card-meta { font-size: var(--app-size-xs); color: var(--ai-ink-muted); }
.kb-doc-card-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.kb-doc-toggle { font-size: 18px; cursor: pointer; opacity: 0.5; transition: opacity .15s; }
.kb-doc-toggle.on { opacity: 1; }
.kb-doc-toggle:hover { opacity: 0.8; }
.kb-doc-remove-btn {
  background: none; border: none; color: var(--ai-ink-muted);
  font-size: 14px; cursor: pointer; padding: 2px 6px; border-radius: 4px;
  transition: all .15s;
}
.kb-doc-remove-btn:hover { color: #e74c3c; background: #fef0ef; }
</style>
