import js from "@eslint/js"
import tseslint from "@typescript-eslint/eslint-plugin"
import tsparser from "@typescript-eslint/parser"
import vueplugin from "eslint-plugin-vue"
import vueparser from "vue-eslint-parser"

export default [
  {
    ignores: ["dist/**", "node_modules/**", "src/auto-imports.d.ts", "src/components.d.ts"],
  },

  {
    files: ["**/*.js", "**/*.ts", "**/*.vue"],
    rules: {
      ...js.configs.recommended.rules,

      "no-undef": "off",
      "no-unused-vars": "off",
    },
  },

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

  {
    rules: {
      "no-console": ["warn", { allow: ["warn", "error"] }],
      "no-debugger": "error",
      "prefer-const": "warn",
      "no-var": "error",

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

  {
    files: ["src/modules/**", "src/views/**"],
    rules: {
      "no-console": ["error", { allow: ["warn", "error"] }],
    },
  },

  {
    files: ["src/shared/api-client.ts", "src/shared/api-auth-interceptors.ts"],
    rules: {
      "no-restricted-imports": "off",
      "no-restricted-globals": "off",
      "no-restricted-syntax": "off",
    },
  },
]
