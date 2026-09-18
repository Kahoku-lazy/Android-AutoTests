## 1. 默认值收窄

- [x] 1.1 `config/settings.py:58`：`ALLOWED_HOSTS` 默认值改为 `"*" if DEBUG else "127.0.0.1,localhost"`，并写清「显式 `DJANGO_ALLOWED_HOSTS` 优先」
- [x] 1.2 `config/settings.py` CORS 块：`CORS_ALLOW_ALL_ORIGINS` 默认值改为 `"True" if DEBUG else "False"`，注释同步为「开发放开 / 生产默认关」
- [x] 1.3 接线 `CORS_ALLOWED_ORIGINS`（`os.environ.get("CORS_ALLOWED_ORIGINS", "")` → 去空项列表）

## 2. 模板与文档同步

- [x] 2.1 `.env.example`：新增 `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOWED_ORIGINS` 两键（含说明与默认值语义）
- [x] 2.2 `.env.example`：删除死键 `SCREENSHOT_INTERVAL` / `AGENTSCOPE_PORT`（含其注释行）
- [x] 2.3 `ARCH-00` §七「关键开关（环境变量）」：补 `DJANGO_ALLOWED_HOSTS` / `CORS_ALLOW_ALL_ORIGINS` / `CORS_ALLOWED_ORIGINS` 三行及其 DEBUG 分档默认值

## 3. 验证

- [x] 3.1 开发档位（`DJANGO_DEBUG=True`，即当前 `.env`）：`python manage.py check` 零 issues，且断言 `ALLOWED_HOSTS == ["*"]`、`CORS_ALLOW_ALL_ORIGINS is True`
- [x] 3.2 生产档位（`DJANGO_DEBUG=False` + `DJANGO_SECRET_KEY` 占位，不设其它开关）：断言 `ALLOWED_HOSTS == ["127.0.0.1","localhost"]`、`CORS_ALLOW_ALL_ORIGINS is False`、`CORS_ALLOWED_ORIGINS == []`
- [x] 3.3 显式覆盖仍优先：`DJANGO_ALLOWED_HOSTS=example.com,api.example.com` → 列表生效；`CORS_ALLOWED_ORIGINS=https://a.com, https://b.com` → 去空格后 2 项；`CORS_ALLOW_ALL_ORIGINS=True`（生产）→ `True`
- [x] 3.4 回归：`pytest -m "unit or integration"` → **1 failed, 65 passed, 46 deselected**；唯一失败 `tests/graybox/unit/test_case_manager_ids.py::test_next_case_id_increments_same_day`（`IntegrityError: NOT NULL constraint failed: cm_test_definitions.file_id`）为**既有失败**：本会话早前已用 `git stash push -- config/settings.py` 回退后复现同样错误，且本次再以生产档位（`DJANGO_DEBUG=False`）单跑该用例仍一模一样失败 → 与 ALLOWED_HOSTS/CORS 默认值无关（属 case_manager ID 生成域）。测试客户端 Host `testserver` 不受影响（Django `setup_test_environment()` 追加，源码实测）
- [x] 3.5 `ruff check config/` 通过
- [x] 3.6 `openspec validate fix-d0-fail-open-defaults --strict`
