export const BACKEND_UNAVAILABLE = {
  status: false,
  message: "后端服务未就绪（可能正在重启），请稍后重试",
}

function canWrite(res) {
  return (
    Boolean(res) && typeof res.writeHead === "function" && !res.headersSent && !res.writableEnded
  )
}

export function proxyOnError(proxy) {
  proxy.on("error", (err, req, res) => {
    if (!canWrite(res)) return
    res.writeHead(503, { "Content-Type": "application/json; charset=utf-8" })
    res.end(JSON.stringify(BACKEND_UNAVAILABLE))
  })
}
