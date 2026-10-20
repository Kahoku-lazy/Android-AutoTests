"""
python -m 调试路径: engines.agents.workflow.ui_auto_workflow

本模块的业务功能如下：
1. AgentSOPWorkflow: 把一份 SOP 跑一次 UI 自动化, 事件与运行汇总都写入同一份事件日志。
"""

import asyncio

import yaml

from agentscope.agent import Agent
from agentscope.message import UserMsg
from agentscope.sop import SOP, SOPEngine, SOPStep

from engines.agents.event_log import write_line
from engines.agents.event_sink import set_step_context
from engines.agents.messaging.messages import AgentEventsShow
from engines.agents.role.agents import executor, verifier
from utils.logs import agent_event_log


class AgentSOPWorkflow:
    def __init__(self, executor: Agent, verifier: Agent):
        # executor: 执行角色的 Agent, 负责看页面、点设备
        # verifier: 验收角色的 Agent, 负责截图与查设备日志, 判这一步过不过
        self.log = agent_event_log
        self.executor = executor
        self.verifier = verifier
        self.model_name = str(getattr(getattr(executor, "model", None), "model", "") or "-")

        # 每一步被驳回几次后判失败, 由引擎执行, 不是步骤自己管
        self.MAX_ATTEMPTS = 2

    def dump(self, engine, sop) -> None:
        """流结束后回读运行状态：判决与交付都不在事件流里, 只能从这里看。

        Args:
            engine: 跑完的 SOPEngine, 状态在 engine.state。
            sop: 同一份 SOP, 用来取每步的步骤短名。

        Returns:
            None。
        """
        for index, record in enumerate(engine.state.steps, start=1):
            # record.submission: 这一步交付的内容块列表, 同时也是下一步的输入
            # 标准 SOPStep 交付的是一条 TextBlock; 被驳回时这里会被清回 None
            delivery = record.submission[0].text if record.submission else "-"
            self._log(f"第 {index} 步：{sop.steps[index - 1].subject}")
            # record.phase: 这一步的阶段, pending / running / awaiting / completed / failed
            # len(record.verifications): 已记几条判决 = 已尝试几次
            # record.given: 引擎交给这一步的输入, 第一步是开场输入, 之后是上一步的交付
            self._log(
                f"阶段 {record.phase.value}｜尝试 {len(record.verifications)} 次"
                f"｜引擎给了 {len(record.given)} 条输入"
            )
            self._log(f"交付：{delivery[:120]}")
            for order, verdict in enumerate(record.verifications, start=1):
                # verdict.passed: 这一次尝试过没过
                # verdict.message: 驳回说明, 不通过时会原样回灌给执行者, 所以要看清它
                # verdict.verifier: 谁判的, 模型名 / sop 兜底 / 人工
                self._log(
                    f"第 {order} 次判决 passed={verdict.passed}"
                    f" by={verdict.verifier}｜{verdict.message}"
                )

    async def run_workflow(self, name: str, steps: list[tuple[str, str]], run_input: str) -> None:
        """装配一份 SOP 并跑完一次：事件实时打屏, 结束后回读状态。

        Args:
            name: 流程名, 只用于日志与汇总, 模型看不到。
            steps: [(步骤描述, 需要达成的结果), ...], 一个二元组就是一步。
            run_input: 开场输入, 只交给第一步。

        Returns:
            运行阶段字符串。完成时为 completed。
        """
        # 一份 SOP = 一串 SOPStep; SOP 本身不含运行状态, 可以反复跑
        sop = SOP(
            name=name,
            steps=[
                SOPStep(
                    subject=subject,  # 步骤描述: 写进执行者的步骤提醒
                    description=description,  # 需要达成的结果: 只给验收者当判卷标准
                    executor=self.executor,  # 执行者: 干活的一侧
                    verifier=self.verifier,  # 验收者: 判卷的一侧
                    max_attempts=self.MAX_ATTEMPTS,  # 最大重试次数: 驳回几次后整轮失败
                )
                for subject, description in steps
            ],
        )

        engine = SOPEngine(sop)  # 引擎持有本次运行的状态, 即 engine.state

        try:
            buf: dict = {}  # 增量累积器: 块碎片、工具入参、工具返回都攒在这里
            # 发言开始早于模型调用, 「开始」行用角色上的模型名
            models = {
                self.executor.name: self.executor.model.model,
                self.verifier.name: self.verifier.model.model,
            }
            # 开场输入只交给第一步; 之后的步骤拿上一步的交付（handover）
            async for event in engine.reply_stream(UserMsg(name="user", content=run_input)):
                _stamp_step(engine)
                await show_event(event, buf, models)

        except Exception as exc:
            # 裸 SOPStep 不接工具异常：设备日志为空时会打到这里, 事件流当场结束
            # 此时该步停在 running: 既不记驳回也不重试
            # 注意 Exception 接不住 BaseExceptionGroup（带取消时 asyncio 抛的是它）
            self._log(f"事件流被异常打断：{type(exc).__name__}: {exc}")

        # 结论不在事件流里: 跑完必须回 engine.state 读
        # 阶段是 running / pending 说明事件流被打断了, 不是"还在跑"
        self._log(f"运行阶段：{engine.phase}")
        self.dump(engine, sop)
        phase = getattr(engine.phase, "value", engine.phase)
        return str(phase or "")

    def _log(self, action: str) -> None:
        """运行汇总写入与事件时间线同一份日志。模型名用执行者的模型。"""
        write_line(self.model_name, action)


