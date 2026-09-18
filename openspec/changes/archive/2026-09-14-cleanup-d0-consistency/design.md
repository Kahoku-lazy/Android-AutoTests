## Context

- 5 项现象与证据见 proposal 表格；全部集中在 `config/settings.py`（D0 装配文件），互不耦合。
- #10 的判定依据：符号外部消费扫描 0 命中 + 值必然等于写回值（`.env` 由 `load_dotenv()` 注入 `os.environ`，真实环境变量本身已在 `os.environ`）→ 无任何场景产生差异。
- #12 的判定依据：`REST_FRAMEWORK.DEFAULT_RENDERER_CLASSES` 未做环境分档，而 `BrowsableAPIRenderer` 只服务浏览器调试。

## Goals / Non-Goals

**Goals:**

- 让 D0 装配文件的注释、格式与「实际部署行为」三者一致；清掉唯一的空转代码。

**Non-Goals:**

- 不改任何运行语义（除 #12 在生产去掉调试渲染器）；
- 不动 `run.py` / `run_daphne.py` / `config/urls.py`（本单未发现问题）；
- 不顺手重排 JAZZMIN/日志等无关区块（除 `ruff format` 必需的那一行）。

## Decisions

**D1 #10 选择删除而非保留加注释。**
理由：与项目既有的「零消费符号即删」治理一致（`remove-dead-d0-config` 先例）；保留一个 0 消费的符号会持续误导读者以为有代码在用它。为保住能力可发现性，在 `.env.example` 补该键说明。

**D2 #12 按 `DEBUG` 分档，而不是彻底删除 `BrowsableAPIRenderer`。**
理由：本地开发时可浏览 API 有实际价值；生产不需要。分档即可，避免牺牲开发体验。

**D3 #9 注释只写「代码真相 + 一处指路」，不复制实现细节。**
理由：`ARCH-00` 已在上一轮把该层拍平（L2 空置），代码注释保持一行指路即可，避免二次漂移。

**D4 #11 直接运行 `ruff format` 而非手工改缩进。**
理由：`--diff` 已确认改动面就是这一行，工具改比自己改更可靠；改完必须跑 `ruff format --check` 全量确认。

## Risks / Trade-offs

- [`ruff format` 顺带改动其它行] → 先跑 `--diff` 取证（本次已确认仅 1 行），改后以 `--check` 复核；若出现额外改动需回退并手工处理。
- [#10 删除后有人以为「不再支持容器内连 ADB」] → `.env.example` 保留该键说明，并在注释里写明「由 `.env`/环境变量直接对 uiautomator2 生效」。
- [#12 生产去掉 HTML 渲染器影响某些调试流程] → 只影响 `Accept: text/html` 的浏览器访问；JSON 客户端（前端/工具）不受影响；已在 Impact 登记。
