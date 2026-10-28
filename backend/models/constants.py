"""公共常量 — 跨模块共享的状态枚举和常量定义。

所有模块的状态字符串统一使用此处的 Enum，避免硬编码散布各处。

使用方式:
    from backend.models.constants import DeviceStatus
    device.status = DeviceStatus.ONLINE
    if device.status == DeviceStatus.BUSY:
        ...
"""

from enum import StrEnum


class DeviceStatus(StrEnum):
    """设备状态 — dp_devices.status（L1b 收敛：仅两态，离线即删除记录）"""

    ONLINE = "ONLINE"
    BUSY = "BUSY"


class LockStatus(StrEnum):
    """设备锁状态 — dp_device_locks.status"""

    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class LockReleaseReason(StrEnum):
    """锁释放原因 — dp_device_locks.release_reason"""

    MANUAL = "manual"
    TIMEOUT = "timeout"
    DISCONNECT = "disconnect"
    FORCE = "force"


class ConnectionType(StrEnum):
    """设备连接类型 — dp_devices.connection_type"""

    USB = "USB"
    WIFI = "WIFI"


class AgentStatus(StrEnum):
    """Agent 状态 — ai_agents.status"""

    ACTIVE = "active"
    INACTIVE = "inactive"


class ConversationStatus(StrEnum):
    """对话状态 — ai_conversations.status"""

    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    """消息角色 — ai_messages.role"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SOPStatus(StrEnum):
    """SOP 工作流状态 — tr_test_sop.status"""

    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    """任务状态 — ai_tasks.status"""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class TaskKind(StrEnum):
    """任务类型 — task_tasks.task_kind / ai_agents.task_kind"""

    DEVICE_CONTROL = "device_control"
    CASE_AUTHORING = "case_authoring"


class BugCategory(StrEnum):
    """BUG 分类 — bug_tickets.category。"""

    UI_AUTOMATION = "ui_automation"
    CASE_AUTHORING = "case_authoring"


class BugStatus(StrEnum):
    """BUG 处理状态 — bug_tickets.status。"""

    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class MemoryMode(StrEnum):
    """Agent 记忆模式 — ai_agents.memory_mode"""

    INMEMORY = "inmemory"
    LONGTERM = "longterm"


class ModelProvider(StrEnum):
    """AI 模型提供商 —— 平台只支持 DeepSeek 与阿里百炼（DashScope）"""

    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"


# ── 聚合映射（方便遍历和校验）──

ALL_STATUS_ENUMS = {
    "device": DeviceStatus,
    "lock": LockStatus,
    "agent": AgentStatus,
    "conversation": ConversationStatus,
    "sop": SOPStatus,
    "task": TaskStatus,
    "bug": BugStatus,
}
