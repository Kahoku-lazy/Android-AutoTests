"""知识库磁盘目录：列表、上传落盘、Word/PDF 旁路转 md。"""

from pathlib import Path

import pytest

from apps.ai_assistant import kb_files


@pytest.fixture
def rag_root(tmp_path, monkeypatch):
    root = tmp_path / "rag_datas"
    root.mkdir()
    monkeypatch.setattr(kb_files, "RAG_DATAS_DIR", root)
    return root


@pytest.mark.unit
def test_list_rag_files_builds_tree_fields(rag_root: Path):
    (rag_root / "项目文档").mkdir()
    (rag_root / "项目文档" / "a.md").write_text("# hi", encoding="utf-8")
    (rag_root / "note.txt").write_text("txt", encoding="utf-8")

    docs = kb_files.list_rag_files()
    by_id = {d["id"]: d for d in docs}

    assert by_id["项目文档/a.md"]["type"] == "project_doc"
    assert by_id["项目文档/a.md"]["size"] == len("# hi".encode("utf-8"))
    assert by_id["note.txt"]["type"] == ""
    assert by_id["note.txt"]["source"] == "note.txt"


@pytest.mark.unit
def test_save_upload_writes_under_rag_datas(rag_root: Path):
    saved = kb_files.save_upload("手册.md", "# 手册".encode("utf-8"))
    assert saved["id"] == "手册.md"
    assert (rag_root / "手册.md").read_text(encoding="utf-8") == "# 手册"


@pytest.mark.unit
def test_save_upload_rejects_path_traversal(rag_root: Path):
    with pytest.raises(ValueError, match="非法"):
        kb_files.save_upload("../escape.md", b"x")


@pytest.mark.unit
def test_preview_txt_returns_text(rag_root: Path):
    (rag_root / "a.txt").write_text("hello", encoding="utf-8")
    result = kb_files.preview_document("a.txt")
    assert result["kind"] == "text"
    assert result["content"] == "hello"
    assert result["converted"] is False


@pytest.mark.unit
def test_preview_pdf_writes_sibling_md(rag_root: Path, monkeypatch):
    (rag_root / "说明.pdf").write_bytes(b"%PDF-fake")

    def fake_pdf(_path: str) -> str:
        return "# 说明正文"

    monkeypatch.setattr(kb_files, "_parse_pdf", fake_pdf)
    result = kb_files.preview_document("说明.pdf")
    assert result["kind"] == "markdown"
    assert result["converted"] is True
    assert result["content"] == "# 说明正文"
    assert (rag_root / "说明.md").read_text(encoding="utf-8") == "# 说明正文"


@pytest.mark.unit
def test_preview_docx_reuses_existing_sibling_md(rag_root: Path, monkeypatch):
    (rag_root / "合同.docx").write_bytes(b"PK")
    (rag_root / "合同.md").write_text("已有", encoding="utf-8")

    def boom(_path: str) -> str:
        raise AssertionError("不应再解析")

    monkeypatch.setattr(kb_files, "_parse_docx", boom)
    result = kb_files.preview_document("合同.docx")
    assert result["content"] == "已有"
    assert result["converted"] is False
