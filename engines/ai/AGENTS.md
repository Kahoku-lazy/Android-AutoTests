# 平台 Agent 功能设计

> 涉及平台 AI助手 AgentScope 框架代码变动时 **必须** 阅读此文档

## 技术栈

1. Agent框架当前版本： AgentScope 2.0.7.post1


## AgentScope 开发文档

1. 参考文档路径： `dev_docs/项目笔记/AgentScope`


## 测试

>代码修改后先检查是否需要执行迁移指令： `python manage.py migrate ai_assistant`,

1. 模型测试指令文件：`apps/ai_assistant/management/commands/model_test.py`
``` bash
# 1. 规划模型：输入用户需求 → 输出 plans（目标/步骤/验收标准）
python manage.py model_test planner "启动 govee 应用并进入设备列表"

# 2. 执行模型：输入步骤 → 在设备上执行 → 输出结果（需设备）
python manage.py model_test executor "1. 确认 govee 包名 2. 启动 govee" --serial RF8N21MSW7A

# 3. 验收模型：输入验收标准 → 截图二次确认 → 输出 pass/fail + completed/failed
python manage.py model_test verifier "前台 package 应为 govee 包名" --serial RF8N21MSW7A

# 4. 测试模型：输入用户需求 → 输出结果（需设备）
python manage.py model_test full "启动 govee 应用并进入设备列表" --serial RF8N21MSW7A
```
