## Why

导入 YAML 用例时，业务类型只能取 YAML 里写死的 `business` 字段，没写就一律落成「家电」。实际情况是按产品线定的：H6810（灯带）这一批 56 条用例的业务类型应该是「照明」，但 YAML 里没有该字段，于是每次同步都会把业务类型刷回家电——现在库里已经有 54 条错标成家电，只有 2 条被手工改成照明。

## What Changes

- 导入新增「默认业务类型」参数（`appliance` / `lighting` / `app`，缺省 `appliance`）：YAML 显式写了 `business` 时仍以 YAML 为准，没写时用这个默认值。
- 命令行 `import_case_yaml` 增加 `--business`；用例库网页导入弹窗增加「业务类型」下拉。
- 用 `--business lighting` 重跑 H6810 同步，把已入库的 56 条用例统一改成照明。

## 关联文档

- 无独立 PRD 编号：沿用 [PRD-平台总需求](../../dev_docs/ARCH_PRD/PRD-平台总需求.md) §四「文档式用例」的业务类型枚举（家电 / 照明 / APP），本次只让导入可以选择默认值。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `case-manager-yaml-sync`: 「导入保留执行提示与元数据」增加默认业务类型参数及其优先级规则。

## Impact

- **backend**：`case_manager/api_yaml.py`（解析与导入接受默认业务类型并校验）、`import_case_yaml` 命令新增 `--business`、`views_drf.import_yaml` 接受 `business_type`。
- **前端**：`case-manager` 的导入弹窗增加业务类型下拉，`api.ts` 类型补充返回字段无变化。
- **数据**：重跑 H6810 同步，项目内 56 条用例业务类型统一为 `lighting`。
- **测试**：新增默认业务类型、YAML 优先、非法取值三组用例。
