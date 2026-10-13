"""规划智能体验收测试（零 Django）—— 四层结构：输入 → 运行 → 验收 → 报告。

层级约定
    第 1 层 输入数据：四键 JSON（任务标题 / 任务目标 / 附件文本内容 / 设备ID）
    第 2 层 运行脚本：调用规划智能体（PlannerRole），拿回原始输出 / 用量 / 费用 / 耗时
    第 3 层 结构验收：按规则逐条判定模型输出（契约、控件表述、日志口径、步骤顺序）
    第 4 层 输出报告：控制台分层打印 + Markdown 报告落 tests/reports/planner_acceptance/

用法
    python tests/ai_planner/planner_acceptance.py                    # 跑全部输入
    python tests/ai_planner/planner_acceptance.py --only classic
    python tests/ai_planner/planner_acceptance.py --with-context     # 附件里并入界面状态说明
    python tests/ai_planner/planner_acceptance.py --model deepseek-v4-pro
    python tests/ai_planner/planner_acceptance.py --raw              # 附加打印模型原始输出

密钥：环境变量 DEEPSEEK_API_KEY → 仓库根 .env 的 DEEPSEEK_API_KEY。
网络：默认对本 API 主机旁路系统代理（本机系统代理不通时会表现为 TLS 握手被中断）。
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import pathlib
import re
import sys
import time

from dataclasses import dataclass, field
from datetime import datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from engines.ai.agents import ModelConfig, PlannerRole  # noqa: E402
from engines.ai.base import ToolSpec  # noqa: E402
from engines.ai.workflow.workflow import Plan, Step, _coerce, _parse_json  # noqa: E402

DEEPSEEK_BASE_URL = "https://api.deepseek.com/v1"
API_HOST = "api.deepseek.com"
KEY_NAME = "DEEPSEEK_API_KEY"
REPORT_DIR = ROOT / "tests" / "reports" / "planner_acceptance"

# ══════════════════════════════════════════════════════════════════════════
# 运行环境（密钥 / 代理 / 控制台输出）
# ══════════════════════════════════════════════════════════════════════════


def read_env_file(path: pathlib.Path) -> dict[str, str]:
    """极简 .env 解析：KEY=VALUE，忽略注释与空行，去掉成对引号与行尾注释。"""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        value = value.split(" #", 1)[0].strip() if " #" in value else value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        if key.strip():
            values[key.strip()] = value
    return values


def resolve_api_key(env_file: pathlib.Path) -> tuple[str, str]:
    """返回 (密钥, 来源说明)：先环境变量，再 .env。"""
    value = (os.environ.get(KEY_NAME) or "").strip()
    if value:
        return value, f"环境变量 {KEY_NAME}"
    value = (read_env_file(env_file).get(KEY_NAME) or "").strip()
    if value:
        return value, f"{env_file.name} 的 {KEY_NAME}"
    return "", ""


def bypass_system_proxy_for_api() -> None:
    """把 API 主机加入 NO_PROXY：避免被不通的本地系统代理劫持（表现为 TLS 握手中断）。"""
    hosts = [h.strip() for h in os.environ.get("NO_PROXY", "").split(",") if h.strip()]
    for host in (API_HOST, f".{API_HOST.split('.', 1)[1]}"):
        if host not in hosts:
            hosts.append(host)
    os.environ["NO_PROXY"] = os.environ["no_proxy"] = ",".join(hosts)


def say(text: str = "") -> None:
    """控制台输出：GBK 控制台写不出 ✕ / ✓（样式栏的关键控件），换成 [X] / [V] 保持可读。"""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(enc)
    except (UnicodeEncodeError, LookupError):
        for raw, ascii_form in (("✕", "[X]"), ("✓", "[V]"), ("｜", "|"), ("·", ".")):
            text = text.replace(raw, ascii_form)
        try:
            text.encode(enc)
        except (UnicodeEncodeError, LookupError):
            text = text.encode(enc, errors="replace").decode(enc, errors="replace")
    print(text)


def normalize(text: str) -> str:
    """统一比较口径：全角竖线/空格等归一，便于按关键词判定。"""
    return (text or "").replace("｜", "|").replace("　", " ").strip()


# ══════════════════════════════════════════════════════════════════════════
# 第 1 层：输入数据（四键 JSON 结构）
# ══════════════════════════════════════════════════════════════════════════

# 测试点原文（来自 logs/01/H6810自动化测试点.md）
ATTACH_CLASSIC = (
    "经典页面功能测试：\n"
    "1. 长按H6810设备卡片页，选择经典，点击保存成功。\n"
    "2. 点击经典卡片页上的开关OFF/ON，日志断言是否开关成功。\n"
    "3. 检查经典卡片页上WIFI&蓝牙 图标显示正确。\n"
)
ATTACH_DYNAMIC = (
    "灵动页面功能测试：\n"
    "1. 长按H6810设备卡片页，选择灵动，点击保存成功\n"
    "2. 检查灵动卡片页上WIFI&蓝牙 图标显示正确。\n"
    "3. 点击灵动卡片页上的开关OFF/ON，日志断言是否开关成功。\n"
)

# 界面状态说明（`--with-context` 时并入「附件文本内容」，与业务文档口径一致）
CONTEXT = (
    "【界面状态说明 · 设备列表页（卡片页）】\n"
    "一、整段交互在同一页，不跳转页面\n"
    "- 普通态 S0：页头第一行是标题「设备」＋右侧功能图标，其下有「全部 / AI 设备」标签行与设备卡片网格。\n"
    "- 长按卡片后（样式选择模式 S1）：同一页顶部换了一条栏（不是弹窗、不是新页面、无遮罩）："
    "第一行为「左 ✕ 取消 · 中间『灵动 | 经典』分段切换 · 右 ✓ 保存」，下方多出一行"
    "「卡片大小同步应用到同类设备」＋复选圈，卡片网格仍在。\n"
    "- 保存后（S2）：没有任何保存结果提示；判断已保存、已回到普通态的唯一依据是："
    "① 顶部那一行恢复为标题「设备」＋右侧功能图标（✕ / 分段 / ✓ 与同步行全部消失）；"
    "② 目标卡片已变成所选样式的布局。\n"
    "二、经典样式卡片\n"
    "- 布局：设备图靠左，名称在图右侧同一行；卡片下半部是「ON | OFF」文字分段开关，点哪一半即开或关。\n"
    "- 连接：WiFi 与蓝牙连接成功后，卡片右上角出现蓝色蓝牙图标＋蓝色 WiFi 图标；未连接时右上角显示红色 WiFi 斜杠图标。\n"
    "三、灵动样式卡片\n"
    "- 布局：名称在卡片左上角，设备图在名称下方；卡片右下角是圆形电源按钮（按钮上没有文字）。\n"
    "- 连接：连接成功后卡片右上角出现蓝色蓝牙图标＋蓝色 WiFi 图标；未连接时名称下方显示「设备离线」。\n"
    "- 注意：灵动卡片上没有 ON / OFF 文字控件。\n"
    "四、规划时必须遵守\n"
    "1. 长按后的界面写成“同页顶部出现样式栏”，不要写成弹窗 / 菜单 / 新页面。\n"
    "2. 保存动作写成“点击右上角 ✓”，不存在文字「保存」按钮，也不存在保存成功提示。\n"
    "3. 检查蓝牙 / WiFi 图标前必须先有一步“等待设备 WiFi 与蓝牙连接成功”，图标在卡片右上角。\n"
    "4. 开关类步骤的结果一律由设备日志断言；禁止用页面表现（选中态、按钮颜色）作为断言依据。\n"
)


@dataclass
class PlannerInput:
    """一条输入：严格按四键 JSON 结构组装。"""

    case_id: str
    title: str
    goal: str
    attach: str
    device: str = ""
    style: str = "classic"  # classic | dynamic：决定开关控件形态的验收口径
    steps_range: tuple[int, int] = (3, 12)

    def payload(self, *, context: str = "") -> str:
        """四键中文 JSON（无 markdown 包裹），键序固定；`context` 非空时并入「附件文本内容」。"""
        attach = f"{context}\n【测试点】\n{self.attach}" if context else self.attach
        return json.dumps(
            {
                "任务标题": self.title,
                "任务目标": self.goal,
                "附件文本内容": attach,
                "设备ID": self.device,
            },
            ensure_ascii=False,
        )


def build_inputs() -> list[PlannerInput]:
    """输入清单：经典 / 灵动两条。"""
    return [
        PlannerInput(
            case_id="classic",
            title="经典页面功能测试（H6810 卡片页）",
            goal="按附件中的测试点，完成 H6810 设备卡片页「经典页面」的功能测试",
            attach=ATTACH_CLASSIC,
            style="classic",
        ),
        PlannerInput(
            case_id="dynamic",
            title="灵动页面功能测试（H6810 卡片页）",
            goal="按附件中的测试点，完成 H6810 设备卡片页「灵动页面」的功能测试",
            attach=ATTACH_DYNAMIC,
            style="dynamic",
        ),
    ]


# ══════════════════════════════════════════════════════════════════════════
# 第 2 层：运行脚本（调用模型）
# ══════════════════════════════════════════════════════════════════════════


@dataclass
class RunResult:
    """一次运行的产物。"""

    case: PlannerInput
    model: str
    seconds: float
    usage: dict
    cost: float
    raw: str
    plan: Plan | None

    @property
    def cost_text(self) -> str:
        return f"{self.cost:.6f} 元"


def build_stub_tools(flow_detail: str = "") -> list[ToolSpec]:
    """页面流工具的**桩实现**：工具必须存在。

    规划提示词要求"先列页面流、再读某篇摘要"；若一把工具都不给，模型会直接吐出工具调用碎片，
    导致解析不出计划（实测发生过）。桩让工具可用：默认返回空清单，`--flow` 传文件时返回该摘要。
    """
    if flow_detail:
        listing = json.dumps(
            {"total": 1, "documents": [{"doc_id": "LOCAL-FLOW", "title": "本地注入的页面流摘要"}]},
            ensure_ascii=False,
        )
    else:
        listing = json.dumps({"total": 0, "documents": []}, ensure_ascii=False)
    detail = flow_detail or json.dumps({"error": "本地未注入页面流摘要"}, ensure_ascii=False)

    def list_page_flows(query: str = "", user_id: str = "") -> str:
        return listing

    def get_page_flow(doc_id: str = "", user_id: str = "") -> str:
        return detail

    return [
        ToolSpec(name="list_page_flows", handler=list_page_flows, read_only=True, auto_allow=True),
        ToolSpec(name="get_page_flow", handler=get_page_flow, read_only=True, auto_allow=True),
    ]


def build_role(model_name: str, api_key: str, tools: list[ToolSpec]) -> PlannerRole:
    """与生产同一份角色实现（提示词与工具子集都取自 config.py）；工具用桩，读库部分留在 Django 侧。"""
    return PlannerRole(
        ModelConfig(
            provider="deepseek",
            model_name=model_name,
            api_key=api_key,
            base_url=DEEPSEEK_BASE_URL,
        ),
        tools=tools,
    )


def run_one(case: PlannerInput, role: PlannerRole, *, context: str) -> RunResult:
    """跑一条输入：调模型 → 解析计划。"""
    payload = case.payload(context=context)
    role.reset_context()  # 每条输入独立上下文，与生产“每步清上下文”一致
    started = time.perf_counter()
    result = asyncio.run(role.run(payload))
    seconds = time.perf_counter() - started

    plan = None
    parsed = _parse_json(result.output or "")
    if parsed:
        plan = _coerce(Plan, parsed.get("plan"))

    return RunResult(
        case=case,
        model=role.model_name,
        seconds=seconds,
        usage=dict(result.usage or {}),
        cost=float(result.cost or 0.0),
        raw=result.output or "",
        plan=plan,
    )


def run_all(
    cases: list[PlannerInput],
    model_name: str,
    api_key: str,
    *,
    context: str = "",
    flow_detail: str = "",
) -> list[RunResult]:
    role = build_role(model_name, api_key, build_stub_tools(flow_detail))
    results: list[RunResult] = []
    for case in cases:
        results.append(run_one(case, role, context=context))
    return results


# ══════════════════════════════════════════════════════════════════════════
# 第 3 层：结构验收（按规则判定模型输出）
# ══════════════════════════════════════════════════════════════════════════

PASS, FAIL, NA = "pass", "fail", "n/a"

SWITCH_HINTS = ("开关", "ON", "OFF", "电源")
ICON_HINTS = ("蓝牙", "WiFi", "WIFI", "wifi")
ICON_ACTION_HINTS = ("检查", "查看", "确认", "核对")
PAGE_STATE_WORDS = ("选中态", "选中状态", "灰色", "蓝色", "变为蓝", "变为灰", "颜色")
FAKE_FEEDBACK_WORDS = ("提示保存成功", "显示保存成功", "保存成功提示", "保存成功")
POPUP_WORDS = ("弹窗", "弹出菜单", "菜单中", "设置菜单")
NEGATIONS = ("不是", "不", "无", "没有", "非", "未")
SIDE_EFFECT_VERBS = (
    "点击",
    "输入",
    "滑动",
    "拖动",
    "长按",
    "启动",
    "打开",
    "返回",
    "关闭",
    "开启",
    "切换",
    "选择",
)
CONJUNCTIONS = ("然后", "并且", "并", "同时", "接着", "之后")


def affirmed_word(text: str, words: tuple[str, ...]) -> str:
    """在文本里找**未被否定**的目标词（"不是弹窗 / 无弹窗" 不算命中）。"""
    for word in words:
        for match in re.finditer(re.escape(word), text):
            prefix = text[max(0, match.start() - 4) : match.start()]
            if not any(neg in prefix for neg in NEGATIONS):
                return word
    return ""


@dataclass
class Check:
    """一条验收项。"""

    name: str
    status: str
    detail: str = ""

    @property
    def mark(self) -> str:
        return {"pass": "[OK]", "fail": "[NG]", "n/a": "[--]"}[self.status]


@dataclass
class Verdict:
    """一条输入的验收结论。"""

    case_id: str
    checks: list[Check] = field(default_factory=list)
    suspects: list[str] = field(default_factory=list)

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if c.status == FAIL]

    @property
    def passed(self) -> bool:
        return not self.failed


def _steps(plan: Plan | None) -> list[Step]:
    return list(plan.steps) if plan else []


def _plan_text(plan: Plan | None) -> str:
    return normalize("\n".join(f"{s.action} {s.assertion}" for s in _steps(plan)))


def _step_text(step: Step) -> str:
    return normalize(f"{step.action} {step.assertion}")


def _switch_steps(plan: Plan | None) -> list[Step]:
    return [s for s in _steps(plan) if any(h in normalize(s.action) for h in SWITCH_HINTS)]


def _is_icon_step(step: Step) -> bool:
    """图标检查步骤：动作含"检查/查看/确认"且文本含蓝牙或 WiFi（等待步骤不算，避免误判顺序）。"""
    action = normalize(step.action)
    return any(h in action for h in ICON_ACTION_HINTS) and any(
        h in normalize(_step_text(step)) for h in ICON_HINTS
    )


def _icon_steps(plan: Plan | None) -> list[Step]:
    return [s for s in _steps(plan) if _is_icon_step(s)]


def _is_wait_step(step: Step) -> bool:
    """等待连接步骤：动作含"等待"，且文本提到蓝牙 / WiFi / 连接。"""
    action = normalize(step.action)
    text = normalize(_step_text(step))
    return "等待" in action and (any(h in text for h in ICON_HINTS) or "连接" in text)


def check_contract(run: RunResult) -> Check:
    if run.plan is None:
        return Check("输出契约（可解析出计划）", FAIL, "JSON 不可解析或缺少 plan")
    if not run.plan.steps:
        return Check("输出契约（可解析出计划）", FAIL, "plan.steps 为空")
    empty = [
        i
        for i, s in enumerate(run.plan.steps, 1)
        if not s.action.strip() or not s.assertion.strip()
    ]
    if empty:
        return Check("输出契约（可解析出计划）", FAIL, f"第 {empty} 步 action/assert 为空")
    return Check("输出契约（可解析出计划）", PASS, f"{len(run.plan.steps)} 步，字段完整")


def check_steps_range(run: RunResult) -> Check:
    lo, hi = run.case.steps_range
    n = len(_steps(run.plan))
    if not n:
        return Check("步骤数区间", FAIL, "没有步骤")
    if not lo <= n <= hi:
        return Check("步骤数区间", FAIL, f"{n} 步不在 [{lo}, {hi}]")
    return Check("步骤数区间", PASS, f"{n} 步，落在 [{lo}, {hi}]")


def check_style_bar(run: RunResult) -> Check:
    """长按后应描述为同页顶部出现样式栏，而不是弹窗/菜单。"""
    for step in _steps(run.plan):
        text = _step_text(step)
        if "长按" not in text:
            continue
        if "灵动" not in text or "经典" not in text:
            return Check(
                "长按后的样式栏表述", FAIL, "长按那一步的断言未同时说明「灵动 | 经典」分段"
            )
        bad = affirmed_word(text, POPUP_WORDS)
        if bad:
            return Check("长按后的样式栏表述", FAIL, f"误写成弹窗/菜单：{bad}")
        return Check("长按后的样式栏表述", PASS, "同页顶部样式栏（含灵动/经典分段），无弹窗表述")
    return Check("长按后的样式栏表述", FAIL, "没有找到长按卡片的步骤")


def check_save_control(run: RunResult) -> Check:
    """保存控件应是右上角 ✓，且以结构特征判定成功（样式栏消失 / 恢复标题）。"""
    for step in _steps(run.plan):
        action = normalize(step.action)
        assertion = normalize(step.assertion)
        if not re.search(r"[✓√]|对勾|打勾|勾选|右上角", action):
            continue
        if not any(w in assertion for w in ("消失", "恢复", "回到")):
            return Check(
                "保存控件与成功判定", FAIL, "保存那一步未以“样式栏消失 / 恢复标题”作为成功依据"
            )
        fake = affirmed_word(assertion, FAKE_FEEDBACK_WORDS)
        if fake:
            return Check("保存控件与成功判定", FAIL, f"依赖了不存在的保存反馈：{fake}")
        return Check("保存控件与成功判定", PASS, "点右上角确认，且以结构特征判定成功")
    return Check("保存控件与成功判定", FAIL, "没有找到点击右上角确认的步骤")


def check_no_fake_wording(run: RunResult) -> Check:
    """整体不得出现界面上不存在的控件表述。"""
    text = _plan_text(run.plan)
    bad = []
    if re.search(r"「?保存」?\s*按钮", text):
        bad.append("「保存」按钮")
    if any(w in text for w in ("弹出卡片设置", "卡片设置弹窗", "卡片设置菜单")):
        bad.append("卡片设置弹窗/菜单")
    fake = affirmed_word(text, FAKE_FEEDBACK_WORDS)
    if fake:
        bad.append(f"保存成功提示（{fake}）")
    if bad:
        return Check("无虚构控件/反馈", FAIL, f"出现不存在的表述：{bad}")
    return Check("无虚构控件/反馈", PASS, "无「保存按钮 / 弹窗 / 保存成功提示」")


def check_switch_log_only(run: RunResult) -> Check:
    """开关类步骤：只认设备日志断言，标 log_check=true，且不得用页面表现判定。"""
    steps = _switch_steps(run.plan)
    if not steps:
        return Check("开关只认日志断言", FAIL, "没有找到开关类步骤")
    problems = []
    for i, step in enumerate(steps, 1):
        assertion = normalize(step.assertion)
        if "日志" not in assertion:
            problems.append(f"第 {i} 条开关步骤断言未提日志")
        if not step.log_check:
            problems.append(f"第 {i} 条开关步骤未标 log_check=true")
        hit = [w for w in PAGE_STATE_WORDS if w in assertion]
        if hit:
            problems.append(f"第 {i} 条开关步骤用页面表现判定：{hit}")
    if problems:
        return Check("开关只认日志断言", FAIL, "；".join(problems))
    return Check("开关只认日志断言", PASS, f"{len(steps)} 条开关步骤均为纯日志断言且标记正确")


def check_switch_control_form(run: RunResult) -> Check:
    """开关控件形态按样式区分：经典＝ON | OFF 文字分段；灵动＝右下角圆形电源按钮。"""
    steps = _switch_steps(run.plan)
    if not steps:
        return Check("开关控件形态", FAIL, "没有找到开关类步骤")
    action_text = normalize(" ".join(s.action for s in steps))
    if run.case.style == "classic":
        if "ON" in action_text and "OFF" in action_text:
            return Check("开关控件形态", PASS, "点名了 ON / OFF 文字分段的半边")
        return Check("开关控件形态", FAIL, "未点名「ON | OFF」文字分段中的哪一半")
    if "电源" in action_text or "圆形" in action_text:
        return Check("开关控件形态", PASS, "使用了灵动页的圆形电源按钮表述")
    return Check("开关控件形态", FAIL, "灵动页未使用圆形电源按钮表述（疑似套用 ON/OFF）")


def check_wait_before_icons(run: RunResult) -> Check:
    """检查蓝牙/WiFi 图标之前必须有一处“等待连接成功”。"""
    steps = _steps(run.plan)
    icon_index = next((i for i, s in enumerate(steps) if _is_icon_step(s)), None)
    if icon_index is None:
        return Check("图标检查前先等连接", FAIL, "没有找到检查蓝牙/WiFi 图标的步骤")
    if any(_is_wait_step(s) for s in steps[:icon_index]):
        return Check("图标检查前先等连接", PASS, "图标检查之前已有等待连接成功的步骤")
    return Check("图标检查前先等连接", FAIL, "图标检查之前没有“等待 WiFi 与蓝牙连接成功”的步骤")


def check_icon_assert(run: RunResult) -> Check:
    """图标断言需写明位置与两个图标。"""
    steps = _icon_steps(run.plan)
    if not steps:
        return Check("图标断言完整", FAIL, "没有找到检查蓝牙/WiFi 图标的步骤")
    text = normalize(" ".join(_step_text(s) for s in steps))
    missing = []
    if "蓝牙" not in text:
        missing.append("蓝牙")
    if not any(w in text for w in ("WiFi", "WIFI", "wifi")):
        missing.append("WiFi")
    if "右上角" not in text:
        missing.append("位置（右上角）")
    if missing:
        return Check("图标断言完整", FAIL, f"缺少：{missing}")
    return Check("图标断言完整", PASS, "含蓝牙、WiFi 与位置（右上角）")


def collect_suspects(run: RunResult) -> list[str]:
    """提示级（不判失败）：一步多动作。"""
    found = []
    for i, step in enumerate(_steps(run.plan), 1):
        action = normalize(step.action)
        verbs = [v for v in SIDE_EFFECT_VERBS if v in action]
        if len(verbs) >= 2 and any(c in action for c in CONJUNCTIONS):
            found.append(f"第 {i} 步疑似一步多动作（命中动作 {verbs}）：{step.action}")
    return found


RULES = (
    check_contract,
    check_steps_range,
    check_style_bar,
    check_save_control,
    check_no_fake_wording,
    check_switch_control_form,
    check_switch_log_only,
    check_wait_before_icons,
    check_icon_assert,
)


def verify(run: RunResult) -> Verdict:
    """结构验收：逐条跑规则。"""
    verdict = Verdict(case_id=run.case.case_id)
    verdict.checks = [rule(run) for rule in RULES]
    verdict.suspects = collect_suspects(run)
    return verdict


# ══════════════════════════════════════════════════════════════════════════
# 第 4 层：输出报告（控制台 + Markdown）
# ══════════════════════════════════════════════════════════════════════════


def render_console(
    cases: list[PlannerInput],
    results: list[RunResult],
    verdicts: list[Verdict],
    *,
    context: str,
    context_label: str,
    model_name: str,
    key_source: str,
    flow_injected: bool = False,
) -> None:
    by_case = {v.case_id: v for v in verdicts}

    say("=" * 78)
    say("第 1 层 · 输入数据")
    say("=" * 78)
    for case in cases:
        say(f"[{case.case_id}] 四键 JSON（{len(case.payload(context=context))} 字符）：")
        say("  " + case.payload(context=context))
    say(f"（上下文来源：{context_label}）")

    say("")
    say("=" * 78)
    say("第 2 层 · 运行结果")
    say(
        f"（注入的工具：list_page_flows / get_page_flow 桩，页面流摘要：{'已注入' if flow_injected else '空清单'}）"
    )
    say("=" * 78)
    total_cost = 0.0
    for run in results:
        total_cost += run.cost
        say(
            f"[{run.case.case_id}] 模型 {run.model} | 耗时 {run.seconds:.1f}s | "
            f"输入 {run.usage.get('input_tokens', 0)} / 输出 {run.usage.get('output_tokens', 0)} token | "
            f"费用 {run.cost_text} | 步骤数 {len(_steps(run.plan))}"
        )
    say(f"合计费用 {total_cost:.6f} 元 | 密钥来源：{key_source}")

    say("")
    say("=" * 78)
    say("第 3 层 · 结构验收")
    say("=" * 78)
    for case in cases:
        verdict = by_case[case.case_id]
        state = "通过" if verdict.passed else f"未通过（{len(verdict.failed)} 项）"
        say(f"[{case.case_id}] {state}")
        for check in verdict.checks:
            say(f"  {check.mark} {check.name}" + (f" — {check.detail}" if check.detail else ""))
        for suspect in verdict.suspects:
            say(f"  [提示] {suspect}")

    say("")
    say("=" * 78)
    say("第 4 层 · 报告")
    say("=" * 78)


def render_markdown(
    cases: list[PlannerInput],
    results: list[RunResult],
    verdicts: list[Verdict],
    *,
    context: str,
    context_label: str,
    model_name: str,
    key_source: str,
    started_at: datetime,
) -> pathlib.Path:
    by_case = {v.case_id: v for v in verdicts}
    total_cost = sum(r.cost for r in results)
    passed = sum(1 for v in verdicts if v.passed)

    lines = [
        "# 规划智能体验收报告",
        "",
        f"- 时间：{started_at:%Y-%m-%d %H:%M:%S}",
        f"- 模型：`{model_name}`（密钥来源：{key_source}）",
        f"- 上下文来源：{context_label}",
        f"- 输入条数：{len(cases)}，结构验收通过：{passed}/{len(verdicts)}",
        f"- 合计费用：{total_cost:.6f} 元",
        "",
        "## 第 1 层 · 输入数据",
        "",
    ]
    for case in cases:
        lines += [
            f"### {case.case_id}",
            "",
            "```json",
            case.payload(context=context),
            "```",
            "",
        ]

    lines += ["## 第 2 层 · 运行结果", ""]
    lines += [
        "| 输入 | 模型 | 步骤数 | 耗时(s) | 输入token | 输出token | 费用(元) |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for run in results:
        lines.append(
            f"| {run.case.case_id} | {run.model} | {len(_steps(run.plan))} | {run.seconds:.1f} | "
            f"{run.usage.get('input_tokens', 0)} | {run.usage.get('output_tokens', 0)} | {run.cost:.6f} |"
        )

    lines += ["", "## 第 3 层 · 结构验收", ""]
    for case in cases:
        verdict = by_case[case.case_id]
        lines += [
            f"### {case.case_id} — {'通过' if verdict.passed else '未通过'}",
            "",
            "| 验收项 | 结果 | 说明 |",
            "| --- | --- | --- |",
        ]
        for check in verdict.checks:
            mark = {"pass": "✅", "fail": "❌", "n/a": "—"}[check.status]
            lines.append(f"| {check.name} | {mark} | {check.detail} |")
        if verdict.suspects:
            lines += ["", "提示（不判失败）：", ""] + [f"- ⚠️ {s}" for s in verdict.suspects]
        lines.append("")

    lines += ["## 第 4 层 · 模型原始输出", ""]
    for run in results:
        lines += [f"### {run.case.case_id}", "", "```json", run.raw.strip() or "(空)", "```", ""]

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    tag = re.sub(r"[^0-9A-Za-z._-]+", "-", model_name) or "planner"
    path = REPORT_DIR / f"{tag}-{'ctx' if context else 'raw'}-{started_at:%Y%m%d-%H%M%S}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


# ══════════════════════════════════════════════════════════════════════════
# 主流程
# ══════════════════════════════════════════════════════════════════════════


def main() -> int:
    parser = argparse.ArgumentParser(description="规划智能体验收测试（零 Django，四层）")
    parser.add_argument("--only", help="只跑指定 case_id（逗号分隔）")
    parser.add_argument("--model", default="deepseek-flash", help="模型名（默认 deepseek-flash）")
    parser.add_argument("--env-file", default=str(ROOT / ".env"), help="密钥所在 .env 路径")
    parser.add_argument("--with-context", action="store_true", help="附件里并入内置界面状态说明")
    parser.add_argument(
        "--context-file",
        action="append",
        help="上下文文件（可重复给多个），内容并入「附件文本内容」；与 --with-context 可叠加",
    )
    parser.add_argument(
        "--flow", help="页面流摘要文件（JSON），作为桩工具的返回值；不给则返回空清单"
    )
    parser.add_argument(
        "--use-system-proxy", action="store_true", help="走系统代理（默认旁路直连）"
    )
    parser.add_argument("--raw", action="store_true", help="附加打印模型原始输出")
    args = parser.parse_args()

    if not args.use_system_proxy:
        bypass_system_proxy_for_api()

    cases = build_inputs()
    if args.only:
        wanted = {x.strip() for x in args.only.split(",") if x.strip()}
        cases = [c for c in cases if c.case_id in wanted]
        if not cases:
            say(f"没有匹配的输入：{args.only}")
            return 2

    api_key, key_source = resolve_api_key(pathlib.Path(args.env_file))
    if not api_key:
        say(f"未找到密钥：环境变量 {KEY_NAME} 或 {args.env_file} 中的 {KEY_NAME}")
        return 2

    started_at = datetime.now()
    flow_detail = pathlib.Path(args.flow).read_text(encoding="utf-8") if args.flow else ""

    # 上下文：文件（可多个）+ 可选内置界面状态说明
    context_parts: list[str] = []
    context_labels: list[str] = []
    for path_text in args.context_file or []:
        context_path = pathlib.Path(path_text)
        if not context_path.exists():
            say(f"上下文文件不存在：{context_path}")
            return 2
        context_parts.append(context_path.read_text(encoding="utf-8"))
        context_labels.append(context_path.name)
    if args.with_context:
        context_parts.append(CONTEXT)
        context_labels.append("内置界面状态说明")
    context = "\n\n".join(context_parts)
    context_label = "、".join(context_labels) if context_labels else "无"

    results = run_all(
        cases,
        args.model,
        api_key,
        context=context,
        flow_detail=flow_detail,
    )
    verdicts = [verify(run) for run in results]

    render_console(
        cases,
        results,
        verdicts,
        context=context,
        context_label=context_label,
        model_name=args.model,
        key_source=key_source,
        flow_injected=bool(flow_detail),
    )
    report = render_markdown(
        cases,
        results,
        verdicts,
        context=context,
        context_label=context_label,
        model_name=args.model,
        key_source=key_source,
        started_at=started_at,
    )
    say(f"报告文件：{report.relative_to(ROOT)}")
    say(f"结构验收：{'全部通过' if all(v.passed for v in verdicts) else '存在未通过项（见上表）'}")

    if args.raw:
        for run in results:
            say("")
            say(f"-- {run.case.case_id} 模型原始输出 --")
            say(run.raw)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
