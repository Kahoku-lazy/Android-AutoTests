<template>
  <div class="toolbox-host">
    <section class="tb-live panel">
      <div class="tb-live-head">
        <div>
          <h3 class="tb-live-title">助手此刻可用的工具</h3>
          <p class="tb-live-hint">总闸开 × 目录已启用 = 真正交给智能体 · 点芯片跳到来源</p>
        </div>
        <div class="tb-live-stats">
          <span
            v-for="src in ASSEMBLY_SOURCES"
            :key="src.key"
            class="tb-stat"
            :class="isGateOn(src.gateKey) ? 'on' : 'off'"
          >
            {{ src.name }}
            <strong>{{ sourceLiveCount(src) }}</strong>
          </span>
        </div>
      </div>
      <div class="tb-chips">
        <button
          v-for="chip in visibleChips"
          :key="chip.source + ':' + chip.name"
          type="button"
          class="tb-chip"
          :class="'tb-chip--' + chip.source"
          @click="jumpToChip(chip)"
        >
          <span class="tb-chip-dot" />
          {{ chip.name }}
        </button>
        <button
          v-if="liveChips.length > LIVE_CHIP_PREVIEW"
          type="button"
          class="tb-chip tb-chip--more"
          @click="chipsExpanded = !chipsExpanded"
        >
          {{ chipsExpanded ? '收起' : `+${liveChips.length - LIVE_CHIP_PREVIEW} 展开全部` }}
        </button>
        <span v-if="!liveChips.length" class="tb-chips-empty">
          暂无生效工具 — 打开左侧总闸并启用目录项
        </span>
      </div>
      <div v-if="unarmedSources.length" class="tb-unarmed">
        <button
          v-for="src in unarmedSources"
          :key="src.key"
          type="button"
          class="tb-unarmed-btn"
          :disabled="!props.canManage"
          @click="armSource(src)"
        >
          未装配 · {{ src.name }} · 点此打开
        </button>
      </div>
    </section>

    <div class="tb-split">
      <aside class="tb-sources panel">
        <div class="tb-sources-label">工具来源 · 交给助手</div>
        <button
          v-for="src in ASSEMBLY_SOURCES"
          :key="src.key"
          type="button"
          class="tb-source"
          :class="{ active: activeSource === src.key, dimmed: !isGateOn(src.gateKey) }"
          @click="activeSource = src.key"
        >
          <div class="tb-source-top">
            <span class="tb-source-name">{{ src.name }}</span>
            <span v-if="!isGateOn(src.gateKey)" class="tb-badge-off">未装配</span>
          </div>
          <div class="tb-source-meta">{{ sourceMeta(src) }}</div>
          <div class="tb-source-gate" @click.stop>
            <span>交给助手</span>
            <el-switch
              :model-value="isGateOn(src.gateKey)"
              :disabled="!props.canManage"
              @update:model-value="toggleFlag(src.gateKey, $event as boolean)"
            />
          </div>
        </button>
        <p v-if="!props.canManage" class="tb-readonly-hint">仅管理员可改装配</p>
      </aside>

      <section class="tb-catalog panel">
        <div class="tb-cat-head">
          <div>
            <h3 class="tb-cat-title">{{ activeSourceDef.name }}</h3>
            <p class="tb-cat-sub">
              {{ activeSourceDef.desc }} ·
              {{ isGateOn(activeSourceDef.gateKey)
                ? '开关立即影响生效清单'
                : '总闸关闭：下面的启停不会进入运行时' }}
            </p>
          </div>
          <div v-if="props.canManage" class="tb-cat-actions">
            <label v-if="activeSource === 'skill'" class="tb-btn tb-btn-primary">
              + Skill 文件夹
              <input type="file" webkitdirectory multiple hidden @change="onSkillFolderPicked" />
            </label>
          </div>
        </div>

        <div class="tb-search">
          <input
            v-model="searchQuery"
            type="search"
            class="tb-search-input"
            placeholder="搜索工具名 / 说明…"
          />
        </div>

        <div v-loading="catalogLoading" class="tb-cat-body">
          <template v-if="activeSource === 'biz'">
            <EmptyState
              v-if="!platformLoading && !filteredCategories.length"
              icon="🔌"
              text="暂无平台业务工具"
            />
            <el-collapse v-else v-model="platformExpanded" class="platform-collapse">
              <el-collapse-item
                v-for="cat in filteredCategories"
                :key="cat.key"
                :name="cat.key"
              >
                <template #title>
                  <div class="cat-head" :style="{ '--mc-color': cat.color }">
                    <span class="cat-icon">{{ cat.icon }}</span>
                    <span class="cat-name">{{ cat.key }}</span>
                    <span class="cat-count">{{ enabledCount(cat) }}/{{ cat.tools.length }} 已启用</span>
                    <span v-if="props.canManage" class="cat-actions">
                      <button
                        type="button"
                        class="pt-action-btn"
                        :disabled="allEnabled(cat) || platformToggling"
                        @click.stop="toggleCategory(cat, true)"
                      >全部启用</button>
                      <button
                        type="button"
                        class="pt-action-btn"
                        :disabled="enabledCount(cat) === 0 || platformToggling"
                        @click.stop="toggleCategory(cat, false)"
                      >全部关闭</button>
                    </span>
                  </div>
                </template>
                <div class="cat-tools" :style="{ '--mc-color': cat.color }">
                  <div
                    v-for="tool in filterTools(cat.tools)"
                    :id="toolDomId('biz', tool.name)"
                    :key="tool.name"
                    class="pt-tool"
                    :class="{ flash: highlightName === tool.name }"
                  >
                    <div class="pt-tool-head">
                      <span class="pt-tool-icon">{{ tool.icon }}</span>
                      <span class="pt-tool-name">{{ tool.name }}</span>
                      <span class="pt-tool-badge" :class="tool.read_only ? 'pt-badge-ro' : 'pt-badge-wr'">
                        {{ tool.read_only ? '只读' : '写' }}
                      </span>
                      <span class="pt-tool-state" :class="tool.enabled ? 'on' : 'off'">
                        {{ tool.enabled ? '已启用' : '已停用' }}
                      </span>
                      <el-switch
                        v-if="props.canManage"
                        class="pt-tool-sw"
                        :model-value="tool.enabled"
                        :disabled="platformToggling"
                        @update:model-value="toggleTool(tool.name, $event as boolean)"
                      />
                    </div>
                    <p class="pt-tool-summary">{{ tool.summary }}</p>
                  </div>
                </div>
              </el-collapse-item>
            </el-collapse>
          </template>

          <template v-else>
            <EmptyState
              v-if="!loading && !filteredSkillItems.length"
              icon="📁"
              text="暂无 Skill，请把文件夹放到 engines/ai/skills 或点击右上角上传"
            />
            <div v-else class="toolbox-grid">
              <div
                v-for="item in filteredSkillItems"
                :id="toolDomId('skill', item.name)"
                :key="item.id"
                class="tb-card"
                :class="{ flash: highlightName === item.name, clickable: !item.missing }"
                @click="openSkill(item)"
              >
                <div class="tb-card-header">
                  <span class="tb-card-name">{{ item.name }}</span>
                  <span class="tb-card-type" :class="item.origin === 'local' ? 'tb-type-local' : 'tb-type-skill'">
                    {{ item.origin === 'local' ? '本地' : '上传' }}
                  </span>
                  <span v-if="item.missing" class="pt-tool-state off">目录缺失</span>
                  <span v-else class="pt-tool-state" :class="item.enabled ? 'on' : 'off'">
                    {{ item.enabled ? '已启用' : '已停用' }}
                  </span>
                </div>
                <p v-if="item.description" class="tb-card-desc">{{ item.description }}</p>
                <div class="tb-card-footer" @click.stop>
                  <span class="tb-card-date">{{ item.created_at?.slice(0, 10) }}</span>
                  <el-switch
                    v-if="props.canManage && !item.missing"
                    :model-value="item.enabled"
                    @update:model-value="() => toggleItem(item)"
                  />
                  <button
                    v-if="item.origin === 'uploaded'"
                    type="button"
                    class="tb-card-btn danger"
                    @click="removeItem(item)"
                  >删除</button>
                </div>
              </div>
            </div>
          </template>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import EmptyState from '@/shared/components/patterns/EmptyState.vue'
