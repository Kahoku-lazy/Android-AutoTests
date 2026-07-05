# Functional Tests

按模块组织的功能测试用例与自动化脚本。由 `functional-testing` skill 驱动执行。

## 目录结构

```
tests/functional/
├── README.md
├── ai-assistant/
│   ├── test_spec.md       # 用例规格（13 条）
│   └── run_tests.py       # 自动化脚本
├── auth/
│   ├── test_spec.md       # 用例规格（7 条）
│   └── run_tests.py       # 自动化脚本
├── device-pool/
│   └── test_spec.md       # 用例规格
├── frontend/
│   └── check_modules.sh   # 前端模块加载检查
├── element-locator/
├── case-manager/
├── test-runner/
└── report-generator/
```

## 执行方式

```bash
# 全量执行
python tests/functional/ai-assistant/run_tests.py

# 单条用例
python tests/functional/ai-assistant/run_tests.py --case AI-DB-01

# 按层次
python tests/functional/ai-assistant/run_tests.py --layer DB

# 前端检查
bash tests/functional/frontend/check_modules.sh
```

## 新增模块测试

1. 创建 `tests/functional/{module}/` 目录
2. 编写 `test_spec.md`（按 `references/test-case-design.md` 规范）
3. 编写 `run_tests.py`（参考 `ai-assistant/run_tests.py` 模板）
4. 更新 `functional-testing` skill 的模块映射表

## 清理规则

测试脚本创建的测试数据必须清理：
- 测试数据 name 以 `TEST-` 开头
- 创建时间在 10 分钟内
- 清理前人工确认不会误删生产数据
