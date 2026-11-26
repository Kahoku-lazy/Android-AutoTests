<script setup lang="ts">
import { computed, onMounted, ref } from "vue"
import { avatarUrl } from "../api/assistants"
import { markerVars } from "../helpers/marker"
import type { MarkerTile } from "../types"

const props = withDefaults(
  defineProps<{
    item: MarkerTile
    index: number
    canEdit?: boolean
    canPublish?: boolean
    error?: string
  }>(),
  {
    canEdit: true,
    canPublish: false,
    error: "",
  },
)
const emit = defineEmits<{ edit: []; activate: []; publish: [] }>()

const src = ref("")

const title = computed(() =>
  props.item.kind === "assistant" ? props.item.card.display_name : props.item.card.name,
)

const detail = computed(() =>
  props.item.kind === "assistant"
    ? props.item.card.role_name || "配置已不存在"
    : `${props.item.card.executor_name} → ${props.item.card.verifier_name}`,
)

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

const secondaryLabel = computed(() => (props.item.kind === "assistant" ? "对话" : "任务"))

const avatar = computed(() => (props.item.kind === "assistant" ? src.value : ""))

const isDraft = computed(() => props.item.card.release_state === "draft")

const showPublish = computed(() => isDraft.value && props.canPublish)

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
    <span v-if="isDraft" class="assistant-card__chip">草稿</span>
    <img v-if="avatar" class="assistant-card__avatar" :src="avatar" alt="" />
    <span v-else class="assistant-card__swatch" aria-hidden="true" />
    <h3 class="assistant-card__name" :title="title">{{ title }}</h3>
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
      <button
        v-if="showPublish"
        type="button"
        class="assistant-card__action assistant-card__action--publish"
        @click="emit('publish')"
      >
        发布
      </button>
    </div>
    <p v-if="error" class="assistant-card__error">{{ error }}</p>
  </article>

  <article v-else class="sop-card" :style="markerVars(item.card.marker)" :data-tilt="index % 3">
    <span class="sop-card__tape" aria-hidden="true" />
    <span v-if="isDraft" class="sop-card__chip">草稿</span>
    <h3 class="sop-card__name" :title="title">{{ title }}</h3>
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
      <button
        v-if="showPublish"
        type="button"
        class="sop-card__action sop-card__action--publish"
        @click="emit('publish')"
      >
        发布
      </button>
      <span v-else class="sop-card__block" aria-hidden="true" />
    </div>
    <p v-if="error" class="sop-card__error">{{ error }}</p>
  </article>
</template>

<style scoped>
.assistant-card {
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
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-xs);
}

.assistant-card__action {
  min-height: 30px;
  padding: 0 var(--app-space-sm);
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

.sop-card {
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

.sop-card__trail {
  display: flex;
  align-items: center;
  gap: var(--app-space-sm);
  margin-top: var(--app-space-md);
}

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

.sop-card__block {
  border-color: transparent;
  background: color-mix(in srgb, var(--assistant-marker) 30%, var(--paper));
  pointer-events: none;
}

.assistant-card__chip,
.sop-card__chip {
  position: absolute;
  top: 8px;
  right: 8px;
  padding: 1px var(--app-space-xs);
  border: 1.5px dashed var(--ink);
  border-radius: 2px;
  background: color-mix(in srgb, var(--c-dashboard) 32%, var(--paper));
  color: var(--ink);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-heavy);
  line-height: var(--app-line-height-tight);
}

.assistant-card__action--publish,
.sop-card__action--publish {
  background: linear-gradient(
    180deg,
    color-mix(in srgb, var(--c-case) 20%, var(--paper)),
    color-mix(in srgb, var(--c-case) 5%, var(--paper))
  );
}

.assistant-card__error,
.sop-card__error {
  margin: 0;
  max-width: 100%;
  color: var(--app-marker-red);
  font-size: var(--app-size-xs);
  font-weight: var(--app-font-weight-bold);
  line-height: var(--app-line-height-snug);
  text-align: center;
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
