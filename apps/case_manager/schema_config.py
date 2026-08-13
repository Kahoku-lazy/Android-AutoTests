"""API 测试用例 config_json 的 JSON Schema 定义。

用于 jsonschema.validate() 校验 config_json 结构完整性。
前端 TypeScript 类型定义需与此 Schema 保持对齐。
"""

CONFIG_JSON_SCHEMA: dict = {
    "type": "object",
    "required": ["case_info", "steps", "test_data", "validation"],
    "properties": {
        "case_info": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "id": {
                    "type": "string",
                    "description": "用例唯一标识，格式 API-YYYYMMDD-HHMMSS-XXXX",
                },
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 500,
                    "description": "测试标题，必填",
                },
                "description": {
                    "type": "string",
                    "default": "",
                    "description": "测试点描述",
                },
                "precondition": {
                    "type": "string",
                    "default": "",
                    "description": "前置条件",
                },
            },
            "additionalProperties": False,
        },
        "steps": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["url", "method", "assert"],
                "properties": {
                    "name": {
                        "type": "string",
                        "default": "",
                        "description": "步骤名称",
                    },
                    "domain": {
                        "type": "string",
                        "default": "",
                        "description": "接口域名",
                    },
                    "url": {
                        "type": "string",
                        "minLength": 1,
                        "description": "接口路径，支持 {{var}}",
                    },
                    "method": {
                        "type": "string",
                        "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                        "description": "HTTP 方法",
                    },
                    "headers": {
                        "type": "object",
                        "default": {},
                        "description": "请求头，支持 {{var}}",
                    },
                    "body": {
                        "type": "object",
                        "default": {},
                        "description": "请求体，支持 {{var}}",
                    },
                    "request_schema": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "null"},
                        ],
                        "default": None,
                        "description": "请求体 JSON Schema",
                    },
                    "response_schema": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "null"},
                        ],
                        "default": None,
                        "description": "响应体 JSON Schema（断言用）",
                    },
                    "extract": {
                        "type": "array",
                        "default": [],
                        "items": {
                            "type": "object",
                            "required": ["name", "path"],
                            "properties": {
                                "name": {"type": "string", "minLength": 1},
                                "path": {"type": "string", "minLength": 1},
                            },
                            "additionalProperties": False,
                        },
                        "description": "变量提取规则",
                    },
                    "assert": {
                        "type": "boolean",
                        "description": "是否对该步骤执行响应断言",
                    },
                },
                "additionalProperties": False,
            },
        },
        "test_data": {
            "type": "array",
            "default": [],
            "items": {
                "type": "object",
                "required": ["input"],
                "properties": {
                    "input": {
                        "type": "object",
                        "description": "输入变量，key 对应步骤中的 {{key}}",
                    },
                    "output_schema": {
                        "oneOf": [
                            {
                                "type": "object",
                                "required": ["step_index", "schema"],
                                "properties": {
                                    "step_index": {"type": "integer", "minimum": 0},
                                    "schema": {"type": "object"},
                                },
                                "additionalProperties": False,
                            },
                            {"type": "null"},
                        ],
                        "default": None,
                        "description": "行级输出断言",
                    },
                },
                "additionalProperties": False,
            },
        },
        "validation": {
            "type": "array",
            "default": [],
            "items": {
                "type": "object",
                "required": ["step_index", "enabled"],
                "properties": {
                    "step_index": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "校验哪个步骤的请求体",
                    },
                    "enabled": {
                        "type": "boolean",
                        "description": "是否启用该校验",
                    },
                    "schema": {
                        "oneOf": [
                            {"type": "object"},
                            {"type": "null"},
                        ],
                        "default": None,
                        "description": "JSON Schema 校验规则",
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}

# ─── 辅助函数 ───


def get_default_config(case_id: str = "", title: str = "") -> dict:
    """生成一个新的空 config_json 模板。

    Args:
        case_id: 用例 ID，如不提供则需后续自动生成
        title: 测试标题

    Returns:
        合法的 config_json dict（含 4 个模块的空结构）
    """
    return {
        "case_info": {
            "id": case_id,
            "title": title,
            "description": "",
            "precondition": "",
        },
        "steps": [],
        "test_data": [],
        "validation": [],
    }


def validate_config_json(config: dict) -> None:
    """校验 config_json 结构完整性。

    调用 jsonschema.validate() 验证 config 是否符合 CONFIG_JSON_SCHEMA。
    也执行额外的业务逻辑校验（如 steps 非空、case_info.title 非空等）。

    Args:
        config: 待校验的 config_json dict

    Raises:
        ValueError: 校验失败，message 包含具体错误原因
    """
    import jsonschema

    # 结构校验
    try:
        jsonschema.validate(config, CONFIG_JSON_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValueError(f"config_json 结构校验失败: {e.message}") from e

    # 业务校验
    info = config.get("case_info", {})
    if not info.get("title", "").strip():
        raise ValueError("case_info.title 不能为空")

    steps = config.get("steps", [])
    if not steps:
        raise ValueError("steps 不能为空（至少需要 1 个步骤）")


# ═══════════════════════════════════════════════════════════════════
# Single-request API schema — data-driven, 1 request template + N cases.
# Distinguished from multi-step schema by top-level key: "meta" (single)
# vs "case_info" (multi).  Frontend probes the same way.
# ═══════════════════════════════════════════════════════════════════

SINGLE_API_SCHEMA: dict = {
    "type": "object",
    "required": ["meta", "request", "cases"],
    "properties": {
        "meta": {
            "type": "object",
            "required": ["title"],
            "properties": {
                "title": {
                    "type": "string",
                    "minLength": 1,
                    "maxLength": 500,
                    "description": "用例集名称",
                },
                "description": {
                    "type": "string",
                    "default": "",
                    "description": "用例集描述",
                },
                "base_url": {
                    "type": "string",
                    "default": "",
                    "description": "接口域名，如 http://localhost:8765",
                },
                "auth": {
                    "oneOf": [
                        {
                            "type": "object",
                            "required": ["type"],
                            "properties": {
                                "type": {"enum": ["bearer", "basic", "api_key"]},
                                "token": {"type": "string"},
                                "username": {"type": "string"},
                                "password": {"type": "string"},
                                "key": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "additionalProperties": False,
                        },
                        {"type": "null"},
                        {"const": {"type": "none"}},
                    ],
                    "default": {"type": "none"},
                    "description": "全局鉴权（行级 input.auth 可覆盖）",
                },
            },
            "additionalProperties": False,
        },
        "request": {
            "type": "object",
            "required": ["method", "path"],
            "properties": {
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"],
                },
                "path": {
                    "type": "string",
                    "minLength": 1,
                    "description": "接口路径，支持 {{var}}",
                },
                "headers": {
                    "type": "object",
                    "default": {},
                    "description": "全局请求头，支持 {{var}}",
                },
            },
            "additionalProperties": False,
        },
        "cases": {
            "type": "array",
            "minItems": 1,
            "items": {
                "type": "object",
                "required": ["id", "scenario", "expect"],
                "properties": {
                    "id": {
                        "type": "string",
                        "minLength": 1,
                        "description": "行标识，如 TC-LOGIN-001",
                    },
                    "category": {
                        "type": "string",
                        "default": "",
                        "description": "分类：功能/校验/认证/安全/...",
                    },
                    "scenario": {
                        "type": "string",
                        "minLength": 1,
                        "description": "场景描述",
                    },
                    "description": {
                        "type": "string",
                        "default": "",
                    },
                    "input": {
                        "type": "object",
                        "default": {},
                        "properties": {
                            "headers": {
                                "type": "object",
                                "default": {},
                                "description": "行级请求头（合并到 request.headers）",
                            },
                            "body": {
                                "type": "object",
                                "default": {},
                                "description": "请求体，支持 {{var}}",
                            },
                            "auth": {
                                "oneOf": [
                                    {
                                        "type": "object",
                                        "required": ["type"],
                                        "properties": {
                                            "type": {"enum": ["bearer", "basic", "api_key"]},
                                            "token": {"type": "string"},
                                            "username": {"type": "string"},
                                            "password": {"type": "string"},
                                            "key": {"type": "string"},
                                            "value": {"type": "string"},
                                        },
                                        "additionalProperties": False,
                                    },
                                    {"type": "null"},
                                ],
                                "default": None,
                                "description": "行级鉴权（覆盖 meta.auth）",
                            },
                        },
                        "additionalProperties": False,
                    },
                    "expect": {
                        "type": "object",
                        "required": ["status"],
                        "properties": {
                            "status": {
                                "type": "integer",
                                "minimum": 100,
                                "maximum": 599,
                                "description": "预期 HTTP 状态码",
                            },
                            "headers_schema": {
                                "oneOf": [{"type": "object"}, {"type": "null"}],
                                "default": None,
                                "description": "响应头 JSON Schema",
                            },
                            "body_schema": {
                                "oneOf": [{"type": "object"}, {"type": "null"}],
                                "default": None,
                                "description": "响应体 JSON Schema",
                            },
                        },
                        "additionalProperties": False,
                    },
                },
                "additionalProperties": False,
            },
        },
    },
    "additionalProperties": False,
}


def get_default_single_config(title: str = "", base_url: str = "") -> dict:
    """生成一个新的单接口 config_json 模板。

    Args:
        title: 用例集名称
        base_url: 接口域名

    Returns:
        合法的单接口 config_json dict
    """
    return {
        "meta": {
            "title": title,
            "description": "",
            "base_url": base_url,
            "auth": {"type": "none"},
        },
        "request": {
            "method": "GET",
            "path": "",
            "headers": {},
        },
        "cases": [],
    }


def validate_single_api_config(config: dict) -> None:
    """校验单接口 config_json 结构完整性。

    Args:
        config: 待校验的 config_json dict

    Raises:
        ValueError: 校验失败
    """
    import jsonschema

    try:
        jsonschema.validate(config, SINGLE_API_SCHEMA)
    except jsonschema.ValidationError as e:
        raise ValueError(f"config_json 结构校验失败: {e.message}") from e

    if not config["meta"]["title"].strip():
        raise ValueError("meta.title 不能为空")

    cases = config.get("cases", [])
    if not cases:
        raise ValueError("cases 不能为空（至少需要 1 行测试数据）")


def is_single_format(config: dict) -> bool:
    """判断 config_json 是否为单接口格式（按顶层 key 探测）。"""
    return "meta" in config and "cases" in config


def validate_any_api_config(config: dict) -> None:
    """自动探测格式并校验 config_json。

    - 有 "meta" key → 单接口格式
    - 有 "case_info" key → 多接口格式
    - 都没有 → 抛出 ValueError
    """
    if is_single_format(config):
        validate_single_api_config(config)
    elif "case_info" in config or "steps" in config:
        validate_config_json(config)
    else:
        raise ValueError("无法识别 config_json 格式：缺少 meta（单接口）或 case_info（多接口）")
