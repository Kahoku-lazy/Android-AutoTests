## Context

MIDDLEWARE 顺序：CommonMiddleware（APPEND_SLASH 301）先于 JWTAuthenticationMiddleware——无尾斜杠请求在鉴权前就被 301，重定向丢 header 后才 401。修复必须在 CommonMiddleware 之前完成路径规范化。

## Goals / Non-Goals

**Goals:**

- 无尾斜杠 API 请求与有尾斜杠等价（无 301、无 401）
- 预检日志显示真实分辨率

**Non-Goals:**

- 不统一各 App 路由尾斜杠写法（约定不动，middleware 兜底）

## Decisions

- **规范化方向**：仅当"无斜杠版 resolve 失败 + 带斜杠版 resolve 成功"才补斜杠（保护 runner 等原生无斜杠路由）
- **挂载点**：MIDDLEWARE 列表第一项（CommonMiddleware 之前）；middleware 内用 `get_resolver()` 惰性取 resolver（避免启动期解析）
- **#2 修复**：`_verify_display` 补键循环扩展 `displayWidth/displayHeight`（u2 info 为真值来源，与既有 productName 补键同模式）

## 模块防火墙自检

- gateway 层改动（横切），无跨 App import；engines 修改为本模块内部逻辑；通过

## Risks / Trade-offs

- [规范化误伤原生无斜杠路由] → resolve 双向探测 + 单测覆盖 /api/runner/tasks 不动
- [resolver 性能] → 仅对 /api/ 无尾斜杠路径触发（低频）
