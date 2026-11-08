/*
 * 前端一次页面访问的流程（人工维护，非自动采集）
 *
 * 静态 AST 只能证明 import 存在，推不出"谁先谁后"；所以这里按 frontend/AGENTS 与
 * 实际代码入口人工梳理，每一步带 source。改路由/请求层请同步这里。
 */
window.__FLOW_FRONTEND__ = {
  updated: "2026-11-03",
  source: "人工维护（依据 frontend/src/router.ts、modules/*/routes.ts、shared/api 与前端 AGENTS）",
  caveat: "这是文档级流程，不是从运行日志采到的真实调用链；与代码不一致时以代码为准。",
  steps: [
    {
      key: "entry",
      label: "① 进入应用",
      actor: "frontend/src/main.ts",
      detail: "挂载 Vue 应用与 router；全局样式与 Doodle Craft 令牌在入口一次性注入。",
      source: "frontend/src/main.ts"
    },
    {
      key: "guard",
      label: "② 路由守卫",
      actor: "router.ts beforeEach",
      detail: "无 token 只能停留在 /login，已登录访问 /login 则回 /dashboard；其余页面放行。",
      source: "frontend/src/router.ts"
    },
    {
      key: "route",
      label: "③ 命中模块路由",
      actor: "modules/<模块>/routes.ts",
      detail: "按 path 命中模块路由表，懒加载对应视图组件（一个模块一组路由）。",
      source: "frontend/src/modules/*/routes.ts"
    },
    {
      key: "page",
      label: "④ 页面渲染",
      actor: "modules/<模块>/views/*.vue",
      detail: "视图组件组合 shared 共享件（卡片/表格/图表）渲染；状态用组合式函数管理。",
      source: "frontend/src/modules/*/views/"
    },
    {
      key: "api",
      label: "⑤ 调接口",
      actor: "modules/<模块>/api 或 shared/api",
      detail: "请求统一走 api 层（axios 实例 + 拦截器）：注入 token、解包 {status,data} 信封、错误统一提示。",
      source: "frontend/src/shared/api/"
    },
    {
      key: "render",
      label: "⑥ 回写与展示",
      actor: "页面组件",
      detail: "响应数据落组件状态并渲染；长任务轮询或事件流更新列表与详情。",
      source: "frontend/src/shared/composables/"
    }
  ]
};
