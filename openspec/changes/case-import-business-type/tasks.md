## 1. 导入默认业务类型

- [x] 1.1 `api_yaml.parse_yaml_text(text, *, default_business_type="appliance")` 与 `import_yaml_text(..., default_business_type=...)`：YAML 有 `business` 时以 YAML 为准，否则用默认值；取值不在枚举内时抛 `ValueError` 并列出可选值；验证：`tests/graybox/unit/test_case_yaml_import.py` 新增 3 条（默认值生效、YAML 优先、非法取值），共 13 条全绿。
- [x] 1.2 命令行 `import_case_yaml` 增加 `--business`（choices：appliance / lighting / app，默认 appliance），结论行打印业务类型；验证：以 `--business lighting` 实跑成功，`--business bad` 由 argparse 拒绝。
- [x] 1.3 网页导入接口与弹窗支持业务类型：`POST /api/cases/import-yaml/` 接受 `business_type`，弹窗加业务类型单选与说明；验证：`tests/api/test_case_yaml_import_api.py` 新增 2 条（指定值生效、非法值 400），共 8 条全绿；弹窗截图核对。

## 2. 数据修正与收口

- [x] 2.1 以 `--business lighting` 重跑 H6810 同步，把 56 条用例业务类型统一为照明；验证：项目 #19 共 56 条，`business_type` 分布为 `{'lighting': 56}`。
- [x] 2.2 门禁：`python run.py check` 阻塞项 **23/23 通过**；`tests/api/test_case_yaml_import_api.py` + `tests/graybox/{unit,integration}` 相关 32 条全绿。
