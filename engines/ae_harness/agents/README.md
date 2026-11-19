# engines/ae_harness/agents

单个聊天智能体的最简实现：一个 Agent = 一个模型 + 一段提示词。

## 链路

```text
调用方传入提示词正文与连接参数
  │
  ▼
models.py        校验连接参数，造聊天模型
  │
  ▼
creator.py       模型 + 提示词正文 → Agent
```

| 文件 | 只做一件事 |
| --- | --- |
| `config.py` | `load_log_keywords` 按型号读日志关键词 |
| `models.py` | `ChatModel` 字段声明即校验；`create_model` 按调用方传入的连接参数造模型，并顺带交出用的是哪把密钥 |
| `creator.py` | `create_agent` 把调用方传入的提示词正文和模型包装成 Agent，连同密钥环境变量名一起返回；只创建不回复 |
| `../tools/adb/` | adb 设备工具：设备查询、点击、滑动、长按、输入、按键、装卸载、息屏、解锁、截图、UI dump |

## 如何创建 Agent

```python
from engines.ae_harness.agents.creator import create_agent

bundle = create_agent(
    name="ui_executor",  # 智能体名字，出现在消息里
    system_prompt="你是 UI 执行者。",  # 平台运营配置传入的正文
    provider="openai",
    api_key_env="OPENAI_API_KEY",
    model_name="deepseek-flash",
    base_url="https://test-llm.lanjingerp.com/v1",
)

agent = bundle.agent  # 挂工具、跑任务都从这里拿
print(bundle.api_key_env)  # OPENAI_API_KEY，供用量记账归组
```

### 返回值

`create_agent` 返回 `AgentBundle`，两段：

| 字段 | 内容 |
| --- | --- |
| `agent` | 装配好的智能体，工具包为空 |
| `api_key_env` | 本次使用的密钥环境变量名，只有名字、没有值 |

`api_key_env` 是「用了哪把密钥」的回执，不是角色能力——角色本身仍只有名称、模型、系统提示词三样。它由 `models.create_model` 在造模型时顺带交出，因此不需要再解析一遍配置表；用量记账按这个名字归组。

### 参数

| 参数 | 必填 | 说明 |
| --- | --- | --- |
| `name` | 是 | 智能体名字 |
| `system_prompt` | 是 | 系统提示词正文，由调用方传入 |
| `provider` | 是 | 厂商名：`deepseek` / `dashscope` / `openai` |
| `api_key_env` | 是 | 密钥环境变量名，必须与厂商成对 |
| `model_name` | 是 | 厂商正式模型名 |
| `base_url` | 否 | 基础地址；空串时用厂商默认 |
| `stream` | 否 | 默认 `True` |

工具不在参数里，创建后挂载，见下文「工具」。

### 提示词来源

系统提示词不在本目录维护。平台新建 Agent 时从运营配置读取正文，再传给 `create_agent`。

没有模型短名，也没有 `models.yaml`。换模型只改调用方传入的 `provider`、`api_key_env`、`model_name`、`base_url`。

## 跑一次回复

```python
import asyncio

from agentscope.message import UserMsg


async def main() -> None:
    result = await agent.reply([UserMsg(name="user", content="你好")])
    print(result.get_text_content())


asyncio.run(main())
```

本目录没有可运行的角色入口。要跑一轮，在 `backend_bridge` 用上面的参数装配。

## 增加模型

不改本目录。调用方传入一组新的连接参数即可，`provider` 与 `api_key_env` 必须对应：

| provider | api_key_env | base_url |
| --- | --- | --- |
| `deepseek` | `DEEPSEEK_API_KEY` | 不写用 `https://api.deepseek.com` |
| `dashscope` | `DASHSCOPE_API_KEY` | 不用 |
| `openai` | `OPENAI_API_KEY` | 固定 `https://test-llm.lanjingerp.com/v1` |

`base_url` 不需要时传空串，由 `models.py` 用厂商默认地址。

## 工具

工具不属于角色三要素，`create_agent` 不接收工具。拿到智能体之后再挂：

```python
from engines.ae_harness.agents.creator import create_agent
from engines.ae_harness.tools import build_adb_tools

bundle = create_agent(
    "ui_executor",
    "你是 UI 执行者。",
    provider="openai",
    api_key_env="OPENAI_API_KEY",
    model_name="deepseek-flash",
    base_url="https://test-llm.lanjingerp.com/v1",
)

for tool in build_adb_tools():
    await bundle.agent.toolkit.add_tool(tool)
```

`add_tool` 是 async，逐个加即可。验收角色改用 `build_adb_readonly_tools()`，只挂 5 个只读工具。

