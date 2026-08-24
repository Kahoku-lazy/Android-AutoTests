<script setup>
import { ref } from 'vue'
import { useToolbox } from '../composables/useToolbox'

const props = defineProps({
  form: { type: Object, required: true },
  isNew: { type: Boolean, default: false },
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
  agentImportedTools: { type: Array, default: () => [] },
  wsSkillEnabledCount: { type: Number, default: 0 },
  platformToolSelectedCount: { type: Number, default: 0 },
  kbDocSelectedCount: { type: Number, default: 0 },
})

const emit = defineEmits([
  'toggle-platform-tool', 'toggle-category', 'toggle-skill', 'toggle-doc-enabled', 'select-all-skills', 'deselect-all-skills',
  'open-import-dialog', 'remove-doc',
  'toolbox-imported', 'remove-imported',
])

// ── AI Toolbox import ──
const { items: toolboxItems, loading: toolboxLoading, importingIds, importFromToolbox: doImportFromToolbox } = useToolbox()

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
    if (id.startsWith('dir:')) {
      return {
        id,
        dirPath: id.slice(4),
        type: 'directory',
        size: 0,
        enabled: sources[id] === true,
      }
    }
    const doc = props.knowledgeDocs.find(d => d.id === id)
    return doc ? { ...doc, enabled: sources[id] === true } : null
  }).filter(Boolean)
}
function togglePlatformTool(name) { emit('toggle-platform-tool', name) }
function toggleSkill(name) { emit('toggle-skill', name) }
function toggleDocEnabled(id) { emit('toggle-doc-enabled', id) }
function importedToolOf(item) { return props.agentImportedTools.find(t => t.name === item.name) }
async function handleImport(item) {
  const ok = await doImportFromToolbox(props.form.id, item)
  if (ok) emit('toolbox-imported')
}
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
              <span class="label-with-help">MCP 工具 <el-tooltip content="MCP Server 统一在「AI 工具箱」中配置，智能体只能从工具箱导入。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_mcp_tools" />
            <span class="form-hint">从「AI 工具箱选取」导入</span>
          </el-form-item>
          <el-form-item>
            <template #label>
              <span class="label-with-help">自定义 Skills <el-tooltip content="Skill 统一在「AI 工具箱」中上传，智能体只能从工具箱导入。" placement="top" effect="dark"><span class="help-icon">?</span></el-tooltip></span>
            </template>
            <el-switch v-model="form.enable_skills" />
            <span class="form-hint">从「AI 工具箱选取」导入</span>
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
          <p class="form-hint">
            Agent 每次对话自动恢复当前会话的完整上下文（无需配置）。跨会话长期记忆、
            元工具、查询重写等高级能力当前版本暂未开放。
          </p>
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
                 role="button" tabindex="0"
                 @click="emit('toggle-category', cat)"
                 @keydown.enter.prevent="emit('toggle-category', cat)"
                 @keydown.space.prevent="emit('toggle-category', cat)">
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
                 :class="{ selected: isSkillEnabled(skill.name) }"
                 role="button" tabindex="0"
                 @click="toggleSkill(skill.name)"
                 @keydown.enter.prevent="toggleSkill(skill.name)"
                 @keydown.space.prevent="toggleSkill(skill.name)">
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
              AI 调用 <code>search_knowledge_base</code> 时只检索已启用的文档 / 目录。
            </div>
            <div v-for="doc in importedDocs()" :key="doc.id" class="kb-doc-card">
              <div class="kb-doc-card-left">
                <span class="kb-doc-card-name">
                  {{ doc.type === 'directory' ? '📁' : '📄' }} {{ doc.type === 'directory' ? doc.dirPath : (doc.source || doc.id) }}
                </span>
                <span class="kb-doc-card-meta">
                  {{ doc.type === 'directory' ? '目录引用（动态包含其下全部文件）' : `${doc.type} · ${formatSkillSize(doc.size)}` }}
                </span>
              </div>
              <div class="kb-doc-card-right">
                <span :class="['kb-doc-toggle', { on: doc.enabled }]"
                      role="button" tabindex="0"
                      @click="toggleDocEnabled(doc.id)"
                      @keydown.enter.prevent="toggleDocEnabled(doc.id)"
                      @keydown.space.prevent="toggleDocEnabled(doc.id)"
                      :title="doc.enabled ? '已启用索引' : '已禁用索引'">
                  {{ doc.enabled ? '🔛' : '🔘' }}
                </span>
                <button class="kb-doc-remove-btn" @click="emit('remove-doc', doc.id)" title="移除引用">✕</button>
              </div>
            </div>
          </div>
        </div>
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
            <template v-if="importedToolOf(item)">
              <span class="tb-imported-badge">✓ 已导入</span>
              <button
                class="tb-remove-btn"
                @click="emit('remove-imported', importedToolOf(item).id)"
              >
                移除
              </button>
            </template>
            <button
              v-else
              class="tb-import-btn"
              :disabled="importingIds.has(item.id)"
              @click="handleImport(item)"
            >
              {{ importingIds.has(item.id) ? '导入中...' : '导入' }}
            </button>
          </div>
        </div>
      </el-collapse-item>
    </el-collapse>
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
.memory-tools-collapse :deep(.el-collapse-item) { background:var(--app-bg-card);border:2px solid var(--ai-warm-border);border-radius:12px;margin-bottom:8px;overflow:hidden; }
.memory-tools-collapse :deep(.el-collapse-item__header) { padding:14px 18px;font-size:var(--app-size-md);font-weight:700;color:var(--ink);background:var(--ai-warm-bg);border-bottom:1px solid var(--ai-bg-subtle); }
.memory-tools-collapse :deep(.el-collapse-item__content) { padding:18px; }
.collapse-title-row { display:flex;align-items:center;gap:10px;width:100%; }
.collapse-badge { font-size:var(--app-size-xs);font-weight:600;color:var(--ai-teal);background:var(--ai-teal-bg);padding:2px 10px;border-radius:6px 10px 6px 10px; }
.collapse-badge--muted { color:var(--ai-ink-muted);background:var(--app-border-lighter); }
.platform-tools-grid { display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px; }
.platform-tool-item { display:flex;align-items:center;gap:10px;padding:10px 14px;border:1.5px solid var(--ai-warm-border);border-radius:10px;cursor:pointer;transition:all .15s ease;background:var(--app-bg-card); }
.platform-tool-item:hover { border-color:var(--ai-teal);background:var(--ai-teal-bg); }
.platform-tool-item.selected { border-color:var(--ai-teal);background:var(--ai-teal-bg); }
.platform-tool-info { display:flex;flex-direction:column;gap:2px;min-width:0; }
.platform-tool-name { font-weight:600;font-size:var(--app-size-sm);color:var(--ink); }
.platform-tool-desc { font-size:var(--app-size-xs);color:var(--ai-ink-muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis; }
.mcp-card { background:var(--ai-warm-bg);border:1.5px solid var(--ai-warm-border);border-radius:12px;padding:16px;margin-bottom:12px; }
.mcp-card-head { display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin-bottom:8px; }
.mcp-card-name { font-weight:700;font-size:var(--app-size-sm);color:var(--ink); }
.mcp-card-transport { font-size:var(--app-size-xs);color:var(--ai-ink-muted);background:var(--app-border-lighter);padding:2px 8px;border-radius:6px; }
.mcp-card-status { font-size:var(--app-size-xs);font-weight:600;padding:2px 8px;border-radius:6px; }
.mcp-card-status.connected { color:var(--app-status-success-text);background:var(--app-status-success-bg); }
.mcp-card-status.failed { color:var(--app-status-danger-text);background:var(--app-status-danger-bg); }
.mcp-card-body { margin-bottom:10px; }
.mcp-card-body code { font-size:var(--app-size-sm);color:#8a7b66;background:var(--app-bg-card);padding:4px 10px;border-radius:6px; }
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
  background: var(--ai-ink-muted); color: var(--app-bg-card);
  font-size:var(--app-size-xs); font-weight: 700; cursor: help;
  opacity: 0.5; transition: opacity 0.15s;
}
.help-icon:hover { opacity: 1; background: var(--app-accent-purple, #b39ef3); }

/* ── Module cards ── */
.section-desc { font-size: var(--app-size-sm); color: var(--ai-ink-muted); margin-bottom: 12px; }
.module-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.module-card {
  display: flex; align-items: center; gap: 12px; padding: 16px;
  border: 2px solid var(--ai-warm-border); border-radius: 14px;
  background: var(--app-bg-card); cursor: pointer; transition: all 0.15s;
  position: relative; overflow: hidden;
}
.module-card::before {
  content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%;
  background: var(--mc-color, #ccc); opacity: 0; transition: opacity 0.15s;
}
.module-card:hover { border-color: var(--mc-color, var(--ai-teal)); transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.06); }
.module-card.selected { border-color: var(--mc-color, var(--ai-teal)); }
.module-card.selected::before { opacity: 0.08; }
.mc-icon { font-size:var(--app-size-2xl); flex-shrink: 0; position: relative; z-index: 1; }
.mc-body { flex: 1; min-width: 0; position: relative; z-index: 1; }
.mc-name { font-weight: 700; font-size: var(--app-size-sm); color: var(--ink); }
.mc-count { font-size: var(--app-size-xs); color: var(--ai-ink-muted); margin-top: 2px; }
.mc-check { flex-shrink: 0; position: relative; z-index: 1; }
.mc-check-on {
  display: inline-flex; align-items: center; justify-content: center;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--mc-color, var(--ai-teal)); color: var(--app-bg-card);
  font-size:var(--app-size-sm); font-weight: 700;
}

/* ── KB imported doc cards ── */
.kb-imported-list { display: flex; flex-direction: column; gap: 8px; }
.kb-doc-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px; border: 1.5px solid var(--ai-warm-border);
  border-radius: 12px; background: var(--app-bg-card); transition: border-color .15s;
}
.kb-doc-card:hover { border-color: var(--ai-teal); }
.kb-doc-card-left { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
.kb-doc-card-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); }
.kb-doc-card-meta { font-size: var(--app-size-xs); color: var(--ai-ink-muted); }
.kb-doc-card-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.kb-doc-toggle { font-size:var(--app-size-md); cursor: pointer; opacity: 0.5; transition: opacity .15s; }
.kb-doc-toggle.on { opacity: 1; }
.kb-doc-toggle:hover { opacity: 0.8; }
.kb-doc-remove-btn {
  background: none; border: none; color: var(--ai-ink-muted);
  font-size:var(--app-size-sm); cursor: pointer; padding: 2px 6px; border-radius: 4px;
  transition: all .15s;
}
.kb-doc-remove-btn:hover { color: #e74c3c; background: #fef0ef; }

/* ── 工具箱导入列表 ── */
.collapse-title-badge { font-size:var(--app-size-xs); font-weight: 600; color: var(--ai-ink-muted); background: var(--app-border-lighter); padding: 2px 10px; border-radius: 6px 10px 6px 10px; }
.toolbox-import-list { display: flex; flex-direction: column; gap: 8px; }
.toolbox-import-row {
  display: flex; align-items: center; justify-content: space-between; gap: 12px;
  padding: 12px 16px; border: 1.5px solid var(--ai-warm-border);
  border-radius: 12px; background: var(--app-bg-card); transition: border-color .15s;
}
.toolbox-import-row:hover { border-color: var(--ai-teal); }
.toolbox-import-info { display: flex; align-items: center; gap: 10px; min-width: 0; }
.toolbox-import-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.tb-card-type { font-size: var(--app-size-xs); font-weight: 700; padding: 2px 8px; border-radius: 6px; flex-shrink: 0; }
.tb-type-mcp { color: #0fa89b; background: rgba(25, 200, 185, 0.12); }
.tb-type-skill { color: #7c5cd6; background: rgba(124, 92, 214, 0.12); }
.tb-type-extension { color: #b06c1f; background: rgba(240, 173, 78, 0.15); }
.tb-import-btn {
  flex-shrink: 0; border: none; border-radius: 8px; cursor: pointer;
  padding: 6px 16px; font-size: var(--app-size-sm); font-weight: 700; font-family: inherit;
  background: var(--ai-teal); color: #fff; transition: opacity .15s;
}
.tb-import-btn:hover:not(:disabled) { opacity: 0.85; }
.tb-import-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.tb-imported-badge {
  flex-shrink: 0; font-size: var(--app-size-xs); font-weight: 700;
  color: var(--app-status-success-text, #2e7d32);
  background: var(--app-status-success-bg, rgba(76, 175, 80, 0.12));
  padding: 4px 10px; border-radius: 8px;
}
.tb-remove-btn {
  flex-shrink: 0; border: 1.5px solid #e74c3c; border-radius: 8px; cursor: pointer;
  padding: 5px 14px; font-size: var(--app-size-sm); font-weight: 700; font-family: inherit;
  background: #fef0ef; color: #e74c3c; transition: all .15s;
}
.tb-remove-btn:hover { background: #e74c3c; color: #fff; }
</style>
