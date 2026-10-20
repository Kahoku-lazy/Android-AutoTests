## 1. 最近任务包名

- [x] 1.1 从 `dumpsys activity recents` 原文解析包名，按出现顺序去重；跳过系统界面、解析到的桌面包名，解析不到桌面时再跳过常见桌面包名。验证：不连设备的单元测试覆盖「被测应用保留、桌面与系统界面剔除、同一包只出现一次」。

## 2. 收尾动作

- [x] 2.1 提供可注入的收尾：对保留下来的包逐个 `app_stop`，然后按 Home；成功与失败各记一条事件日志，不写入步骤清单。设备只连接一次。验证：用假设备断言停止顺序是先被测包、后 Home，且异常被接住后仍有失败日志。

## 3. 挂到平台用例循环

- [x] 3.1 `run_platform_sop` 在每条已开始的用例 `finally` 里调用收尾。通过、失败、执行中取消都调用；下一条尚未开始时的取消不调用；序列号为空则跳过并记日志；收尾抛错不改变通过、失败或取消。失败的用例之后仍不开始下一条。验证：扩展平台用例测试，注入假收尾，覆盖上述四种时机与判决不变。
- [x] 3.2 `task_runner` 把任务上的 `device_serial` 传入平台入口。验证：阅读调用处，序列号来自任务字段，不从开场说明拆。

## 4. 校验

- [x] 4.1 `python -m pytest tests/engines/agents/test_platform_case_title.py tests/engines/agents/test_close_recent_apps.py -q` 通过，且 `ruff check` 覆盖本次改动的引擎与 `apps/ai_assistant/task_runner.py`。
