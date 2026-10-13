## MODIFIED Requirements

### Requirement: 截图工具只编一次并同时给出模型图与本地图

截图工具 SHALL 取**原始帧**后只编码一次作为模型输入，且该编码 MUST 为**无损、不缩放**（原始帧原尺寸 → PNG → base64），MUST NOT 对给模型的图做有损压缩或降采样，也 MUST NOT 先落到有损格式再二次压缩。工具返回 SHALL 同时包含给模型的图片数据（base64 与媒体类型 `image/png`）与本地图片信息（相对路径与文件名）。本地图片 SHALL 以**毫秒**精度时间戳命名（`capture_YYYYmmdd_HHMMSS_mmm.jpg`），SHALL 保存为全分辨率，且扩展名 MUST 与真实格式一致。`keep_local` 为假时 MUST NOT 写本地文件，但仍 SHALL 把图片数据给模型。

#### Scenario: 一次编码

- **WHEN** 角色调用截图工具
- **THEN** 设备只被取一次原始帧；给模型的图片由该原始帧直接编码得到，MUST NOT 存在中间的重复压缩

#### Scenario: 同时返回 base64 与本地路径

- **WHEN** 截图成功且 `keep_local` 为真
- **THEN** 工具返回里既有给模型的图片数据，也有本地图片的相对路径与文件名

#### Scenario: 本地图毫秒命名且格式一致

- **WHEN** 截图落盘
- **THEN** 文件名为 `capture_YYYYmmdd_HHMMSS_mmm.jpg`（毫秒三位），内容为全分辨率 JPEG，扩展名与真实格式一致

#### Scenario: 模型图不超过档位

- **WHEN** 角色调用截图工具并拿到给模型的图片
- **THEN** 该图片为**无损格式（PNG）**，且尺寸与原始帧一致（不缩放、不有损压缩）

#### Scenario: 不落盘时仍给模型

- **WHEN** `keep_local` 为假
- **THEN** 不写本地文件，本地路径与文件名如实为空，但给模型的图片数据仍 SHALL 返回
