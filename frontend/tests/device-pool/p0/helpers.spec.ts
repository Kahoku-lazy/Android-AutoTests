import { describe, expect, it } from 'vitest'
import { validateLanConnect } from '@/modules/device-pool/helpers'

describe('[P0] validateLanConnect', () => {
  it('已配对：只填 IP 与连接端口', () => {
    const r = validateLanConnect({
      ip: '10.162.95.96',
      connectPort: '43523',
      pairPort: '',
      pairCode: '',
    })
    expect(r.ok).toBe(true)
    expect(r.payload).toEqual({ target: '10.162.95.96:43523' })
  })

  it('首次配对：附带 pair_port / pair_code', () => {
    const r = validateLanConnect({
      ip: '10.162.95.96',
      connectPort: '43523',
      pairPort: '41395',
      pairCode: '387429',
    })
    expect(r.ok).toBe(true)
    expect(r.payload).toEqual({
      target: '10.162.95.96:43523',
      pair_port: '41395',
      pair_code: '387429',
    })
  })

  it('只填配对端口不填配对码时失败', () => {
    const r = validateLanConnect({
      ip: '10.162.95.96',
      connectPort: '43523',
      pairPort: '41395',
      pairCode: '',
    })
    expect(r.ok).toBe(false)
    expect(r.firstError).toBe('pairCode')
  })
})
