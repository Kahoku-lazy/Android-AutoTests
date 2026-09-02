"""工作流层：只负责运行流程。设备执行 / 平台任务通过类区分。"""

from __future__ import annotations

import json
import logging

from typing import Literal

from agentscope.message import UserMsg
from pydantic import BaseModel, Field

from .model import DeviceExecution, PlatformTask

logger = logging.getLogger("ai_assistant.workflow")


# ── 数据契约 ──


class GoalPlan(BaseModel):
    """单个目标：目标 + 步骤 + 验收标准。"""

    goal: str = Field(description="目标描述")
    steps: list[str] = Field(description="执行步骤列表")
    verification: str = Field(description="验收标准")


class PlannerOutput(BaseModel):
    """规划模型输出：多目标列表。"""

    plans: list[GoalPlan] = Field(description="拆解后的目标列表（多目标依次执行）")


class FailedItem(BaseModel):
    """未通过的项。"""

    item: str = Field(description="未通过的那一步 / 目标项")
    reason: str = Field(description="未通过的原因")


class VerificationResult(BaseModel):
    """验收模型输出：二次确认结果。"""

    result: Literal["pass", "fail"] = Field(description="是否通过")
    completed: list[str] = Field(description="已完成的项")
    failed: list[FailedItem] = Field(description="未通过的项（带理由）")
    summary: str = Field(description="一句话总结")


# ── 工作流 ──


def _msg_text(content) -> str:
    """提取 Msg.content 的纯文本（兼容 str 与块列表）。"""
    if isinstance(content, str):
        return content
    return "".join(getattr(b, "text", "") for b in content or [])


def _empty_usage() -> dict:
    """任务级 token 用量累加器：总量 + 按模型拆分（供仪表盘计费）。"""
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_input_tokens": 0,
        "models": {},
    }


def _acc_usage(acc: dict, msg, model_name: str = "") -> None:
    """把一次 reply 的 usage 累加进任务级累加器（含按模型拆分）。"""
    usage = getattr(msg, "usage", None)
    if usage is None:
        return
    inp = int(getattr(usage, "input_tokens", 0) or 0)
    out = int(getattr(usage, "output_tokens", 0) or 0)
    hit = int(getattr(usage, "cache_input_tokens", 0) or 0)
    acc["input_tokens"] += inp
    acc["output_tokens"] += out
    acc["cache_input_tokens"] += hit
    if model_name:
        m = acc["models"].setdefault(
            model_name, {"input_tokens": 0, "output_tokens": 0, "cache_input_tokens": 0}
        )
        m["input_tokens"] += inp
        m["output_tokens"] += out
        m["cache_input_tokens"] += hit


