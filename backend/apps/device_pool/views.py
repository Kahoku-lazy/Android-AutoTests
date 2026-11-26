import re
import time

from drf_spectacular.utils import OpenApiTypes, extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from engines.device.action import System, open_device
from utils.adb import AdbUnavailableError
from utils.logs import backend_log

from . import api
from .contracts import ConnectionType, DeviceError
from .models import Device
from .pool import device as device_pool


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def list_devices(request):
    try:
        return Response(api.list_devices(getattr(request, "user_id", "")))
    except DeviceError:
        raise
    except AdbUnavailableError as exc:
        return Response({"message": str(exc)}, status=503)
    except Exception:
        backend_log.exception("list_devices failed")
        return Response({"message": "设备列表加载失败"}, status=500)


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def device_current(request):
    current_serial = device_pool.current_serial
    info: dict = {}
    app: dict = {}
    dev = None

    if current_serial:
        try:
            dev = Device.objects.get(serial=current_serial)
        except Device.DoesNotExist:
            dev = None
        if dev is not None:
            info, app = _probe_current_device(current_serial, dev)

    if dev is not None:
        return Response(
            {
                "serial": current_serial,
                "screen_w": dev.screen_w or info.get("displayWidth", 0),
                "screen_h": dev.screen_h or info.get("displayHeight", 0),
                "package": app.get("package", ""),
                "model": dev.model,
                "brand": dev.brand,
                "connection_type": dev.connection_type
                or (ConnectionType.WIFI if ":" in current_serial else ConnectionType.USB),
            }
        )
    return Response(
        {
            "serial": current_serial,
            "screen_w": info.get("displayWidth", 0),
            "screen_h": info.get("displayHeight", 0),
            "package": app.get("package", ""),
        }
    )


_CURRENT_PROBE_TTL_SECONDS = 10.0
_current_probe_cache: dict[str, tuple[float, dict, dict]] = {}


def _probe_current_device(serial: str, dev: Device) -> tuple[dict, dict]:
    now = time.monotonic()
    cached = _current_probe_cache.get(serial)
    if cached is not None and now - cached[0] < _CURRENT_PROBE_TTL_SECONDS:
        return cached[1], cached[2]

    info: dict = {}
    app: dict = {}
    connection, device_info, _control = open_device(
        System.ANDROID, serial, dev.connection_addr or serial
    )
    try:
        width, height = device_info.screen_size()
        info = {"displayWidth": width, "displayHeight": height}
        app = device_info.current_app() or {}
    except Exception:
        backend_log.warning("读取设备前台失败 serial=%s", serial)
    finally:
        connection.disconnect()

    _current_probe_cache[serial] = (now, info, app)
    return info, app


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def activate_device(request, serial):
    return Response({"current": api.activate_device(serial, getattr(request, "user_id", ""))})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def scan_device(request):
    target = (request.data.get("target") or "").strip()
    user_id = getattr(request, "user_id", "")

    try:
        if target:
            if ":" in target:
                ip, _, port = target.partition(":")
                ip_ok = bool(
                    re.match(
                        r"^((25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(25[0-5]|2[0-4]\d|[01]?\d?\d)$",
                        ip,
                    )
                )
                port_ok = port.isdigit() and 1024 <= int(port) <= 65535
                if not (ip_ok and port_ok):
                    return Response({"message": "无效的 IP 或端口"}, status=400)

                pair_port = (request.data.get("pair_port") or "").strip()
                pair_code = (request.data.get("pair_code") or "").strip()
                if pair_port or pair_code:
                    if not (pair_port and pair_code):
                        return Response({"message": "请同时填写配对端口和配对码"}, status=400)

                result = api.scan_and_register(
                    target, user_id, pair_port=pair_port, pair_code=pair_code
                )
                return Response({"count": 1, **result})

            adb_serials = api.list_connectable_serials()
            if target in adb_serials:
                return Response({"count": 1, **api.register_connected_device(target, user_id)})
            return Response({"message": f"device {target} not found"}, status=400)

        return Response(api.scan_all_devices(user_id))
    except DeviceError:
        raise
    except AdbUnavailableError as exc:
        return Response({"message": str(exc)}, status=503)
    except Exception:
        backend_log.exception("scan_device failed")
        return Response({"message": "扫描失败"}, status=500)


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def connect_device(request, serial):
    activate = request.data.get("activate", True)
    mode = request.data.get("mode", "")
    user_id = getattr(request, "user_id", "") or ""

    return Response(api.connect_device(serial, user_id, activate=activate, mode=mode))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def disconnect_device(request, serial):
    api.disconnect_device(serial)
    backend_log.warning("设备 %s 已删除", serial)
    return Response({"serial": serial, "deleted": True})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def disconnect_observe(request, serial):
    api.release_observe(serial)
    return Response({"serial": serial, "message": "设备观察连接已断开"})


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def lock_device(request, serial):
    locked = request.data.get("locked", True)
    user_id = getattr(request, "user_id", "") or request.data.get("user_id", "")

    return Response(api.set_device_lock(serial, bool(locked), user_id))


@extend_schema(request=OpenApiTypes.OBJECT, responses=OpenApiTypes.OBJECT)
@api_view(["POST"])
def release_device(request, serial):
    return Response(api.release_occupy(serial))


@extend_schema(responses=OpenApiTypes.OBJECT)
@api_view(["GET"])
def heartbeat(request):
    return Response(api.heartbeat_sync())
