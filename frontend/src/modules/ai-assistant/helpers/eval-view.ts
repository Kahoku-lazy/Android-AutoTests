import { EVAL_FAILED, EVAL_PASSED, EVAL_UNAVAILABLE } from "../constants"

export function evalBlocked(orchestration: string): string {
  return orchestration === "sop" || orchestration === "" ? "" : EVAL_UNAVAILABLE
}

export function evalVerdict(passed: boolean): string {
  return passed ? EVAL_PASSED : EVAL_FAILED
}
