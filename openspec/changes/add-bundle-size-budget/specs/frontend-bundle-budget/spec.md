## Purpose

给构建产物装一道离线的体积闸：谁把首屏或某个懒加载块撑大了，提交前就红，而不是等用户觉得慢再回头查。
它盯的是「原因」（字节），`tests/perf` 盯的是「结果」（时间与传输），两者互补。

## ADDED Requirements

### Requirement: 入口资源体积有上限

门禁 SHALL 从构建产物 `frontend/dist/index.html` 中识别入口脚本与入口样式（`script[src]`、`link[href]`），
对其 gzip 体积设上限；MUST NOT 依赖文件哈希命名推断入口。
`entry_js_kb` MUST 同时计入 `<script src>` 与 `rel="modulepreload"` / `rel="preload"` 指向的 JS——
后者是浏览器首屏一定会预下载的块，漏算会让「把大包拆成预载块」看起来像优化。
产物不存在时 SHALL 先执行一次构建再用其结果判定；入口引用识别不到时 MUST 失败并说明原因，MUST NOT 静默通过。

#### Scenario: 入口脚本超预算即失败

- **WHEN** 入口 JS 的 gzip 体积超过 `entry_js_kb`
- **THEN** 门禁失败，信息含指标名、实测 KB、预算 KB 与超出量

#### Scenario: 首屏预载块被计入入口

- **WHEN** 构建产物把某个大块写进 `index.html` 的 `rel="modulepreload"`，而入口 `<script src>` 很小
- **THEN** `entry_js_kb` 仍把该预载块的 gzip 体积算进去，并输出「脚本 X KB + 首屏预载 Y KB」的构成
- **AND** 只把大块改成预载、入口脚本本身变小，MUST NOT 被判定为体积下降

#### Scenario: 入口识别不到不静默通过

- **WHEN** `dist/index.html` 中找不到任何 `script[src]` 或 `link[href]` 指向的资产
- **THEN** 门禁失败并提示检查构建产物，而不是报告「全部在预算内」

### Requirement: 单块与总量同时受控

门禁 SHALL 对 `dist/assets/*.js` 计算最大单块 gzip 体积与全部 JS 的 gzip 总量，并各自设上限。
两项 MUST 都参与判定：只守单块会放过「很多中等块」，只守总量会放过「一个巨块」。

#### Scenario: 单个巨块被拦下

- **WHEN** 某个 chunk 的 gzip 体积超过 `largest_chunk_kb`
- **THEN** 门禁失败并在信息中给出该 chunk 的文件名与体积

#### Scenario: 零散膨胀被拦下

- **WHEN** 单块都没超，但 JS 总量超过 `total_js_kb`
- **THEN** 门禁失败并给出总量实测值与预算值

### Requirement: 预算基线可追溯且改变需说明理由

预算 SHALL 与基线值一起登记在 `frontend/bundle-budgets.json`（`baseline` 与 `budget` 两组键）。
调整预算时 MUST 同时更新基线或写明依据，MUST NOT 只把 `budget` 调大以让红灯变绿。

#### Scenario: 同一文件里能读懂阈值来源

- **WHEN** 查看 `frontend/bundle-budgets.json`
- **THEN** 能同时读到当前实测基线、预算上限与统计口径（gzip level 9）
