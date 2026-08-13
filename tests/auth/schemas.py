"""认证模块 API 响应 JSON Schema — 一次定义，所有测试复用。

Schema 的角色：
  1. 替代 3-6 个独立 `assert body["key"]` 检查
  2. ``additionalProperties: False`` 确保后端不意外新增/删除字段
  3. Schema 本身就是 API 响应的可执行文档

用法：
    import jsonschema
    from tests.auth.schemas import AUTH_SUCCESS_SCHEMA, ERROR_400_SCHEMA

    body = resp.json()
    jsonschema.validate(instance=body, schema=AUTH_SUCCESS_SCHEMA)
"""

# ═══════════════════════════════════════════════════════════════════
# 成功响应
# ═══════════════════════════════════════════════════════════════════

AUTH_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "refresh_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                    },
                    "required": ["id", "username"],
                    "additionalProperties": False,
                },
            },
            "required": ["access_token", "refresh_token", "token_type", "user"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

REFRESH_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
            },
            "required": ["access_token", "token_type"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

LOGOUT_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {"type": "object"},
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

ME_USER_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                    },
                    "required": ["id", "username"],
                },
            },
            "required": ["user"],
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

REGISTER_SUCCESS_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "access_token": {"type": "string", "minLength": 10},
                "refresh_token": {"type": "string", "minLength": 10},
                "token_type": {"const": "bearer"},
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer"},
                        "username": {"type": "string"},
                        "email": {"type": "string"},
                    },
                    "required": ["id", "username", "email"],
                },
            },
            "required": ["access_token", "refresh_token", "token_type", "user"],
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}

# ═══════════════════════════════════════════════════════════════════
# 错误响应 — 所有非成功状态码共享此结构
# ═══════════════════════════════════════════════════════════════════

ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": False},
        "message": {"type": "string", "minLength": 1},
    },
    "required": ["status", "message"],
    "additionalProperties": False,
}

ERROR_503_RETRY_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": False},
        "message": {"type": "string", "minLength": 1},
        "retry": {"const": True},
    },
    "required": ["status", "message", "retry"],
    "additionalProperties": False,
}
