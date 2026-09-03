
## 简介

负责平台的测试工作，测试范围有接口、单元测试、集成测试、端到端测试，对应的测试信息详细阅读对应的模块。


## 代码规范

1. 所有的测试用例文件名称**必须**以 `test_` 开头。
2. 测试报告统一输出到 `reports/`目录


## 单元测试

> 运行指令： `python -m pytest tests/graybox/unit -v`

1. 单元测试用例路径： `tests/graybox/unit`，文件以 `test_` 开头。
2. 单元测试文档路径： `dev_docs/05-开发与测试/单元测试文档`

## 集成测试

> 运行指令： `python -m pytest tests/graybox/integration -v`

1. 集成测试用例路径： `tests/graybox/integration`，文件以 `test_` 开头。
2. 集成测试文档路径： `dev_docs/05-开发与测试/集成测试文档`

## 接口测试

> 运行指令： `python -m pytest tests/api -v`

1. 接口文档路径： `dev_docs/05-开发与测试/接口文档`
2. 接口测试用例路径： `tests/api`
3. 接口测试使用Jsonschema来断言响应结果，测试用例使用YAML编写，文件放在tests/api/case中。YAML用例要有测试标题，测试点
