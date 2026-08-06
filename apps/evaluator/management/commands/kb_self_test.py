"""KB self-test + diff management command.

Usage:
    python manage.py kb_self_test [--output report.json] [--verbose]

Performs test queries against the ChromaDB knowledge base and verifies
that retrieved fragments actually exist in the source files (anti-hallucination
check).  Outputs a scored report.
"""

from __future__ import annotations

import json

from pathlib import Path

from django.core.management.base import BaseCommand

ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent.parent

KB_TEST_QUERIES = [
    "如何创建测试用例",
    "设备状态有哪些",
    "XPath 定位策略",
    "AgentScope 是什么",
    "StepType 包含哪些步骤",
    "API 响应格式是什么",
    "如何锁定设备",
    "知识库怎么用",
    "测试用例结构字段",
    "平台架构层次",
]


class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument("--output", default="", help="Save JSON report to file.")
        parser.add_argument("--detail", action="store_true", help="Show per-fragment details.")

    def handle(self, **options):
        from apps.ai_assistant.api import get_kb_doc_count, search_knowledge

        detail = options["detail"]
        output_path = options.get("output") or ""

        if detail:
            self.stdout.write(f"ChromaDB collection: {get_kb_doc_count()} docs\n")

        results = []
        for query in KB_TEST_QUERIES:
            docs = search_knowledge(query, top_k=3)
            verified = []
            for d in docs:
                meta = d.get("metadata", {})
                source = meta.get("source", "")
                # Verify: check if source file exists and content is present
                verification = self._verify_fragment(d["content"], source)
                verified.append(
                    {
                        "source": source,
                        "score": round(d["score"], 4),
                        "content_preview": d["content"][:150],
                        **verification,
                    }
                )

            results.append(
                {
                    "query": query,
                    "total_hits": len(docs),
                    "top_score": round(docs[0]["score"], 4) if docs else 0,
                    "documents": verified,
                }
            )

            if detail:
                status = "OK" if docs else "EMPTY"
                self.stdout.write(f"  [{status}] {query} → {len(docs)} hits")

        # ── Scoring ──
        queries_with_hits = sum(1 for r in results if r["total_hits"] > 0)
        coverage = round(queries_with_hits / len(KB_TEST_QUERIES) * 100, 1)

        top_scores = [r["top_score"] for r in results if r["total_hits"] > 0]
        avg_score = round(sum(top_scores) / len(top_scores), 2) if top_scores else 0

        total_frags = sum(r["total_hits"] for r in results)
        verified_frags = sum(
            1 for r in results for d in r["documents"] if d.get("match_type") != "not_found"
        )
        accuracy = round(verified_frags / total_frags * 100, 1) if total_frags else 0

        report = {
            "test_queries": len(KB_TEST_QUERIES),
            "total_fragments": total_frags,
            "scores": {
                "coverage": coverage,  # % of queries with results
                "avg_relevance": avg_score,  # avg top-hit distance score
                "accuracy": accuracy,  # % of fragments found in source
            },
            "details": results,
        }

        # ── Output ──
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write("  [KB Self-Test Report]")
        self.stdout.write("=" * 60)
        self.stdout.write(f"  测试查询数:    {report['test_queries']}")
        self.stdout.write(f"  检索片段总数:  {report['total_fragments']}")
        self.stdout.write(f"  覆盖率:        {coverage}%  (有结果的查询占比)")
        self.stdout.write(f"  平均相关度:    {avg_score}  (Top-1 距离分)")
        self.stdout.write(f"  真实性:        {accuracy}%  (片段在源文件中存在)")
        self.stdout.write("=" * 60)

        if detail:
            self.stdout.write("\n  Query Details:")
            for r in results:
                self.stdout.write(f"  [{r['total_hits']} hits] {r['query']}")
                for d in r["documents"]:
                    icon = "OK" if d.get("match_type") != "not_found" else "??"
                    self.stdout.write(f"    {icon} {d['source']} (score={d['score']})")

        if output_path:
            out = Path(output_path)
            out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
            self.stdout.write(f"\n  Report saved to: {out}")

    # ── helpers ──

    def _verify_fragment(self, content: str, source: str) -> dict:
        """Check whether a KB fragment exists (or is derived from) its source file."""
        if not source or source == "generated":
            return {"match_type": "generated", "note": "Generated reference doc"}

        # Try to find the source file
        doc_dir = ROOT / "dev_docs"
        file_path = doc_dir / source
        if not file_path.exists():
            # ChromaDB stores relative path — try glob
            matches = list(doc_dir.rglob(source))
            if matches:
                file_path = matches[0]
            else:
                return {"match_type": "not_found", "note": f"Source file missing: {source}"}

        try:
            file_content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return {"match_type": "not_found", "note": "Cannot read source file"}

        # Truncated content check: ChromaDB truncates at 4000 chars, so we check
        # if the first N chars of the fragment appear in the file.
        check_len = min(len(content), 150)
        check_text = content[:check_len].strip()

        if check_text in file_content:
            return {"match_type": "exact", "note": ""}
        # Try shorter match
        check_text_short = content[:80].strip()
        if check_text_short in file_content:
            return {"match_type": "partial", "note": "80-char match found"}
        # Try keyword-based match
        keywords = [w for w in check_text_short.split() if len(w) >= 4]
        found_kw = sum(1 for kw in keywords if kw in file_content)
        if keywords and found_kw / len(keywords) >= 0.5:
            return {
                "match_type": "keyword",
                "note": f"{found_kw}/{len(keywords)} keywords found",
            }
        return {"match_type": "not_found", "note": "No match in source"}
