---
name: write-ops-catch-must-report
description: 写操作 catch 必须报错，禁止静默吞错
metadata: 
  node_type: memory
  type: project
  originSessionId: b05814f4-5f5d-4bc7-9238-26a81baf151e
---

前端写操作（delete/create/update）的 catch 块**必须**调用 `ElMessage.error()` 或 `formatApiError()`，禁止 `catch (_) {}` 静默吞错。

```javascript
// ❌ 禁止
try { await client.post(`/api/xx/${id}/delete`) } catch (_) {}

// ✅ 正确
try {
  await client.post(`/api/xx/${id}/delete`)
  items.value = items.value.filter(i => i.id !== id)
} catch (e) {
  ElMessage.error(formatApiError(e, '删除失败'))
}
```

读操作（list/get/query）的 catch 可以静默，但必须保证数据为空态。

**Why:** 历史高频问题（3 次 ⚠️）：删除/创建后数据"自动恢复"、操作失败无提示。根因都是写操作静默吞错。前端写操作是用户唯一能感知到的反馈渠道。

**How to apply:** 每次改完代码后搜索自查：
```bash
grep -rn "catch\s*(_\|)\s*{" frontend/src/modules/ --include="*.vue" --include="*.js"
```
命中后区分读/写操作，写操作补 `ElMessage.error()`。详见 [[frontend-rules]] §写操作静默吞错检查。
