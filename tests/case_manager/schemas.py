"""JSON Schema validators for API test case responses.

Validates both success (200) and error (400/404/409) response shapes
returned by the /api/cases/api-testing/definitions endpoints.
"""

# ── Shared fragments ──

_CASE_INFO_SCHEMA = {
    "type": "object",
    "required": ["id", "title"],
    "properties": {
        "id": {"type": "string"},
        "title": {"type": "string"},
        "description": {"type": "string"},
        "precondition": {"type": "string"},
    },
}

_STEP_SCHEMA = {
    "type": "object",
    "required": ["url", "method", "assert"],
    "properties": {
        "name": {"type": "string"},
        "domain": {"type": "string"},
        "url": {"type": "string"},
        "method": {
            "type": "string",
            "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
        },
        "headers": {"type": "object"},
        "body": {"type": "object"},
        "request_schema": {"oneOf": [{"type": "object"}, {"type": "null"}]},
        "response_schema": {"oneOf": [{"type": "object"}, {"type": "null"}]},
        "extract": {"type": "array"},
        "assert": {"type": "boolean"},
    },
}

_VALIDATION_RULE_SCHEMA = {
    "type": "object",
    "required": ["step_index", "enabled"],
    "properties": {
        "step_index": {"type": "integer"},
        "enabled": {"type": "boolean"},
        "schema": {"oneOf": [{"type": "object"}, {"type": "null"}]},
    },
}

_TEST_DATA_ROW_SCHEMA = {
    "type": "object",
    "required": ["input"],
    "properties": {
        "input": {"type": "object"},
        "output_schema": {"oneOf": [{"type": "object"}, {"type": "null"}]},
    },
}

CONFIG_JSON_SCHEMA = {
    "type": "object",
    "required": ["case_info", "steps", "test_data", "validation"],
    "properties": {
        "case_info": _CASE_INFO_SCHEMA,
        "steps": {"type": "array", "items": _STEP_SCHEMA},
        "test_data": {"type": "array", "items": _TEST_DATA_ROW_SCHEMA},
        "validation": {"type": "array", "items": _VALIDATION_RULE_SCHEMA},
    },
}

# 单接口格式（meta/request/cases）的简化 schema，够测试校验关键结构即可
_SINGLE_CONFIG_JSON_SCHEMA = {
    "type": "object",
    "required": ["meta", "request", "cases"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["title"],
            "properties": {"title": {"type": "string"}},
        },
        "request": {
            "type": "object",
            "required": ["method", "path"],
            "properties": {"method": {"type": "string"}, "path": {"type": "string"}},
        },
        "cases": {"type": "array"},
    },
}

# ── Top-level API response schemas ──

# GET /api/cases/api-testing/definitions  (list)
API_LIST_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "definitions"],
    "properties": {
        "status": {"const": True},
        "definitions": {
            "type": "array",
            "items": {
                "type": "object",
                "required": ["id", "title", "config_json"],
                "properties": {
                    "id": {"type": "string"},
                    "title": {"type": "string"},
                    "case_type": {"const": "api_testing"},
                    "config_json": {"oneOf": [CONFIG_JSON_SCHEMA, _SINGLE_CONFIG_JSON_SCHEMA]},
                },
            },
        },
    },
}

# GET /api/cases/api-testing/definitions/{id}  (detail)
API_DETAIL_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "definition"],
    "properties": {
        "status": {"const": True},
        "definition": {
            "type": "object",
            "required": ["id", "title", "config_json"],
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "config_json": {"oneOf": [CONFIG_JSON_SCHEMA, _SINGLE_CONFIG_JSON_SCHEMA]},
            },
        },
    },
}

# Error response (400/401/404/409)
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "message"],
    "properties": {
        "status": {"const": False},
        "message": {"type": "string"},
    },
}

# POST success response
API_CREATE_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["status", "id"],
    "properties": {
        "status": {"const": True},
        "id": {"type": "string"},
    },
}
