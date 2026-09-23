## REMOVED Requirements

### Requirement: Interaction behavior unchanged

**Reason**: 该要求把「账号切换菜单保持可用」写进了侧栏的交互契约。本次变更移除多账号机制，账号切换菜单与「添加账号」入口一并消失，该要求与目标状态直接冲突。

**Migration**: 其中仍然成立的部分（折叠、拖拽调宽、退出登录）由本变更新增的要求 `Sidebar interactions preserved without account switching` 承接；账号菜单相关表述作废。

## ADDED Requirements

### Requirement: Sidebar interactions preserved without account switching

侧栏的折叠、拖拽调宽与退出登录行为 MUST 保持可用；侧栏 MUST NOT 再提供账号切换菜单或「添加账号」入口，底部账号区 SHALL 只呈现当前账号名。本变更 MUST NOT 改变路由 path 或鉴权流程。

#### Scenario: Collapse and resize still work

- **WHEN** 用户折叠侧栏并拖拽调整宽度
- **THEN** 侧栏可折叠、宽度可调整，行为与改前一致

#### Scenario: Logout returns to login page

- **WHEN** 用户点击侧栏的「退出」
- **THEN** 登出后回到 `/login`，不再停留在工作台

#### Scenario: No account switch menu remains

- **WHEN** 用户点击侧栏底部的当前账号名
- **THEN** 不展开任何账号列表，也不出现「添加账号」入口
- **AND** 界面只显示当前账号名（折叠态下通过 title 提示）
