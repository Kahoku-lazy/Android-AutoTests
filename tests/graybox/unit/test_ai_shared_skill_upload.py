"""共享 Skill 文件夹上传：相对路径契约与拒绝语义（spec: ai-shared-skill-upload）。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.ai_assistant import skills_catalog, views_toolbox_drf
from apps.ai_assistant.models import AISharedTool
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()

UPLOAD_URL = "/api/ai/toolbox/upload-skill/"
TREE_URL = "/api/ai/toolbox/skills/{name}/tree/"

SKILL_MD = "---\nname: demo-skill\ndescription: 演示用 Skill\n---\n\n# demo\n"


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def skills_root(tmp_path, monkeypatch):
    """共享 Skill 根目录指向临时目录：不写真实 engines/ai/skills，也不留库残留。"""
    root = tmp_path / "skills"
    root.mkdir()
    monkeypatch.setattr(views_toolbox_drf, "SHARED_SKILLS_DIR", str(root))
    monkeypatch.setattr(skills_catalog, "SHARED_SKILLS_DIR", str(root))
    return root


@pytest.fixture
def user():
    return User.objects.create_user(username="skill_uploader", password="x")


def _upload(client, user, *, name="demo-skill", entries, paths):
    """entries = [(相对路径, 内容)]；paths 与 entries 按序对应，缺省用 entries 的路径。"""
    data = {
        "name": name,
        "files": [SimpleUploadedFile(rel, content.encode("utf-8")) for rel, content in entries],
        "paths": paths,
    }
    return client.post(UPLOAD_URL, data=data, **_auth_headers(user))


def _assert_nothing_written(root, name="demo-skill"):
    """校验失败时 MUST NOT 创建记录或写出文件。"""
    assert not (root / name).exists()
    assert not AISharedTool.objects.filter(item_type="skill", name=name).exists()


# ── 成功路径：保留子目录层级 ──


def test_folder_upload_keeps_subdirectories(client, user, skills_root):
    entries = [("demo-skill/SKILL.md", SKILL_MD), ("demo-skill/references/a.md", "# a\n")]
    resp = _upload(client, user, entries=entries, paths=[rel for rel, _ in entries])

    assert resp.status_code == 200
    assert resp.json()["data"]["id"]
    assert (skills_root / "demo-skill" / "SKILL.md").read_text(encoding="utf-8") == SKILL_MD
    sub = skills_root / "demo-skill" / "references" / "a.md"
    assert sub.read_text(encoding="utf-8") == "# a\n"
    # 介绍取自 SKILL.md frontmatter，而不是「N 个文件 — MD: N」的文件摘要
    row = AISharedTool.objects.get(item_type="skill", name="demo-skill")
    assert row.description == "演示用 Skill"
    assert "个文件" not in row.description

    listed = client.get("/api/ai/toolbox/", **_auth_headers(user))
    assert listed.status_code == 200
    card = next(i for i in listed.json()["data"]["items"] if i["name"] == "demo-skill")
    assert card["description"] == "演示用 Skill"

    tree_resp = client.get(TREE_URL.format(name="demo-skill"), **_auth_headers(user))
    assert tree_resp.status_code == 200
    nodes = {node["name"]: node for node in tree_resp.json()["data"]["tree"]}
    assert nodes["references"]["is_dir"] is True
    assert [child["name"] for child in nodes["references"]["children"]] == ["a.md"]


def test_uploaded_skill_intro_ignores_file_type_stats(client, user, skills_root):
    """介绍不随文件数量/类型统计变化（spec: ai-shared-skill-upload）。"""
    entries = [
        ("demo-skill/SKILL.md", SKILL_MD),
        ("demo-skill/scripts/run.py", "print('x')\n"),
    ]
    resp = _upload(client, user, entries=entries, paths=[rel for rel, _ in entries])

    assert resp.status_code == 200
    row = AISharedTool.objects.get(item_type="skill", name="demo-skill")
    assert row.description == "演示用 Skill"
    assert "个文件" not in row.description
    assert "CLI" not in row.description


# ── 拒绝：目录层面 ──


def test_duplicate_folder_rejected_without_touching_existing(client, user, skills_root):
    existing = skills_root / "demo-skill"
    existing.mkdir()
    keep = "---\nname: existing\ndescription: 已存在\n---\n"
    (existing / "SKILL.md").write_text(keep, encoding="utf-8")

    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD)],
        paths=["demo-skill/SKILL.md"],
    )

    assert resp.status_code == 400
    assert "已存在同名 skill 文件夹" in resp.json()["message"]
    assert (existing / "SKILL.md").read_text(encoding="utf-8") == keep
    assert not AISharedTool.objects.filter(item_type="skill", name="demo-skill").exists()


def test_missing_root_skill_md_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/references/a.md", "# a\n")],
        paths=["demo-skill/references/a.md"],
    )

    assert resp.status_code == 400
    assert "缺少 SKILL.md" in resp.json()["message"]
    _assert_nothing_written(skills_root)


@pytest.mark.parametrize(
    ("skill_md", "expected"),
    [
        ("---\ndescription: 只有描述\n---\n", "name"),
        ("---\nname: demo-skill\n---\n", "description"),
    ],
)
def test_skill_md_frontmatter_fields_required(client, user, skills_root, skill_md, expected):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", skill_md)],
        paths=["demo-skill/SKILL.md"],
    )

    assert resp.status_code == 400
    assert expected in resp.json()["message"]
    _assert_nothing_written(skills_root)


# ── 拒绝：相对路径入参 ──


def test_empty_files_rejected(client, user, skills_root):
    resp = client.post(UPLOAD_URL, data={"name": "demo-skill"}, **_auth_headers(user))

    assert resp.status_code == 400
    assert "no files uploaded" in resp.json()["message"]
    _assert_nothing_written(skills_root)


def test_missing_paths_field_rejected(client, user, skills_root):
    """只发 files 不发 paths：必须是明确的「缺相对路径」，而不是把文件夹上传判成非法。"""
    data = {"name": "demo-skill", "files": [SimpleUploadedFile("SKILL.md", SKILL_MD.encode())]}
    resp = client.post(UPLOAD_URL, data=data, **_auth_headers(user))

    assert resp.status_code == 400
    message = resp.json()["message"]
    assert "相对路径" in message
    assert "只接受文件夹上传" not in message
    _assert_nothing_written(skills_root)


def test_paths_count_mismatch_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD), ("demo-skill/references/a.md", "# a\n")],
        paths=["demo-skill/SKILL.md"],
    )

    assert resp.status_code == 400
    assert "不一致" in resp.json()["message"]
    _assert_nothing_written(skills_root)


def test_path_traversal_rejected(client, user, skills_root, tmp_path):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD)],
        paths=["demo-skill/../evil.md"],
    )

    assert resp.status_code == 400
    assert "非法相对路径" in resp.json()["message"]
    assert not (tmp_path / "evil.md").exists()
    _assert_nothing_written(skills_root)


def test_absolute_path_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD)],
        paths=["/demo-skill/SKILL.md"],
    )

    assert resp.status_code == 400
    assert "非法相对路径" in resp.json()["message"]
    _assert_nothing_written(skills_root)


def test_paths_outside_named_folder_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD), ("other-skill/a.md", "# a\n")],
        paths=["demo-skill/SKILL.md", "other-skill/a.md"],
    )

    assert resp.status_code == 400
    assert "不在 skill 文件夹" in resp.json()["message"]
    _assert_nothing_written(skills_root)
    assert not (skills_root / "other-skill").exists()


def test_single_file_without_folder_path_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("SKILL.md", SKILL_MD)],
        paths=["SKILL.md"],
    )

    assert resp.status_code == 400
    assert "只接受文件夹上传" in resp.json()["message"]
    _assert_nothing_written(skills_root)


# ── 拒绝：文件类型与大小 ──


def test_unsupported_extension_rejected(client, user, skills_root):
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD), ("demo-skill/logo.svg", "<svg/>")],
        paths=["demo-skill/SKILL.md", "demo-skill/logo.svg"],
    )

    assert resp.status_code == 400
    assert "不支持的文件类型" in resp.json()["message"]
    _assert_nothing_written(skills_root)


def test_oversize_upload_rejected(client, user, skills_root, monkeypatch):
    monkeypatch.setattr(views_toolbox_drf, "_SHARED_SKILL_MAX_MB", 0.5)
    resp = _upload(
        client,
        user,
        entries=[("demo-skill/SKILL.md", SKILL_MD), ("demo-skill/big.md", "x" * (600 * 1024))],
        paths=["demo-skill/SKILL.md", "demo-skill/big.md"],
    )

    assert resp.status_code == 400
    assert "超过" in resp.json()["message"]
    _assert_nothing_written(skills_root)
