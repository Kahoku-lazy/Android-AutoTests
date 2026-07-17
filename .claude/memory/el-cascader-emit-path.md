---
name: el-cascader-emit-path
description: "el-cascader 默认 emitPath: true 导致 v-model 类型不匹配"
metadata: 
  node_type: memory
  type: project
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

Element Plus `el-cascader` 默认 `emitPath: true`，v-model 绑定的是**路径数组** `[1, 5]`，而后端通常期望单个叶子节点 ID `5`。

必须显式设置 `:props="{ checkStrictly: true, emitPath: false, value: 'value', label: 'label' }"`。

**Why:** 历史出现 1 次（🔴 严重）：case-manager CaseEditor.vue 中 el-cascader 保存时类型不匹配，编辑回显时级联选择器不识别单个 ID，两边静默失败，只有功能测试能暴露。

**How to apply:** 写完含 el-cascader 的代码后自查：
```bash
grep -rn 'el-cascader' frontend/src/modules/ | grep -v 'emitPath'
```
命中说明有 cascader 没设 emitPath。Phase 4 用 curl 做 POST+GET 往返验证 v-model 类型与后端字段类型一致。详见 [[frontend-rules]] §Element Plus 默认值陷阱。
