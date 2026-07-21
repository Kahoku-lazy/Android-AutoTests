# MCP & Skill 独立管理 — 设计规格

> 日期: 2026-07-21 | 模块: ai-assistant | 级别: 🟡 增量

## 概述

每个智能体独立管理 MCP 服务和 Skill，替代现有混在「工具」中的表单模式。MCP 用纯 JSON 配置，Skill 通过文件夹上传。两者都以卡片形式展示。

---

## 1. 数据模型

复用已有 `ai_tools` 表（`AITool` Model），`tool_type` 字段区分：

| tool_type | config_json 结构 |
|-----------|-----------------|
| `mcp` | `{"transport":"stdio","command":"npx","args":["-y","..."],"env":{},"url":"",...}` |
| `skill` | `{"dir_path":"data/skills/{agent_id}/{skill_name}/","file_count":12,"size_bytes":204800,"features":"Bash, Read, Write, 3 scripts"}` |

### MCP config_json 标准格式

```json
{
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@modelcontextprotocol/server-github"],
  "cwd": "",
  "env": {"GITHUB_TOKEN": "xxx"},
  "url": "",
  "headers": {},
  "client_type": "stateful"
}
```

- `transport`: `stdio` | `sse` | `streamable_http`
- stdio 模式：必填 `command`，可选 `args`/`cwd`/`env`
- 远程模式：必填 `url`，可选 `headers`/`client_type`

### Skill config_json 结构

```json
{
  "dir_path": "data/skills/5/my-skill/",
  "original_name": "my-skill",
  "file_count": 12,
  "size_bytes": 204800,
  "features": "Bash, Read, Write, 3 tools detected",
  "uploaded_at": "2026-07-21 15:30:00"
}
```

### 文件存储

```
data/skills/{agent_id}/{skill_name}/
├── *.md, *.py, *.sh, ... （原始文件）
└── _manifest.json          （自动生成的清单）
```

---

## 2. API 设计

### 2.1 列出 Agent 的所有 MCP + Skill

```
GET /api/ai/agents/{id}/tools
```

响应：
```json
{
  "ok": true,
  "data": {
    "mcp": [{ "id": 1, "name": "github", "tool_type": "mcp", "config_json": {...}, "enabled": true }],
    "skills": [{ "id": 2, "name": "my-skill", "tool_type": "skill", "config_json": {...}, "enabled": true }]
  }
}
```

### 2.2 添加/更新 MCP（JSON 配置）

```
POST /api/ai/agents/{id}/tools/mcp/save
```

Body:
```json
{
  "name": "github",
  "config_json": "{\"transport\":\"stdio\",\"command\":\"npx\",\"args\":[\"-y\",\"@mcp/server-github\"]}"
}
```

- 若 `name` 已存在 → 更新 config_json
- 若 `name` 不存在 → 新建 AITool 记录

### 2.3 测试 MCP 连通性

```
POST /api/ai/agents/{id}/tools/mcp/test
```

Body:
```json
{
  "transport": "stdio",
  "command": "npx",
  "args": ["-y", "@mcp/server-github"],
  "url": ""
}
```

后端逻辑：
- stdio：`subprocess.run([command, ...args], capture_output=True, timeout=15)` → 成功/失败
- sse/http：`httpx.get(url, timeout=10)` → HTTP 200 / 错误

响应：
```json
{ "ok": true, "connected": true, "detail": "MCP server responded successfully" }
// 或
{ "ok": true, "connected": false, "detail": "Connection refused: ..." }
```

### 2.4 上传 Skill 文件夹

```
POST /api/ai/agents/{id}/tools/skill/upload
Content-Type: multipart/form-data

files: [file1, file2, ...]   （webkitdirectory 多文件上传）
name: "my-skill"             （skill 名称，取文件夹名）
```

后端逻辑：
1. 验证文件类型（允许 .md/.py/.sh/.js/.json/.yaml/.yml/.txt）
2. 创建 `data/skills/{agent_id}/{name}/` 目录
3. 写入所有文件（保留相对路径结构，防 `..` 穿越）
4. 扫描文件 → 自动检测 features：
   - 统计文件类型分布
   - 检查是否有 CLI 入口脚本（有 `#!/` shebang 或 `if __name__`）
   - 生成 features 摘要，如 `"Python scripts, Shell scripts, 3 tools"`
5. 写入 `_manifest.json`
6. 创建 AITool 记录（tool_type=skill）
7. 返回 skill 卡片信息

响应：
```json
{
  "ok": true,
  "data": {
    "id": 3,
    "name": "my-skill",
    "tool_type": "skill",
    "config_json": {
      "dir_path": "data/skills/5/my-skill/",
      "file_count": 12,
      "size_bytes": 204800,
      "features": "Python: 5 files, Shell: 2 files, Markdown: 3 files, 3 CLI tools"
    },
    "enabled": true,
    "created_at": "2026-07-21T15:30:00"
  }
}
```

