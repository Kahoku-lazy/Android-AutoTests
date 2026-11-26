import re

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
ALIGNED = ROOT / "engines" / "ae_harness" / "event" / "aligned.py"
RENDER = ROOT / "engines" / "ae_harness" / "event" / "render_aligned.py"

pytestmark = [pytest.mark.unit, pytest.mark.arch]

SECTIONS = ("run", "input", "replies", "observations", "summary", "events")


class TestAlignedRecordContract:
    def test_schema_version_is_declared(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert re.search(r'_SCHEMA\s*=\s*"agentscope\.run/1"', content)
        assert '"schema": _SCHEMA' in content

    def test_six_sections_are_emitted(self):
        content = ALIGNED.read_text(encoding="utf-8")
        for section in SECTIONS:
            assert f'"{section}"' in content, f"记录缺 {section} 段"

    def test_folding_goes_through_framework_api(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert "msg.append_event(" in content
        assert "Msg(" in content

    def test_media_is_kept_as_url_source(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert "save_media(dump, self.media_dir, as_url=True)" in content


class TestAlignedReportContract:
    def test_report_reads_reply_blocks_only(self):
        content = RENDER.read_text(encoding="utf-8")
        assert '"replies"' in content
        assert "content" in content
        assert "RunRecord" not in content

    def test_five_block_types_are_mapped(self):
        content = RENDER.read_text(encoding="utf-8")
        for block in ("thinking", "text", "tool_call", "tool_result", "hint"):
            assert f'"{block}"' in content, f"缺 {block} 块映射"

    def test_unknown_block_falls_back(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "_misc_card" in content
        assert "未识别的块类型" in content

    def test_empty_record_shows_no_content(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "无内容" in content
