# AGENTS.md

## 行为规范

1. **必须** 遵循`OpenSpec` 规范驱动流程的四步开发功能, 详细说明见`.agents\docs\github.md` 

2. **必须** 遵循结论先行原则，使用**麦肯锡电梯30秒理论**概括任务结果

3. **禁止带着不确定性的因素去行动**-- 发现有冲突的、有疑惑的、或者前后矛盾等问题必须要先提出来，解决后再执行；

4. **改规则必须先请示（硬约束）**-- 下列四类改动**必须先提交「变更申请」并经需求方确认，才能动代码与文档**，**不得先改后报**：
   - 修改任何 `AGENTS.md`（含各级子目录）的**红线 / 禁止事项 / 准入清单 / 依赖边界**条款；
   - **新增自定义异常类**（`engines/` 红线要求先在对应子 AGENTS 立项）；
   - 放宽或收紧**模块之间的依赖方向**（如 `engines/` 反向依赖 `apps.*`）；
   - 修改**钱与配额**相关口径（计费规则、token 统计口径、预算默认值）。

   「变更申请」至少写清四件事：**改什么、为什么必须改、影响面、怎么回退**。理由再充分也不能自己批——规则的意义就是在"看起来必须破例"时拦住 AI。

5. GitHub 版本提交前 **必须遵循** 项目制订的规则，规则文件路径 `.agents\docs\github.md`.

## 文档与工具说明

### 项目文档

1. 临时生成的代码与文件、临时生成的测试数据 **必须**放到 `temps/` 中，**禁止**在项目根目录下生成临时文件
2. 设计方案与报告，接口文档在 `dev_docs\DEV_TEST`目录中，文件名举例：XXX.md/XXX.html
3. 需求文档与架构文档放在 `dev_docs\ARCH_PRD` 中，文件名举例：ARCH-XXX.md/ARCH-XXX.html 或 PRD-XXX.md/PRD-XXX.html
4. 项目全局的Python代码编写规则文档在`.agents\docs\Python代码规则.md`


### 项目工具

1. 启动/停止/检查平台： `python run.py start / stop / status`
2. 本地质量门禁： `python run.py check` 
3. 测试统一入口： `python -m pytest -c tests/pytest.ini` — 测试资产全部在 `tests/` 下（`pytest.ini` / `test_settings.py` / 用例）。
