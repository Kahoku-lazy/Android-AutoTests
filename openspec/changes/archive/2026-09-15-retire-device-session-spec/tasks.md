## 1. 复核（已完成）

- [x] 1.1 读 `openspec/specs/device-session/spec.md`：4 条需求（租用互斥 / EXCLUSIVE 业务锁前置 / per-serial 并发隔离 / 错误语义转换）全部描述 `DeviceSession` 协议
- [x] 1.2 实测零消费：`grep DeviceSession|LeaseConflict|LeaseMode|LeaseError|DEVICE_SESSION_ENABLED` 在 `apps/` `engines/` `tests/` **无代码命中**（仅 2 处 docstring + ARCH-00 历史叙述）
- [x] 1.3 确认删除出处：`ARCH-00` 行 53 / 369 / 504 / 506 / v3.3 变更行均记载 `flatten-device-session`（2026-09-03）删除该层、收敛到 `DeviceLock` + 引擎工厂
- [x] 1.4 确认 `ARCH-00` 行 36 与行 532 把 spec 处置挂为「退役另案」→ 本单即该案
- [x] 1.5 确认 `openspec spec` 子命令**无 remove/delete**，故退役须经 `REMOVED Requirements` delta 完成
- [x] 1.6 读 `openspec instructions specs` 确认 delta 格式：`## REMOVED Requirements` + **Reason** + **Migration**

## 2. 修改

- [x] 2.1 新增 `specs/device-session/spec.md` delta：4 条 REMOVED，各附 Reason / Migration
- [x] 2.2 `ARCH-00` 行 36：`spec 退役另案` → `spec 已于 2026-09-15 退役`
- [x] 2.3 `ARCH-00` 行 530-532 目录树：删掉 `├── engine-protocol/spec.md` / `└── device-session/spec.md` 两行的旧写法，改为只剩 `└── engine-protocol/spec.md`（与归档后的实际文件树一致）
- [x] 2.4 `engines/device/base.py` docstring：`上层经 DeviceSession（L2）消费本协议` → `上层经引擎工厂（open_engine / close_engine）消费本协议`
- [x] 2.5 `engines/device/registry.py` docstring：`引擎名由调用方（未来 DeviceSession）从 settings 解析后传入` → `引擎名由调用方（apps/device_pool）从 settings 解析后传入`

## 3. 验证

- [x] 3.1 `openspec validate "retire-device-session-spec" --strict` → **有效**
- [x] 3.2 **归档时被工具拦下一次（有价值）**：首次 `openspec archive` 返回 `archive_spec_validation_failed` ——
      *"This change removes the last requirement 'device-session' has. To retire the capability and delete its spec, add `retire_capabilities: true` to the change's .openspec.yaml"*；**未改动任何文件**（fail-closed）。
      按提示加 `retire_capabilities: true` 后归档成功，输出
      `device-session - capability retired; deleted the main spec ... at openspec/specs/device-session/spec.md. Its section(s) went with it: Purpose.`
- [x] 3.3 归档后终态复核：`openspec spec list` **不再含 `device-session`**；`openspec/specs/device-session/` 目录**已删除**；`openspec validate --specs` 全部 ✓（`overview` 那条 Purpose 占位告警与本次无关 —— 仓库内并无 `openspec/specs/overview` 目录，属既有告警）
- [x] 3.4 `python manage.py check` → 0 issues；`makemigrations --check` → `No changes detected`；`ruff check .` → All checks passed；`ruff format --check .` → 248 files already formatted
- [x] 3.5 `pytest tests/graybox/unit tests/arch -q` → **109 passed**（零回归，印证「纯契约 / 文档」定性）；`--check-boundaries` → 零违规

## 4. 两个必须写下的注意点

1. **`retire_capabilities` 是「移除最后一条需求」的必需开关**：不加就归档失败。这是 OpenSpec 的防误删设计 —— 只有显式声明才允许删掉整个 capability 的 spec。首次被拦时工具**没有改动任何文件**（fail-closed），可放心重试。
2. **`openspec/` 在 `.gitignore:193`**（注释：`OpenSpec 本地工作流（自动生成，不入库）`）。因此：
   - 本次 spec 退役**不在 git diff 里**（`git ls-files openspec` = 0），**回滚不能靠 `git checkout`**；
   - 回滚办法：把 `openspec/changes/archive/2026-09-15-retire-device-session-spec/specs/device-session/spec.md` 里的 4 条原需求写回 `openspec/specs/device-session/spec.md`（并去掉 `.openspec.yaml` 之外无影响）；
   - 文档与注释侧的改动（`ARCH-00` · 两个引擎 py）**在 git 里**，可 `git checkout` 还原。

## 5. 续做

1. 是否把「设备租用 / 设备锁」升格为正式 spec（现由 `ARCH-00` §4.4 承担）—— 独立裁决
2. `ARCH-00` 行 36 仍把 `device-session` 与 `engine-protocol` 并列在「正式契约」句里（已注明「已于 2026-09-15 退役」）；下次大改可整体删掉该并列
