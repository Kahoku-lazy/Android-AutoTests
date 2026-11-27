__all__ = ["describe_operations"]

HTTP_METHODS = frozenset({"get", "post", "put", "patch", "delete", "head", "options"})

RESOURCES = {
    "ai/agent-reports": "智能体报告",
    "ai/assistants/threads": "对话栏",
    "ai/assistants": "助手",
    "ai/eval-candidates": "评测候选",
    "ai/eval-cases": "题库",
    "ai/eval-methods": "评测方法",
    "ai/eval-reports": "评测报告",
    "ai/eval-runs": "评测运行",
    "ai/eval-scores": "评分",
    "ai/eval-suite-scores": "套件评分",
    "ai/model-configs": "模型配置",
    "ai/roles": "角色",
    "ai/sop-workflows": "工作流",
    "ai/tool-catalog": "工具目录",
    "auth": "登录鉴权",
    "bugs": "bug 单",
    "cases/projects": "用例项目",
    "cases/stats": "用例统计",
    "dashboard/activities": "仪表盘动态",
    "dashboard/stats": "仪表盘统计",
    "devices": "设备",
    "knowledge-search/evaluations": "知识库评测",
    "knowledge-search/modules": "知识库模块",
    "knowledge-search/query": "知识库检索",
    "knowledge-search/settings": "检索设置",
    "media/signed": "任务媒体",
    "ops/users": "运营账号",
    "reports": "测试报告",
    "serial-log/keywords": "串口关键词",
    "serial-log/ports": "串口端口",
    "system/drain": "系统排空",
    "tasks": "任务",
}

TAILS = {
    "activate": "激活设备",
    "avatar": "读取助手头像",
    "cancel": "取消任务",
    "clear": "清空任务",
    "current": "读取当前设备",
    "delete": "删除任务",
    "disable": "停用账号",
    "disconnect": "断开设备",
    "disconnect-observe": "断开观察占用",
    "discover": "发现可用模型",
    "drain": "系统排空",
    "enable": "启用账号",
    "grant-author": "授予作者权限",
    "grant-operator": "授予运营权限",
    "heartbeat": "设备心跳",
    "import-yaml": "导入 YAML 用例",
    "index": "重建知识库索引",
    "lines": "读取串口日志行",
    "link": "关联任务媒体",
    "lock": "加锁设备",
    "login": "登录",
    "logout": "登出",
    "logs": "运行日志",
    "me": "读取当前用户",
    "model-grants": "维护模型使用名单",
    "publish": "发布",
    "purge": "注销账号",
    "query": "知识库检索",
    "refresh": "刷新令牌",
    "register": "注册账号",
    "release": "释放设备占用",
    "rerun": "重跑任务",
    "reset-password": "重置账号密码",
    "revoke-author": "撤销作者权限",
    "revoke-operator": "撤销运营权限",
    "rows": "维护用例行",
    "scan": "扫描设备",
    "settings": "读取或保存检索设置",
    "stats": "统计",
    "submit": "提交任务",
    "sync": "同步 bug 单",
    "toggle": "切换端口开关",
    "upload-file": "上传任务文件",
    "view": "保存用例视图",
}

OVERRIDES = {
    ("post", "api/ai/assistants/threads/{thread_id}/logs/"): "签发日志票据",
    ("post", "api/ai/assistants/threads/{thread_id}/logs/{report_id}/"): "签发日志票据",
    ("get", "api/ai/assistants/threads/{thread_id}/logs/{report_id}/"): "读取日志文件",
    ("get", "api/ai/assistants/threads/{thread_id}/logs/"): "运行日志列表",
    ("post", "api/ai/assistants/threads/{thread_id}/"): "发送消息",
    ("patch", "api/ai/assistants/threads/{thread_id}/"): "重命名对话栏",
    ("post", "api/cases/projects/{id}/rows/"): "新增用例行",
    ("patch", "api/cases/projects/{id}/rows/{case_id}/"): "更新用例行",
    ("delete", "api/cases/projects/{id}/rows/{case_id}/"): "删除用例行",
    ("get", "api/tasks/{task_id}/"): "任务详情",
    ("get", "api/tasks/{task_id}/media/{media_id}/"): "读取任务媒体",
    ("post", "api/tasks/{task_id}/media/{media_id}/link/"): "关联任务媒体",
    ("post", "api/ops/users/disable/"): "批量停用账号",
    ("post", "api/ops/users/purge/"): "批量注销账号",
    ("get", "api/ops/users/"): "运营账号列表",
    ("post", "api/devices/{serial}/"): "连接设备",
    ("get", "api/knowledge-search/modules/"): "知识库模块列表",
    ("post", "api/knowledge-search/modules/{id}/index/"): "重建知识库索引",
    ("get", "api/knowledge-search/evaluations/{id}/"): "知识库评测详情",
    ("get", "api/serial-log/ports/{port}/lines/"): "读取串口日志行",
    ("post", "api/serial-log/ports/toggle/"): "切换端口开关",
    ("get", "media/signed/{task_id}/{media_id}/{expires}/{signature}/"): "读取签名媒体",
}


def _normalize(path: str) -> str:
    return path.strip("/")


def _resource(path: str) -> str:
    segments = [part for part in path.split("/") if part]
    if segments and segments[0] == "api":
        segments = segments[1:]
    for size in (3, 2, 1):
        key = "/".join(segments[:size])
        if key in RESOURCES:
            return RESOURCES[key]
    static = [part for part in segments if not part.startswith("{")]
    return static[-1] if static else "资源"


def _summary(method: str, path: str) -> str:
    normalized = _normalize(path)
    if (method, normalized) in OVERRIDES:
        return OVERRIDES[(method, normalized)]

    segments = [part for part in normalized.split("/") if part]
    if segments and segments[0] == "api":
        segments = segments[1:]
    tail = segments[-1] if segments else ""
    if tail in TAILS:
        return TAILS[tail]

    resource = _resource(path)
    last_is_param = tail.startswith("{")
    if method == "get":
        return f"{resource}详情" if last_is_param else f"{resource}列表"
    if method == "post":
        return f"创建{resource}"
    if method in {"patch", "put"}:
        return f"更新{resource}"
    if method == "delete":
        return f"删除{resource}"
    return f"{method.upper()} {path}"


def describe_operations(result, generator=None, request=None, public=False):
    for path, operations in (result.get("paths") or {}).items():
        for method, operation in operations.items():
            if method not in HTTP_METHODS:
                continue
            if operation.get("summary") or operation.get("description"):
                continue
            operation["summary"] = _summary(method, path)
    return result
