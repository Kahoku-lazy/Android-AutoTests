<script setup lang="ts">
import { computed } from "vue"

const props = withDefaults(
  defineProps<{
    variant?: "note" | "sticky"

    status?: "ok" | "run" | "fail" | "wait"

    accent?: string

    tape?: boolean

    tapeColor?: string

    tilt?: number

    as?: "article" | "div" | "section"
  }>(),
  {
    variant: "note",
    status: "ok",
    accent: undefined,
    tape: true,
    tapeColor: undefined,
    tilt: undefined,
    as: "article",
  },
)

const rootStyle = computed(() => {
  const style: Record<string, string> = {}

  const accent =
    props.accent ||
    (props.variant === "sticky"
      ? props.status === "fail"
        ? "var(--app-marker-red)"
        : props.status === "ok"
          ? "var(--c-case)"
          : props.status === "run"
            ? "var(--c-workflow)"
            : "var(--app-offline)"
      : "var(--c-case)")

  style["--note-accent"] = accent

  if (props.tapeColor) {
    style["--note-tape"] = props.tapeColor
  } else {
    style["--note-tape"] = accent
  }

  if (props.tilt !== undefined) {
    style["--note-tilt"] = `${props.tilt}deg`
  } else if (props.variant === "sticky") {
    style["--note-tilt"] = props.status === "fail" ? "1.4deg" : "-1.2deg"
  } else {
    style["--note-tilt"] = "-0.8deg"
  }

  return style
})
</script>

<template>
  <component
    :is="as"
    class="doodle-note"
    :class="[
      `doodle-note--${variant}`,
      variant === 'sticky' ? `doodle-note--status-${status}` : '',
    ]"
    :style="rootStyle"
  >
    <span v-if="tape" class="doodle-note__tape" aria-hidden="true" />
    <div v-if="$slots.header" class="doodle-note__header">
      <slot name="header" />
    </div>
    <div class="doodle-note__body">
      <slot />
    </div>
    <div v-if="$slots.actions" class="doodle-note__actions">
      <slot name="actions" />
    </div>
  </component>
</template>

<style scoped>
.doodle-note {
  --note-accent: var(--comp-note-accent);
  --note-tape: var(--comp-note-tape);
  --note-tilt: var(--comp-note-tilt);
  --note-radius: var(--comp-note-radius);

  --note-status-ok-bg: var(--comp-note-status-ok-bg);
  --note-status-fail-bg: var(--comp-note-status-fail-bg);
  --note-status-run-bg: var(--comp-note-status-run-bg);

  --note-tape-border: var(--comp-note-tape-border);
  position: relative;
  display: flex;
  flex-direction: column;
  gap: var(--app-space-sm, 8px);
  padding: var(--app-space-md, 12px);
  border: 1px solid var(--app-border-subtle);
  border-radius: var(--note-radius);
  background: var(--paper);
  box-shadow: 4px 4px 0 0 var(--note-accent);
  transform: rotate(var(--note-tilt));
  transition:
    transform var(--app-duration, 0.2s) var(--app-ease, ease),
    box-shadow var(--app-duration, 0.2s) var(--app-ease, ease);
  overflow: visible;
  min-width: 0;
}

.doodle-note:hover {
  transform: rotate(0deg) translate(-1px, -1px);
  box-shadow: 5px 5px 0 0 var(--note-accent);
}

.doodle-note__tape {
  position: absolute;
  z-index: var(--z-raised);
  top: -10px;
  left: 50%;
  width: 64px;
  height: 18px;
  transform: translateX(-50%) rotate(-2deg);
  opacity: 0.48;
  pointer-events: none;
  border: 1px solid var(--note-tape-border);
  background: repeating-linear-gradient(
    90deg,
    color-mix(in srgb, var(--note-tape) 70%, #fff),
    color-mix(in srgb, var(--note-tape) 70%, #fff) 8px,
    var(--note-tape) 8px,
    var(--note-tape) 16px
  );
}

.doodle-note__header,
.doodle-note__body {
  min-width: 0;
}

.doodle-note__actions {
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: var(--app-space-sm, 8px);
  margin-top: auto;
  padding-top: var(--app-space-sm, 8px);
  border-top: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
}

.doodle-note--note {
  background: var(--paper);
}

.doodle-note--sticky.doodle-note--status-ok {
  background: var(--note-status-ok-bg);
}

.doodle-note--sticky.doodle-note--status-fail {
  background: var(--note-status-fail-bg);
}

.doodle-note--sticky.doodle-note--status-run {
  background: var(--note-status-run-bg);
}

.doodle-note--sticky.doodle-note--status-wait {
  background: var(--paper);
}

@media (prefers-reduced-motion: reduce) {
  .doodle-note {
    transform: none;
    transition: none;
  }
  .doodle-note:hover {
    transform: none;
  }
}
</style>
