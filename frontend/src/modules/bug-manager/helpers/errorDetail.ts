export interface ErrorDetailLine {
  label: string

  text: string
}

const LABEL_RE = /^([^\s：:/]{1,12}[：:])[ \t]?(.*)$/

export function splitErrorDetail(text: string): ErrorDetailLine[] {
  if (!text) return []
  return text.split(/\r?\n/).map((line) => {
    const matched = LABEL_RE.exec(line)

    if (!matched || matched[2].startsWith("//")) return { label: "", text: line }
    return { label: matched[1], text: matched[2] }
  })
}
