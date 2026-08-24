"""DeviceSession 协议单元测试（mock 引擎）— L2 详档 §2.3 验收。"""

import pytest

from apps.device_pool.session import DeviceSession, LeaseConflict, LeaseError, LeaseMode
from tests.device_pool.fakes import FakeEngine, install_fake_engine

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


@pytest.fixture(autouse=True)
def _clean():
    DeviceSession._lease_holders.clear()
    yield
    DeviceSession._lease_holders.clear()


class TestLeaseLifecycle:
    def test_lease_registers_holder(self, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT, addr="S")
        assert session.serial == "S"
        assert DeviceSession._lease_holders["S"] is session

    def test_conflicting_lease_raises(self, monkeypatch):
        install_fake_engine(monkeypatch)
        DeviceSession.lease("S", LeaseMode.TRANSIENT)
        with pytest.raises(LeaseConflict, match="已被租用"):
            DeviceSession.lease("S", LeaseMode.EXCLUSIVE)

    def test_release_allows_release(self, monkeypatch):
        install_fake_engine(monkeypatch)
        s1 = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        s1.release()
        s2 = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        assert DeviceSession._lease_holders["S"] is s2

    def test_lease_is_lazy_connect(self, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT, addr="1.2.3.4:5555")
        assert engine.connected == []  # lease 不连接
        session.info()
        assert engine.connected == [("S", "1.2.3.4:5555")]  # 首操作连接

    def test_ensure_connected_idempotent(self, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        session.info()
        session.info()
        assert len(engine.connected) == 1


class TestPerSerialLock:
    def test_same_serial_serialized(self, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        # 同 serial 操作经同一把锁：连续两次 click 串行（无死锁即通过）
        session.click(1, 1)
        session.click(2, 2)
        assert ("click", 1, 1) in engine.calls
        assert ("click", 2, 2) in engine.calls

    def test_cross_serial_independent_locks(self, monkeypatch):
        install_fake_engine(monkeypatch)
        s1 = DeviceSession.lease("S1", LeaseMode.TRANSIENT)
        s2 = DeviceSession.lease("S2", LeaseMode.TRANSIENT)
        s1.click(1, 1)
        s2.click(2, 2)
        # 跨 serial 并行：两把独立锁，互不阻塞（无死锁即通过）


class TestErrorMapping:
    def test_connect_error_to_lease_error(self, monkeypatch):
        engine = FakeEngine()
        engine.connect_error = "Airtest connection failed: x"
        install_fake_engine(monkeypatch, engine)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        with pytest.raises(LeaseError, match="设备连接失败"):
            session.info()

    def test_reconnect_error_to_lease_error(self, monkeypatch):
        engine = FakeEngine()
        engine.alive = False
        install_fake_engine(monkeypatch, engine)

        def _boom():
            from engines.android.airtest_u2 import EngineConnectError

            raise EngineConnectError("boom")

        engine.reconnect = _boom
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        with pytest.raises(LeaseError, match="设备重连失败"):
            session.reconnect()


class TestExclusiveLeasePrecondition:
    """executor-session-toggle：EXCLUSIVE 租用需先持 process 业务锁。"""

    pytestmark = pytest.mark.django_db

    def test_no_business_lock_rejected(self, monkeypatch):
        from apps.device_pool.models import Device

        install_fake_engine(monkeypatch)
        Device.objects.create(serial="EX-1", status="ONLINE")
        with pytest.raises(LeaseConflict, match="业务锁"):
            DeviceSession.lease("EX-1", LeaseMode.EXCLUSIVE)

    def test_with_process_lock_allowed(self, monkeypatch):
        from apps.device_pool.models import Device, DeviceLock

        install_fake_engine(monkeypatch)
        dev = Device.objects.create(serial="EX-1", status="BUSY", occupied_by="runner-EX-1")
        DeviceLock.objects.create(
            device=dev,
            user_id="runner-EX-1",
            lock_type="process",
            timeout_seconds=3600,
            status="active",
        )
        session = DeviceSession.lease("EX-1", LeaseMode.EXCLUSIVE)
        assert session.mode is LeaseMode.EXCLUSIVE
        session.release()


class TestDelegation:
    def test_operations_delegate(self, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        session.click(1, 2)
        session.swipe(1, 2, 3, 4)
        session.input_text("hi")
        session.start_app("com.x")
        assert ("click", 1, 2) in engine.calls
        assert ("swipe", 1, 2, 3, 4, 0.5) in engine.calls
        assert ("input_text", "hi", True) in engine.calls
        assert ("start_app", "com.x") in engine.calls

    def test_is_alive_before_connect_false(self, monkeypatch):
        engine = FakeEngine()
        engine.alive = True
        install_fake_engine(monkeypatch, engine)
        session = DeviceSession.lease("S", LeaseMode.TRANSIENT)
        assert session.is_alive() is False  # 未连接视为不可用
        session.info()
        assert session.is_alive() is True
