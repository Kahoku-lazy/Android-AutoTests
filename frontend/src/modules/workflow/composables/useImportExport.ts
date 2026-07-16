import type { Block, StepBlock, FlatTestStep } from '@/modules/workflow/types/testCase'

export interface TestCaseExport {
  format: 'testcase-scratch-v1'
  name: string
  description: string
  package_name: string
  exportedAt: string
  blocks: Block[]
  /** Flat steps aligned with platform TestStep (tree walk, skips container structure) */
  flat_steps: FlatTestStep[]
}

function flattenSteps(blocks: Block[]): FlatTestStep[] {
  const result: FlatTestStep[] = []
  function walk(list: Block[]): void {
    for (const b of list) {
      if (b.kind === 'step') {
        result.push(stepToFlat(b))
      } else if (b.kind === 'branch') {
        walk(b.passChildren)
        walk(b.failChildren)
      } else if (b.kind === 'loop') {
        walk(b.children)
      }
    }
  }
  walk(blocks)
  return result
}

function stepToFlat(b: StepBlock): FlatTestStep {
  const flat: FlatTestStep = {
    type: b.stepType,
    xpath: b.xpath,
    xpath2: b.xpath2,
    timeout: b.timeout,
    expected_text: b.expected_text,
    index: b.index,
    direction: b.direction || '',
    distance: b.distance ?? 500,
    description: b.description || b.label,
  }
  if (b.package_name) flat.package_name = b.package_name
  return flat
}

export function useImportExport() {
  function buildExport(name: string, description: string, blocks: Block[], packageName = 'com.example.app'): TestCaseExport {
    const cloned: Block[] = JSON.parse(JSON.stringify(blocks))
    return {
      format: 'testcase-scratch-v1',
      name,
      description,
      package_name: packageName,
      exportedAt: new Date().toISOString(),
      blocks: cloned,
      flat_steps: flattenSteps(cloned),
    }
  }

  function downloadFile(data: TestCaseExport, filename?: string): void {
    const json = JSON.stringify(data, null, 2)
    const blob = new Blob([json], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename || `${data.name || 'testcase'}.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  function uploadFile(): Promise<TestCaseExport | null> {
    return new Promise((resolve) => {
      const input = document.createElement('input')
      input.type = 'file'
      input.accept = '.json'
      input.onchange = () => {
        const file = input.files?.[0]
        if (!file) { resolve(null); return }
        const reader = new FileReader()
        reader.onload = () => {
          try {
            const data = JSON.parse(reader.result as string)
            if (data.format === 'testcase-scratch-v1' && Array.isArray(data.blocks)) {
              resolve(data as TestCaseExport)
            } else {
              resolve(null)
            }
          } catch { resolve(null) }
        }
        reader.readAsText(file)
      }
      input.click()
    })
  }

  async function copyToClipboard(data: TestCaseExport): Promise<boolean> {
    try {
      await navigator.clipboard.writeText(JSON.stringify(data, null, 2))
      return true
    } catch {
      return false
    }
  }

  async function readFromClipboard(): Promise<TestCaseExport | null> {
    try {
      const text = await navigator.clipboard.readText()
      const data = JSON.parse(text)
      if (data.format === 'testcase-scratch-v1' && Array.isArray(data.blocks)) {
        return data as TestCaseExport
      }
      // Also accept plain block arrays
      if (Array.isArray(data) && data.length > 0 && data[0].kind) {
        return {
          format: 'testcase-scratch-v1',
          name: '导入的用例',
          description: '',
          package_name: '',
          exportedAt: '',
          blocks: data,
          flat_steps: flattenSteps(data),
        }
      }
      return null
    } catch {
      return null
    }
  }

  return { buildExport, downloadFile, uploadFile, copyToClipboard, readFromClipboard, flattenSteps }
}
