# Database — Android-AutoTests

> 获取表结构：Read 各 App 的 `models.py`，这是唯一真相源。级联规则去 models.py 看 `on_delete` 确认。

## 写操作铁律

```
前端 HTTP → Django View → api.py → ORM
AgentScope → Tool.call() → api.py → run_sync() → ORM
Django Admin → ORM（仅管理员）
```

**所有写操作必须通过 `api.py` 函数，禁止直接 ORM INSERT/UPDATE/DELETE。** 读操作放开：同模块和跨模块都可直接 ORM 查询。

## 设备状态

`(new) → ONLINE ⇄ BUSY → OFFLINE / DISCONNECTED → ONLINE`

## 表前缀

`dp_` `el_` `cm_` `tr_` `rg_` `ai_` `wf_` `ev_`
