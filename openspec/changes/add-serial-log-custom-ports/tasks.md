# Tasks: add-serial-log-custom-ports

## 1. 规则变更落地（已获需求方批准）

- [x] 1.1 修改 `backend/apps/serial_log/AGENTS.md` 真相源条款为双轨口径（config 行以配置为真相源、custom 行以 `sl_log_ports` 为真相源），并补三个写接口到接口表；验证：条款与 design D7 一致，`python utils/gen_arch_stats.py --check-md` 相关文档无告警
- [x] 1.2 修改 `frontend/src/modules/serial-log/AGENTS.md` 端点清单（补 POST/PATCH/DELETE）与权限说明（自定义端口增删改仅超管）；验证：清单与 urls.py 最终路径一致

## 2. 后端数据层：origin 迁移与 api 写点

- [x] 2.1 `LogPort` 增加 `origin` 列（config/custom，default=config）并生成迁移；验证：`python manage.py makemigrations --check` 通过，临时 SQLite 演练全新安装 + 旧库升级（存量行 origin=config、开关值不变）
- [x] 2.2 `api.py` 新增 `create_custom_port` / `update_custom_port` / `delete_custom_port` / `list_custom_port_specs`（唯一写点，含同号校验数据侧兜底）；`ensure_log_ports` 改为只 upsert config 行、不碰 custom 行；验证：新增单测覆盖「配置同步不改写 custom 行」「配置后加同号端口跳过并记 warning」，`python -m pytest -c tests/pytest.ini tests/serial_log -q` 通过

## 3. 后端编排：来源合并 / 本机 IP / 失败细化

- [x] 3.1 新增 `utils/netinfo.py`（纯标准库 UDP 出站探测 + gethostbyname 回退）；`settings.py` 增加 `DEVICE_LOG_ADVERTISE_HOST`；验证：单测覆盖探测成功 / 失败回退 / 配置覆盖三态，ruff check 通过
- [x] 3.2 `sources.source_specs()` 合并配置 + custom 行（经 api 读库，排序去重）；验证：单测覆盖合并结果与 AI 读行路径按端口反查 custom 通道，`python -m pytest -c tests/pytest.ini tests/serial_log -q` 通过
- [x] 3.3 `port_service` 扩展：`list_ports` 返回 `listen_ip` 与行级 `origin`/`address`；新增 `create_port` / `update_port` / `delete_port` 编排（单端口增量 open/close、上限拒绝、`_await_listening` 后用 PortDetector 细化失败 note）；验证：单测覆盖「新增不触发其它端口 close」「满 10 拒绝」「失败 note 区分占用/绑定失败」「删除保留日志文件」，pytest 通过

## 4. 后端接口层：三个写端点

- [x] 4.1 `views.py` + `urls.py` 增加 `POST /ports/`、`PATCH /ports/<port>/`、`DELETE /ports/<port>/`（View 只分发、超管校验、400 可读校验错误、config 行编辑/删除可读拒绝）；验证：api 测试覆盖 201/200/400/403 与信封 snake_case，`python manage.py spectacular --validate` 通过
- [x] 4.2 后端门禁小结：`python manage.py check` + `ruff check`/`ruff format --check`（相关路径）+ `python -m pytest -c tests/pytest.ini tests/serial_log -q` + `python utils/gen_arch_stats.py --check-boundaries` 全绿

## 5. 前端契约与编排层

- [x] 5.1 `api.ts` 增加 `createLogPort` / `updateLogPort` / `deleteLogPort`，`LogPortRow` 补 `origin`/`address`，列表响应补 `listen_ip`；`constants.ts` 补波特率常用值与新增/编辑/删除/失败文案；验证：`npx vue-tsc --noEmit` 通过
- [x] 5.2 新增 `useCustomPorts.ts`（CRUD 编排 + 提交前校验 + 清表单）；`useLogPorts.ts` 失败判定改 `ElMessage.error` + 重试（再次 toggle true）；验证：composable 单测覆盖「enabled&&!listening → error 提示」「重试成功转监听中」「no_log 不判失败」，`npx vue-tsc --noEmit` 通过

## 6. 前端 UI 层

- [x] 6.1 `WifiPortPanel.vue` 加本机 IP 条（复制入口 + 说明）、新增端口按钮（仅超管）、端口列来源徽标与 `IP:端口` 副行；验证：`npm run lint:styles` + `npx vue-tsc --noEmit` 通过，非超管入口不可用
- [x] 6.2 新增模块私有 `PortFormDialog.vue`（el-dialog + sketch-kit 表单，新增/编辑复用，编辑时端口号禁改）与行内编辑/删除入口（删除走 ElMessageBox 含验收降级警告）；验证：组件 ≤500 行、`npm run lint:styles` 通过、表单校验场景（重号/越界/SKU 空）有单测
- [x] 6.3 状态胶囊增加「监听失败」红态与行下失败原因、失败行重试按钮；验证：`npm run lint:styles`（令牌引用完整、无字面色值）+ 既有 serial-log 前端测试更新后全绿 + `npm run build` 通过

## 7. 全链路验收与关单

- [x] 7.1 迁移与恢复演练：临时 SQLite 全新安装 + 旧库升级两条路径，重启后 config 与 custom 端口均按开关恢复监听、关闭端口不监听；验证：演练脚本输出与 spec 场景一致（serial-log-module 关单附加项）
- [x] 7.2 本地门禁 `python run.py check` 通过；前后端改动逐文件暂存、按 Conventional Commits 提交并推 Kahoku，确认 ci-phase1.yml 6 个 job 全绿
- [ ] 7.3 人工验收（对照 delta spec 场景）：新增端口即监听且其它端口不断流；占用端口新增/开启 → 红色失败提示 + 可重试；编辑 SKU 只重启本端口；删除保留日志文件；IP 展示与复制、配置覆盖生效；非超管全只读；验证：验收记录附入 change 目录后交需求方确认