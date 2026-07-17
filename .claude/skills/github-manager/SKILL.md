---
name: github-manager
description: |
  GitHub 项目管理 — 代码提交、分支管理、PR 创建与审查、Issue 管理、发布流程。
  遵循 Conventional Commits 规范，auto-dev 完成后自动触发提交。
  Keywords: 提交, 推送, PR, Issue, 分支, 发布, 合并, commit, push, pull request, branch, release, github
  Trigger: 用户表达"提交/推送/发PR/创建Issue/发布/合并/切分支"等 Git/GitHub 操作时。
---

# GitHub Manager — 项目管理与代码发布

**目的**: 统一管理项目的 Git 工作流：提交规范、分支策略、PR 流程、Issue 跟踪、发布管理。

## 工作流

### 1. 代码提交

**触发**: auto-dev Phase 5 完成后 / 用户说"提交"

```
Step 1: 检查工作区状态
  git status → 确认所有变更是预期的

Step 2: 按 Conventional Commits 生成 commit message
  feat:     新功能
  fix:      Bug 修复
  refactor: 重构（不改变功能）
  docs:     文档变更
  chore:    构建/工具/依赖变更
  style:    格式化（不影响代码逻辑）
  test:     测试相关
  security: 安全修复

  格式: {type}({scope}): {描述}
  示例:
    feat(agent): 新增批量删除 Agent 功能
    fix(dashboard): 修复统计概览 loading 状态不重置
    refactor(adapter): 提取轮询公共方法 _poll_until()
    security(agent): 修复 user_id 未校验导致的越权访问

Step 3: git add + git commit + git push

Step 4: 输出提交摘要
```

### 2. 分支管理

**分支策略**:

```
master/main    ← 生产分支，只接受 PR 合并
  ├── develop  ← 开发分支
  │   ├── feat/{name}     ← 功能分支
  │   ├── fix/{name}      ← 修复分支
  │   └── refactor/{name} ← 重构分支
  └── hotfix/{name}       ← 紧急修复（从 main 切出）
```

**命令**:

| 操作 | 命令 |
|------|------|
| 创建功能分支 | `git checkout -b feat/{name}` |
| 切回 develop | `git checkout develop` |
| 合并分支 | `git merge feat/{name}` |
| 删除已合并分支 | `git branch -d feat/{name}` |
| 查看所有分支 | `git branch -a` |

### 3. PR 流程

```
Step 1: 确保当前分支已推送到远程
  git push origin {branch}

Step 2: 生成 PR 描述
  标题: Conventional Commits 格式
  正文:
    ## 变更摘要
    - 改了什么

    ## 涉及文件
    - path/to/file

    ## 审查结果
    - quality-gate 评分: XX/100
    - P0: N / P1: N / P2: N

    ## 测试结果
    - 编译: ✅
    - 静态分析: ✅
    - API 测试: ✅/⚠️跳过/❌
    - 端到端: ✅/⚠️跳过/❌

  (auto-dev 交付的 HTML 报告路径自动贴入 PR)

Step 3: 创建 PR
  gh pr create --title "..." --body "..." --base develop

Step 4: 请求审查
  gh pr review {pr_number} --request-reviewers {reviewer}
```

### 4. Issue 管理

**从需求创建 Issue**:

```
Step 1: 用 Phase -1 的需求提炼结果生成 Issue

  标题: {type}({module}): {简短描述}
  正文:
    ## 背景
    {用户反馈/需求来源}

    ## 涉及模块
    - {module}

    ## 预期行为
    {具体描述}

    ## 验收标准
    - [ ] {标准1}
    - [ ] {标准2}

  标签: module:{name} priority:{P0/P1/P2} type:{feat/fix/refactor}

Step 2: 创建
  gh issue create --title "..." --body "..." --label "..."
```

**从审查结果创建 Issue**:

```
quality-gate 或 code-health-check 发现的问题 → 自动生成 Issue:

  标题: fix({module}): {问题简述}
  正文:
    ## 来源
    quality-gate 报告: {report_path}

    ## 问题
    {问题描述 + 代码片段}

    ## 严重度
    P{0/1/2}

    ## 修复建议
    {具体方案}

  标签: quality-gate priority:{P0/P1/P2}
```

### 5. 发布流程

```
Step 1: 确认所有 PR 已合并到 develop
Step 2: 从 develop 创建 release 分支
  git checkout -b release/v{version} develop

Step 3: 更新版本号、生成 CHANGELOG

Step 4: 合并到 main
  git checkout main && git merge release/v{version}

Step 5: 打 tag
  git tag -a v{version} -m "Release v{version}"

Step 6: 推送
  git push origin main --tags
```

## 与 auto-dev 的衔接

```
auto-dev Phase 5 (交付)
  ↓
用户确认交付结果
  ↓
github-manager:
  ├── 生成 Conventional Commits message
  ├── git add + commit + push
  ├── 如果用户要求 → 创建 PR (附带审查+测试报告)
  └── 如果发现问题 → 创建 Issue (附带 quality-gate 结果)
```

## 命令速查

```bash
# 查看状态
git status

# 提交
git add {files}
git commit -m "{type}({scope}): {msg}"
git push origin {branch}

# PR
gh pr create --title "..." --body "..." --base develop
gh pr list
gh pr review {number} --approve

# Issue
gh issue create --title "..." --body "..." --label "..."
gh issue list --label "quality-gate"

# 分支
git checkout -b feat/{name}
git branch -d feat/{name}

# 发布
git tag -a v{version} -m "Release v{version}"
git push origin --tags
```
