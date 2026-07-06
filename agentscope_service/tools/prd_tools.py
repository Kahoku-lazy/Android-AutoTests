"""PRD → test-case design tools — wraps iot-test-case-agent pipeline.

Provides three tools callable from the AI assistant:
  ParsePRDTool             — read a PRD file, auto-detect product info
  DesignTestCasesFromPRDTool — run the 3-phase design pipeline
  ImportDesignedCasesTool   — batch-save generated cases into cm_test_definitions
"""

import json
import os
import sys
import uuid
import tempfile
from pathlib import Path

from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior
from agentscope.message import TextBlock

from .db_helper import run_sync

# ── Lazy import of testcase_designer (may not be deployed in production) ──
_DESIGNER_AVAILABLE = False
try:
    _PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
    _DESIGNER_PATH = _PROJECT_ROOT / "PM-Project-main" / "iot-test-case-agent"
    if _DESIGNER_PATH.exists():
        sys.path.insert(0, str(_DESIGNER_PATH))
        from testcase_designer.config import ProductConfig, load_product_config, make_output_dir
        from testcase_designer.converters import convert_to_markdown
        from testcase_designer.run_auto import run_auto
        from testcase_designer import tools as _tc_tools

        _DESIGNER_AVAILABLE = True
except Exception:
    pass

# ── Session-scoped staging area for designed cases (before import) ──
_staged_cases: dict[str, list[dict]] = {}


class ParsePRDTool(ToolBase):
    """Read a PRD file and auto-detect product information."""

    name = "parse_prd"
    description = """解析 PRD 需求文档，自动提取产品信息和需求概要。

【触发条件】
  - 用户上传了 PRD 文档（.md / .docx / .pdf）
  - 需要从需求文档中了解产品功能和测试范围

【参数】
  - file_path: 需求文档的绝对路径（从文件上传结果获取）
  - 或 content: 需求文档的完整文本内容（当文件已在消息中时）

【返回】
  - 产品代号、产品名称、模块列表、需求概要
  - 如果 testcase_designer 可用，还会运行完整的矛盾分析"""
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "PRD 文件的绝对路径（如 /path/to/requirement.md）",
            },
            "content": {
                "type": "string",
                "description": "PRD 文档的完整文本内容（与 file_path 二选一）",
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only.")

    async def call(self, file_path="", content="", **kwargs):
        if not _DESIGNER_AVAILABLE:
            # Fallback: read file content manually
            if file_path and Path(file_path).exists():
                text = Path(file_path).read_text(encoding="utf-8")
            elif content:
                text = content
            else:
                return ToolChunk(
                    content=[
                        TextBlock(
                            text="【提示】PRD 解析器未部署（testcase_designer 不可用）。"
                            "请直接在对话中描述需求，我将帮你设计测试用例。"
                        )
                    ]
                )
            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps(
                            {
                                "status": "parsed_fallback",
                                "content_length": len(text),
                                "content_preview": text[:2000],
                                "message": "PRD 已读取（简化模式）。请 AI 直接基于内容设计用例。",
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            )

        # Full mode: use testcase_designer
        try:
            if file_path and Path(file_path).exists():
                content_text = convert_to_markdown(Path(file_path))
            elif content:
                # Save content to temp file for the pipeline
                tmpdir = Path(tempfile.gettempdir())
                tmpfile = tmpdir / f"prd_{uuid.uuid4().hex[:8]}.md"
                tmpfile.write_text(content, encoding="utf-8")
                file_path = str(tmpfile)
                content_text = content
            else:
                return ToolChunk(content=[TextBlock(text="请提供 file_path 或 content 参数。")])

            # Extract TOC
            import re

            toc = []
            for m in re.finditer(r"^(#{1,4})\s+(.+)$", content_text, re.MULTILINE):
                toc.append({"level": len(m.group(1)), "title": m.group(2).strip()})

            # Auto-detect product info
            from testcase_designer.web import _auto_detect

            info = _auto_detect(file_path) if file_path and Path(file_path).exists() else {}

            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps(
                            {
                                "status": "parsed",
                                "filename": Path(file_path).name if file_path else "inline",
                                "total_chars": len(content_text),
                                "toc": toc,
                                "product_code": info.get("product_code", ""),
                                "product_name": info.get("product_name", ""),
                                "module_name": info.get("module_name", ""),
                                "designer_available": True,
                                "message": (
                                    f"已解析 PRD 文档，共 {len(content_text)} 字，"
                                    f"{len(toc)} 个章节。"
                                    f"产品: {info.get('product_name', '未识别')}。"
                                    f"下一步：调用 design_test_cases_from_prd 生成用例。"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            )
        except Exception as e:
            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False)
                    )
                ]
            )


