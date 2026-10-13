## Context

见 proposal.md 的 Why。`xpath_action` 的 `get_text` 目前只取第一条文本，`index` 不参与取值。点击和长按已经按同一 xpath 的命中顺序使用 `index`。

## Goals / Non-Goals

**Goals:**

- `get_text` 返回全部命中，下标与点击所用下标一致，并带像素范围。
- `text` 仍是 `index` 指向的那一条，便于只读该字段的调用方。

**Non-Goals:**

- 不改 `exists`、`click`、`long_click`。
- 不改 xpath 语法，也不在返回里增加 resource-id、class 等其它属性。

## Decisions

1. **命中列表放在设备控制实现，三处工具都调用它。**  
   平台调试页走引擎包装，执行模型走设备控制对象。两边都要同一份下标和范围。  
   备选：只改 `apps/ai_assistant/tools.py`。否决原因是执行模型看不到这份列表。

2. **每条命中含 `index`、`text`、`bounds`。**  
   `bounds` 用元素上的 `[左,上][右,下]` 像素范围。相同文本靠范围区分位置。  
   备选：只返回下标和文本。相同文案无法分辨在页面上的位置。

3. **`text` 保留为 `index` 那一条。**  
   未命中或下标越界时 `text` 为空，`items` 仍列出实际命中。  
   备选：去掉 `text`，只留 `items`。会让只读 `text` 的调用方失效。

## 模块防火墙自检

- 设备实现留在 `engines/device`，工具只调用其方法，不碰 uiautomator2 句柄。
- 无跨 App import，无写库，无前端改动。

## Risks / Trade-offs

- [返回变大] → 只在 `get_text` 增加字段，点击路径不多取元素列表给模型。
- [范围字符串依赖页面层级里的 bounds] → 与点击下标同源；没有 bounds 时该字段为空字符串，下标仍然给出。
