## REMOVED Requirements

### Requirement: 光标锚定浮层完整可见于视口内

**Reason**: 页面流画布随模块整体删除，画布内浮层视口收敛不再有承载实现。

**Migration**: 无。其它模块的浮层行为由各自规格约束，不受影响。

### Requirement: 关联页面列表不被裁切

**Reason**: 页面流画布随模块整体删除，「选择 Android 页面」列表已随元素定位退役与本单删除，不再有承载实现。

**Migration**: 无。

### Requirement: 浮层高于视口时按视口收敛

**Reason**: 页面流画布随模块整体删除，浮层收敛算法不再有承载实现。

**Migration**: 无。

### Requirement: 浮层仍为光标锚定的非模态菜单

**Reason**: 页面流画布随模块整体删除，画布右键菜单不再有承载实现。

**Migration**: 无。非模态浮层的通用口径仍由 `frontend-l5-overlay` 约束。
