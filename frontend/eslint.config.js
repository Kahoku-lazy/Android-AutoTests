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

  // ── JS base (ESLint recommended) ──
  {
    files: ["**/*.js", "**/*.ts", "**/*.vue"],
    rules: js.configs.recommended.rules,
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
    },
  },
]
