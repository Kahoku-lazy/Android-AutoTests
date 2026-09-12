import { describe, expect, it } from 'vitest'
import { emptySheetRow } from '@/modules/case-manager/composables/useCaseSheet'

describe('emptySheetRow', () => {
  it('creates a dirty new draft row', () => {
    const row = emptySheetRow()
    expect(row.isNew).toBe(true)
    expect(row.dirty).toBe(true)
    expect(row.id.startsWith('temp-')).toBe(true)
    expect(row.test_type).toBe('app')
    expect(row.business_type).toBe('appliance')
  })

  it('generates unique temp ids', () => {
    const a = emptySheetRow()
    const b = emptySheetRow()
    expect(a.id).not.toBe(b.id)
  })
})
