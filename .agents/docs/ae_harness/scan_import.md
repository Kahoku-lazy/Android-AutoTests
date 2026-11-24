# 依赖图可视化
```bash
pip install pydeps  # 安装
```

```bash
pydeps engines --show-deps --no-output    
```       


## 架构契约守卫

依赖方向统一由仓库根的 `.linting` 定义，执行器是 `utils/linting`（门禁名 `linting`）：

```bash
python -m utils.linting          # 全量检查（19 个模块 / 16 条红线）
python -m utils.linting --json   # 机器可读输出
```

`.linting` 里与 engines 相关的片段：

```toml
root_packages = ["engines", "backend"]
include_external_packages = true

[[forbid]]
slug = "engines-purity"
name = "engines must not import django or backend apps"
source = ["engines"]
forbidden = ["django", "backend.apps", "apps"]
allow_indirect_imports = true
```

口径：

- `engines` 禁止 import `django` / `backend.apps` / 旧的 `apps` 包；
- 底座引擎（`device` / `vision` / `uart_log`）禁止反向依赖 `backend_bridge` / `ae_harness`；
- `ae_harness` 禁止依赖其他引擎包与根 `utils`；
- 合同的完整清单见 `.linting`，规则与验收方法见 `.agents/lint/linting.md`。

`tach` / `import-linter` 已不再安装；需要第三方工具复跑时，用
`python -m utils.linting export --out-dir <目录>` 按 `.linting` 重新生成它们各自的配置。
