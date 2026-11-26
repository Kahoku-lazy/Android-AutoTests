from __future__ import annotations

import pytest

from utils.check_gates import (
    BUSINESS_ASSET_DIRS,
    FORBIDDEN_ASSET_PATHS,
    RESTRICTED_VENDOR_TOKENS,
    business_asset_gate,
)

pytestmark = [pytest.mark.unit]

_TOKEN = RESTRICTED_VENDOR_TOKENS[0]


def test_gate_contract() -> None:
    gate = business_asset_gate()
    assert gate.name == "business-asset"
    assert gate.blocking is True


def test_managed_dirs_cover_asset_roots() -> None:
    assert {directory.name for directory in BUSINESS_ASSET_DIRS} == {"app_info"}


def test_forbidden_paths_cover_removed_assets() -> None:
    assert len(FORBIDDEN_ASSET_PATHS) == 2
    assert all(path.endswith((".md", ".yaml")) for path in FORBIDDEN_ASSET_PATHS)


def test_clean_tree_passes() -> None:
    ok, lines = business_asset_gate().run()
    assert ok is True, lines
    assert lines == []


def test_content_hit_fails(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    (tmp_path / "asset.md").write_text(f"应用资料：{_TOKEN} home", encoding="utf-8")
    monkeypatch.setattr("utils.check_gates.BUSINESS_ASSET_DIRS", (tmp_path,))
    monkeypatch.setattr("utils.check_gates.FORBIDDEN_ASSET_PATHS", ())
    ok, lines = business_asset_gate().run()
    assert ok is False
    assert any("asset.md" in line for line in lines)


def test_forbidden_path_revival_fails(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    revived = tmp_path / "revived.md"
    revived.write_text("x", encoding="utf-8")
    monkeypatch.setattr("utils.check_gates.BUSINESS_ASSET_DIRS", ())
    monkeypatch.setattr("utils.check_gates.FORBIDDEN_ASSET_PATHS", (str(revived),))
    ok, lines = business_asset_gate().run()
    assert ok is False
    assert any("已禁用资产路径重新出现" in line for line in lines)
