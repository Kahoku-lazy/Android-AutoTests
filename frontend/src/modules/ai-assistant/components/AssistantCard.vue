<script setup lang="ts">
/**
 * 卡片两种形体，同在一个文件里（虚线白名单按文件判定，所以两张卡必须同源）：
 *
 * 1. 助手颜料片：纸底 + 2.5px 墨色虚线框 + 该助手笔色硬影 + 图钉 + 头像或笔色圆。
 * 2. 工作流便签卡（Tape Strip）：白卡 + 1.5px 浅墨虚线框 + 顶部半透明笔色胶带，
 *    左对齐放名称与「执行 → 验收」，底部一排是「配置 / 任务」两枚文字按钮
 *    外加一块纯色占位块（只占位，不带功能）。
 *
 * 视觉登记在 doodle-craft `references/components/assistant-marker-card.md`。
 */
import { computed, onMounted, ref } from "vue"
import { avatarUrl } from "../api/assistants"
import { markerVars } from "../helpers/marker"
import type { MarkerTile } from "../types"

const props = withDefaults(
  defineProps<{ item: MarkerTile; index: number; canEdit?: boolean }>(),
  { canEdit: true },
)
const emit = defineEmits<{ edit: []; activate: [] }>()

const src = ref("")

const title = computed(() =>
  props.item.kind === "assistant" ? props.item.card.display_name : props.item.card.name,
)

const detail = computed(() =>
  props.item.kind === "assistant"
    ? props.item.card.role_name || "配置已不存在"
    : `${props.item.card.executor_name} → ${props.item.card.verifier_name}`,
)

/** 便签卡正文分三行：名称、执行者、验收者；助手卡片用不到这两行。 */
const executorLine = computed(() => {
  if (props.item.kind !== "workflow") return ""
  if (props.item.card.orchestration === "team") return `队长：${props.item.card.leader_name}`
  return `执行者：${props.item.card.executor_name}`
})

const verifierLine = computed(() => {
  if (props.item.kind !== "workflow") return ""
  if (props.item.card.orchestration === "team") return `成员：${props.item.card.member_count} 名`
  return `验收者：${props.item.card.verifier_name}`
})

/** 第二枚动作：助手是进对话，工作流是开任务弹窗。 */
const secondaryLabel = computed(() => (props.item.kind === "assistant" ? "对话" : "任务"))

/** 只有助手名片有头像；工作流一律用笔色。 */
const avatar = computed(() => (props.item.kind === "assistant" ? src.value : ""))

onMounted(async () => {
  if (props.item.kind === "assistant" && props.item.card.has_avatar) {
    src.value = await avatarUrl(props.item.card.assistant_id)
  }
})
</script>

<template>
  <article
    v-if="item.kind === 'assistant'"
    class="assistant-card"
    :style="markerVars(item.card.marker)"
    :data-tilt="index % 3"
  >
    <span class="assistant-card__pin" aria-hidden="true" />
    <img v-if="avatar" class="assistant-card__avatar" :src="avatar" alt="" />
    <span v-else class="assistant-card__swatch" aria-hidden="true" />
    <h3 class="assistant-card__name" :title="title">
      {{ title }}
      <span v-if="item.kind === 'assistant' && item.card.release_state === 'draft'">草稿</span>
    </h3>
    <p class="assistant-card__role" :title="detail">{{ detail }}</p>
    <div class="assistant-card__actions">
      <button
        v-if="canEdit !== false"
        type="button"
        class="assistant-card__action assistant-card__action--config"
        @click="emit('edit')"
      >
        配置
      </button>
      <button
        type="button"
        class="assistant-card__action assistant-card__action--chat"
        @click="emit('activate')"
      >
        {{ secondaryLabel }}
      </button>
    </div>
  </article>

  <article v-else class="sop-card" :style="markerVars(item.card.marker)" :data-tilt="index % 3">
    <span class="sop-card__tape" aria-hidden="true" />
    <h3 class="sop-card__name" :title="title">
      {{ title }}
      <span v-if="item.card.release_state === 'draft'">草稿</span>
    </h3>
    <p class="sop-card__line" :title="executorLine">{{ executorLine }}</p>
    <p class="sop-card__line" :title="verifierLine">{{ verifierLine }}</p>
    <div class="sop-card__trail">
      <button
        v-if="canEdit !== false"
        type="button"
        class="sop-card__action sop-card__action--config"
        @click="emit('edit')"
      >
        配置
      </button>
      <button
        type="button"
        class="sop-card__action sop-card__action--task"
        @click="emit('activate')"
      >
        任务
      </button>
      <span class="sop-card__block" aria-hidden="true" />
    </div>
  </article>