class DesignTestCasesFromPRDTool(ToolBase):
    """Run the iot-test-case-agent's 3-phase pipeline to design test cases from a PRD."""

    name = "design_test_cases_from_prd"
    description = """基于 PRD 需求文档，运行三阶段用例设计流水线，生成标准化测试用例。

【触发条件】
  - 用户要求"根据 PRD 生成测试用例"
  - parse_prd 完成后，用户确认要生成用例
  - 用户说"帮我设计用例" / "生成测试用例"

【流水线阶段】
  Phase 1: 需求分析 — 矛盾检测 → 复杂度 L1~L4 → 方案对比（2-3个方案）
  Phase 2: 用例生成 — 五法组合（场景流/等价类边界值/判定表/正交排列/错误推测）
  Phase 3: 质量审查 — 四维审计（捏造/数据不实/遗漏/缺陷），最多 2 轮修正

【参数】
  - file_path: PRD 文件路径
  - product_code: 产品代号（如 "H717D"）
  - product_name: 产品中文名（如 "智能制冰机"）
  - version: 版本号（默认 "V1"）
  - auto_mode: 是否全自动模式（默认 true，跳过方案选择交互）

【返回】
  - 生成的用例数量、设计思路摘要、文件路径
  - 用例数据暂存，等待调用 import_designed_cases 入库

【注意】此工具可能需要较长时间运行（2-5 分钟）"""
    input_schema = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "PRD 文件路径（必填）",
            },
            "product_code": {
                "type": "string",
                "description": "产品代号，如 H717D",
            },
            "product_name": {
                "type": "string",
                "description": "产品中文名，如 智能制冰机",
            },
            "product_name_en": {
                "type": "string",
                "description": "产品英文名（可选）",
            },
            "version": {
                "type": "string",
                "description": "版本号，默认 V1",
            },
            "auto_mode": {
                "type": "boolean",
                "description": "是否全自动模式（跳过方案选择）。默认 true。",
            },
        },
        "required": ["file_path"],
    }
    is_concurrency_safe = False
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(
            behavior=PermissionBehavior.ALLOW,
            message="Test case design is always allowed.",
        )

    async def call(
        self,
        file_path,
        product_code="",
        product_name="",
        product_name_en="",
        version="V1",
        auto_mode=True,
        **kwargs,
    ):
        if not _DESIGNER_AVAILABLE:
            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps(
                            {
                                "status": "unavailable",
                                "message": (
                                    "用例设计引擎（testcase_designer）未部署。"
                                    "我将基于 PRD 内容直接在对话中设计测试用例。"
                                    "请告诉我要测试的功能模块。"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            )

        if not Path(file_path).exists():
            return ToolChunk(content=[TextBlock(text=f"错误：PRD 文件不存在 — {file_path}")])

        try:
            import asyncio
            import threading

            config = ProductConfig(
                product_code=product_code,
                product_name=product_name,
                product_name_en=product_name_en,
            )

            output_dir = make_output_dir(version)
            _tc_tools._session_state["output_dir"] = output_dir
            _tc_tools._session_state["saved_documents"] = []

            result_holder = {"error": None, "output_dir": output_dir}

            def _run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(
                        run_auto(
                            requirement_file=file_path,
                            output_dir=output_dir,
                            version=version,
                            config=config,
                        )
                    )
                except Exception as e:
                    result_holder["error"] = str(e)
                finally:
                    loop.close()

            thread = threading.Thread(target=_run_in_thread, daemon=True)
            thread.start()
            thread.join(timeout=300)  # 5-minute timeout

            if thread.is_alive():
                return ToolChunk(
                    content=[
                        TextBlock(
                            text=json.dumps(
                                {
                                    "status": "timeout",
                                    "message": "用例设计超时（5分钟）。PRD 可能过大，请拆分后再试。",
                                },
                                ensure_ascii=False,
                            )
                        )
                    ]
                )

            if result_holder["error"]:
                return ToolChunk(
                    content=[
                        TextBlock(
                            text=json.dumps(
                                {"status": "error", "message": result_holder["error"]},
                                ensure_ascii=False,
                            )
                        )
                    ]
                )

            # Collect generated documents
            saved = _tc_tools._session_state.get("saved_documents", [])
            output_dir_path = Path(output_dir)

            # Parse generated test case files into structured data
            staged = []
            for doc_path in sorted(output_dir_path.glob("*.md")):
                if "用例设计思路" in doc_path.name or "评估报告" in doc_path.name:
                    continue
                if "测试用例" not in doc_path.name:
                    continue
                content_text = doc_path.read_text(encoding="utf-8")
                cases = _extract_test_case_rows(content_text)
                for c in cases:
                    c["_source_file"] = doc_path.name
                staged.extend(cases)

            # Also check CSV files
            for csv_path in sorted(output_dir_path.glob("*.csv")):
                cases = _extract_csv_rows(csv_path)
                for c in cases:
                    c["_source_file"] = csv_path.name
                staged.extend(cases)

            # Store in session-scoped staging
            session_id = output_dir_path.name
            _staged_cases[session_id] = staged

            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps(
                            {
                                "status": "designed",
                                "output_dir": output_dir,
                                "session_id": session_id,
                                "total_cases": len(staged),
                                "saved_files": [Path(f).name for f in saved],
                                "cases_preview": [
                                    {
                                        "id": c.get("id", ""),
                                        "title": c.get("title", ""),
                                        "priority": c.get("priority", "P1"),
                                        "method": c.get("method", ""),
                                    }
                                    for c in staged[:10]
                                ],
                                "message": (
                                    f"用例设计完成！共生成 {len(staged)} 条测试用例。"
                                    f"请调用 import_designed_cases 将用例入库。"
                                    f"session_id: {session_id}"
                                ),
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            )

        except Exception as e:
            import traceback

            return ToolChunk(
                content=[
                    TextBlock(
                        text=json.dumps(
                            {
                                "status": "error",
                                "message": str(e),
                                "traceback": traceback.format_exc()[:1000],
                            },
                            ensure_ascii=False,
                        )
                    )
                ]
            )


class ImportDesignedCasesTool(ToolBase):
    """Batch-import designed test cases into cm_test_definitions."""

    name = "import_designed_cases"
    description = """将 design_test_cases_from_prd 生成的测试用例批量导入到平台用例库。

【触发条件】
  - design_test_cases_from_prd 完成后
  - 用户说"导入用例" / "保存到用例库"

【参数】
  - session_id: 设计会话 ID（从 design_test_cases_from_prd 返回）
  - directory_id: 目标目录 ID（可选，从 list_test_cases 的目录树获取）
  - package_name: 目标 Android 包名（可选）
  - case_ids: 要导入的用例编号列表（可选，默认全部）
  - overwrite: 是否覆盖已存在的同名用例（默认 false）

【返回】
  - 导入成功/失败的用例数量"""
    input_schema = {
        "type": "object",
        "properties": {
            "session_id": {
                "type": "string",
                "description": "设计会话 ID（从 design_test_cases_from_prd 返回的 session_id）",
            },
            "directory_id": {
                "type": "integer",
                "description": "目标目录 ID（可选，从 get_directory_tree 获取）",
            },
            "package_name": {
                "type": "string",
                "description": "目标 Android 包名（可选，如 com.example.app）",
            },
            "case_ids": {
                "type": "array",
                "items": {"type": "string"},
                "description": "要导入的用例编号列表（可选，默认全部导入）",
            },
            "overwrite": {
                "type": "boolean",
                "description": "是否覆盖已存在的同名用例（默认 false）。",
            },
        },
        "required": ["session_id"],
    }
    is_concurrency_safe = False
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(
            behavior=PermissionBehavior.ALLOW,
            message="Case import is always allowed.",
        )

    async def call(
        self,
        session_id,
        directory_id=None,
        package_name="",
        case_ids=None,
        overwrite=False,
        **kwargs,
    ):
        staged = _staged_cases.get(session_id, [])
        if not staged:
            return ToolChunk(
                content=[
                    TextBlock(
                        text=f"会话 {session_id} 没有暂存的用例。请先运行 design_test_cases_from_prd。"
                    )
                ]
            )

        # Filter by case_ids if specified
        if case_ids:
            staged = [c for c in staged if c.get("id") in case_ids]
            if not staged:
                return ToolChunk(
                    content=[
                        TextBlock(
                            text=f"指定的用例编号未找到。可用编号: {[c.get('id') for c in _staged_cases.get(session_id, [])]}"
                        )
                    ]
                )

        # Verify directory exists if specified
        if directory_id is not None:
            from apps.case_manager.models import CaseDirectory

            try:
                await run_sync(lambda: CaseDirectory.objects.get(id=directory_id))
            except Exception:
                return ToolChunk(
                    content=[TextBlock(text=f"目录 ID {directory_id} 不存在。请先通过目录树确认。")]
                )

        from apps.case_manager.api import save_definition, get_definition

        imported = []
        skipped = []
        failed = []

        for case in staged:
            cid = case.get("id", "")
            title = case.get("title", "")
            if not cid or not title:
                failed.append({"reason": "missing id or title", "case": case})
                continue

            # Check for existing case
            existing = await run_sync(lambda: get_definition(cid))
            if existing and not overwrite:
                skipped.append({"id": cid, "title": title, "reason": "already exists"})
                continue

            try:
                # Build steps_json from narrative steps
                steps_text = case.get("steps", "")
                steps_data = [
                    {
                        "type": "log",
                        "description": steps_text[:500] if steps_text else "待补充测试步骤",
                    }
                ]

                await run_sync(
                    lambda cid=cid, title=title, case=case, steps_data=steps_data: save_definition(
                        case_id=cid,
                        title=title,
                        category=case.get("method", ""),
                        description=(
                            f"前置条件: {case.get('precondition', '无')}\n"
                            f"预期结果: {case.get('expected_result', '无')}\n"
                            f"量化指标: {case.get('metrics', '无')}"
                        ),
                        steps=case.get("steps", ""),
                        steps_data=steps_data,
                        enabled=False,  # Not executable until XPath added
                        package_name=package_name,
                        directory_id=directory_id,
                        priority=case.get("priority", "P1"),
                        design_method=case.get("method", ""),
                        precondition=case.get("precondition", ""),
                        expected_result=case.get("expected_result", ""),
                        metrics=case.get("metrics", ""),
                    )
                )
                imported.append({"id": cid, "title": title})
            except Exception as e:
                failed.append({"id": cid, "title": title, "reason": str(e)})

        # Clean up staging
        if not failed:
            _staged_cases.pop(session_id, None)

        return ToolChunk(
            content=[
                TextBlock(
                    text=json.dumps(
                        {
                            "status": "imported",
                            "imported": imported,
                            "imported_count": len(imported),
                            "skipped": skipped,
                            "skipped_count": len(skipped),
                            "failed": failed,
                            "failed_count": len(failed),
                            "message": (
                                f"导入完成：成功 {len(imported)} 条"
                                + (f"，跳过 {len(skipped)} 条（已存在）" if skipped else "")
                                + (f"，失败 {len(failed)} 条" if failed else "")
                                + (
                                    f"。用例已保存到用例库，可在 case-manager 中编辑 XPath 后执行。"
                                    if imported
                                    else ""
                                )
                            ),
                        },
                        ensure_ascii=False,
                    )
                )
            ]
        )


# ── Helpers ──


def _extract_test_case_rows(md_content: str) -> list[dict]:
    """Parse 9-column test case table rows from Markdown content.

    Columns: # | 用例编号 | 测试标题 | 方法 | 优先级 | 前置条件 | 测试步骤 | 预期结果 | 量化指标
    """
    import re

    rows = []
    in_table = False
    header_found = False

    for line in md_content.split("\n"):
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table and header_found:
                in_table = False
                header_found = False
            continue

        cells = [c.strip() for c in stripped.split("|")][1:-1]  # remove leading/trailing empties

        if not in_table and any(kw in stripped for kw in ["用例编号", "测试标题", "预期结果"]):
            in_table = True
            continue

        if in_table and not header_found and re.match(r"^[\s\-:|\s]+$", stripped):
            header_found = True
            continue

        if in_table and header_found and len(cells) >= 7:
            # Skip rows where first column is just a number
            if cells[0] and re.match(r"^\d+$", cells[0]):
                cells = cells[1:]

            row = {
                "id": cells[0] if len(cells) > 0 else "",
                "title": cells[1] if len(cells) > 1 else "",
                "method": cells[2] if len(cells) > 2 else "",
                "priority": cells[3] if len(cells) > 3 else "P1",
                "precondition": cells[4] if len(cells) > 4 else "",
                "steps": cells[5] if len(cells) > 5 else "",
                "expected_result": cells[6] if len(cells) > 6 else "",
                "metrics": cells[7] if len(cells) > 7 else "",
            }
            if row["id"] and row["title"]:
                rows.append(row)

    return rows


def _extract_csv_rows(csv_path: Path) -> list[dict]:
    """Parse test case rows from CSV file."""
    import csv

    rows = []
    try:
        with open(csv_path, encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append(
                    {
                        "id": row.get("用例编号", ""),
                        "title": row.get("测试标题", ""),
                        "method": row.get("方法", ""),
                        "priority": row.get("优先级", "P1"),
                        "precondition": row.get("前置条件", ""),
                        "steps": row.get("测试步骤", ""),
                        "expected_result": row.get("预期结果", ""),
                        "metrics": row.get("量化指标", ""),
                    }
                )
    except Exception:
        pass
    return rows
