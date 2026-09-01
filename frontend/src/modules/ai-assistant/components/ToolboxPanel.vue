<template>
  <div class="toolbox-host">
    <!-- 能力开关（平台唯一智能体的工具能力总开关） -->
    <section class="tb-section">
      <div class="tb-section-head">
        <h3 class="tb-section-title">🎛️ 能力开关</h3>
        <span class="tb-section-sub">平台唯一智能体的工具能力总开关</span>
      </div>
      <div v-loading="cfgLoading" class="capability-cards">
        <div v-for="(label, key) in CAPABILITY_LABELS" :key="key" class="capability-card">
          <div class="capability-body">
            <span class="capability-name">{{ label }}</span>
            <span class="capability-hint">{{ capabilityHints[key] }}</span>
          </div>
          <el-switch
            :model-value="platformConfig[key]"
            :disabled="!props.canManage"
            @update:model-value="toggleFlag(key, $event as boolean)"
          />
        </div>
      </div>
    </section>

    <!-- 平台业务工具：展开展示每个工具并说明功能 + 全局启停 -->
    <section class="tb-section">
      <div class="tb-section-head">
        <h3 class="tb-section-title">🔌 平台业务工具</h3>
        <span class="tb-section-sub">平台内置业务工具，按模块展开并说明功能；此处全局启用/停用，智能体只保留「业务工具」总开关</span>
      </div>
      <div v-loading="platformLoading" class="platform-cats">
        <EmptyState
          v-if="!platformLoading && platformCategories.length === 0"
          icon="🔌" text="暂无平台业务工具"
        />
        <el-collapse v-model="platformExpanded" class="platform-collapse">
          <el-collapse-item
            v-for="cat in platformCategories" :key="cat.key" :name="cat.key"
          >
            <template #title>
              <div class="cat-head" :style="{ '--mc-color': cat.color }">
                <span class="cat-icon">{{ cat.icon }}</span>
                <span class="cat-name">{{ cat.key }}</span>
                <span class="cat-count">{{ enabledCount(cat) }}/{{ cat.tools.length }} 已启用</span>
                <span v-if="props.canManage" class="cat-actions">
                  <button
                    class="pt-action-btn"
                    :disabled="allEnabled(cat) || platformToggling"
                    @click.stop="toggleCategory(cat, true)"
                  >全部启用</button>
                  <button
                    class="pt-action-btn"
                    :disabled="enabledCount(cat) === 0 || platformToggling"
                    @click.stop="toggleCategory(cat, false)"
                  >全部关闭</button>
                </span>
              </div>
            </template>
            <div class="cat-tools" :style="{ '--mc-color': cat.color }">
              <div v-for="tool in cat.tools" :key="tool.name" class="pt-tool">
                <div class="pt-tool-head">
                  <span class="pt-tool-icon">{{ tool.icon }}</span>
                  <span class="pt-tool-name">{{ tool.name }}</span>
                  <span class="pt-tool-badge" :class="tool.read_only ? 'pt-badge-ro' : 'pt-badge-wr'">
                    {{ tool.read_only ? '只读' : '写' }}
                  </span>
                  <span class="pt-tool-state" :class="tool.enabled ? 'on' : 'off'">
                    {{ tool.enabled ? '已启用' : '已停用' }}
                  </span>
                  <span v-if="props.canManage" class="pt-tool-actions">
                    <button
                      class="pt-action-btn"
                      :disabled="tool.enabled || platformToggling"
                      @click="toggleTool(tool.name, true)"
                    >启用</button>
                    <button
                      class="pt-action-btn"
                      :disabled="!tool.enabled || platformToggling"
                      @click="toggleTool(tool.name, false)"
                    >停用</button>
                  </span>
                </div>
                <p class="pt-tool-summary">{{ tool.summary }}</p>
              </div>
            </div>
          </el-collapse-item>
        </el-collapse>
      </div>
    </section>

    <!-- 工作区 Skills（内置工具，随「内置工具」开关启用） -->
    <section class="tb-section">
      <div class="tb-section-head">
        <h3 class="tb-section-title">🛠️ 工作区 Skills</h3>
        <span class="tb-section-sub">{{ skillEnabledCount() }}/{{ workspaceSkills.length }} 已启用（Bash · Edit · Glob · Grep · Read · Write）</span>
      </div>
      <div v-loading="cfgLoading" class="ws-skills-list">
        <EmptyState v-if="!cfgLoading && !workspaceSkills.length" icon="🛠️" text="暂无工作区 Skills" />
        <div v-for="skill in workspaceSkills" :key="skill.name" class="ws-skill-item">
          <el-switch
            :model-value="isSkillEnabled(skill.name)"
            :disabled="!props.canManage"
            @update:model-value="toggleSkill(skill.name)"
          />
          <div class="ws-skill-info">
            <span class="ws-skill-name">{{ skill.name }}</span>
            <span v-if="skill.description" class="ws-skill-desc">{{ skill.description }}</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 共享工具（Skill / MCP / 扩展） -->
    <section class="tb-section">
      <div class="toolbox-header">
        <h3 class="toolbox-title">🧰 共享工具</h3>
        <span class="toolbox-subtitle">Skill、MCP 工具与扩展 — 多智能体可复用</span>
      <div class="toolbox-actions">
        <button class="tb-btn tb-btn-primary" @click="openMcpDialog()">+ MCP 工具</button>
        <label class="tb-btn tb-btn-outline">
          + Skill 文件夹
          <input
            type="file"
            webkitdirectory
            multiple
            hidden
            @change="onSkillFolderPicked"
          />
        </label>
      </div>
    </div>

    <div class="toolbox-filters">
      <button
        v-for="f in filters"
        :key="f.key"
        class="tb-filter-btn"
        :class="{ active: activeFilter === f.key }"
        @click="activeFilter = f.key"
      >
        {{ f.label }}
      </button>
    </div>

    <div v-loading="loading" class="toolbox-grid">
      <EmptyState v-if="!loading && filteredItems.length === 0" icon="🧰" text="暂无共享工具，点击上方按钮添加" />
      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="tb-card"
      >
        <div class="tb-card-header">
          <span class="tb-card-name">{{ item.name }}</span>
          <span class="tb-card-type" :class="'tb-type-' + item.item_type">
            {{ typeLabel(item.item_type) }}
          </span>
          <span class="pt-tool-state" :class="item.enabled ? 'on' : 'off'">
            {{ item.enabled ? '已启用' : '已停用' }}
          </span>
        </div>
        <div class="tb-card-body">
          <p v-if="item.description" class="tb-card-desc">{{ item.description }}</p>
          <pre v-if="item.config_json && item.config_json !== '{}'" class="tb-card-config">{{
            formatConfig(item.config_json)
          }}</pre>
        </div>
        <div class="tb-card-footer">
          <span class="tb-card-date">{{ item.created_at?.slice(0, 10) }}</span>
          <button v-if="props.canManage" class="tb-card-btn" @click="toggleItem(item)">
            {{ item.enabled ? '停用' : '启用' }}
          </button>
          <button class="tb-card-btn" @click="editItem(item)">编辑</button>
          <button class="tb-card-btn danger" @click="removeItem(item)">删除</button>
        </div>
      </div>
    </div>
    </section>

    <!-- MCP / Extension edit dialog (reuses AgentMcpDialog pattern) -->
    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑' : '添加 MCP 工具 / 扩展'"
      width="520px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="例如: GitHub MCP Server" />
        </el-form-item>
        <el-form-item label="类型">
          <el-select v-model="form.item_type" style="width:100%">
            <el-option label="MCP 工具" value="mcp" />
            <el-option label="扩展" value="extension" />
          </el-select>
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="此工具的用途说明" />
        </el-form-item>
        <el-form-item label="配置 JSON">
          <el-input
            v-model="form.config_json"
            type="textarea"
            :rows="6"
            placeholder='{"transport":"stdio","command":"npx","args":["-y","@modelcontextprotocol/server-..."]}'
            class="tb-json-input"
          />
          <span class="tb-json-hint">
            stdio：transport=stdio + command/args/env；HTTP：transport=http/sse + url/headers/timeout
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveItem">
          {{ editingId ? '保存' : '创建' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { useToolbox } from '../composables/useToolbox'
import { usePlatformTools } from '../composables/usePlatformTools'
import { usePlatformConfig } from '../composables/usePlatformConfig'

const props = defineProps<{ canManage?: boolean }>()

const {
  activeFilter, filters, loading, filteredItems, typeLabel, formatConfig,
  dialogVisible, editingId, saving, form,
  openMcpDialog, editItem, saveItem, removeItem, onSkillFolderPicked, toggleItem,
} = useToolbox()

const {
  categories: platformCategories,
  loading: platformLoading,
  toggling: platformToggling,
  expanded: platformExpanded,
  enabledCount, allEnabled, toggleTool, toggleCategory,
} = usePlatformTools()

const {
  config: platformConfig,
  workspaceSkills,
  loading: cfgLoading,
  CAPABILITY_LABELS, toggleFlag, isSkillEnabled, toggleSkill, skillEnabledCount,
} = usePlatformConfig()

const capabilityHints: Record<string, string> = {
  enable_business_tools: '启用「平台业务工具」中已启用的工具',
  enable_workspace_tools: '启用「工作区 Skills」中已启用的技能',
  enable_mcp_tools: '启用「共享工具」中已启用的 MCP 工具',
  enable_skills: '启用「共享工具」中已启用的 Skill 文件夹',
}
</script>

<style scoped>
.toolbox-host {
  padding: 16px 20px 32px;
  height: 100%;
  overflow-y: auto;
}
.toolbox-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}
.toolbox-title { font-size:var(--app-size-md); font-weight: 700; color: var(--app-text-primary, #2c2c2c); margin: 0; }
.toolbox-subtitle { font-size:var(--app-size-sm); color: var(--app-text-secondary, #888); flex: 1; }
.toolbox-actions { display: flex; gap: 8px; }
.tb-btn {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 8px 16px; border-radius: 8px; font-size:var(--app-size-sm); font-weight: 600;
  border: none; cursor: pointer; font-family: inherit; transition: all 0.15s;
}
.tb-btn-primary { background: #6c5ce7; color: var(--app-bg-card); }
.tb-btn-primary:hover { background: #5a4bd1; }
.tb-btn-outline { background: var(--app-bg-card); color: #6c5ce7; border: 1.5px solid #6c5ce7; }
.tb-btn-outline:hover { background: #f5f3ff; }
.toolbox-filters { display: flex; gap: 6px; margin-bottom: 16px; }
.tb-filter-btn {
  padding: 6px 14px; border-radius: 8px; border: 1px solid var(--app-border, #e0e0e0);
  background: var(--app-bg-card); font-size:var(--app-size-sm); font-weight: 600; cursor: pointer;
  font-family: inherit; color: var(--app-text-secondary, #666); transition: all 0.15s;
}
.tb-filter-btn.active { background: #6c5ce7; color: var(--app-bg-card); border-color: #6c5ce7; }
.toolbox-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 12px; }
.tb-card {
  background: var(--app-bg-card); border-radius: 12px; border: 1px solid var(--app-border, #e8e8e8);
  padding: 14px 16px; display: flex; flex-direction: column; gap: 8px;
  transition: box-shadow 0.15s;
}
.tb-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.tb-card-header { display: flex; align-items: center; gap: 8px; }
.tb-card-name { font-weight: 700; font-size:var(--app-size-sm); color: var(--app-text-primary, #2c2c2c); flex:1; }
.tb-card-type { font-size:var(--app-size-xs); font-weight: 700; padding: 2px 8px; border-radius: 6px; }
.tb-type-mcp { background: #e8f5e9; color: #2e7d32; }
.tb-type-skill { background: #e3f2fd; color: #1565c0; }
.tb-type-extension { background: #fff3e0; color: #e65100; }
.tb-card-body { flex: 1; }
.tb-card-desc { font-size:var(--app-size-sm); color: var(--app-text-secondary, #666); margin: 0; }
.tb-card-config { font-size:var(--app-size-xs); color: #888; background: #f8f8f8; padding: 6px 8px;
  border-radius: 6px; margin: 4px 0 0; overflow-x: auto; white-space: pre-wrap; }
.tb-card-footer { display: flex; align-items: center; gap: 8px; }
.tb-card-date { font-size:var(--app-size-xs); color: #aaa; flex: 1; }
.tb-card-btn {
  font-size:var(--app-size-xs); font-weight: 600; padding: 4px 10px; border-radius: 6px;
  border: 1px solid var(--app-border, #ddd); background: var(--app-bg-card); cursor: pointer;
  font-family: inherit; color: var(--app-text-secondary, #555);
}
.tb-card-btn:hover { background: #f5f5f5; }
.tb-card-btn.danger { color: #c43f3f; border-color: #f5d5d5; }
.tb-card-btn.danger:hover { background: #fef0f0; }
.tb-json-input :deep(textarea) { font-family: monospace; font-size:var(--app-size-xs); }
.tb-json-hint { font-size: var(--app-size-xs); color: var(--app-text-secondary); line-height: 1.5; }

/* ── 平台业务工具展开展示区 ── */
.tb-section { margin-bottom: var(--app-space-lg); }
.tb-section-head {
  display: flex; align-items: baseline; flex-wrap: wrap;
  gap: var(--app-space-sm); margin-bottom: var(--app-space-md);
}
.tb-section-title { font-size: var(--app-size-md); font-weight: 700; color: var(--app-text); margin: 0; }
.tb-section-sub { font-size: var(--app-size-xs); color: var(--app-text-secondary); }

.platform-collapse { --el-collapse-border-color: transparent; }
.platform-collapse :deep(.el-collapse-item) {
  background: var(--app-bg-card);
  border: 2px solid var(--ai-warm-border);
  border-radius: var(--app-radius-lg);
  margin-bottom: var(--app-space-sm);
  overflow: hidden;
}
.platform-collapse :deep(.el-collapse-item__header) {
  padding: 0 var(--app-space-md);
  font-size: var(--app-size-md);
  font-weight: 700;
  color: var(--ink);
  background: var(--ai-warm-bg);
  border-bottom: 1px solid var(--ai-bg-subtle);
}
.platform-collapse :deep(.el-collapse-item__content) { padding: var(--app-space-md); }

.cat-head { display: flex; align-items: center; gap: var(--app-space-sm); width: 100%; }
.cat-icon { font-size: var(--app-size-md); }
.cat-name { font-weight: 700; font-size: var(--app-size-sm); color: var(--ink); }
.cat-count {
  flex-shrink: 0;
  align-self: center;
  font-size: var(--app-size-xs);
  font-weight: 600;
  line-height: 1.2;
  height: auto;
  color: var(--mc-color, var(--ai-teal-text));
  border: 1px solid var(--mc-color, var(--ai-teal));
  padding: 0 var(--app-space-xs);
  border-radius: var(--app-radius-sm);
}

.cat-tools { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.pt-tool {
  background: var(--app-bg-card);
  border: 1.5px solid var(--ai-warm-border);
  border-radius: var(--app-radius-md);
  padding: var(--app-space-sm) var(--app-space-md);
  transition: border-color var(--app-duration);
}
.pt-tool:hover { border-color: var(--mc-color, var(--ai-teal)); }
.pt-tool-head { display: flex; align-items: center; gap: var(--app-space-sm); }
.pt-tool-icon { font-size: var(--app-size-md); }
.pt-tool-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); font-family: var(--app-font-mono); }
.pt-tool-badge {
  flex-shrink: 0; font-size: var(--app-size-xs); font-weight: 700;
  padding: 0 var(--app-space-sm); border-radius: var(--app-radius-sm);
}
.pt-badge-ro { color: var(--app-status-success-text); background: var(--app-status-success-bg); }
.pt-badge-wr { color: var(--app-status-danger-text); background: var(--app-status-danger-bg); }
.pt-tool-summary {
  margin: var(--app-space-xs) 0 0;
  font-size: var(--app-size-xs);
  color: var(--app-text-secondary);
  line-height: 1.5;
}
.cat-actions { margin-left: auto; display: inline-flex; gap: var(--app-space-xs); flex-shrink: 0; }
.pt-tool-actions { margin-left: auto; display: inline-flex; gap: var(--app-space-xs); flex-shrink: 0; }
.pt-tool-state {
  font-size: var(--app-size-xs); font-weight: 700;
  padding: 0 var(--app-space-sm); border-radius: var(--app-radius-sm); flex-shrink: 0;
}
.pt-tool-state.on { color: var(--app-status-success-text); background: var(--app-status-success-bg); }
.pt-tool-state.off { color: var(--app-text-muted); background: var(--ai-bg-neutral); }
.pt-action-btn {
  font-size: var(--app-size-xs); font-weight: 700; padding: 0 var(--app-space-sm);
  border-radius: var(--app-radius-sm); border: 1.5px solid var(--ai-warm-border);
  background: var(--app-bg-card); color: var(--app-text-secondary);
  cursor: pointer; font-family: inherit; transition: all var(--app-duration);
}
.pt-action-btn:hover:not(:disabled) { border-color: var(--mc-color, var(--ai-teal)); color: var(--mc-color, var(--ai-teal-text)); }
.pt-action-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* ── 能力开关 ── */
.capability-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: var(--app-space-sm); }
.capability-card {
  display: flex; align-items: center; gap: var(--app-space-md);
  padding: var(--app-space-md);
  border: 1.5px solid var(--ai-warm-border); border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
}
.capability-body { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.capability-name { font-weight: 700; font-size: var(--app-size-sm); color: var(--ink); }
.capability-hint { font-size: var(--app-size-xs); color: var(--app-text-secondary); }

/* ── 工作区 Skills ── */
.ws-skills-list { display: flex; flex-direction: column; gap: var(--app-space-sm); }
.ws-skill-item {
  display: flex; align-items: center; gap: var(--app-space-md);
  padding: var(--app-space-sm) var(--app-space-md);
  border: 1.5px solid var(--ai-warm-border); border-radius: var(--app-radius-md);
  background: var(--app-bg-card);
}
.ws-skill-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.ws-skill-name { font-weight: 600; font-size: var(--app-size-sm); color: var(--ink); font-family: var(--app-font-mono); }
.ws-skill-desc { font-size: var(--app-size-xs); color: var(--app-text-secondary); }
</style>