</template>

<style scoped>
/* ── 助手颜料片 ─────────────────────────────────────── */

.assistant-card {
  /* 由行内 --assistant-marker 现算：同一份声明在不同卡片上得到各自的深浅 */
  --assistant-marker-soft: color-mix(in srgb, var(--assistant-marker) 34%, var(--paper));
  --assistant-marker-tint: color-mix(in srgb, var(--assistant-marker) 10%, var(--paper));

  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--app-space-sm);
  padding: var(--app-space-lg) var(--app-space-md) var(--app-space-md);
  background: var(--paper);
  border: 2.5px dashed var(--ink);
  border-radius: 2px;
  box-shadow: 4px 4px 0 0 var(--assistant-marker);
  transition:
    transform var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
}

/* 上边沿中心那枚笔色图钉：跨在虚线上，纸色描边把虚线断开，读作"钉在板上" */
.assistant-card__pin {
  position: absolute;
  top: -6px;
  left: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: var(--assistant-marker);
  box-shadow: 0 0 0 3px var(--paper);
  transform: translateX(-50%);
}

.assistant-card[data-tilt="0"],
.sop-card[data-tilt="0"] {
  transform: rotate(-0.8deg);
}
.assistant-card[data-tilt="1"],
.sop-card[data-tilt="1"] {
  transform: rotate(0.6deg);
}
.assistant-card[data-tilt="2"],
.sop-card[data-tilt="2"] {
  transform: rotate(-0.3deg);
}

.assistant-card:hover {
  transform: rotate(0deg) translate(-2px, -2px);
  box-shadow: 6px 6px 0 0 var(--assistant-marker);
}

.assistant-card__name {
  margin: 0;
  max-width: 100%;
  overflow: hidden;
  color: var(--ink);
  font-size: var(--app-size-md);
  font-weight: var(--app-font-weight-heavy);
  line-height: var(--app-line-height-tight);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assistant-card__avatar,
.assistant-card__swatch {
  flex: none;
  width: 88px;
  height: 88px;
  border: 2.5px solid var(--ink);
  border-radius: 50%;
}

.assistant-card__avatar {
  object-fit: cover;
}

/* 无头像：该助手笔色的深到浅；圆内不写字 */
.assistant-card__swatch {
  background: linear-gradient(
    165deg,
    var(--assistant-marker) 0%,
    var(--assistant-marker-soft) 100%
  );
}

.assistant-card__role {
  margin: 0;
  max-width: 100%;
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
  line-height: var(--app-line-height-snug);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.assistant-card__actions {
  display: flex;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-xs);
}

.assistant-card__action {
  min-height: 30px;
  padding: 0 var(--app-space-md);
  border: 1.5px dashed var(--ink);
  border-radius: 2px;
  background: transparent;
  color: var(--ink);
  font-family: inherit;
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  cursor: pointer;
  transition:
    background-color var(--app-duration-fast) var(--app-ease),
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

.assistant-card__action:hover {
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 0 var(--assistant-marker);
}

/* 动作底色：语义渐变（纵向 20% → 5%，混纸色）。
   配置 = 天蓝、对话 = 薄荷绿；hover 不再换底色（换了会冲掉渐变），只位移 + 硬影。 */
.assistant-card__action--config {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c-workflow) 20%, var(--paper)),
    color-mix(in srgb, var(--c-workflow) 5%, var(--paper))
  );
}

.assistant-card__action--chat {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c-device) 20%, var(--paper)),
    color-mix(in srgb, var(--c-device) 5%, var(--paper))
  );
}

.assistant-card__action:active {
  transform: translate(1px, 1px);
  box-shadow: none;
}

.assistant-card__action:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

/* ── 工作流便签卡（Tape Strip） ──────────────────────── */