### 2.5 删除 Tool（MCP 或 Skill）

```
DELETE /api/ai/agents/{id}/tools/{tool_id}
```

- MCP：仅删除 DB 记录
- Skill：删除 DB 记录 + 清理 `data/skills/{agent_id}/{name}/` 目录

### 2.6 启用/禁用 Tool

```
POST /api/ai/agents/{id}/tools/{tool_id}/toggle
```

Body:
```json
{ "enabled": true }
```

---

## 3. 前端设计

### 3.1 MCP 卡片区

位置：AgentDetail.vue Step 4「记忆与工具」内

- **添加按钮**："+ 添加 MCP 服务器" → 弹出 Modal
- **Modal 内容**：
  - `el-input`：MCP 名称
  - `el-input` type="textarea"：JSON 配置（代码编辑器风格，等宽字体）
  - 格式校验：保存前 `try { JSON.parse() }` 校验
- **卡片展示**（保存后）：
  ```
  ┌─────────────────────────────────────┐
  │ 📡 github  [stdio]  ✅ 已连接       │
  │ npx -y @mcp/server-github           │
  │ [测试连通] [编辑] [启用/禁用] [删除]  │
  └─────────────────────────────────────┘
  ```
- **测试连通**：按钮点击 → POST test → 卡片右上角短暂显示绿色 ✓ 或红色 ✗
- **编辑**：打开 Modal 预填 JSON，修改后保存
- **颜色**：卡片用 `app-teal` 色调

### 3.2 Skill 卡片区

位置：MCP 卡片区下方

- **上传按钮**："+ 上传 Skill" → 触发 `<input webkitdirectory>`
- **上传进度**：上传中显示进度条
- **卡片展示**（上传后）：
  ```
  ┌─────────────────────────────────────┐
  │ 📦 my-skill                  12 文件│
  │ Python: 5 · Shell: 2 · MD: 3       │
  │ 200 KB · 2026-07-21 15:30          │
  │ [删除]                              │
  └─────────────────────────────────────┘
  ```
- **颜色**：卡片用 `purple` 色调

### 3.3 移除旧表单

- 移除现有 MCP 表单字段（transport/command/args/url/env/headers 等逐项编辑）
- 移除现有 `addTool()` / `removeTool()` / `syncToolConfig()` 函数
- 移除 `parseToolFromApi()` 的复杂映射逻辑
- 保留平台工具选择、工作区 Skills 开关、知识库文档范围（它们不在本次改动范围）

---

## 4. 实现范围

### 后端改动

| 文件 | 操作 |
|------|------|
| `apps/ai_assistant/views/tool_views.py` | 新增 `list_agent_tools` `save_mcp` `test_mcp` `upload_skill` `delete_tool` `toggle_tool` |
| `apps/ai_assistant/urls.py` | 注册 6 个新端点 |
| `apps/ai_assistant/views/__init__.py` | 导出新视图 |
| `apps/ai_assistant/views/agent_views.py` | create_agent/update_agent 中 tools 处理适配（仅 MCP JSON） |

### 前端改动

| 文件 | 操作 |
|------|------|
| `AgentDetail.vue` | Step 4 重构：MCP 卡片区 + Skill 卡片区替换旧表单 |
| `api.js` | 新增 `saveMcp` `testMcp` `uploadSkill` `deleteTool` `toggleTool` |

### 不改动

- `AITool` / `AIAgent` Model（字段已齐全）
- 平台工具选择、Skills 开关、知识库文档（独立功能）
- Agent 创建/编辑的 5 步流程结构
- 对话/消息/SSE 流

---

## 5. 安全约束

- Skill 文件名过滤 `..` `/` `\` 防路径穿越
- Skill 总大小限制 50MB
- MCP JSON 中的 `env` 字段不包含敏感信息（遵循安全规则）
- 删除 Skill 时同步清理文件（避免残留）
- 所有端点通过 `check_agent_owner` 验证 Agent 归属权

---

## 6. 验收条件

1. 新建/编辑 Agent → Step 4 可见 MCP 卡片区和 Skill 卡片区（替代旧表单）
2. MCP 卡片区：点击添加 → Modal 填名称 + JSON → 保存 → 卡片出现
3. MCP 卡片：点击测试连通 → 显示连接结果（绿✓/红✗）
4. Skill 卡片区：选择文件夹上传 → 显示进度 → 卡片出现（名称/大小/功能/时间）
5. Skill 功能自动检测：features 字段准确反映文件内容
6. 每个 Agent 的 MCP/Skill 独立（Agent A 的 MCP 不在 Agent B 中可见）
7. 删除 Skill 同时清理 `data/skills/` 下文件
