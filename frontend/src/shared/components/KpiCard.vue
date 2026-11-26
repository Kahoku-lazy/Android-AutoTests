<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(
  defineProps<{
    value?: string | number
    label?: string
    color?: string

    shape?: "diamond" | "triangle" | "square" | "circle"
    variant?: "kpi" | "entry"

    desc?: string

    live?: boolean

    deco?: "none" | "pin" | "tape"

    tilt?: number

    clickable?: boolean
  }>(),
  {
    value: "",
    label: "",
    color: "var(--c-dashboard)",
    shape: "diamond",
    variant: "kpi",
    desc: "",
    live: false,
    deco: "none",
    tilt: undefined,
    clickable: undefined,
  },
)

const emit = defineEmits<{
  click: [e: MouseEvent | KeyboardEvent]
}>()

const isEntry = computed(() => props.variant === "entry")

const isClickable = computed(() => {
  if (props.clickable !== undefined) return props.clickable

  return isEntry.value ? false : true
})

const rootStyle = computed(() => {
  const style: Record<string, string> = {
    "--kpi-accent": props.color,
  }
  if (props.tilt !== undefined) {
    style["--kpi-tilt"] = `${props.tilt}deg`
  }
  return style
})

function onActivate(e: MouseEvent | KeyboardEvent) {
  if (!isClickable.value) return
  emit("click", e)
}

function onKeydown(e: KeyboardEvent) {
  if (!isClickable.value) return
  if (e.key === "Enter" || e.key === " ") {
    e.preventDefault()
    onActivate(e)
  }
}
</script>

<template>
  <div
    class="kpi-card"
    :class="[`kpi-card--${variant}`, { 'is-clickable': isClickable, 'has-deco': deco !== 'none' }]"
    :style="rootStyle"
    :role="isClickable ? 'button' : undefined"
    :tabindex="isClickable ? 0 : undefined"
    @click="onActivate"
    @keydown="onKeydown"
  >
    <span v-if="deco === 'pin'" class="kpi-card__pin" aria-hidden="true" />
    <span v-if="deco === 'tape'" class="kpi-card__tape" aria-hidden="true" />

    <template v-if="!isEntry">
      <div
        class="kpi-card__shape"
        :class="`kpi-card__shape--${shape}`"
        :style="{ background: color }"
      >
        <span v-if="shape !== 'circle'" class="kpi-card__shape-inner" />
      </div>
      <div class="kpi-card__label">{{ label }}</div>
      <div class="kpi-card__value">
        <slot name="value">{{ value }}</slot>
      </div>
      <slot />
    </template>

    <template v-else>
      <div class="kpi-card__head">
        <span class="kpi-card__icon">
          <slot name="icon">
            <span class="kpi-card__icon-fallback" />
          </slot>
        </span>
        <span class="kpi-card__title">{{ label }}</span>
        <span v-if="live" class="kpi-card__live" aria-hidden="true" />
      </div>

      <div class="kpi-card__stat">
        <slot name="value">
          <strong class="kpi-card__value">{{ value }}</strong>
        </slot>
        <div v-if="desc || $slots.desc" class="kpi-card__desc">
          <slot name="desc">{{ desc }}</slot>
        </div>
      </div>

      <slot />
    </template>
  </div>
</template>

<style scoped>
.kpi-card {
  --kpi-accent: var(--comp-kpi-accent);

  --kpi-pin-shadow: var(--comp-kpi-pin-shadow);
  --kpi-tape-border: var(--comp-kpi-tape-border);
  --kpi-icon-shadow: var(--comp-kpi-icon-shadow);
  --kpi-shape-border: var(--comp-kpi-shape-border);

  --kpi-live-pulse: var(--comp-kpi-live-pulse);
  --kpi-live-pulse-fade: var(--comp-kpi-live-pulse-fade);
  --kpi-tilt: var(--comp-kpi-tilt);
  --kpi-radius: var(--comp-kpi-radius);
  position: relative;
  background: var(--color-white);

  border: 2.5px solid color-mix(in srgb, var(--kpi-accent) 42%, var(--paper));
  border-radius: var(--kpi-radius);

  box-shadow:
    4px 4px 0 0 color-mix(in srgb, var(--kpi-accent) 42%, var(--paper)),
    8px 8px 0 0 color-mix(in srgb, var(--kpi-accent) 20%, var(--paper)),
    12px 12px 0 0 color-mix(in srgb, var(--kpi-accent) 8%, var(--paper));
  transform: rotate(var(--kpi-tilt));
  transition:
    transform var(--app-duration, 0.2s) var(--app-ease, ease),
    box-shadow var(--app-duration, 0.2s) var(--app-ease, ease);
}

.kpi-card.is-clickable {
  cursor: pointer;
}

.kpi-card.is-clickable:hover {
  transform: rotate(0deg) translate(-1px, -1px);
  box-shadow:
    5px 5px 0 0 color-mix(in srgb, var(--kpi-accent) 42%, var(--paper)),
    9px 9px 0 0 color-mix(in srgb, var(--kpi-accent) 20%, var(--paper)),
    13px 13px 0 0 color-mix(in srgb, var(--kpi-accent) 8%, var(--paper));
}

.kpi-card:focus-visible {
  outline: 2px solid var(--c-dashboard);
  outline-offset: 3px;
}

.kpi-card__pin,
.kpi-card__tape {
  position: absolute;
  z-index: var(--z-raised);
  pointer-events: none;
}

.kpi-card__pin {
  top: -7px;
  left: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: 2px solid var(--ink);
  background: var(--kpi-accent);
  transform: translateX(-50%);
  box-shadow: 1px 2px 0 0 var(--kpi-pin-shadow);
}

