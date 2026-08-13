# [P2] 默认不写 Vitest

本目录**故意不放 `.spec.ts`**。后续复杂模块同样：P2 只登记、不测。

## 登录模块 P2 清单（跳过 Vitest）

| 项 | 原因 | 去向 |
|----|------|------|
| `LoginView.vue` 整页 mount | 薄拼装，mock 多、收益低 | E2E 或人工点验 |
| `useHeroImage` 插画加载/失败 | 装饰性，无业务分支价值 | 不测 |
| 真后端登录/注册联调 | 依赖服务与网络 | E2E |
| 路由守卫踢回 `/login` | 全链路鉴权 | E2E |
| 跨 tab `storage` 同步 | 多窗口真实环境 | E2E（可选） |

优先级约定见：`../../PRIORITY_TEMPLATE.md`
