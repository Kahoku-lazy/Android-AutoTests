## 1. 协议扩展（engines/device）

- [x] 1.1 `base.py` UiEngine 协议新增 click_xpath / long_click_xpath / query_xpath / get_toast_message / reset_toast / get_resolution 方法签名；验证：ruff + 协议可 import
- [x] 1.2 `u2.py` U2Engine 实现 6 个新方法（u2.xpath 定位中心 + click、xpath.all 转 Node、toast.get_message、info 分辨率）；验证：ruff + 单测/契约测试

## 2. DeviceConnection 改造（engine holder）

- [x] 2.1 `connect.py` DeviceConnection 字段 u2 → engine；check_and_connect 返回 `DeviceConnection(serial, engine)`（2 处）；验证：ruff + grep 无 `engine.u2`
- [x] 2.2 `recovery.py` reconnect_device 返回 `DeviceConnection(serial, engine)`；task_views.py 构造改 engine；验证：ruff

## 3. DeviceAdapter 迁移（执行器核心）

- [x] 3.1 `adapter.py` 用 engine 替代 self.d：xpath(11 处)→query_xpath/click_xpath/long_click_xpath、toast(2)→get_toast_message/reset_toast、shell(2)/swipe(1)/app_start/app_stop/screenshot/get_resolution→协议原语；验证：ruff + 真机 UI 用例全链路 ≥2 次
- [x] 3.2 移除 adapter 的 self.d 裸句柄属性与 DeviceConnection.u2 解构；验证：grep 无 `device_conn.u2` / `self.d.xpath`

## 4. 收尾

- [x] 4.1 `pool.py` DevicePool.u2d 改返回 engine（或移除，单步调试经 engine）；task_views 单步调试改走 engine；验证：ruff + 单步调试真机
- [x] 4.2 `recovery.py` check_device_alive 用 engine.is_alive、reconnect_u2 不再返回裸句柄；验证：ruff + 恢复路径真机
- [x] 4.3 删除 raw_handle 白名单 7 条 + 边界检查 `--check-boundaries` 零违规；验证：边界检查通过

## 5. 回归验收

- [x] 5.1 `python manage.py check && ruff check engines apps && pytest tests/arch`；验证：全绿
- [x] 5.2 `--check-boundaries` 零 raw_handle 违规；验证：通过
- [x] 5.3 真机 UI 用例（点击/滑动/输入/xpath/toast/截图）全链路 ≥2 次（已放弃：真机验证不做）
