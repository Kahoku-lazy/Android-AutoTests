/**
 * [P0] 必测 — 媒体路径拼接的唯一登记处
 * 目录：tests/shared/p0/
 *
 * 原实现分散在设备检查器 store / 元素定位 elementPresentation / AI 助手 task-detail，
 * 本用例锁定收敛后的口径：有相对路径才产出 `/media/` URL，空路径产空串。
 */
import { describe, expect, it } from 'vitest'
import { mediaUrl } from '@/shared/helpers/mediaUrl'

describe('[P0] shared/mediaUrl', () => {
  it('相对路径拼成 /media/ URL', () => {
    expect(mediaUrl('locator/pages/1/el_a.png')).toBe('/media/locator/pages/1/el_a.png')
    expect(mediaUrl('inspector/captures/capture_1.png')).toBe(
      '/media/inspector/captures/capture_1.png',
    )
  })

  it('空路径不产 URL（避免请求站点根）', () => {
    expect(mediaUrl('')).toBe('')
    expect(mediaUrl(undefined)).toBe('')
    expect(mediaUrl(null)).toBe('')
  })
})
