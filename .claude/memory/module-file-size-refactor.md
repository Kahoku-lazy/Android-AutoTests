---
name: module-file-size-refactor
description: 单文件超限重构模式 — AI 遇到需要拆分的超大文件时的标准做法（从 AI 助手模块化重构方案提炼）
metadata: 
  node_type: memory
  type: project
  originSessionId: f1410bd3-1472-4dd6-9403-e8f5d0bdfa1f
---

## 文件超限拆分模式

### 触发条件

当文件超过以下上限时，必须拆分而非继续堆代码：

| 文件类型 | 上限 | 当前违规示例 |
|---------|:--:|------|
| `.vue` 组件 | 500 行 | `ChatView.vue` 2800 行、`StepEditor.vue` 949 行 |
| `.py` 模块 | 400 行 | `views.py` 1200 行、`prd_tools.py` 701 行 |

### Django views 拆分模式

`views.py` → `views/` 目录，按子域拆分：
```
apps/{name}/
├── views/
│   ├── __init__.py          # 汇总导出
│   ├── {domain1}_views.py
│   ├── {domain2}_views.py
│   └── ...
└── urls.py                  # 路由指向 views/ 子模块
```

**原则**：按 URL 前缀分组（如 auth/agent/conversation/file），而非按函数类型。

### Vue 组件拆分模式

大组件 → 1 主框架 + N 子组件 + M composables：
```
modules/{name}/
├── MainView.vue            # 主框架 ~300 行：布局 + 路由
├── components/
│   ├── SubComponent1.vue   # 每个 < 400 行
│   └── SubComponentN.vue
└── composables/
    ├── useFeature1.js      # 每个 < 200 行
    └── useFeatureN.js
```

**拆分原则**：
- 子组件：模板中 > 150 行的语义区域
- Composable：script 中 > 200 行的独立逻辑
- CSS：> 120 行外置为 `.css` 文件
- 常量：> 50 行纯数据定义外提到 `constants.js`

### 代码去重模式

| 情况 | 做法 |
|------|------|
| 同一映射在 N 处重复定义 | 抽取为独立模块（如 `provider_registry.py`） |
| 多个文件各自实现相同的工具函数 | 归入 `shared/` 目录 |
| 写了但从未被使用的模块 | 删除或移归档（如 `permissions.py`、`serializers.py`） |

**How to apply:** 新增功能前先检查目标文件当前行数。若接近上限，先执行拆分（Phase 1），再添加新功能（Phase 2）。
