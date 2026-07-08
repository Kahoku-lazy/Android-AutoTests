"""
Test-Runner 全功能自动化测试.

用法:
    python run_tests.py                    # 全量
    python run_tests.py --layer API        # API 层
    python run_tests.py --layer DB         # DB 层
    python run_tests.py --case TR-API-01   # 单条
"""
import sys, os, time, argparse

_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path:
    sys.path.insert(0, _current_dir)

import helpers as H
import api_tests   # noqa: F401
import db_tests    # noqa: F401
import ui_tests    # noqa: F401


def run_tests(layer=None):
    passed = 0; failed = 0; skipped = 0
    tests_to_run = {}
    for cid, (tl, tf, desc) in H.ALL_TESTS.items():
        if layer and tl != layer:
            continue
        tests_to_run[cid] = (tl, tf, desc)

    print(f"\n{'='*50}")
    print(f"  Test-Runner Functional Tests")
    print(f"  Layer: {layer or 'ALL'}, Cases: {len(tests_to_run)}")
    print(f"{'='*50}\n")

    for cid, (tl, tf, desc) in tests_to_run.items():
        try:
            result = tf()
            if result is None:
                skipped += 1
            elif result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            failed += 1
            H.record(cid, tl, desc, False, str(e), "no exception", 0)

    print(f"\n{'='*50}")
    print(f"  Results: {passed} PASS, {failed} FAIL, {skipped} SKIP, {len(tests_to_run)} total")
    print(f"{'='*50}")

    # Cleanup
    H.cleanup_all()

    return passed, failed, skipped


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--layer", choices=["API", "DB", "UI"], help="Test layer")
    parser.add_argument("--case", help="Single test case ID")
    args = parser.parse_args()

    if args.case:
        entry = H.ALL_TESTS.get(args.case)
        if not entry:
            print(f"Unknown case: {args.case}")
            sys.exit(1)
        tl, tf, desc = entry
        try:
            ok = tf()
            if ok is None:
                print(f"SKIP {args.case} — {desc}")
            else:
                status = "PASS" if ok else "FAIL"
                print(f"[{status}] {args.case} — {desc}")
        except Exception as e:
            print(f"[FAIL] {args.case} — {e}")
        H.cleanup_all()
    else:
        run_tests(layer=args.layer)
