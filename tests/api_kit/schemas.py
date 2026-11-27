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


SNAPSHOT_LIST_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"const": True},
        "data": {
            "type": "object",
            "properties": {
                "total": {"type": "integer"},
                "items": {"type": "array"},
            },
            "required": ["total", "items"],
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


ME_SUCCESS_SCHEMA = {
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
                        "is_superuser": {"type": "boolean"},
                        "is_operator": {"type": "boolean"},
                        "is_assistant_author": {"type": "boolean"},
                    },
                    "required": [
                        "id",
                        "username",
                        "is_superuser",
                        "is_operator",
                        "is_assistant_author",
                    ],
                    "additionalProperties": False,
                },
            },
            "required": ["user"],
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
        "data": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    "required": ["status", "data"],
    "additionalProperties": False,
}


SCHEMAS = {
    "auth_success": AUTH_SUCCESS_SCHEMA,
    "register_success": REGISTER_SUCCESS_SCHEMA,
    "refresh_success": REFRESH_SUCCESS_SCHEMA,
    "me_success": ME_SUCCESS_SCHEMA,
    "logout_success": LOGOUT_SUCCESS_SCHEMA,
    "error": ERROR_SCHEMA,
    "device_list": DEVICE_LIST_SCHEMA,
    "heartbeat": HEARTBEAT_SCHEMA,
    "device_current": DEVICE_CURRENT_SCHEMA,
    "snapshot_list": SNAPSHOT_LIST_SCHEMA,
}
