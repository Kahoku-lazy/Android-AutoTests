## Why

D0 复检的最后一批问题：**注释失真、格式不合规、空转代码、渲染器不分环境**。逐条都有实测证据：

| # | 位置 | 现象 | 证据 |
|---|------|------|------|
| 8 | `config/settings.py:87` | 注释写「`# Django Apps (8)`」，其下实际列出 **11** 个 App | 逐行计数 |
| 9 | `config/settings.py:156` / `:160` | `:156` 写「调用方（`DeviceSession`）经 `engines.device.registry` 取引擎」，而 `DeviceSession` 已于 2026-09-03 归档变更 `flatten-device-session` 中删除；`:160` 写「调用方（`engine_adapter`）」，真实消费点是 `apps/ai_assistant/views_drf.py:795 get_ai_engine(settings.AI_ENGINE).run(req)` | 全仓 `DeviceSession` 仅剩注释；消费点 grep |
| 10 | `config/settings.py:286-288` | `ANDROID_ADB_SERVER_ADDRESS` 从 `os.environ` 读出后**原值写回** `os.environ` → 空转代码；该设置符号**无任何外部消费方** | 符号消费扫描：外部消费 0（`.env` 已由 `load_dotenv()` 注入，环境变量本身也已在位） |
| 11 | `config/settings.py:329` | `JAZZMIN_SETTINGS["icons"]` 内该项缩进错位 | `ruff format --check config/settings.py` → **1 file would be reformatted**；`--diff` 只含这一行 |
| 12 | `config/settings.py:255-258` | `DEFAULT_RENDERER_CLASSES` 无条件下带 `BrowsableAPIRenderer` → 生产也给已登录用户暴露 HTML 可浏览 API | 配置原文（未按 `DEBUG` 分档） |

## What Changes

1. **#8** 注释改为与列表一致的数目（并按「11 个 App，其中 test_runner 仅卸表迁移」写清现状）。
2. **#9** 两处注释改为代码真相：设备引擎消费方改为「上层经 `engines.device.registry` 工厂」；AI 引擎消费方指向 `apps/ai_assistant/views_drf.py`（`get_ai_engine(settings.AI_ENGINE)`）。
3. **#10** 删除空转的 `ANDROID_ADB_SERVER_ADDRESS` 读-写-回 三行（其能力已由 `.env` 注入 `os.environ` 实现），并在 `.env.example` 补上该键说明（避免能力被「删代码」顺手删掉而不留痕）。
4. **#11** 运行 `ruff format config/settings.py`，使 `ruff format --check` 通过（预期只改这一行）。
5. **#12** `BrowsableAPIRenderer` 按 `DEBUG` 分档（生产不注册），并加注释说明理由。

## 关联文档

- 取证：`temps/scan_d0.py`（符号消费数）· `python -m ruff format --diff config/settings.py`
- 代码：`config/settings.py` · `.env.example`
- 前序：`openspec/changes/archive/2026-09-14-fix-arch00-device-runner-drift/`（同类「代码已变、注释未变」问题，那次修的是 ARCH-00 文档，本单修 D0 代码注释）
- 范围外登记：`API schema 告警`（另单）· `api_docs.py` 治理（`fix-d0-config-drift`）

## Capabilities

### New Capabilities

（无；`.openspec.yaml` 已声明 `skip_specs: true`）

### Modified Capabilities

（无）

## Impact

- **修改**：`config/settings.py` · `.env.example`
- **不影响**：运行时行为（#10/#11 无行为变化；#12 仅在生产去掉 HTML 渲染器，JSON 契约不变）、API、前端、DB
- **测试范围**：`python manage.py check` · `ruff check` + `ruff format --check config run.py` · `pytest -m "unit or integration"` · `openspec validate --strict`
