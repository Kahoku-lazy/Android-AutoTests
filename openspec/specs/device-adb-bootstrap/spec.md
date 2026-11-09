# device-adb-bootstrap Specification

## Purpose
TBD - created by archiving change adb-platform-bootstrap. Update Purpose after archive.

## Requirements

### Requirement: adb 只使用平台自带来源

平台运行期使用的 adb MUST 来自以下顺序之一：`ADB_PATH` 环境变量、项目内 `tools/platform-tools/adb`、Python 依赖 `adbutils` 包内置的 adb。解析 MUST NOT 回退到系统 PATH；三者都不可用时 MUST 抛出一个可操作的错误，说明运行 `python run.py setup` 安装，而不是把错误吞成空结果。

解析结果 MUST 同时用于平台自身的 adb 子进程与 `uiautomator2`（通过 `ADBUTILS_ADB_PATH`），两者 MUST 使用同一份二进制。

#### Scenario: 项目内 adb 优先于其它来源

- **WHEN** `tools/platform-tools/adb` 存在，且环境里也装了系统 adb
- **THEN** 平台执行的 adb 子进程首项是项目内路径
- **AND** 系统 PATH 上的 adb 不会被调用

#### Scenario: 没有系统 adb 也能工作

- **WHEN** PATH 中没有任何 adb，但项目内或 `adbutils` 包内置的 adb 存在
- **THEN** 设备发现与设备动作仍能执行
- **AND** `uiautomator2` 使用的也是同一份 adb

#### Scenario: 全部来源缺失时给出可操作错误

- **WHEN** `ADB_PATH`、项目内 adb、`adbutils` 内置三者都不存在
- **THEN** 设备列表接口返回 503 且响应 message 指向 `python run.py setup`
- **AND** 不返回「空设备列表」冒充成功

### Requirement: 控制台可安装并校验 platform-tools

`python run.py setup` SHALL 检测项目内 adb；缺失时按当前操作系统下载官方 platform-tools，校验文件大小与校验和后再解压安装到 `tools/platform-tools/`，并在安装后执行一次 `adb version` 自检。

`--check` SHALL 只做检测并以退出码表示结果；`--force` SHALL 重新安装；`--from-file` SHALL 支持离线 zip。已安装且校验通过时 MUST NOT 重复下载。

#### Scenario: 检测到缺失后安装

- **WHEN** 项目内没有 adb，执行 `python run.py setup`
- **THEN** 下载对应系统的 platform-tools，校验通过后解压到 `tools/platform-tools/`
- **AND** 输出 `adb version` 与安装路径

#### Scenario: 校验和不符不落位

- **WHEN** 下载/提供的 zip 大小或校验和与记录不一致
- **THEN** 安装失败并报错
- **AND** `tools/platform-tools/` 保持原状（不存在或仍是旧版本）

#### Scenario: 已安装时幂等

- **WHEN** 项目内 adb 已存在且校验通过
- **THEN** `python run.py setup` 不重新下载
- **AND** 退出码为 0

#### Scenario: 离线安装

- **WHEN** 使用 `--from-file <zip>` 且 zip 校验通过
- **THEN** 不访问网络，直接完成安装

### Requirement: adb 缺失时设备接口可操作

adb 全部来源缺失时，设备列表与扫描接口 SHALL 返回 503 与可操作提示；设备状态同步 MUST NOT 因缺少 adb 而把已有设备误判为离线或清空。

#### Scenario: 设备列表明确报错

- **WHEN** adb 不可用，请求 `GET /api/devices/`
- **THEN** 返回 503
- **AND** 响应 message 提示运行 `python run.py setup`
