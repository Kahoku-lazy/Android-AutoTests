import type { RouteRecordRaw } from "vue-router"

const routes: RouteRecordRaw[] = [
  {
    path: "/serial-log",
    name: "serial-log",
    component: () => import("@/modules/serial-log/index.vue"),
    meta: { title: "串口日志" },
  },
]

export default routes
