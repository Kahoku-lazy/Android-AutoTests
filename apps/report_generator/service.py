"""Report generation — CSV / Markdown / JSON (from core/report.py)."""

import json
import re

from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
LOG_DIR = BASE_DIR / "logs"
EXPORT_DIR = BASE_DIR / "exports"

# Windows + cross-platform invalid filename characters
_INVALID_FILENAME_CHARS = re.compile(r'[<>:"/\\|?*]')


def _sanitize_filename(name: str, max_len: int = 40) -> str:
    """Replace invalid filename characters and trim to max_len."""
    safe = _INVALID_FILENAME_CHARS.sub("_", name)
    # Collapse consecutive underscores
    safe = re.sub(r"_+", "_", safe)
    # Strip leading/trailing underscores and whitespace
    safe = safe.strip("_ \t")
    if not safe:
        safe = "unnamed"
    return safe[:max_len]


class ReportGenerator:
    @staticmethod
    def save_csv(result: dict, failure_details: list[dict] = None) -> str:
        """Append one case result to its per-case CSV file.

        Each test case gets its own CSV: {case_title}.csv
        Subsequent runs append rows to the same file.
        """
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        safe_name = _sanitize_filename(result.get("case_title", "unnamed"), max_len=40)
        csv_path = LOG_DIR / f"{safe_name}.csv"

        exists = csv_path.exists()
        with open(csv_path, "a", encoding="utf-8-sig") as f:
            if not exists:
                f.write("用例名称,测试步骤,计划轮次,实际执行,通过,失败,成功率,时间\n")
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(
                f"{result['case_title']},{result['case_steps']},{result['planned']},"
                f"{result['actual']},{result['pass']},{result['fail']},{result['rate']},{ts}\n"
            )

        if failure_details:
            ReportGenerator._save_failure_md(str(csv_path), failure_details, [result])

        return str(csv_path)

    @staticmethod
    def _save_failure_md(base_path: str, failure_details: list, all_results: list):
        md_path = Path(base_path).with_suffix("").as_posix() + "_failures.md"
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(f"# 测试失败详情\n\n")
            f.write(f"生成时间: {datetime.now().isoformat()}\n\n")
            for r in all_results:
                f.write(f"## {r['case_title']} — 通过率: {r['rate']}\n\n")
                case_failures = [
                    fd for fd in failure_details if fd["case_title"] == r["case_title"]
                ]
                for fd in case_failures:
                    f.write(f"### 第 {fd['iteration']} 轮\n")
                    f.write(f"- 耗时: {fd['elapsed_ms']}ms\n")
                    f.write(f"- 日志:\n```\n")
                    for line in fd.get("log", []):
                        f.write(f"{line}\n")
                    f.write("```\n\n")

    @staticmethod
    def save_log(run_id: str, log_lines: list[str], case_name: str = "") -> str:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = _sanitize_filename(case_name or run_id, max_len=30)
        log_path = LOG_DIR / f"{name}_{ts}.log"
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Run ID: {run_id}\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write("-" * 40 + "\n")
            for line in log_lines:
                f.write(f"{line}\n")
        return str(log_path)

    @staticmethod
    def generate_json_report(results: list, failure_details: list) -> str:
        return json.dumps(
            {
                "generated_at": datetime.now().isoformat(),
                "total_cases": len(results),
                "total_failures": len(failure_details),
                "results": results,
                "failures": failure_details,
            },
            ensure_ascii=False,
            indent=2,
        )

    @staticmethod
    def save_json_report(results: list, failure_details: list) -> str:
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = EXPORT_DIR / f"report_{ts}.json"
        path.write_text(
            ReportGenerator.generate_json_report(results, failure_details), encoding="utf-8"
        )
        return str(path)