import { useToolbox } from '../composables/useToolbox'
import { usePlatformTools } from '../composables/usePlatformTools'
import { usePlatformConfig } from '../composables/usePlatformConfig'
import { useToolboxAssembly } from '../composables/useToolboxAssembly'
import { skillViewerRoute } from '../constants'
import type { AssemblySourceDef } from '../helpers/toolbox-assembly'
import type { SharedToolItem } from '../api/toolbox'

const props = defineProps<{ canManage?: boolean }>()
const router = useRouter()

const {
  items, loading,
  removeItem, onSkillFolderPicked, toggleItem,
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
  toggleFlag,
} = usePlatformConfig()

const {
  ASSEMBLY_SOURCES, LIVE_CHIP_PREVIEW,
  activeSource, activeSourceDef, searchQuery, chipsExpanded, highlightName,
  liveChips, visibleChips, unarmedSources,
  isGateOn, sourceLiveCount, sourceMeta, toolDomId, jumpToChip, filterTools,
  filteredCategories, filteredSkillItems,
} = useToolboxAssembly({
  platformConfig,
  platformCategories,
  platformExpanded,
  sharedItems: items,
})

const catalogLoading = computed(() => {
  if (activeSource.value === 'biz') return platformLoading.value
  return loading.value
})

function armSource(src: AssemblySourceDef) {
  if (!props.canManage) return
  toggleFlag(src.gateKey, true)
  activeSource.value = src.key
}

function openSkill(item: SharedToolItem) {
  if (item.missing) return
  router.push(skillViewerRoute(item.name))
}
</script>

<style src="./ToolboxPanel.style.css" scoped></style>
