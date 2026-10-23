/**
 * Vite 开发代理的上游不可用兜底。
 *
 * 后端重启或未监听时，连接会被拒绝；Vite 默认回空 body 的 500，
 * 前端只能看到 "Request failed with status code 500"。这里统一改成
 * 503 + 可读 message，让「后端没起来」和「业务接口 500」可区分。
 *
 * 只接管尚未写出的 HTTP 响应：后端自身的 5xx 不经过 error 事件，原样透传；
 * WS 升级失败时 res 是 socket，不做处理。
 */

export const BACKEND_UNAVAILABLE = {
  status: false,
  message: "后端服务未就绪（可能正在重启），请稍后重试",
}

/** res 是否是可写的 HTTP 响应（WS 升级失败时是 socket）。 */
function canWrite(res) {
  return (
    Boolean(res) &&
    typeof res.writeHead === "function" &&
    !res.headersSent &&
    !res.writableEnded
  )
}

/** 代理 error 事件处理：连接失败回 503 JSON，其余情况不碰响应。 */
export function proxyOnError(proxy) {
  proxy.on("error", (err, req, res) => {
    if (!canWrite(res)) return
    res.writeHead(503, { "Content-Type": "application/json; charset=utf-8" })
    res.end(JSON.stringify(BACKEND_UNAVAILABLE))
  })
}
