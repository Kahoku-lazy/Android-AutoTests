import { describe, expect, it } from "vitest"

import { BACKEND_UNAVAILABLE, proxyOnError } from "../../../vite-proxy.js"

function fakeProxy() {
  const handlers = {}
  return {
    on(event, handler) {
      handlers[event] = handler
    },
    emit(event, ...args) {
      handlers[event]?.(...args)
    },
  }
}

function fakeResponse(overrides = {}) {
  const res = {
    headersSent: false,
    writableEnded: false,
    statusCode: null,
    headers: null,
    body: "",
    writeHead(status, headers) {
      res.statusCode = status
      res.headers = headers
      res.headersSent = true
      return res
    },
    end(chunk) {
      res.body += chunk ?? ""
      res.writableEnded = true
    },
    ...overrides,
  }
  return res
}

describe("vite 代理上游不可用兜底", () => {
  it("连接失败时回 503 与可读 message", () => {
    const proxy = fakeProxy()
    proxyOnError(proxy)
    const res = fakeResponse()

    proxy.emit("error", new Error("ECONNREFUSED"), { url: "/api/x" }, res)

    expect(res.statusCode).toBe(503)
    expect(res.headers["Content-Type"]).toContain("application/json")
    expect(JSON.parse(res.body)).toEqual(BACKEND_UNAVAILABLE)
  })

  it("响应已写出时不再写第二次", () => {
    const proxy = fakeProxy()
    proxyOnError(proxy)
    let writes = 0
    const res = fakeResponse({
      headersSent: true,
      writeHead: () => {
        writes += 1
      },
    })

    proxy.emit("error", new Error("ECONNRESET"), { url: "/api/y" }, res)

    expect(writes).toBe(0)
  })

  it("WS 的 socket 响应不写 HTTP 状态码", () => {
    const proxy = fakeProxy()
    proxyOnError(proxy)

    expect(() => proxy.emit("error", new Error("ECONNRESET"), { url: "/ws" }, {})).not.toThrow()
  })
})
