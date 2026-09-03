"""接口响应 JSON Schema — 供 YAML 用例按名字引用（expect.schema）。

Schema 角色：
  1. 替代散落的 assert body["key"] 检查
  2. additionalProperties: False 锁死响应结构，防止字段漂移
  3. 作为 API 响应的可执行文档
"""

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


ERROR_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": False},
        "message": {"type": "string", "minLength": 1},
    },
    "required": ["status", "message"],
    "additionalProperties": False,
}


DEVICE_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "devices": {"type": "array"},
                "current": {"type": ["string", "null"]},
            },
            "required": ["devices", "current"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}


HEARTBEAT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "updated": {"type": "integer"},
                "offline": {"type": "integer"},
                "online": {"type": "integer"},
                "busy": {"type": "integer"},
                "offline_count": {"type": "integer"},
                "disconnected": {"type": "integer"},
                "total": {"type": "integer"},
            },
            "required": [
                "updated",
                "offline",
                "online",
                "busy",
                "offline_count",
                "disconnected",
                "total",
            ],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}


DEVICE_CURRENT_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "serial": {"type": "string"},
                "screen_w": {"type": "integer"},
                "screen_h": {"type": "integer"},
                "package": {"type": "string"},
                "model": {"type": "string"},
                "brand": {"type": "string"},
                "connection_type": {"type": "string"},
            },
            "required": ["serial", "screen_w", "screen_h", "package"],
            "additionalProperties": False,
        },
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}


# YAML expect.schema 引用名 -> schema 对象
SCHEMAS = {
    "auth_success": AUTH_SUCCESS_SCHEMA,
    "register_success": REGISTER_SUCCESS_SCHEMA,
    "error": ERROR_SCHEMA,
    "device_list": DEVICE_LIST_SCHEMA,
    "heartbeat": HEARTBEAT_SCHEMA,
    "device_current": DEVICE_CURRENT_SCHEMA,
}