class DeviceExecutionWorkflow:
    """设备执行工作流：planner → executor ↔ verifier 循环。"""

    def __init__(self, dev: DeviceExecution, serial: str = ""):
        self.dev = dev
        self.serial = serial
        self._usage = _empty_usage()

    async def _plan(self, user_input: str) -> list[GoalPlan]:
        logger.info("【① planner 输入】user_input=%r", user_input)
        msg = await self.dev.planner_agent.reply(
            UserMsg(name="user", content=user_input),
            structured_schema=PlannerOutput,
        )
        _acc_usage(self._usage, msg, self.dev.config.planner.model_name)
        out = msg.structured_output
        if not out:
            logger.warning("【① planner 输出】未返回结构化输出")
            return []
        plans = [GoalPlan(**p) for p in (out.get("plans") or [])]
        logger.info(
            "【① planner 输出】plans=%s",
            json.dumps([p.model_dump() for p in plans], ensure_ascii=False),
        )
        return plans

    async def _execute(self, plan: GoalPlan) -> str:
        steps_txt = "\n".join(f"{i}. {s}" for i, s in enumerate(plan.steps, 1))
        prompt = f"当前设备 serial：{self.serial}\n请按以下步骤在设备上真实执行：\n{steps_txt}"
        logger.info(
            "【executor 输入】goal=%r steps=%s",
            plan.goal,
            json.dumps(plan.steps, ensure_ascii=False),
        )
        msg = await self.dev.executor_agent.reply(UserMsg(name="user", content=prompt))
        _acc_usage(self._usage, msg, self.dev.config.executor.model_name)
        result = _msg_text(msg.content)
        logger.info("【executor 输出】result=%s", result)
        return result

    async def _verify(self, plan: GoalPlan, result: str) -> VerificationResult:
        prompt = (
            f"当前设备 serial：{self.serial}\n"
            f"验收标准：{plan.verification}\n"
            f"执行结果：{result}\n"
            f"请截图二次确认是否达成验收标准。"
        )
        logger.info(
            "【verifier 输入】verification=%r 执行结果=%s",
            plan.verification,
            result,
        )
        msg = await self.dev.verifier_agent.reply(
            UserMsg(name="user", content=prompt),
            structured_schema=VerificationResult,
        )
        _acc_usage(self._usage, msg, self.dev.config.verifier.model_name)
        out = msg.structured_output
        if out is None:
            verdict = VerificationResult(
                result="fail", completed=[], failed=[], summary="验收模型未返回结果"
            )
        else:
            verdict = VerificationResult(**out)
        logger.info(
            "【verifier 输出】result=%s completed=%s failed=%s summary=%s",
            verdict.result,
            json.dumps(verdict.completed, ensure_ascii=False),
            json.dumps([f.model_dump() for f in verdict.failed], ensure_ascii=False),
            verdict.summary,
        )
        return verdict

    async def run(self, user_input: str) -> dict:
        max_loops = self.dev.config.max_loops
        logger.info("=" * 60)
        logger.info(
            "【工作流开始】user_input=%r | planner=%s executor=%s verifier=%s max_loops=%d",
            user_input,
            self.dev.config.planner.model_name,
            self.dev.config.executor.model_name,
            self.dev.config.verifier.model_name,
            max_loops,
        )
        plans = await self._plan(user_input)
        if not plans:
            logger.error("【工作流】规划模型未产出目标 → 任务失败")
            return {
                "status": "fail",
                "message": "任务失败",
                "reason": "规划模型未产出目标",
                "usage": self._usage,
            }

        done: list[str] = []
        log: list[dict] = []
        for idx, plan in enumerate(plans, 1):
            logger.info("【② 目标 %d/%d】goal=%r", idx, len(plans), plan.goal)
            # 每个目标独立上下文：清空 executor/verifier 的历史消息与截图，
            # 避免跨目标累积（旧截图/旧消息）干扰当前目标执行与验收。
            self.dev.executor_agent.state.context.clear()
            self.dev.verifier_agent.state.context.clear()
            verdict = None
            for loop in range(max_loops):
                logger.info("【② 目标 %d 内层循环 %d/%d】开始", idx, loop + 1, max_loops)
                result = await self._execute(plan)
                verdict = await self._verify(plan, result)
                log.append({"goal": plan.goal, "loop": loop + 1, "result": verdict.result})
                if verdict.result == "pass":
                    logger.info("【② 目标 %d 循环 %d】验收 pass → 进入下一个目标", idx, loop + 1)
                    done.extend(verdict.completed)
                    break
                logger.warning(
                    "【② 目标 %d 循环 %d】验收 fail → 退回 failed=%s 给 executor 重试",
                    idx,
                    loop + 1,
                    json.dumps([f.model_dump() for f in verdict.failed], ensure_ascii=False),
                )
            if verdict is None or verdict.result != "pass":
                logger.error("【② 目标 %d】循环用尽（%d 次）仍 fail → 任务失败", idx, max_loops)
                return {
                    "status": "fail",
                    "message": "任务失败",
                    "failed_goal": plan.goal,
                    "failed": [f.model_dump() for f in verdict.failed] if verdict else [],
                    "log": log,
                    "usage": self._usage,
                }
        logger.info(
            "【工作流结束】全部目标 pass，completed=%s",
            json.dumps(done, ensure_ascii=False),
        )
        return {"status": "success", "completed": done, "log": log, "usage": self._usage}


