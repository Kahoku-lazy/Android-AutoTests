import { describe, expect, it } from "vitest"
import { mediaUrl } from "@/shared/helpers/mediaUrl"

describe("[P0] shared/mediaUrl", () => {
  it("相对路径拼成 /media/ URL", () => {
    expect(mediaUrl("locator/pages/1/el_a.png")).toBe("/media/locator/pages/1/el_a.png")
    expect(mediaUrl("inspector/captures/capture_1.png")).toBe(
      "/media/inspector/captures/capture_1.png",
    )
  })

  it("空路径不产 URL（避免请求站点根）", () => {
    expect(mediaUrl("")).toBe("")
    expect(mediaUrl(undefined)).toBe("")
    expect(mediaUrl(null)).toBe("")
  })
})
