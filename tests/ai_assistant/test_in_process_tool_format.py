"""in_process_tool._format_result 序列化分支单元测试。

覆盖 dict（JSON 输出）/ 单模型实例（字段 dict）/ list（模型逐项 dict）
三分支——确保 get_case 等详情工具不再被 str() 化为标题。
"""

from types import SimpleNamespace

import pytest

from apps.ai_assistant.agent_scope.in_process_tool import _format_result

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def _text(chunk) -> str:
    return chunk.content[0].text


class _FakeField:
    def __init__(self, name, attname=None):
        self.name = name
        self.attname = attname or name


class _FakeModel:
    _meta = SimpleNamespace(
        fields=[
            _FakeField("id"),
            _FakeField("title"),
            _FakeField("none_val"),
            _FakeField("parent", attname="parent_id"),  # 模拟外键字段
        ]
    )

    def __init__(self):
        self.id = "TC-1"
        self.title = "登录用例"
        self.none_val = None
        self.parent_id = 25  # 只读原始列，绝不访问 parent 相关对象（防懒加载 ORM 查询）


def test_format_dict_as_json():
    chunk = _format_result({"case_id": "TC-1", "steps": [{"type": "click"}]})
    text = _text(chunk)
    assert '"case_id": "TC-1"' in text  # JSON 双引号，而非 Python repr 单引号
    assert '"type": "click"' in text


def test_format_single_model_instance_as_fields():
    chunk = _format_result(_FakeModel())
    text = _text(chunk)
    assert '"id": "TC-1"' in text
    assert '"title": "登录用例"' in text
    assert '"none_val": ""' in text
    assert '"parent": 25' in text  # 外键字段输出原始 id，不触发懒加载


def test_format_list_of_models():
    chunk = _format_result([_FakeModel()])
    assert '"id": "TC-1"' in _text(chunk)


def test_format_primitive_still_works():
    assert _text(_format_result(None)) == "操作完成，无返回数据。"
    assert _text(_format_result(True)) == "操作成功。"
    assert _text(_format_result("纯文本")) == "纯文本"
    assert "查询结果为空" in _text(_format_result([]))


def test_format_dict_truncated_with_marker():
    big = {"k": "x" * 5000}
    text = _text(_format_result(big))
    assert text.endswith("…(输出截断)")
    assert len(text) <= 4000 + len("…(输出截断)")
