"""Simulate AI conversation: 帮我写登录功能的业务测试用例"""
import os, asyncio, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from agentscope_service.tools.case_tools import (
    GetDirectoryTreeTool, ListAllCasesTool, SaveStorageCaseTool,
)
from agentscope_service.tools.task_tools import (
    CreateCaseGenTaskTool, UpdateCaseGenTaskTool,
)
from agentscope_service.tools.tool_context import ToolContext

async def simulate():
    ctx = ToolContext(user_id='1', agent_id='2', session_id='sim-test')
    print('=' * 60)
    print('模拟对话: "帮我写登录功能的业务测试用例"')
    print('=' * 60)

    # Step 1
    print('\n[Step 1] 识别类型: 功能/业务 → storage')

    # Step 2: 创建任务卡片
    print('\n[Step 2] 创建任务卡片')
    task = CreateCaseGenTaskTool(); task._ctx = ctx
    r = await task.call(title='登录功能业务测试用例', case_type='storage', total_count=8)
    text = r.content[0].text
    run_id = [w for w in text.split() if w.startswith('case-gen-')][0]
    print(f'  {text[:200]}')

    # Step 3a: 查看目录树
    print('\n[Step 3a] get_directory_tree("storage")')
    tree_tool = GetDirectoryTreeTool(); tree_tool._ctx = ctx
    r = await tree_tool.call(case_type='storage')
    tree_text = r.content[0].text[:400]
    print(f'  {tree_text}')

    # Step 3b: 查看已有用例
    print('\n[Step 3b] list_all_cases("storage")')
    list_tool = ListAllCasesTool(); list_tool._ctx = ctx
    r = await list_tool.call(case_type='storage', limit=10)
    print(f'  {r.content[0].text[:300]}')

    # Step 3c: 测试点分解
    print('\n[Step 3c] 五法测试点分解')
    methods = {
        '场景流法': 3, '等价类边界值': 3, '判定表': 3, '错误推测法': 2,
    }
    total = sum(methods.values())
    for m, n in methods.items():
        print(f'  {m}: {n} 个')
    print(f'  合计: {total} 个测试点 → 精简为 8 条用例')

    # Step 4: 目录规划
    print('\n[Step 4] 目录规划: 放入已有目录或根级')

    # Step 5: 生成用例
    print('\n[Step 5] save_storage_case 批量写入 8 条用例')
    cases = [
        {'title':'正确账号密码登录成功', 'priority':'P1',
         'precondition':'应用已安装，已有有效账号',
         'steps':'1.打开登录页\n2.输入正确手机号\n3.输入正确密码\n4.点击登录按钮',
         'expected_result':'登录成功，跳转到首页，显示用户信息'},
        {'title':'密码错误登录失败', 'priority':'P1',
         'precondition':'应用在登录页，已有有效账号',
         'steps':'1.输入正确手机号\n2.输入错误密码\n3.点击登录按钮',
         'expected_result':'提示"账号或密码错误"，停留在登录页，密码输入框清空'},
        {'title':'账号为空', 'priority':'P2',
         'precondition':'应用在登录页',
         'steps':'1.不输入账号\n2.输入密码\n3.点击登录按钮',
         'expected_result':'登录按钮不可点击或提示"请输入账号"'},
        {'title':'密码为空', 'priority':'P2',
         'precondition':'应用在登录页',
         'steps':'1.输入账号\n2.不输入密码\n3.点击登录按钮',
         'expected_result':'登录按钮不可点击或提示"请输入密码"'},
        {'title':'账号密码均为空', 'priority':'P2',
         'precondition':'应用在登录页',
         'steps':'1.账号和密码都留空\n2.点击登录按钮',
         'expected_result':'登录按钮不可点击，两个输入框都显示校验提示'},
        {'title':'记住密码功能验证', 'priority':'P2',
         'precondition':'应用在登录页，已有有效账号',
         'steps':'1.勾选"记住密码"\n2.输入正确账号密码\n3.点击登录\n4.退出应用\n5.重新打开登录页',
         'expected_result':'账号和密码输入框已自动填充'},
        {'title':'连续5次密码错误锁定', 'priority':'P1',
         'precondition':'应用在登录页，已有有效账号',
         'steps':'1.连续5次输入错误密码\n2.每次点击登录按钮',
         'expected_result':'第5次后提示"账号已锁定，请15分钟后再试"，禁止继续登录'},
        {'title':'SQL注入/XSS特殊字符', 'priority':'P2',
         'precondition':'应用在登录页',
         'steps':"1.在账号框输入 ' OR '1'='1\n2.在密码框输入 <script>alert(1)</script>\n3.点击登录",
         'expected_result':'登录失败，系统正常处理特殊字符，不出现异常或数据泄露'},
    ]

    save_tool = SaveStorageCaseTool(); save_tool._ctx = ctx
    r = await save_tool.call(
        case_id='TC-FUNC-login-v2',
        title='登录功能业务测试用例（全场景覆盖）',
        cases=cases,
        description='基于五法测试设计：场景流、等价类边界值、判定表、错误推测'
    )
    print(f'  {r.content[0].text[:400]}')

    # 更新任务完成
    update_tool = UpdateCaseGenTaskTool(); update_tool._ctx = ctx
    r = await update_tool.call(run_id=run_id, status='COMPLETED',
        progress_current=len(cases), progress_total=len(cases))
    print(f'\n[任务卡片] {r.content[0].text}')

    # 验证数据
    from apps.case_manager.models_storage import StorageTestCase
    obj = StorageTestCase.objects.get(id='TC-FUNC-login-v2')
    row_count = len(obj.rows[0]['values']) if obj.rows else 0
    print(f'\n✅ 数据库验证: TC-FUNC-login-v2 包含 {row_count} 条用例')
    print(f'   列: {[c["key"] for c in obj.rows]}')
    print(f'   标题: {obj.rows[1]["values"]}')

asyncio.run(simulate())
