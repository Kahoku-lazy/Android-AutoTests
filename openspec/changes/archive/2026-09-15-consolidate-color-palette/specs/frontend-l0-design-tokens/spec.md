## ADDED Requirements

### Requirement: 颜色原子以调色板为准且只降不增
T0 主 token 的颜色原子 SHALL 收敛为一套经感知聚类（CIE76 ΔE ≤ 8）确定的调色板：每个原子 MUST 属于该调色板，原子总数 MUST NOT 超过登记上限，命名 MUST 形如 `--color-<色相>-<明度 2 位>[-s<饱和>][-a<alpha 2 位>]`，SHALL NOT 再出现序号兜底名（`-2`…`-9`）。透明度 SHALL 只取调色板登记的 alpha 档位。调色板之外的色值 MUST NOT 进入 T0。

#### Scenario: 新颜色需求先复用调色板
- **WHEN** 开发需要一个新的颜色或透明度
- **THEN** MUST 先复用调色板内最接近的原子（ΔE ≤ 8）；确需新增 MUST 先修订调色板并同步上限，SHALL NOT 直接往 tokens.css 追加原子

#### Scenario: 门禁拦截调色板外原子
- **WHEN** 静态校验扫描 `shared/styles/tokens.css`
- **THEN** 颜色原子总数 MUST ≤ 登记上限、每个原子名 MUST 命中调色板白名单、且 SHALL NOT 命中序号兜底名模式；任一命中即 exit 非 0
