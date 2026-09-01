"""任务发布 + 多线路配置接口测试（live-server）。"""

import allure


@allure.feature("ai_assistant")
@allure.story("task_publish")
def test_submit_task_goal_required(base_url, api_session, auth_headers):
    """任务目标缺失 → 400。"""
    resp = api_session.post(
        f"{base_url}/api/ai/tasks/submit",
        json={"route": "device_control"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@allure.feature("ai_assistant")
@allure.story("task_publish")
def test_submit_task_invalid_route(base_url, api_session, auth_headers):
    """非法线路枚举 → 400。"""
    resp = api_session.post(
        f"{base_url}/api/ai/tasks/submit",
        json={"goal": "打开 govee", "route": "unknown"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


@allure.feature("ai_assistant")
@allure.story("task_publish")
def test_submit_platform_task_placeholder(base_url, api_session, auth_headers):
    """平台任务线路 → 占位返回（不执行 reasoning）。"""
    resp = api_session.post(
        f"{base_url}/api/ai/tasks/submit",
        json={"goal": "生成登录用例", "route": "platform_task"},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") is True
    assert body.get("data", {}).get("result") == "线路开发中"


@allure.feature("ai_assistant")
@allure.story("task_publish")
def test_list_agent_tasks_shape(base_url, api_session, auth_headers):
    """任务列表形状。"""
    resp = api_session.get(f"{base_url}/api/ai/agent-tasks", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("status") is True
    assert isinstance(body.get("data", {}).get("tasks"), list)