class PlatformTaskWorkflow:
    """平台任务工作流：planner → executor ↔ verifier 循环（设备可选）。"""

    def __init__(self, pt: PlatformTask, serial: str = ""):
        self.pt = pt
        self.serial = serial
        self._usage = _empty_usage()

    async def _plan(self, user_input: str, requirements: str = "") -> list[GoalPlan]:
        prompt = user_input if not requirements else f"{user_input}\n任务要求：{requirements}"
        logger.info("【① planner 输入】user_input=%r requirements=%r", user_input, requirements)
        msg = await self.pt.planner_agent.reply(
            UserMsg(name="user", content=prompt),
            structured_schema=PlannerOutput,
        )
        _acc_usage(self._usage, msg, self.pt.config.planner.model_name)
        out = msg.structured_output
        if not out:
            logger.warning("【① planner 输出】未返回结构化输出")
            return []
        plans = [GoalPlan(**p) for p in (out.get("plans") or [])]
        logger.info(
            "【① planner 输出】plans=%s",
            json.dumps([p.model_dump() for p in plans], ensure_ascii=False),
        )
        return plans

    async def _execute(self, plan: GoalPlan, report_name: str = "") -> str:
        steps_txt = "\n".join(f"{i}. {s}" for i, s in enumerate(plan.steps, 1))
        prompt = f"请完成以下目标的步骤：\n{steps_txt}"
        if self.serial:
            prompt = f"设备 serial：{self.serial}\n{prompt}"
        if report_name:
            prompt += f"\n报告/产物命名：{report_name}"
        logger.info(
            "【executor 输入】goal=%r steps=%s",
            plan.goal,
            json.dumps(plan.steps, ensure_ascii=False),
        )
        msg = await self.pt.executor_agent.reply(UserMsg(name="user", content=prompt))
        _acc_usage(self._usage, msg, self.pt.config.executor.model_name)
        result = _msg_text(msg.content)
        logger.info("【executor 输出】result=%s", result)
        return result

    async def _verify(self, plan: GoalPlan, result: str, checklist: str = "") -> VerificationResult:
        verification = (
            plan.verification if not checklist else f"{plan.verification}\n校验清单：{checklist}"
        )
        prompt = (
            f"验收标准：{verification}\n执行结果：{result}\n请用查询工具二次确认是否达成验收标准。"
        )
        logger.info("【verifier 输入】verification=%r 执行结果=%s", plan.verification, result)
        msg = await self.pt.verifier_agent.reply(
            UserMsg(name="user", content=prompt),
            structured_schema=VerificationResult,
        )
        _acc_usage(self._usage, msg, self.pt.config.verifier.model_name)
        out = msg.structured_output
        if out is None:
            verdict = VerificationResult(
                result="fail", completed=[], failed=[], summary="验收模型未返回结果"
            )
        else:
            verdict = VerificationResult(**out)
        logger.info(
            "【verifier 输出】result=%s completed=%s failed=%s summary=%s",
            verdict.result,
            json.dumps(verdict.completed, ensure_ascii=False),
            json.dumps([f.model_dump() for f in verdict.failed], ensure_ascii=False),
            verdict.summary,
        )
        return verdict

    async def run(
        self,
        user_input: str,
        requirements: str = "",
        checklist: str = "",
        report_name: str = "",
    ) -> dict:
        max_loops = self.pt.config.max_loops
        logger.info("=" * 60)
        logger.info(
            "【工作流开始】user_input=%r | planner=%s executor=%s verifier=%s max_loops=%d",
            user_input,
            self.pt.config.planner.model_name,
            self.pt.config.executor.model_name,
            self.pt.config.verifier.model_name,
            max_loops,
        )
        plans = await self._plan(user_input, requirements)
        if not plans:
            logger.error("【工作流】规划模型未产出目标 → 任务失败")
            return {
                "status": "fail",
                "message": "任务失败",
                "reason": "规划模型未产出目标",
                "usage": self._usage,
            }

        done: list[str] = []
        log: list[dict] = []
        for idx, plan in enumerate(plans, 1):
            logger.info("【② 目标 %d/%d】goal=%r", idx, len(plans), plan.goal)
            # 每个目标独立上下文：清空 executor/verifier 的历史消息，避免跨目标干扰
            self.pt.executor_agent.state.context.clear()
            self.pt.verifier_agent.state.context.clear()
            verdict = None
            for loop in range(max_loops):
                logger.info("【② 目标 %d 内层循环 %d/%d】开始", idx, loop + 1, max_loops)
                result = await self._execute(plan, report_name)
                verdict = await self._verify(plan, result, checklist)
                log.append({"goal": plan.goal, "loop": loop + 1, "result": verdict.result})
                if verdict.result == "pass":
                    logger.info("【② 目标 %d 循环 %d】验收 pass → 进入下一个目标", idx, loop + 1)
                    done.extend(verdict.completed)
                    break
                logger.warning(
                    "【② 目标 %d 循环 %d】验收 fail → 退回 failed=%s 给 executor 重试",
                    idx,
                    loop + 1,
                    json.dumps([f.model_dump() for f in verdict.failed], ensure_ascii=False),
                )
            if verdict is None or verdict.result != "pass":
                logger.error("【② 目标 %d】循环用尽（%d 次）仍 fail → 任务失败", idx, max_loops)
                return {
                    "status": "fail",
                    "message": "任务失败",
                    "failed_goal": plan.goal,
                    "failed": [f.model_dump() for f in verdict.failed] if verdict else [],
                    "log": log,
                    "usage": self._usage,
                }
        logger.info(
            "【工作流结束】全部目标 pass，completed=%s",
            json.dumps(done, ensure_ascii=False),
        )
        return {"status": "success", "completed": done, "log": log, "usage": self._usage}
