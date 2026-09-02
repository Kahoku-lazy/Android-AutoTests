import js from "@eslint/js"
import tseslint from "@typescript-eslint/eslint-plugin"
import tsparser from "@typescript-eslint/parser"
import vueplugin from "eslint-plugin-vue"
import vueparser from "vue-eslint-parser"

/** @type {import('eslint').Linter.FlatConfig[]} */
export default [
  // ── Global ignores ──
  {
    ignores: [
      "dist/**",
      "node_modules/**",
      "src/auto-imports.d.ts",
      "src/components.d.ts",
    ],
  },

  // ── JS base (ESLint recommended；no-undef/no-unused-vars 交给 TS 类型检查) ──
  {
    files: ["**/*.js", "**/*.ts", "**/*.vue"],
    rules: {
      ...js.configs.recommended.rules,
      // TS 项目：undefined/unused 由 vue-tsc 类型检查负责；ESLint 的这两个 JS 规则
      // 会误报浏览器全局（window/document/localStorage）与 unplugin-auto-import（computed/ref）。
      "no-undef": "off",
      "no-unused-vars": "off",
    },
  },

  // ── Vue files ──
  ...vueplugin.configs["flat/essential"],
  {
    files: ["**/*.vue"],
    languageOptions: {
      parser: vueparser,
      parserOptions: {
        parser: tsparser,
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    rules: {
      "vue/multi-word-component-names": "off",
      "vue/no-v-html": "off",
    },
  },

  // ── TypeScript files ──
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsparser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
    },
    plugins: {
      "@typescript-eslint": tseslint,
    },
    rules: {
      "@typescript-eslint/no-explicit-any": "warn",
      "@typescript-eslint/no-unused-vars": [
        "warn",
        { argsIgnorePattern: "^_", varsIgnorePattern: "^_" },
      ],
      "@typescript-eslint/no-empty-function": "warn",
    },
  },

  // ── Common rules for all files ──
  {
    rules: {
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "prefer-const": "warn",
      "no-var": "error",
      // 通道①：前端 HTTP 唯一出口 — 禁止直接 import 第三方 HTTP 库（别名/default as/require 均命中）
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "axios",
              message: "禁止直接 import axios，请走 @/shared/api-client（唯一 HTTP 出口）",
            },
            { name: "ky", message: "禁止 import 第三方 HTTP 库，请走 @/shared/api-client" },
            { name: "got", message: "禁止 import 第三方 HTTP 库，请走 @/shared/api-client" },
            { name: "superagent", message: "禁止 import 第三方 HTTP 库，请走 @/shared/api-client" },
          ],
        },
      ],
      // 通道①：禁止裸用全局 HTTP 手段（fetch / XMLHttpRequest / sendBeacon）
      "no-restricted-globals": [
        "error",
        { name: "fetch", message: "禁止直接使用全局 fetch，请走 @/shared/api-client" },
        { name: "XMLHttpRequest", message: "禁止使用 XMLHttpRequest，请走 @/shared/api-client" },
      ],
      "no-restricted-syntax": [
        "error",
        {
          selector: "CallExpression[callee.property.name='sendBeacon']",
          message: "禁止使用 navigator.sendBeacon 发数据，请走 @/shared/api-client",
        },
      ],
      // ── 历史遗留代码问题：降级为 warning，不阻塞通道门禁（后续逐步清理）──
      "vue/no-mutating-props": "warn",
      "vue/no-unused-vars": "warn",
      "vue/no-use-v-if-with-v-for": "warn",
      "no-unreachable": "warn",
      "preserve-caught-error": "warn",
      "no-empty": "warn",
      "no-useless-assignment": "warn",
      "no-irregular-whitespace": "warn",
    },
  },

  // ── 唯一出口 SSOT 豁免：仅这两个文件允许 import axios ──
  {
    files: ["src/shared/api-client.ts", "src/shared/api-auth-interceptors.ts"],
    rules: {
      "no-restricted-imports": "off",
      "no-restricted-globals": "off",
      "no-restricted-syntax": "off",
    },
  },
]
