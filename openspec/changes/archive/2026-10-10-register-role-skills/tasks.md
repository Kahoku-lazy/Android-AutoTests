## 1. 角色注册技能

- [x] 1.1 在 `BaseRole` 增加注册技能的方法：接受目录路径、已装载技能或技能加载器，相对路径按仓库根目录解析，默认扫描子目录，同一绝对目录重复注册时跳过，非法类型抛出含类型名的错误。验证：对 `engines/agents/skills/executor` 连续注册两次后只有一个加载器，且列出 `platform-tools-manual`；传入整数时抛出 `TypeError`。
- [x] 1.2 缺少 basic 组时拒绝注册。验证：阅读 `register_skills` 在找不到 basic 组时抛出 `RuntimeError`。

## 2. 执行角色技能名单

- [x] 2.1 `engines/agents` 的工具包组装支持按调用方选择是否扫描子目录，默认仍不扫描。验证：`ruff check engines/agents/tools/tool_wrapper.py` 通过，且未改 `engines/ai` 的同名函数。
- [x] 2.2 `EXECUTOR_SKILLS_NAMES` 解析为仓库绝对路径后挂进执行角色工具包，并扫描子目录。验证：按当前名单组装后可用技能为 `platform-tools-manual`；名单为空时可用技能为空。
- [x] 2.3 对改动文件跑格式与静态检查。验证：`ruff check` 与 `ruff format --check` 对 `engines/agents/role/base.py`、`engines/agents/tools_config.py`、`engines/agents/tools/tool_wrapper.py` 通过。
