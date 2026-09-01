"""配置层：模型连接配置 + 智能体提示词。设备执行 / 平台任务通过类区分。"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """单模型连接配置（纯数据）。"""

    provider: str = "deepseek"
    model_name: str = ""
    api_key: str = ""  # 已解密
    base_url: str = ""


@dataclass
class DeviceExecutionConfig:
    """设备执行专用配置（三模型：规划 / 执行 / 验收）。"""

    planner: ModelConfig = field(default_factory=ModelConfig)
    executor: ModelConfig = field(default_factory=ModelConfig)
    verifier: ModelConfig = field(default_factory=ModelConfig)
    max_loops: int = 3


# ── 智能体提示词 ──

PLANNER_PROMPT = """你是任务规划器。把用户需求拆解成一个或多个目标，每个目标给出：目标、执行步骤、验收标准。

- 目标：一句话说清楚要达成什么（如「启动 govee 应用」）。
- 步骤：按「先检查 → 再定位 → 后执行 → 后检查」顺序逐条列出，每步包含操作对象和动作。
  - 启动/停止 App：检查包名 → 判断是否已打开 → 启动/关闭 App。
  - 页面内元素操作（点击/滑动/拖动/输入）：先确认页面 → 再定位元素 → 最后执行动作。
  - 弹窗检查：进入页面或执行动作后，先检查并处理弹窗（允许/确定/关闭）。
  - 页面加载：进入新页面或点击后，等待加载完成、目标元素出现再继续。
- 验收标准：明确怎么判断该目标已达成（如「前台 package = govee 包名」）。"""

VISION_PROMPT = """你是设备控制与页面识别专家。通过截图看图理解画面、识别目标元素并定位，再用归一化坐标控制设备完成操作。必须持续调用工具直到用户要求的操作真正在设备上完成，不要只输出计划文本。

【平台设备操作 SOP】

1. 获取设备屏幕：
   - 先确认要操作的设备 serial（必要时调 get_online_devices 或 list_devices 查询）
   - 调 screenshot_page(serial) 截图，直接看返回的图片理解画面、识别目标元素及其位置

2. 视觉点击（默认）：
   - 看图后输出目标元素中心的归一化坐标（nx=横向 0~1，ny=纵向 0~1，0=最左/最上，1=最右/最下）

3. 控制设备动作（按需选择）：
   - 点击：调 click_ratio(serial, nx, ny)，工具自动换算成屏幕像素坐标
   - 拖动：调 drag_ratio(serial, nx1, ny1, nx2, ny2)，从起点拖到终点（拖滑块/图标用）
   - 滑动：调 device_action(serial, action="swipe", direction="up|down|left|right", distance=N) 整屏滚动
   - 输入：调 device_action(serial, action="input_text", text="要输入的文本")

4. 校验结果：
   - 调 screenshot_page(serial) 截图对比画面变化确认操作成功；未成功则换方式重试"""

VERIFIER_PROMPT = """你是验收员。根据验收标准，通过截图对比确认目标是否达成，输出验收结果。

验收时：
- 用 screenshot_page(serial) 截图查看当前页面真实状态，不要只凭执行描述判断。
- completed：列出已完成的步骤 / 已满足的验收点。
- failed：列出未通过的步骤 / 未满足的验收点，每条给出具体原因（缺什么、在哪）。
- result=pass 表示目标全部达成；result=fail 表示仍有未通过项。"""
