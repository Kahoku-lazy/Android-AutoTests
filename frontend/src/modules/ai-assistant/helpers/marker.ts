const MARKER_VARS: Record<string, string> = {
  teal: "var(--assistant-marker-teal)",
  ink: "var(--assistant-marker-ink)",
  amber: "var(--assistant-marker-amber)",
  rose: "var(--assistant-marker-rose)",
  moss: "var(--assistant-marker-moss)",
}

export function markerVars(marker: string): Record<string, string> {
  return { "--assistant-marker": MARKER_VARS[marker] || MARKER_VARS.teal }
}
