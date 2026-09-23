## ADDED Requirements

### Requirement: Back chip sits at the right of the crumb row

当 `.doc-body` 顶部的面包屑条同时渲染波浪祖先链与返回芯片时，返回芯片 MUST 位于该条右端（导航行右上角），祖先链 MUST 仍靠该条左端。系统 SHALL NOT 把返回芯片迁入 `.wb-header`。仅有祖先链、没有返回芯片时，祖先链仍靠左，不为此伪造芯片。仅有返回芯片、没有祖先链时，该芯片仍 MUST 靠该条右端。

#### Scenario: Locator project workspace back chip is top-right of the crumb row

- **WHEN** 用户打开元素定位某项目工作台（`.locator-project-workspace`）
- **THEN** 「返回项目列表」芯片在 `.wb-crumbs` 内可见，且位于该条右端
- **AND** 祖先链（元素定位 Hub → 当前项目）仍靠该条左端
- **AND** `.wb-header` 内没有该芯片
- **AND** 激活芯片后路由回到 `/elements`

#### Scenario: Back-only crumb row still aligns the chip right

- **WHEN** 某 L2 子页只传入返回芯片、不渲染祖先链
- **THEN** 返回芯片仍位于 `.wb-crumbs` 右端
- **AND** 激活后仍进入该芯片绑定的上一层路由
