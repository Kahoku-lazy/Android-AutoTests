/** @type {import('dependency-cruiser').IConfiguration} */
module.exports = {
  forbidden: [
    {
      name: "no-axios-except-client",
      comment: "通道①：前端 HTTP 唯一出口 —— 只有 shared/api-client.ts 允许依赖 axios",
      severity: "error",
      from: { pathNot: "^src/shared/api-(client|auth-interceptors)\\.ts$" },
      to: { path: "^node_modules/axios/" },
    },
  ],
  options: {
    doNotFollow: { path: "node_modules" },
    tsPreCompilationDeps: true,
    tsConfig: { fileName: "./tsconfig.json" },
  },
};