.sop-card {
  /* 与颜料片同一套派生色：按钮 hover 的浅底与占位色块都用它 */
  --assistant-marker-soft: color-mix(in srgb, var(--assistant-marker) 34%, var(--paper));
  --assistant-marker-tint: color-mix(in srgb, var(--assistant-marker) 10%, var(--paper));

  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm);
  padding: var(--app-space-xl);
  background: var(--app-bg-card);
  border: 2px dashed color-mix(in srgb, var(--ink) 32%, transparent);
  border-radius: var(--app-radius-md);
  transition:
    transform var(--app-duration) var(--app-ease),
    border-color var(--app-duration) var(--app-ease),
    box-shadow var(--app-duration) var(--app-ease);
}

/* 胶带：顶中跨在边框上，半透明笔色自浅向下渐隐；无描边，读作胶带而不是贴纸 */
.sop-card__tape {
  position: absolute;
  top: -12px;
  left: 50%;
  width: 88px;
  height: 26px;
  border-radius: 2px;
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--assistant-marker) 42%, transparent) 0%,
    color-mix(in srgb, var(--assistant-marker) 14%, transparent) 100%
  );
  pointer-events: none;
  transform: translateX(-50%) rotate(-2deg);
}

.sop-card:hover {
  border-color: color-mix(in srgb, var(--assistant-marker) 55%, transparent);
  box-shadow: 3px 3px 0 0 color-mix(in srgb, var(--assistant-marker) 28%, transparent);
  transform: rotate(0deg) translate(-2px, -2px);
}

.sop-card__name {
  margin: 0;
  max-width: 100%;
  overflow: hidden;
  color: var(--ink);
  font-size: var(--app-size-lg);
  font-weight: var(--app-font-weight-heavy);
  line-height: var(--app-line-height-tight);
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 执行者 / 验收者各占一行 */
.sop-card__line {
  margin: 0;
  max-width: 100%;
  overflow: hidden;
  color: var(--app-text-secondary);
  font-size: var(--app-size-sm);
  line-height: var(--app-line-height-normal);
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 底部一排：两枚上色按钮，第三块与按钮同尺寸、同样式，只占位不响应 */
.sop-card__trail {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-md);
}

/* 平涂色块口径：细描边、无硬影、圆润一点；可点感由 hover 的浅影补回来 */
.sop-card__action,
.sop-card__block {
  display: inline-flex;
  flex: none;
  align-items: center;
  justify-content: center;
  min-width: 56px;
  height: 26px;
  padding: 0 var(--app-space-sm);
  border: 1px solid color-mix(in srgb, var(--ink) 22%, transparent);
  border-radius: 5px;
  color: var(--ink);
  font-family: inherit;
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  line-height: var(--app-line-height-tight);
}

.sop-card__action {
  background: var(--paper);
  cursor: pointer;
  transition:
    transform var(--app-duration-fast) var(--app-ease),
    box-shadow var(--app-duration-fast) var(--app-ease);
}

/* 配置 = 天蓝渐变、任务 = 薰衣草紫渐变（纵向 20% → 5%，与助手卡动作键同口径） */
.sop-card__action--config {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c-workflow) 20%, var(--paper)),
    color-mix(in srgb, var(--c-workflow) 5%, var(--paper))
  );
}

.sop-card__action--task {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c-element) 20%, var(--paper)),
    color-mix(in srgb, var(--c-element) 5%, var(--paper))
  );
}

.sop-card__action:hover {
  transform: translate(-1px, -1px);
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--ink) 20%, transparent);
}

.sop-card__action:active {
  transform: translate(1px, 1px);
  box-shadow: none;
}

.sop-card__action:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 2px;
}

/* 占位块：尺寸、圆角、描边槽位都与按钮一致，但没有文字、边框透明、不可点 */
.sop-card__block {
  border-color: transparent;
  background: color-mix(in srgb, var(--assistant-marker) 30%, var(--paper));
  pointer-events: none;
}

@media (prefers-reduced-motion: reduce) {
  .assistant-card,
  .assistant-card:hover,
  .assistant-card__action,
  .assistant-card__action:hover,
  .assistant-card__action:active,
  .sop-card,
  .sop-card:hover {
    transform: none;
    transition: none;
  }
}
</style>