| 工具 | 作用 | 只读 |
| --- | --- | --- |
| `adb_devices` | 列出已连接设备（序列号、状态、型号） | 是 |
| `adb_screenshot` | 截屏，返回图片块让模型直接看图 | 是 |
| `adb_dump_ui` | 导出界面控件（文字、描述、边界、可点） | 是 |
| `adb_tap` | 按归一化坐标点击 | 否 |
| `adb_swipe` | 按归一化坐标从一点滑到另一点 | 否 |
| `adb_long_press` | 按归一化坐标长按 | 否 |
| `adb_input_text` | 输入 ASCII 文本 | 否 |
| `adb_press_key` | 按 home / back / power 等 | 否 |
| `adb_install` | 安装或覆盖安装 APK | 否 |
| `adb_uninstall` | 卸载应用 | 否 |
| `adb_app_start` | 按包名启动应用 | 否 |
| `adb_app_stop` | 按包名强制停止（杀进程） | 否 |
| `adb_app_state` | 查看应用在前台、后台还是未运行 | 是 |
| `adb_screen_off` | 熄屏 | 否 |
| `adb_unlock` | 唤醒并解除锁屏 | 否 |

每个函数也可单独调用，返回 JSON 文本：

```python
from engines.ae_harness.tools.adb import adb_devices, adb_tap

print(adb_devices())
print(adb_tap(0.5, 0.5))  # 屏幕中心
```

### 坐标

`adb_tap`、`adb_swipe`、`adb_long_press` 只收**归一化坐标**：左上角 `(0, 0)`，右下角 `(1, 1)`。

工具内部用 `adb shell wm size` 读分辨率，再换算成像素执行，返回里同时给出像素值便于核对：

```json
{"status": true, "nx": 0.5, "ny": 0.5, "x": 720, "y": 1520}
```

超出 0~1 直接返回失败，不会执行动作。

### 截图

`adb_screenshot` 返回的不是纯文本，而是 `ToolChunk`：

| 块 | 内容 |
| --- | --- |
| `TextBlock` | JSON 元信息：`timestamp`、`status`、`bytes`、`image`、`screen`、`cost_ms` |
| `DataBlock` | PNG 的 base64，`media_type=image/png` |

模型因此能直接看到画面，可以在提示词里要求它「先截图再判断」。

不落盘：截图只在内存里编码返回，发送前把长边压到 1568 以内（1440×3040 → 743×1568，约 607 KB → 313 KB）。

`with_timing`（默认 `True`）控制是否在元信息里带 `cost_ms`，即本次抓屏、压缩、编码的总毫秒数；实测约 1100 ms。

### 点位核对

点击前先让工具把待点的位置画在图上：

```python
adb_screenshot(marks=[[0.92, 0.07]])
```

图里会出现红圈加序号，模型看图判断红圈是否落在目标上。这一步替代了「点完看页面有没有变化」的盲试，把点错的代价降到最低。

### 设备选择

所有工具都有 `serial` 参数。只连一台时留空自动选中；连多台时必须指定，否则返回错误并列出在线设备。

### adb 来源

优先使用项目内的 `tools/platform-tools/adb.exe`（当前 37.0.2）；该文件不存在时才退回 PATH 里的 `adb`。

```python
from engines.ae_harness.tools.adb import adb_binary

print(adb_binary())  # D:\...\tools\platform-tools\adb.exe
```

### 已知限制

- `adb_dump_ui` 依赖 `uiautomator dump`。部分设备（实测三星 Android 11）会以 137 退出且不生成文件，此时返回 `available: false` 并附当前焦点窗口，请改用 `adb_screenshot`。
- `adb_input_text` 只支持 ASCII；中文要在设备上装 ADBKeyboard 等输入法。
- 截图存到系统临时目录 `ae_harness_adb_shots/`，返回的是路径，模型看不到图。

## 注意事项

1. **默认不挂工具。** `create_agent` 的 `toolkit` 不传时，Agent 工具为空。
2. **工具可创建后追加。**

   ```python
   from agentscope.permission import PermissionBehavior, PermissionDecision
   from agentscope.tool import FunctionTool

   await agent.toolkit.add_tool(
       FunctionTool(
           fn,
           name="fn",
           description="说明",
           permission=PermissionDecision(
               behavior=PermissionBehavior.ALLOW,
               message="允许",
           ),
       )
   )
   ```

   `add_tool` 是 async；默认权限是询问，不给 `ALLOW` 会停下来等确认。
3. **提示词要与工具匹配。** 提示词由调用方传入；正文要求使用的工具必须已经挂上，否则模型会尝试调用不存在的工具。
4. **上下文会累积。** 同一个 Agent 连续 `reply` 共享上下文；要干净开始就重新 `create_agent`。
