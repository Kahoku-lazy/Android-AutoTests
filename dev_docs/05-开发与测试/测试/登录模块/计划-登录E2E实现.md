# 登录 E2E Implementation Plan

> **For agentic workers:** 按任务顺序执行；每任务可独立验证。

**Goal:** 按 `设计-登录E2E测试.md` 落地 pytest-playwright 登录 E2E，与 API 共用 Allure，tag 区分 `api`/`e2e`。

**Architecture:** 前端补 `data-testid` → `tests/e2e/` 共享 helper → `tests/auth/e2e/` 用例；选择器只走 `selectors.py`。

**Tech Stack:** pytest-playwright、Allure、Vue data-testid、现有 auth API fixtures。

## Global Constraints

- Allure tags: E2E 必须含 `auth`, `e2e`, priority
- Feature=`认证模块`；Story=`登录E2E`/`注册E2E`/`多账号E2E`/`跨TabE2E`
- 服务不可达 → skip，不 fail
- 不写 Vitest 整页 mount

## Tasks

- [x] T1 前端 data-testid + 单账号可打开「添加账号」菜单
- [x] T2 `tests/e2e/` 共享层 + requirements
- [x] T3 `test_login_flow.py`
- [x] T4 `test_register_flow.py`
- [x] T5 `test_account_switch.py` + `test_cross_tab.py`
- [x] T6 case_manager `_login` 迁移 + README

## 验证

```
python -m pytest tests/auth/e2e/ -v -m e2e --browser chromium
→ 12 passed in ~75s (2026-08-12)
```
