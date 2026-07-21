"""Document loader — scans project documentation and generates reference docs."""
from pathlib import Path
from models.step_types import StepType, UI_LABELS

ROOT = Path(__file__).resolve().parent.parent.parent


def load_project_docs() -> list[dict]:
    """Scan dev_docs/ for markdown files and load them as knowledge docs."""
    docs = []
    doc_dir = ROOT / 'dev_docs'
    if not doc_dir.exists():
        return docs

    for md_file in doc_dir.rglob('*.md'):
        try:
            content = md_file.read_text(encoding='utf-8', errors='replace')
            if len(content) < 50:
                continue
            rel_path = str(md_file.relative_to(doc_dir))
            docs.append({
                "id": f"doc:{rel_path}",
                "content": content[:4000],  # truncate very long files
                "metadata": {
                    "source": rel_path,
                    "type": "project_doc",
                    "path": str(md_file),
                },
            })
        except Exception:
            pass
    return docs


def load_step_type_reference() -> list[dict]:
    """Generate reference documentation for all 14 step types."""
    lines = ["# 测试步骤类型参考\n"]
    for st in StepType:
        lines.append(f"## {st.value}")
        lines.append(f"- 中文名称: {UI_LABELS.get(st, '')}")
        lines.append(f"- 类型标识: `{st.value}`")
        lines.append("")

    lines.append("## 步骤结构字段")
    lines.append("- `type`: 步骤类型（必填）")
    lines.append("- `xpath`: 主要 XPath 定位表达式（必填）")
    lines.append("- `xpath2`: 备用 XPath（保留字段）")
    lines.append("- `timeout`: 超时时间，秒（默认 10）")
    lines.append("- `expected_text`: 期望文本（verify_text / poll_text）")
    lines.append("- `index`: wait / poll_text 的轮询间隔秒数")
    lines.append("- `description`: 步骤描述（必填）")

    content = "\n".join(lines)
    return [{
        "id": "ref:step_types",
        "content": content,
        "metadata": {"source": "generated", "type": "reference", "topic": "step_types"},
    }]


def load_all_documents() -> list[dict]:
    """Load all knowledge base documents."""
    docs = []
    docs.extend(load_project_docs())
    docs.extend(load_step_type_reference())
    return docs
