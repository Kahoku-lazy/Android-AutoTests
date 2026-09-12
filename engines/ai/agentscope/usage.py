"""通用 token 用量累加器 — 按模型 / 按角色拆分，供各工作流复用。

接收一轮用量的 dict（input_tokens / output_tokens / cache_input_tokens /
cache_creation_input_tokens），累加总量、按模型、按角色。
"""

from __future__ import annotations


class UsageAccumulator:
    """任务级 token 用量累加器：总量 + 按模型 + 按角色拆分。"""

    def __init__(self) -> None:
        self.input_tokens = 0
        self.output_tokens = 0
        self.cache_input_tokens = 0
        self.cache_creation_input_tokens = 0
        self.models: dict = {}
        self.by_role: dict = {}

    def acc(self, usage: dict, model_name: str = "", role: str = "") -> None:
        """把一轮用量 dict 累加进来（含缓存命中/写入）。"""
        if not isinstance(usage, dict):
            return
        inp = int(usage.get("input_tokens", 0) or 0)
        out = int(usage.get("output_tokens", 0) or 0)
        hit = int(usage.get("cache_input_tokens", 0) or 0)
        write = int(usage.get("cache_creation_input_tokens", 0) or 0)
        self.input_tokens += inp
        self.output_tokens += out
        self.cache_input_tokens += hit
        self.cache_creation_input_tokens += write
        if model_name:
            m = self.models.setdefault(
                model_name,
                {"input_tokens": 0, "output_tokens": 0, "cache_input_tokens": 0},
            )
            m["input_tokens"] += inp
            m["output_tokens"] += out
            m["cache_input_tokens"] += hit
        if role:
            r = self.by_role.setdefault(
                role,
                {"input_tokens": 0, "output_tokens": 0, "cache_input_tokens": 0},
            )
            r["input_tokens"] += inp
            r["output_tokens"] += out
            r["cache_input_tokens"] += hit

    def as_dict(self) -> dict:
        """导出当前累计值（深拷贝内层，避免外部拿到可变引用）。"""
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_input_tokens": self.cache_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "models": {k: dict(v) for k, v in self.models.items()},
            "by_role": {k: dict(v) for k, v in self.by_role.items()},
        }
