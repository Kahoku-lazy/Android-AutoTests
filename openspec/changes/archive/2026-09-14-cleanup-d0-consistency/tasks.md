## 1. 注释与文档一致性（#8 #9）

- [x] 1.1 `config/settings.py` 的 `# Django Apps (8)` → `# Django Apps（11 个；其中 test_runner 已下线，仅保留卸表迁移）`。验证：该旧文案残留 **0**
- [x] 1.2 设备引擎注释去掉 `DeviceSession`：改为「上层经 `engines.device.registry` 工厂（`open_engine` / `close_engine`）取引擎」+ 一句「设备交互无中间层（原 L2 会话层已于 2026-09-03 扁平化删除）」
- [x] 1.3 AI 引擎注释消费方改为 `apps/ai_assistant/views_drf.py`（`get_ai_engine(settings.AI_ENGINE)`）
- [x] 1.4 验证：`DeviceSession` 在 `config/settings.py` 残留 **0**；注释所述消费点用 grep 复核存在（`views_drf.py:795`）

## 2. 空转代码（#10）

- [x] 2.1 删除 `ANDROID_ADB_SERVER_ADDRESS` 的「读出 → 原值写回 `os.environ`」三行空转块（该键由 `.env` / 环境变量直接对 adb 与 uiautomator2 生效），改为一句说明保留可发现性
- [x] 2.2 `.env.example` 补 `ANDROID_ADB_SERVER_ADDRESS`（注释形式 + 用途：容器内连宿主机 ADB daemon，示例 `host.docker.internal:5037`）
- [x] 2.3 验证：`ANDROID_ADB_SERVER_ADDRESS` 在 `config/` `apps/` 下**无任何代码读写**（残留 0，仅 `.env.example` 注释）；`python manage.py check` 零 issues

## 3. 格式与渲染器（#11 #12）

- [x] 3.1 取证：修复前的 `ruff format --diff config/settings.py` 只含 `JAZZMIN_SETTINGS.icons` 一行缩进 —— 该项已由 `fix-d0-config-drift` 整文件格式化时一并修掉（属同文件副作用，该单 tasks 已登记）
- [x] 3.2 `python -m ruff format --check config run.py run_daphne.py manage.py` → **10 files already formatted**（全通过）
- [x] 3.3 `REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES`：`BrowsableAPIRenderer` 改为**仅 `DEBUG` 时注册**（解包写法 + 注释说明「生产不需要 HTML 可浏览 API，JSON 契约不变」）
- [x] 3.4 验证（两档位 + 两进程）：`temps/renderer_behavior_probe.py` 带 JWT 与 `Accept: text/html` 请求 `/api/devices/` —— **本地档位 `DEBUG=True` → `Content-Type: text/html`**（BrowsableAPIRenderer 生效）；**生产档位 `DEBUG=False` → `Content-Type: application/json`**（未注册 → DRF 406 Not Acceptable，JSON 渲染）。另加 `tests/graybox/unit/test_renderer_slot.py`（2 例）锁定契约：信封渲染器恒排第一、Browsable 的存在性与导入档位一致、其余四项渲染/鉴权配置未被带走

## 4. 关单验证

- [x] 4.1 `python manage.py check` → **0 issues**；`python -m ruff check config run.py` → 通过
- [x] 4.2 `python -m pytest -m "unit or integration"` → **1 failed, 96 passed, 46 deselected**（唯一失败为既有 `test_case_manager_ids::test_next_case_id_increments_same_day`，与本变更无关）
- [x] 4.3 `python tools/gen_arch_stats.py --check-boundaries` → **零违规**
- [x] 4.4 `openspec validate cleanup-d0-consistency --strict` → **Change is valid**

## 5. 遗留说明

- 本单未碰 `run.py` / `run_daphne.py` / `config/urls.py`（复检未发现问题）。
- `ANDROID_ADB_SERVER_ADDRESS` 的容器能力现仅由 `.env.example` 记录（代码零读写，符合「能力在环境变量层」的设计）；如需在部署手册中说明，属另单。
