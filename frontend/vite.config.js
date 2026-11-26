import { defineConfig } from "vite"
import vue from "@vitejs/plugin-vue"
import { fileURLToPath, URL } from "node:url"
import { scanModules } from "./tests/module-scan.mjs"
import { proxyOnError } from "./vite-proxy.js"
import AutoImport from "unplugin-auto-import/vite"
import Components from "unplugin-vue-components/vite"
import { ElementPlusResolver } from "unplugin-vue-components/resolvers"

const isTest = !!process.env.VITEST

export default defineConfig({
  plugins: [
    vue(),

    ...(!isTest
      ? [
          AutoImport({
            resolvers: [ElementPlusResolver({ importStyle: false })],
            dts: "src/auto-imports.d.ts",
          }),
          Components({
            resolvers: [ElementPlusResolver({ importStyle: false })],
            dts: "src/components.d.ts",
          }),
        ]
      : []),
  ],
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
  test: {
    projects: scanModules().flatMap((m) =>
      m.prios.map((prio) => ({
        extends: true,
        test: {
          name: `${m.name}/${prio}`,
          include: [`tests/${m.name}/${prio}/**/*.{test,spec}.{js,ts}`],
          environment: "jsdom",
          css: false,
        },
      })),
    ),
  },
  server: {
    host: "0.0.0.0",
    port: 5173,
    proxy: {
      "/api": {
        target: `http://localhost:${process.env.SERVER_PORT || 8766}`,
        configure: proxyOnError,
      },
      "/media": {
        target: `http://localhost:${process.env.SERVER_PORT || 8766}`,
        configure: proxyOnError,
      },
      "/ws": {
        target: `ws://localhost:${process.env.SERVER_PORT || 8766}`,
        ws: true,
      },
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ["vue", "vue-router", "axios", "animejs"],
        },
      },
    },

    chunkSizeWarningLimit: 1500,
  },
})
