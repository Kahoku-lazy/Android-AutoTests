"""生成设备日志关键词表 —— 把 dev_docs/1.txt 转成 config/device_log_keywords.json。

源表是制表符分隔的三列：功能点 / 功能模块 / 串口日志功能点关键字；同一功能点有多个关键字时，
续行只写关键字（例如 `set_video_drama_success` 紧跟在 `游戏/戏剧` 之后），本脚本把续行并入上一条。

编号规则：id 从 0 起按源表从上到下连续编号，一个功能点一个 id；同一个功能点挂在多个关键字下时
共用同一个 id，因此按关键字索引时 id 不连续。

用法：
    python tools/gen_device_log_keywords.py            # 生成数据文件
    python tools/gen_device_log_keywords.py --check     # 只校验，不写文件（CI / 关单用）
"""

from __future__ import annotations

import argparse
import json
import sys

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "dev_docs" / "1.txt"
TARGET = ROOT / "config" / "device_log_keywords.json"
HEADER_FIRST_CELL = "功能点"


def parse_features(text: str) -> list[dict]:
    """源表 → 功能点列表（按源表顺序，含 keywords 多值）。"""
    features: list[dict] = []
    for raw in text.splitlines():
        if not raw.strip():
            continue
        cells = [cell.strip() for cell in raw.split("\t")]
        if cells[0] == HEADER_FIRST_CELL or cells[0] == "":
            continue
        if len(cells) >= 3:
            feature = cells[0].rstrip("：:")
            features.append({"module": cells[1], "feature": feature, "keywords": [cells[2]]})
        elif features:
            # 续行：只有关键字一列，归到上一条功能点
            keywords: list[str] = features[-1]["keywords"]
            if cells[0] not in keywords:
                keywords.append(cells[0])
    return features


def build_payload(features: list[dict]) -> dict:
    """功能点列表 → 数据文件结构（关键字为主索引）。"""
    keywords: dict[str, list[dict]] = {}
    for index, item in enumerate(features):
        entry = {"id": index, "module": item["module"], "feature": item["feature"]}
        for keyword in item["keywords"]:
            keywords.setdefault(keyword, []).append(entry)
    return {
        "source": "dev_docs/1.txt",
        "description": "串口日志关键词 → 功能模块 / 功能点 对照表；由 tools/gen_device_log_keywords.py 生成，请勿手改",
        "feature_count": len(features),
        "keyword_count": len(keywords),
        "keywords": keywords,
    }


def render(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="生成设备日志关键词表数据文件")
    parser.add_argument("--check", action="store_true", help="只校验数据文件与源表是否一致")
    args = parser.parse_args()

    if not SOURCE.exists():
        sys.stderr.write(f"源表不存在: {SOURCE}\n")
        return 1

    payload = build_payload(parse_features(SOURCE.read_text(encoding="utf-8")))
    content = render(payload)

    if args.check:
        if not TARGET.exists():
            sys.stderr.write(
                f"数据文件不存在: {TARGET}（执行 python tools/gen_device_log_keywords.py 生成）\n"
            )
            return 1
        if TARGET.read_text(encoding="utf-8") != content:
            sys.stderr.write(f"数据文件与源表不一致: {TARGET}（重新执行生成脚本）\n")
            return 1
        print(
            f"OK 关键词表一致：{payload['feature_count']} 个功能点 / {payload['keyword_count']} 个关键词"
        )
        return 0

    TARGET.write_text(content, encoding="utf-8")
    print(f"已生成 {TARGET}")
    print(f"  功能点 {payload['feature_count']} 个 / 关键词 {payload['keyword_count']} 个")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
