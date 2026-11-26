from enum import StrEnum


class DeviceStatus(StrEnum):
    ONLINE = "ONLINE"
    BUSY = "BUSY"


class LockStatus(StrEnum):
    ACTIVE = "active"
    RELEASED = "released"
    EXPIRED = "expired"


class LockReleaseReason(StrEnum):
    MANUAL = "manual"
    TIMEOUT = "timeout"
    DISCONNECT = "disconnect"
    FORCE = "force"


class ConnectionType(StrEnum):
    USB = "USB"
    WIFI = "WIFI"


class AgentStatus(StrEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class ConversationStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class SOPStatus(StrEnum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    INTERRUPTED = "interrupted"


class TaskKind(StrEnum):
    DEVICE_CONTROL = "device_control"
    CASE_AUTHORING = "case_authoring"
    ASSISTANT_SOP = "assistant_sop"


class BugCategory(StrEnum):
    UI_AUTOMATION = "ui_automation"
    CASE_AUTHORING = "case_authoring"
    REQUIREMENT_BREAKDOWN = "requirement_breakdown"


class BugStatus(StrEnum):
    OPEN = "open"
    RESOLVED = "resolved"
    IGNORED = "ignored"


class MemoryMode(StrEnum):
    INMEMORY = "inmemory"
    LONGTERM = "longterm"


class ModelProvider(StrEnum):
    DASHSCOPE = "dashscope"
    DEEPSEEK = "deepseek"


ALL_STATUS_ENUMS = {
    "device": DeviceStatus,
    "lock": LockStatus,
    "agent": AgentStatus,
    "conversation": ConversationStatus,
    "sop": SOPStatus,
    "task": TaskStatus,
    "bug": BugStatus,
}
