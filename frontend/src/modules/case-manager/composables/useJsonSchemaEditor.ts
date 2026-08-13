/**
 * useJsonSchemaEditor — visual ↔ code mode toggle for JSON Schema editing.
 *
 * Visual mode: key-value table with field name, type, required, constraints.
 * Code mode: raw JSON text editor.
 *
 * Both modes operate on the same reactive schema object.
 */
import { ref, computed } from 'vue'

export type SchemaField = {
  key: string
  type: string
  required: boolean
  description: string
  minLength?: number
  maxLength?: number
  minimum?: number
  maximum?: number
  enum?: string
  const?: string
}

export function useJsonSchemaEditor(initial: Record<string, any> | null = null) {
  const mode = ref<'visual' | 'code'>('visual')
  const codeText = ref('')
  const fields = ref<SchemaField[]>([])

  // ── Schema → Fields (code → visual) ──
  function schemaToFields(schema: Record<string, any> | null): SchemaField[] {
    if (!schema || typeof schema !== 'object') return []
    const props = schema.properties || {}
    const required: string[] = schema.required || []
    return Object.entries(props).map(([key, def]: [string, any]) => ({
      key,
      type: def.type || 'string',
      required: required.includes(key),
      description: def.description || '',
      minLength: def.minLength,
      maxLength: def.maxLength,
      minimum: def.minimum,
      maximum: def.maximum,
      enum: def.enum ? def.enum.join(', ') : '',
      const: def.const !== undefined ? String(def.const) : '',
    }))
  }

  // ── Fields → Schema (visual → code) ──
  function fieldsToSchema(fs: SchemaField[]): Record<string, any> {
    const properties: Record<string, any> = {}
    const required: string[] = []
    for (const f of fs) {
      if (!f.key) continue
      const def: Record<string, any> = {}
      if (f.type) def.type = f.type
      if (f.description) def.description = f.description
      if (f.minLength !== undefined && f.type === 'string') def.minLength = f.minLength
      if (f.maxLength !== undefined && f.type === 'string') def.maxLength = f.maxLength
      if (f.minimum !== undefined && (f.type === 'number' || f.type === 'integer')) def.minimum = f.minimum
      if (f.maximum !== undefined && (f.type === 'number' || f.type === 'integer')) def.maximum = f.maximum
      if (f.enum) def.enum = f.enum.split(',').map(s => s.trim()).filter(Boolean)
      if (f.const !== undefined && f.const !== '') def.const = f.type === 'number' ? Number(f.const) : f.const
      properties[f.key] = def
      if (f.required) required.push(f.key)
    }
    const result: Record<string, any> = { type: 'object', properties }
    if (required.length) result.required = required
    return result
  }

  // ── Sync to code mode ──
  function toCodeText(schema: Record<string, any> | null): string {
    if (!schema || typeof schema !== 'object') return '{\n  \n}'
    return JSON.stringify(schema, null, 2)
  }

  // ── Parse code text to schema ──
  function parseCodeText(text: string): Record<string, any> | null {
    try {
      return JSON.parse(text)
    } catch {
      return null
    }
  }

  // ── Initialize ──
  if (initial) {
    fields.value = schemaToFields(initial)
    codeText.value = toCodeText(initial)
  }

  function switchToVisual(schema: Record<string, any> | null) {
    mode.value = 'visual'
    fields.value = schemaToFields(schema)
  }

  function switchToCode(schema: Record<string, any> | null) {
    mode.value = 'code'
    codeText.value = toCodeText(schema)
  }

  function addField() {
    fields.value.push({ key: '', type: 'string', required: false, description: '' })
  }

  function removeField(index: number) {
    fields.value.splice(index, 1)
  }

  /** Parse current code text and return parsed schema (null = invalid JSON) */
  function getCodeSchema(): Record<string, any> | null {
    return parseCodeText(codeText.value)
  }

  return {
    mode,
    fields,
    codeText,
    schemaToFields,
    fieldsToSchema,
    toCodeText,
    parseCodeText,
    switchToVisual,
    switchToCode,
    addField,
    removeField,
    getCodeSchema,
  }
}
