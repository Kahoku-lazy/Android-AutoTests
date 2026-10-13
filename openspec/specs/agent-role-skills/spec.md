# agent-role-skills Specification

## Purpose
让角色在回复前把本地技能目录挂进自己的工具包，使模型能看到技能名称与描述，并在运行时读取完整说明。执行角色可见的技能由工具配置中的名单决定。

## Requirements

### Requirement: 角色可注册技能来源
角色 MUST 能在创建智能体之前，把一组技能来源追加到自己的工具包。每一项 MUST 是目录路径、已装载的技能，或技能加载器。目录路径 MUST 被当作本地目录加载；相对路径 MUST 按仓库根目录解析，绝对路径 MUST 保持不变。默认 MUST 扫描该目录下的子目录。空字符串 MUST 被跳过。调用方 MUST 能指定目标工具组；未指定时来源追加到始终激活的常驻组。指定了工具包中不存在的组名时，登记 MUST 失败，且错误信息包含该组名。

#### Scenario: 相对路径下的子目录技能被列出
- **WHEN** 角色未指定目标组，注册仓库内相对路径 `engines/agents/skills/executor`，且该目录的子目录含有带名称与描述的技能说明
- **THEN** 工具包的常驻组列出该子目录技能的名称，并带上要求先通过技能查看器读取完整说明的提示

#### Scenario: 空路径被跳过
- **WHEN** 注册列表中含有只含空白的路径，以及一个有效目录
- **THEN** 空白路径不产生加载器，有效目录仍被注册

#### Scenario: 指定已有工具组
- **WHEN** 角色把 `engines/agents/skills/executor` 登记到工具包中已存在的 `platform_business` 组，且该组当前未激活
- **THEN** 该目录来源挂在 `platform_business`，常驻组不包含该目录；该组未激活时模型输入不列出 `platform-tools-manual`

#### Scenario: 指定不存在的组
- **WHEN** 角色把技能目录登记到工具包中不存在的组名
- **THEN** 登记失败，错误信息包含该组名

### Requirement: 重复目录不重复挂载
同一角色对已经注册过的同一目录再次注册时，MUST 跳过，工具包中该目录只保留一份来源。

#### Scenario: 同一目录注册两次
- **WHEN** 角色对同一技能目录连续注册两次
- **THEN** 工具包中该目录只对应一个来源，且技能仍只列出一次

### Requirement: 非法来源被拒绝
技能来源既不是目录路径、也不是已装载技能或技能加载器时，系统 MUST 拒绝注册，并在错误中说明实际收到的类型。

#### Scenario: 传入数字
- **WHEN** 角色注册的来源是整数
- **THEN** 注册失败，错误信息包含收到的类型名

### Requirement: 执行角色技能名单决定可见技能
执行角色的工具包 MUST 按工具配置中的技能目录名单把技能挂到 `platform_business` 组，并扫描这些目录的子目录。该组未激活时，这些技能 MUST NOT 出现在模型可见的技能列表中。该组激活后，可用技能 MUST 包含名单目录下的子技能。从名单中删掉一项后重新组装工具包，该目录下的技能 MUST NOT 再出现在可用技能列表中。

#### Scenario: 名单包含执行技能目录
- **WHEN** 技能名单包含 `engines/agents/skills/executor`，据此组装执行角色工具包，并打开 `platform_business`
- **THEN** 可用技能包含该目录子技能 `platform-tools-manual`

#### Scenario: 组未打开时技能不可见
- **WHEN** 技能名单包含 `engines/agents/skills/executor`，据此组装执行角色工具包，且 `platform_business` 保持关闭
- **THEN** 模型可见技能列表不包含 `platform-tools-manual`

#### Scenario: 从名单删掉该目录
- **WHEN** 技能名单为空并据此重新组装执行角色工具包，再打开 `platform_business`
- **THEN** 可用技能列表为空

### Requirement: 执行角色启动前登记技能名单
执行角色在创建智能体之前 MUST 把工具配置中的技能目录名单登记到 `platform_business` 组。相对路径 MUST 按仓库根目录解析。名单中的空白路径 MUST 被跳过。同一目录已经挂在该工具包上时 MUST 不新增第二份来源。这些目录 MUST NOT 挂到始终激活的常驻组。登记完成时智能体 MUST 尚未创建。

#### Scenario: 构造后技能目录已登记且智能体未创建
- **WHEN** 使用模型连接配置构造执行角色，且技能名单包含 `engines/agents/skills/executor`
- **THEN** 该目录来源在 `platform_business` 组中，常驻组没有该目录，且智能体尚未创建

#### Scenario: 工具包已含同一目录
- **WHEN** 执行角色所用工具包已经在 `platform_business` 组挂有技能名单中的同一目录，再构造执行角色
- **THEN** 该目录只对应一份技能来源
