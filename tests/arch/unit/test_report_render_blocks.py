from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
RENDER = ROOT / "engines" / "ae_harness" / "event" / "render.py"
ALIGNED = ROOT / "engines" / "ae_harness" / "event" / "render_aligned.py"
BLOCKS = ROOT / "engines" / "ae_harness" / "event" / "render_blocks.py"
REQUIREMENTS = ROOT / "requirements.txt"

pytestmark = [pytest.mark.unit, pytest.mark.arch]


class TestReportFontContract:
    def test_body_font_starts_with_harmonyos(self):
        content = RENDER.read_text(encoding="utf-8")
        assert '"HarmonyOS Sans SC","PingFang SC","Noto Sans SC"' in content
        assert '"Cascadia Mono","Noto Sans SC"' not in content

    def test_platform_font_is_loaded_from_same_origin(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "loadPlatformFont" in content
        assert "/fonts/harmonyos-sans/harmonyos-sans.css" in content
        assert "location.href" in content

    def test_brand_font_stays_inlined(self):
        content = RENDER.read_text(encoding="utf-8")
        assert "_brand_font_src" in content
        assert 'font-family: "Ziku FeiYang"' in content


class TestReportBlocksContract:
    def test_blocks_module_renders_facts_json_and_markdown(self):
        content = BLOCKS.read_text(encoding="utf-8")
        assert 'class="fact"' in content
        assert 'class="json"' in content
        assert "MarkdownIt(" in content
        assert 'class="j-key"' in content

    def test_markdown_dependency_is_declared(self):
        assert "markdown-it-py" in REQUIREMENTS.read_text(encoding="utf-8")

    def test_four_views_share_the_blocks(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert "from .render_blocks import" in content
        assert "facts(" in content
        assert "markdown(" in content
        assert "json_block(" in content

    def test_stage_view_uses_report_phase_language(self):
        content = ALIGNED.read_text(encoding="utf-8")
        assert '_ordinal_svg(ordinal, "阶段")' in content
        assert 'class="phase fold-box"' in content
        assert "_stage_prepare(document, 1)" in content
