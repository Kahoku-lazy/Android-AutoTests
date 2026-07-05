"""公共常量 — 跨模块共享的状态枚举和常量定义。

所有模块的状态字符串统一使用此处的 Enum，避免硬编码散布各处。

使用方式:
    from models.constants import DeviceStatus
    device.status = DeviceStatus.ONLINE
    if device.status == DeviceStatus.BUSY:
        ...
"""

from enum import Enum


class DeviceStatus(str, Enum):
    """设备状态 — dp_devices.status"""
    ONLINE = "ONLINE"
    BUSY = "BUSY"
    OFFLINE = "OFFLINE"
    DISCONNECTED = "DISCONNECTED"


class LockStatus(str, Enum):
    """设备锁状态 — dp_device_locks.status"""
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class LockReleaseReason(str, Enum):
    """锁释放原因 — dp_device_locks.release_reason"""
    MANUAL = "manual"
    TIMEOUT = "timeout"
    DISCONNECT = "disconnect"
    FORCE = "force"


class ConnectionType(str, Enum):
    """设备连接类型 — dp_devices.connection_type"""
    USB = "USB"
    WIFI = "WIFI"


class QueueStatus(str, Enum):
    """排队状态 — dp_device_queue.status"""
    WAITING = "waiting"
    ASSIGNED = "assigned"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TestRunStatus(str, Enum):
    """测试执行状态 — tr_test_runs.status"""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    PASSED = "PASSED"
    FAILED = "FAILED"
    STOPPED = "STOPPED"


class TestResult(str, Enum):
    """单次迭代结果 — tr_test_results.result"""
    PASS = "PASS"
    FAIL = "FAIL"
    ERROR = "ERROR"


class AgentStatus(str, Enum):
    """Agent 状态 — ai_agents.status"""
    ACTIVE = "active"
    INACTIVE = "inactive"


class ConversationStatus(str, Enum):
    """对话状态 — ai_conversations.status"""
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(str, Enum):
    """消息角色 — ai_messages.role"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SOPStatus(str, Enum):
    """SOP 工作流状态 — tr_test_sop.status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(str, Enum):
    """任务状态 — ai_tasks.status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class MemoryMode(str, Enum):
    """Agent 记忆模式 — ai_agents.memory_mode"""
    INMEMORY = "inmemory"
    LONGTERM = "longterm"


class ModelProvider(str, Enum):
    """AI 模型提供商"""
    DASHSCOPE = "dashscope"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


# ── 聚合映射（方便遍历和校验）──

ALL_STATUS_ENUMS = {
    "device": DeviceStatus,
    "lock": LockStatus,
    "queue": QueueStatus,
    "test_run": TestRunStatus,
    "test_result": TestResult,
    "agent": AgentStatus,
    "conversation": ConversationStatus,
    "sop": SOPStatus,
    "task": TaskStatus,
}
