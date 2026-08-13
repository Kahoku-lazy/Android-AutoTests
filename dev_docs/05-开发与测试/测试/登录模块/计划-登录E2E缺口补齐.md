# 登录 E2E 缺口补齐 Implementation Plan

> **Goal:** 按序补齐：Allure 步骤+失败截图 → Token 刷新 → 多账号登出 → 网络故障 → 取消记住/注册失败/Prompt

**Tech:** pytest-playwright、allure.step、page.screenshot、page.route

## Tasks

- [x] T1 `tests/e2e/conftest.py` 失败截图 hook；全部 E2E 用例加 `allure.step`
- [x] T2 `test_token_refresh.py`：伪造过期 access，业务请求触发 refresh
- [x] T3 多账号登出留人用例
- [x] T4 登录 API abort → 错误遮罩
- [x] T5 取消记住账号、注册重复用户、Prompt 可达
- [x] T6 重跑验证 + README

## 验证

```
python -m pytest tests/auth/e2e/ -v -m e2e --browser chromium
→ 19 passed in ~106s (2026-08-12)
```
