# 贡献指南（Contributing Guide）

欢迎贡献 Android-AutoTests！无论是报 Bug、提功能建议、改代码还是补文档，都请先读完本文。

> 阅读顺序建议：[README](README.md)（平台是什么）→ 本文（怎么贡献）→ [AGENTS.md](AGENTS.md)（深度开发规则）。
>  English readers: see [README.en.md](README.en.md) for a project overview; this guide is currently Chinese-first.

## 贡献渠道

| 想做什么 | 去哪里 |
| --- | --- |
| 报 Bug | [Issue（Bug 模板）](https://github.com/Kahoku-lazy/Android-AutoTests/issues/new/choose) |
| 提功能建议 | Issue（功能模板）或 [Discussions](https://github.com/Kahoku-lazy/Android-AutoTests/discussions) |
| 使用问答 / 想法交流 | [Discussions](https://github.com/Kahoku-lazy/Android-AutoTests/discussions) |
| 报告安全漏洞 | **私密渠道**，见 [SECURITY.md](SECURITY.md)，勿公开提 Issue |
| 代码 / 文档 PR | 按下方开发流程 |

## 环境准备

- Python 3.13、Node.js（含 npm）、Git；MySQL（默认）或 SQLite
- 模型密钥：复制 `.env.example` 为 `.env` 并填写（`DEEPSEEK_API_KEY` / `DASHSCOPE_API_KEY` / `OPENAI_API_KEY`，按需）

```bash
git clone https://github.com/Kahoku-lazy/Android-AutoTests.git   # 外部贡献者请先 fork，再 clone 你的 fork
cd Android-AutoTests
pip install -r requirements.txt
cd frontend && npm install && cd ..
python run.py setup      # 首次/换机：安装项目内 adb（唯一会联网的命令）
python run.py start      # 启动平台；status 查看状态；stop 停止
```

## 开发流程（PR 是唯一入口）

仓库单主干 **`Kahoku`**，已启用分支保护：**禁止直推主干、禁止强推，管理员同样生效**。所有改动必须走 PR：

1. **开分支**：从最新 `Kahoku` 拉特性分支，如 `feat/xxx`、`fix/xxx`（外部贡献者在自己的 fork 上操作）。
2. **大功能先立项**：涉及新功能 / 结构性改动，先走 OpenSpec 规范驱动流程（`openspec/changes/` 下 explore → propose → apply → archive），小修复可直接改。
3. **本地门禁**：提交前必须跑 `python run.py check`（与 CI 同一批检查），阻塞项失败先修复。
4. **逐文件暂存**：`git add <具体文件>`，**禁止 `git add -A`**（历史教训：曾把未申报的改动一起带进提交）。
5. **提交规范**：Conventional Commits，`{type}({scope}): {描述}`；type 取 `feat` / `fix` / `refactor` / `docs` / `test` / `chore` / `style` / `security`；一次提交只做一件事。
6. **提 PR**：`gh pr create --base Kahoku`（或网页端），按 PR 模板填写。
7. **CI 全绿才可合并**：`ci-phase1.yml` 的 `python` 与 `frontend` 两个 job 是唯一质量闸门。
8. **首次贡献者注意**：来自 fork 的 PR 需要维护者在 Actions 页批准一次才会运行 CI，请耐心等待。

## 硬性规则（摘要，全文见 AGENTS.md）

- **依赖方向**：`backend →（注入）→ engines`；`engines/` **禁止** `import apps.*` / `django.*`。
- **注释规范**：模块 / 类 / 函数必须有符合模板的 docstring（含 Args / Returns / Raises）。
- **密钥卫生**：严禁提交真实密钥；密钥只从 `.env` 读取，CI 有凭据门禁。
- **临时文件**：一律放 `temps/`，不要污染项目根目录。
- **测试资产**：全部在 `tests/` 下，统一入口 `python -m pytest -c tests/pytest.ini`。
- **文档位置**：设计方案 / 报告在 `dev_docs/DEV_TEST`，需求 / 架构在 `dev_docs/ARCH_PRD`。

## 行为准则

参与本项目即表示同意遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

感谢你的贡献！🐾