async def show_event(event, buf: dict, models: dict | None) -> None:
    """在工作线程里折叠并交给接收方。事件循环里不查库。

    Django 未启动时仍在当前线程调用，供引擎本地调试使用。
    """
    if _django_ready():
        from channels.db import database_sync_to_async

        await database_sync_to_async(AgentEventsShow.show, thread_sensitive=False)(
            event, buf, models
        )
        return
    AgentEventsShow.show(event, buf, models)


def _django_ready() -> bool:
    """当前进程是否已完成 Django 启动。"""
    try:
        from django.apps import apps
    except ImportError:
        return False
    return bool(apps.ready)


def _stamp_step(engine) -> None:
    """把当前正在跑的步骤序号和尝试次数交给事件接收方。"""
    steps = list(getattr(getattr(engine, "state", None), "steps", []) or [])
    for index, record in enumerate(steps, start=1):
        phase = getattr(getattr(record, "phase", None), "value", "")
        if str(phase) in {"running", "awaiting"}:
            attempt = len(getattr(record, "verifications", []) or []) + 1
            set_step_context(index, attempt)
            return
    set_step_context(None, None)


def _case_sections(data) -> list[list]:
    """取出文件里所有「用例列表」。

    用例 YAML 有两种根节点写法，都要认：

    1. 列表：整个文件就是用例列表（旧写法）；
    2. 映射：按测试模块分节，节值是用例列表（如 `TestAgentsWorkflow`），
       其它节放的是参数而不是用例（如 `TestToolDevice: {serial: ...}`），跳过。

    Args:
        data: `yaml.safe_load` 的结果。

    Returns:
        用例列表的列表；认不出时返回空列表。
    """
    if isinstance(data, list):
        return [data]
    if isinstance(data, dict):
        return [value for value in data.values() if isinstance(value, list)]
    return []


def load_test_cases(yaml_path: str) -> dict[str, list[tuple[str, str]]]:
    """读用例 YAML, 返回 {用例名: [(步骤描述, 需要达成的结果), ...]}。"""
    # 显式 encoding="utf-8": Windows 默认编码是 GBK, 而用例 YAML 是 UTF-8
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return {
        str(case.get("title") or "").strip(): [  # title: 用例名
            (
                str(step.get("action") or "").strip(),  # action: 步骤描述, 给执行者
                str(step.get("assert") or "").strip(),  # assert: 需要达成的结果, 给验收者
            )
            for step in case.get("steps") or []
        ]
        for section in _case_sections(data)
        for case in section
        if isinstance(case, dict)
    }


def run_workflow(yml_path: str, run_input: str, case_title: str | None = None) -> None:
    """装配一份 SOP 并跑完一次：事件实时打屏, 结束后回读状态。

    Args:
        yml_path: 用例 YAML 路径。
        run_input: 开场输入, 只交给第一步。参数内容例如：本次要操作的设备 serial 是：R5CT62RH88F。每一步的设备动作都必须带上它。
        case_title: 用例名称，指定执行某条用例；如果为空，则执行所有用例。
    """
    cases = load_test_cases(yml_path)
    for title, steps in cases.items():
        if case_title and title != case_title:
            continue

        workflow = AgentSOPWorkflow(executor.agent, verifier.agent)
        asyncio.run(workflow.run_workflow(title, steps, run_input))