.kpi-card__tape {
  top: -10px;
  left: 50%;
  width: 64px;
  height: 18px;
  transform: translateX(-50%) rotate(-2deg);
  opacity: 0.48;
  border: 1px solid var(--kpi-tape-border);
  background: repeating-linear-gradient(
    90deg,
    color-mix(in srgb, var(--kpi-accent) 70%, #fff),
    color-mix(in srgb, var(--kpi-accent) 70%, #fff) 8px,
    var(--kpi-accent) 8px,
    var(--kpi-accent) 16px
  );
}

.kpi-card--kpi {
  text-align: center;
  padding: var(--app-space-md, 12px) var(--app-space-lg, 16px) var(--app-space-sm, 8px);
  min-width: 120px;
}

.kpi-card__shape {
  width: 22px;
  height: 22px;
  margin: 0 auto 10px;
  border: 2px solid var(--kpi-shape-border);
  display: flex;
  align-items: center;
  justify-content: center;
}

.kpi-card__shape-inner {
  width: 6px;
  height: 6px;
  background: var(--color-white);
  border-radius: 1px;
}

.kpi-card__shape--diamond {
  transform: rotate(45deg);
}

.kpi-card__shape--triangle {
  clip-path: polygon(50% 0%, 0% 100%, 100% 100%);
  border: none;
  width: 24px;
  height: 20px;
}

.kpi-card__shape--triangle .kpi-card__shape-inner {
  width: 5px;
  height: 5px;
  margin-top: var(--app-space-xs, 4px);
}

.kpi-card__shape--square {
  border-radius: 2px;
}

.kpi-card__shape--circle {
  border-radius: 50%;
}

.kpi-card__shape--circle .kpi-card__shape-inner {
  display: none;
}

.kpi-card--kpi .kpi-card__label {
  font-size: var(--app-size-md, 16px);
  font-weight: var(--app-font-weight-bold);
  letter-spacing: 0.04em;
  margin-bottom: 2px;

  color: var(--app-text-primary);
}

.kpi-card--kpi .kpi-card__value {
  font-family: var(--app-font, inherit);
  font-size: var(--app-size-2xl, 28px);
  font-weight: var(--app-font-weight-heavy);
  line-height: 1.1;

  background-image: linear-gradient(
    90deg,
    color-mix(in srgb, var(--kpi-accent) 48%, var(--ink)) 0%,
    color-mix(in srgb, var(--kpi-accent) 30%, var(--ink)) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: color-mix(in srgb, var(--kpi-accent) 30%, var(--ink));
  -webkit-text-fill-color: transparent;
}

.kpi-card--entry {
  display: flex;
  flex-direction: column;
  min-height: 142px;
  width: 100%;
  padding: 14px 12px 10px;
}

.kpi-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  min-width: 0;
}

.kpi-card__icon {
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border: 2px solid var(--ink);
  border-radius: var(--kpi-radius);
  background: var(--kpi-accent);
  color: var(--app-text-primary);
  box-shadow: 2px 2px 0 0 var(--kpi-icon-shadow);
}

.kpi-card__icon :deep(svg) {
  width: 14px;
  height: 14px;
  stroke: var(--ink);
  color: var(--app-text-primary);
}

.kpi-card__icon-fallback {
  width: 10px;
  height: 10px;
  background: var(--ink);
  opacity: 0.35;
}

.kpi-card__title {
  flex: 1;
  min-width: 0;
  font-size: var(--app-size-md, 16px);
  font-weight: var(--app-font-weight-heavy);
  color: var(--app-text-primary);
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
  line-height: var(--app-line-height-tight);
}

.kpi-card__live {
  width: 8px;
  height: 8px;
  flex-shrink: 0;
  border-radius: 50%;
  border: 2px solid var(--app-live);
  background: var(--color-white);
  animation: kpiLivePulse 1.5s ease-in-out infinite;
}

@keyframes kpiLivePulse {
  0%,
  100% {
    box-shadow: 0 0 0 0 var(--kpi-live-pulse);
  }
  50% {
    box-shadow: 0 0 0 5px var(--kpi-live-pulse-fade);
  }
}

.kpi-card__stat {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  text-align: center;
  padding: 0 4px;
}

.kpi-card--entry .kpi-card__value,
.kpi-card--entry .kpi-card__stat :deep(strong) {
  display: block;
  font-family: var(--app-font-display, var(--app-font, inherit));
  font-size: var(--app-size-2xl, 28px);
  font-weight: var(--app-font-weight-heavy);
  letter-spacing: -0.03em;
  line-height: 1;

  background-image: linear-gradient(
    90deg,
    color-mix(in srgb, var(--kpi-accent) 48%, var(--ink)) 0%,
    color-mix(in srgb, var(--kpi-accent) 30%, var(--ink)) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  color: color-mix(in srgb, var(--kpi-accent) 30%, var(--ink));
  -webkit-text-fill-color: transparent;
}

.kpi-card__stat :deep(small) {
  font-size: var(--app-size-sm, 14px);
  font-weight: var(--app-font-weight-bold);
  color: var(--app-status-success-text);
}

.kpi-card__desc {
  font-size: var(--app-size-sm, 14px);
  font-weight: var(--app-font-weight-semibold);
  color: var(--app-text-secondary);
  line-height: var(--app-line-height-snug);
}

@media (prefers-reduced-motion: reduce) {
  .kpi-card {
    transform: none;
    transition: none;
  }
  .kpi-card.is-clickable:hover {
    transform: none;
  }
  .kpi-card__live {
    animation: none;
  }
}
</style>
