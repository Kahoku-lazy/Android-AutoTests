#!/usr/bin/env node
/**
 * Vitest 运行入口（报告输出到 tests/reports/）
 *
 * 用法（在 frontend 目录）:
 *   node tests/run.mjs                  # 默认跑全部
 *   node tests/run.mjs module login     # 只跑指定模块（p0+p1）
 *   node tests/run.mjs prio p0          # 跨模块跑指定优先级
 *   node tests/run.mjs file             # 只跑指定文件
 *   node tests/run.mjs verbose          # 终端详细输出
 *   node tests/run.mjs junit            # 生成 JUnit XML
 *   node tests/run.mjs json             # 生成 JSON 报告
 *   node tests/run.mjs all              # 终端 + JUnit + JSON
 *   node tests/run.mjs watch            # 监听模式
 *   node tests/run.mjs ui               # Vitest UI（需 @vitest/ui）
 *
 * 也可传文件路径：
 *   node tests/run.mjs junit tests/login-form.demo.spec.ts
 */
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'
import { spawnSync } from 'node:child_process'
import { listProjects, scanModules } from './module-scan.mjs'

const __dirname = dirname(fileURLToPath(import.meta.url))
const frontendRoot = join(__dirname, '..')
const reportsDir = join(__dirname, 'reports')

mkdirSync(reportsDir, { recursive: true })

const mode = process.argv[2] || 'default'
const extraArgs = process.argv.slice(3)

const presets = {
  default: ['run', ...extraArgs],
  file: ['run', ...extraArgs],
  verbose: ['run', '--reporter=verbose', ...extraArgs],
  junit: [
    'run',
    '--reporter=default',
    '--reporter=junit',
    `--outputFile.junit=${join(reportsDir, 'junit.xml')}`,
    ...extraArgs,
  ],
  json: [
    'run',
    '--reporter=default',
    '--reporter=json',
    `--outputFile.json=${join(reportsDir, 'report.json')}`,
    ...extraArgs,
  ],
  all: [
    'run',
    '--reporter=default',
    '--reporter=junit',
    '--reporter=json',
    `--outputFile.junit=${join(reportsDir, 'junit.xml')}`,
    `--outputFile.json=${join(reportsDir, 'report.json')}`,
    ...extraArgs,
  ],
  watch: [...extraArgs],
  ui: ['--ui', ...extraArgs],
}

function presetsFor(mode) {
  switch (mode) {
    case 'module': {
      const moduleName = extraArgs[0]
      const valid = scanModules().map((m) => m.name)
      if (!moduleName || !valid.includes(moduleName)) {
        console.error(`未知模块: ${moduleName}`)
        console.error(`可用: ${valid.join(', ')}`)
        process.exit(1)
      }
      return ['run', `tests/${moduleName}`, ...extraArgs.slice(1)]
    }
    case 'prio': {
      const prio = extraArgs[0]
      if (!['p0', 'p1'].includes(prio)) {
        console.error(`未知优先级: ${prio}（可用: p0, p1）`)
        process.exit(1)
      }
      const projects = listProjects().filter((p) => p.endsWith(`/${prio}`))
      return ['run', ...projects.flatMap((p) => ['--project', p]), ...extraArgs.slice(1)]
    }
    default:
      if (!(mode in presets)) {
        console.error(`未知模式: ${mode}`)
        console.error(`可用: ${Object.keys(presets).join(', ')}, module, prio`)
        process.exit(1)
      }
      return presets[mode]
  }
}

const args = presetsFor(mode)
console.log(`> vitest ${args.join(' ')}`)

const result = spawnSync('npx', ['vitest', ...args], {
  cwd: frontendRoot,
  stdio: 'inherit',
  shell: true,
})

if (['junit', 'json', 'all'].includes(mode)) {
  console.log(`\n报告目录: ${reportsDir}`)
}

process.exit(result.status ?? 1)
