import { describe, expect, it } from "vitest"

import { formatApiError } from "@/shared/types/api-error"

describe("formatApiError 对 5xx 的取文案口径", () => {
  it("优先原样返回后端 message，而非通用文案", () => {
    const message = "任务配置文件写入失败：Permission denied，请检查运行账号对该目录的写权限"
    expect(formatApiError({ response: { status: 500, data: { status: false, message } } })).toBe(message)
  })

  it("500 且无 message 时回落到通用文案", () => {
    expect(formatApiError({ response: { status: 500, data: { status: false } } })).toBe(
      "服务暂时异常，请稍后重试",
    )
  })
})
