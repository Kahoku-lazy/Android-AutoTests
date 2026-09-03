# API-用例管理 — /api/cases/*

> 用例管理模块（apps/case_manager）：UI 自动化 / API 接口 / Storage 功能 / Web 自动化四类用例定义 + 两级目录树 + 编辑锁（编辑锁 / 硬锁 / 可见性三态）+ YAML 导出。
> 真相源：apps/case_manager/urls.py + views_drf.py / views_*.py + serializers.py + api*.py。
> **信封双口径**：DRF router（directories / definitions / storage/definitions / api-testing/definitions / web/definitions + 手动注册 lock/unlock/visibility）走标准 {status,data}；legacy 平铺路径走平铺 {status, definitions|tree|definition|...}。

## 1. 总览

| 接口 | 方法 | 鉴权 | 说明 |
|---|---|---|---|
| 目录树列表接口 | GET /api/cases/directories/ | 需登录(Bearer) | 目录树（标准信封） |
| 新建目录接口 | POST /api/cases/directories/ | 需登录(Bearer) | 新建根目录（parent_id 只读，标准信封） |
| 目录详情接口 | GET /api/cases/directories/{pk}/ | 需登录(Bearer) | 单个目录（标准信封） |
| 删除目录接口 | DELETE /api/cases/directories/{pk}/ | 需登录(Bearer) | 删除空目录（标准信封） |
| 目录批量移动接口 | POST /api/cases/directories/batch-move/ | 需登录(Bearer) | 批量移动用例/目录（标准信封） |
| 目录权限接口 | POST /api/cases/directories/{pk}/permission/ | 需登录(Bearer) | 更新目录权限（标准信封） |
| UI 用例列表接口 | GET /api/cases/definitions/ | 需登录(Bearer) | UI 用例列表（标准信封） |
| UI 用例新建接口 | POST /api/cases/definitions/ | 需登录(Bearer) | 新建 UI 用例（标准信封） |
| UI 用例详情接口 | GET /api/cases/definitions/{pk}/ | 需登录(Bearer) | UI 用例详情（标准信封） |
| UI 用例整体更新接口 | PUT /api/cases/definitions/{pk}/ | 需登录(Bearer) | UI 用例全量更新（标准信封） |
| UI 用例部分更新接口 | PATCH /api/cases/definitions/{pk}/ | 需登录(Bearer) | UI 用例部分更新（标准信封） |
| UI 用例删除接口 | DELETE /api/cases/definitions/{pk}/ | 需登录(Bearer) | 删除 UI 用例（标准信封） |
| UI 用例批量导入接口 | POST /api/cases/definitions/batch/ | 需登录(Bearer) | UI 用例批量导入（标准信封） |
| Storage 用例列表接口 | GET /api/cases/storage/definitions/ | 需登录(Bearer) | Storage 用例列表（标准信封） |
| Storage 用例新建接口 | POST /api/cases/storage/definitions/ | 需登录(Bearer) | 新建 Storage 用例（标准信封） |
| Storage 用例详情接口 | GET /api/cases/storage/definitions/{pk}/ | 需登录(Bearer) | Storage 用例详情（标准信封） |
| Storage 用例整体更新接口 | PUT /api/cases/storage/definitions/{pk}/ | 需登录(Bearer) | Storage 全量更新（标准信封） |
| Storage 用例部分更新接口 | PATCH /api/cases/storage/definitions/{pk}/ | 需登录(Bearer) | Storage 部分更新（标准信封） |
| Storage 用例删除接口 | DELETE /api/cases/storage/definitions/{pk}/ | 需登录(Bearer) | 删除 Storage 用例（标准信封） |
| Storage 用例批量导入接口 | POST /api/cases/storage/definitions/batch/ | 需登录(Bearer) | Storage 批量导入（标准信封） |
| API 用例列表接口 | GET /api/cases/api-testing/definitions/ | 需登录(Bearer) | API 用例列表（标准信封） |
| API 用例新建接口 | POST /api/cases/api-testing/definitions/ | 需登录(Bearer) | 新建 API 用例（标准信封） |
| API 用例详情接口 | GET /api/cases/api-testing/definitions/{pk}/ | 需登录(Bearer) | API 用例详情（标准信封） |
| API 用例整体更新接口 | PUT /api/cases/api-testing/definitions/{pk}/ | 需登录(Bearer) | API 全量更新（标准信封） |
| API 用例部分更新接口 | PATCH /api/cases/api-testing/definitions/{pk}/ | 需登录(Bearer) | API 部分更新（标准信封） |
| API 用例删除接口 | DELETE /api/cases/api-testing/definitions/{pk}/ | 需登录(Bearer) | 删除 API 用例（标准信封） |
| API 用例批量导入接口 | POST /api/cases/api-testing/definitions/batch/ | 需登录(Bearer) | API 批量导入（标准信封） |
| Web 用例列表接口 | GET /api/cases/web/definitions/ | 需登录(Bearer) | Web 用例列表（标准信封） |
| Web 用例新建接口 | POST /api/cases/web/definitions/ | 需登录(Bearer) | 新建 Web 用例（标准信封） |
| Web 用例详情接口 | GET /api/cases/web/definitions/{pk}/ | 需登录(Bearer) | Web 用例详情（标准信封） |
| Web 用例整体更新接口 | PUT /api/cases/web/definitions/{pk}/ | 需登录(Bearer) | Web 全量更新（标准信封） |
| Web 用例部分更新接口 | PATCH /api/cases/web/definitions/{pk}/ | 需登录(Bearer) | Web 部分更新（标准信封） |
| Web 用例删除接口 | DELETE /api/cases/web/definitions/{pk}/ | 需登录(Bearer) | 删除 Web 用例（标准信封） |
| Web 用例批量导入接口 | POST /api/cases/web/definitions/batch/ | 需登录(Bearer) | Web 批量导入（标准信封） |
| 获取编辑锁接口(DRF) | POST /api/cases/definitions/{case_id}/lock/ | 需登录(Bearer) | 获取编辑锁（标准信封） |
| 释放编辑锁接口(DRF) | POST /api/cases/definitions/{case_id}/unlock/ | 需登录(Bearer) | 释放编辑锁，body 可带 force（标准信封） |
| 硬锁接口(DRF) | POST /api/cases/definitions/{case_id}/case-lock/ | 需登录(Bearer) | 创建者锁定用例（标准信封） |
| 解除硬锁接口(DRF) | POST /api/cases/definitions/{case_id}/case-unlock/ | 需登录(Bearer) | 创建者解除硬锁（标准信封） |
| 可见性接口(DRF) | POST /api/cases/definitions/{case_id}/visibility/ | 需登录(Bearer) | 更新可见性/权限（标准信封） |
| 目录树列表接口(legacy) | GET /api/cases/directories | 需登录(Bearer) | 目录树含用例节点（平铺） |
| 新建目录接口(legacy) | POST /api/cases/directories/create | 需登录(Bearer) | 新建目录，支持 parent_id（平铺） |
| 目录批量移动接口(legacy) | POST /api/cases/directories/batch-move | 需登录(Bearer) | 批量移动（平铺） |
| 目录更新/删除接口(legacy) | POST /api/cases/directories/{dir_id} | 需登录(Bearer) | action=update/delete（平铺） |
| 目录权限接口(legacy) | POST /api/cases/directories/{dir_id}/permission | 需登录(Bearer) | 更新目录权限（平铺） |
| UI 用例列表/保存接口(legacy) | GET/POST /api/cases/definitions | 需登录(Bearer) | UI 列表与保存（平铺） |
| UI 用例批量导入接口(legacy) | POST /api/cases/definitions/batch | 需登录(Bearer) | UI 批量导入（平铺） |
| UI 用例详情/删除接口(legacy) | GET/DELETE /api/cases/definitions/{case_id} | 需登录(Bearer) | UI 单条详情/删除（平铺） |
| 获取编辑锁接口(legacy) | POST /api/cases/definitions/{case_id}/lock | 需登录(Bearer) | 获取编辑锁（平铺，423 保留） |
| 释放编辑锁接口(legacy) | POST /api/cases/definitions/{case_id}/unlock | 需登录(Bearer) | 释放编辑锁（平铺） |
| 硬锁接口(legacy) | POST /api/cases/definitions/{case_id}/case-lock | 需登录(Bearer) | 硬锁（平铺） |
| 解除硬锁接口(legacy) | POST /api/cases/definitions/{case_id}/case-unlock | 需登录(Bearer) | 解除硬锁（平铺） |
| 可见性接口(legacy) | POST /api/cases/definitions/{case_id}/visibility | 需登录(Bearer) | 更新可见性（平铺） |
| Storage 列表/保存接口(legacy) | GET/POST /api/cases/storage/definitions | 需登录(Bearer) | Storage 列表与保存（平铺） |
| Storage 批量导入接口(legacy) | POST /api/cases/storage/definitions/batch | 需登录(Bearer) | Storage 批量导入（平铺） |
| Storage 详情/删除接口(legacy) | GET/DELETE /api/cases/storage/definitions/{case_id} | 需登录(Bearer) | Storage 详情/删除（平铺） |
| API 列表/保存接口(legacy) | GET/POST /api/cases/api-testing/definitions | 需登录(Bearer) | API 列表与保存（平铺） |
| API 批量导入接口(legacy) | POST /api/cases/api-testing/definitions/batch | 需登录(Bearer) | API 批量导入（平铺） |
| API 详情/删除接口(legacy) | GET/DELETE /api/cases/api-testing/definitions/{case_id} | 需登录(Bearer) | API 详情/删除（平铺） |
| Web 列表/保存接口(legacy) | GET/POST /api/cases/web/definitions | 需登录(Bearer) | Web 列表与保存（平铺） |
| Web 批量导入接口(legacy) | POST /api/cases/web/definitions/batch | 需登录(Bearer) | Web 批量导入（平铺） |
| Web 详情/删除接口(legacy) | GET/DELETE /api/cases/web/definitions/{case_id} | 需登录(Bearer) | Web 详情/删除（平铺） |
| 步骤类型接口 | GET /api/cases/step-types | 需登录(Bearer) | 拉取步骤类型（特例 {status,data:{types}}） |
| 导出 YAML 接口 | POST /api/cases/export/yaml | 需登录(Bearer) | 导出测试点为 YAML（平铺） |
| 导出文件列表接口 | GET /api/cases/exports | 需登录(Bearer) | 已导出 YAML 列表（平铺） |
| 下载导出文件接口 | GET /api/cases/exports/{filename} | 需登录(Bearer) | 下载 YAML（FileResponse 非 JSON） |

## 2. 通用约定

- **鉴权**：本模块无公开端点，全部需登录。携带 Authorization: Bearer <access_token>；DRF ViewSet 由 IsAuthenticated + JWTAuthentication 保护，legacy 视图由全局 JWTAuthenticationMiddleware 注入 request.user_id。
- **响应信封双口径**：
  - **标准信封**（DRF router + 手动注册锁端点）：成功 {status: true, data}；失败 {status: false, message}（由 EnvelopeJSONRenderer 包裹，DRF 原生错误字段被提取为 message）。
  - **平铺**（legacy 路径，views_base.py / views_directories.py / views_lock.py / views_ui.py 等 JsonResponse）：成功 {status: true, 业务字段...}，失败 {status: false, message}；step-types 为特例 {status, data:{types}}。
- **四类定义 + ID 前缀**（服务端自动生成，DRF 忽略客户端传入 id）：
  - UI 自动化 TestDefinition → TC-YYYYMMDD-HHMMSS-XXXX（case_type=ui_automation）
  - API 接口 ApiTestCase → API-YYYYMMDD-HHMMSS-XXXX（case_type=api_testing）
  - Storage 功能 StorageTestCase → ST-YYYYMMDD-HHMMSS-XXXX（case_type=storage）
  - Web 自动化 WebTestCase → WEB-YYYYMMDD-HHMMSS-XXXX（case_type=web_automation）
- **目录树**：两级目录（parent 外键）；case_type 区分四类，各自独立树。legacy 目录树把用例节点混入 children；DRF 目录树只返回目录节点（children 仅目录）。
- **可见性过滤**（列表/详情一致）：public 所有人可见；hidden 仅创建者；restricted 创建者 + permitted_users 内用户。无权限时列表不返回该条，详情返回 404。
- **锁三态**：
  - lock（编辑锁）：字段 editing_by / editing_since，30 分钟空闲超时（EDIT_LOCK_TIMEOUT_SECONDS=1800）。
  - case-lock（硬锁）：字段 locked，仅创建者可切换，锁定后他人只读且不可删除。
  - visibility：visibility + permitted_users + permission + permitted_editors，仅创建者可改。
- **字段取值枚举**：priority = P0/P1/P2；visibility = public/hidden/restricted；permission = edit/readonly/restricted。

### 2.1 四类用例共享字段（写入）

> 下表字段为四类序列化器共有；类型特有字段见各节。DRF 请求体用 directory（整数主键，PrimaryKeyRelatedField）；permitted_users / permitted_editors 在 DRF 中为 **文本字段（JSON 字符串）**，响应另附解析后的 permitted_users_list / permitted_editors_list（数组，只读）。legacy 平铺路径则以数组传入/返回（内部 json.dumps）。

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| title | string | 是(create) | 用例标题，同目录下唯一 |
| directory | int | 否 | 目录主键（DRF）；空=根级（未分类） |
| category | string | 否 | 分类 |
| priority | string | 否 | P0/P1/P2，默认 P1 |
| description | string | 否 | 描述 |
| precondition | string | 否 | 前置条件 |
| enabled | bool | 否 | 是否启用，默认 true |
| case_type | string | 否 | 用例类型（服务端按类型固定，不建议传） |
| visibility | string | 否 | public/hidden/restricted，默认 public |
| permitted_users | string | 否 | 指定可见用户（JSON 数组文本） |
| permission | string | 否 | edit/readonly/restricted，默认 edit |
| permitted_editors | string | 否 | 指定可编辑用户（JSON 数组文本） |
| locked | bool | 否 | 硬锁标记（一般经 case-lock 端点变更） |
| created_by / updated_by | string | 否 | 服务端自动填充，忽略传入 |

只读字段（响应中返回）：id、directory_name、created_at、updated_at、editing_by、editing_since、steps_data（解析后的结构化步骤）、permitted_users_list、permitted_editors_list。

---

## 3. 目录接口（DRF router，标准信封）

> 路由：directories（CaseDirectoryViewSet）。注意：序列化器中 parent_id 为 **只读**，故 DRF 新建/详情无法设置父目录，两级子目录的创建走 legacy POST /directories/create（见 §9.1）。

### 3.1 目录树列表接口：GET /api/cases/directories/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| case_type | string | 否 | ui_automation / storage / api_testing / web_automation |

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {
    "directories": [                     # 根级目录数组（仅目录节点，children 仅目录）
      {
        "id": 1,                         # 目录 ID
        "name": "登录模块",              # 目录名
        "case_type": "ui_automation",    # 目录所属用例类型
        "parent_id": null,               # 父目录 ID（根级为 null）
        "sort_order": 0,                 # 排序
        "created_by": "admin",           # 创建者
        "allow_create": true,            # 是否允许创建
        "allow_delete": false,           # 是否允许删除
        "created_at": "2026-08-21T10:00:00+08:00",
        "updated_at": "2026-08-21T10:00:00+08:00",
        "doc_count": 0,                  # 文档数（本序列化器恒 0）
        "children": [                    # 子目录（两级）
          {"id": 2, "name": "子目录", "parent_id": 1, "children": []}
        ]
      }
    ]
  }
}
```

### 3.2 新建目录接口：POST /api/cases/directories/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| name | string | 是 | 目录名 |
| case_type | string | 否 | 类型，默认 ui_automation |
| sort_order | int | 否 | 排序，默认 0 |
| allow_create | bool | 否 | 默认 true |
| allow_delete | bool | 否 | 默认 false |

> parent_id 为只读，不可传；DRF 创建只能生成根级目录。

**成功响应（201）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {                              # 新目录完整对象（字段同 3.1 节点）
    "id": 1, "name": "登录模块", "case_type": "ui_automation",
    "parent_id": null, "sort_order": 0, "created_by": "admin",
    "allow_create": true, "allow_delete": false,
    "doc_count": 0, "children": []
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 这个字段是必填项。 | name 缺失（DRF 默认） |

### 3.3 目录详情接口：GET /api/cases/directories/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。**成功响应（200）** 为单个目录对象，结构同 §3.1 节点。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 目录不存在（DRF 默认） |

### 3.4 删除目录接口：DELETE /api/cases/directories/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。**成功响应（204）**：无响应体（DRF 标准 destroy）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 403 | 只有目录创建者（{created_by}）可以删除此目录 | 非创建者且未开启 allow_delete |
| 403 | 目录下存在子目录或用例，请先清空后再删除 | 目录非空 |
| 404 | 未找到。 | 目录不存在 |

### 3.5 目录批量移动接口：POST /api/cases/directories/batch-move/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| case_ids | array[string] | 否 | 待移动用例 ID 列表 |
| dir_ids | array[int] | 否 | 待移动目录 ID 列表 |
| target_directory_id | int | 是 | 目标目录 ID |

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {
    "moved": 2,                          # 成功移动数量
    "errors": [                          # 逐项失败原因
      {"id": "TC-001", "reason": "用例不存在: TC-001"}
    ]
  }
}
```

> 该端点始终返回 200，失败项进入 errors（如“目标目录不存在”“不能将目录移动到自身”“只支持两级目录，目标目录已是二级目录”“不能将目录移动到其子目录下”等）。

### 3.6 目录权限接口：POST /api/cases/directories/{pk}/permission/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| allow_create | bool | 否 | 是否允许创建 |
| allow_delete | bool | 否 | 是否允许删除 |

**成功响应（200）**：返回更新后的目录对象（结构同 §3.1 节点）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 403 | 只有创建者可以修改权限 | 非创建者 |
| 400 | 目录不存在: {dir_id} | 目录不存在 |
| 404 | 未找到。 | 目录不存在（get_object） |

---

## 4. UI 自动化用例接口（DRF router，标准信封）

> 路由：definitions（UiCaseViewSet，ModelViewSet）。列表/详情均按可见性过滤；directory_id 查询会连带其子目录用例。UI 特有字段：steps（文本步骤）、steps_data_write（结构化步骤，写）、watchers、package_name、design_method、expected_result、metrics。

### 4.1 用例列表接口：GET /api/cases/definitions/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**查询参数**

| 参数 | 类型 | 必填 | 说明 |
|---|---|---|---|
| directory_id | int | 否 | 目录 ID，含其子目录用例 |
| category | string | 否 | 按分类过滤 |
| priority | string | 否 | 按优先级过滤 |

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": [                              # 用例数组（无分页）
    {
      "id": "TC-20260821-153000-AB12",   # 用例 ID
      "title": "登录成功",              # 标题
      "case_type": "ui_automation",      # 类型
      "category": "登录",                # 分类
      "priority": "P1",                  # 优先级
      "description": "验证正确账号密码登录",
      "precondition": "已安装 App",      # 前置条件
      "enabled": true,                   # 是否启用
      "directory": 5,                    # 目录主键（无目录为 null）
      "directory_name": "登录模块",      # 目录名
      "created_by": "admin",             # 创建者
      "updated_by": "admin",             # 最后更新者
      "created_at": "2026-08-21T15:30:00+08:00",
      "updated_at": "2026-08-21T15:30:00+08:00",
      "locked": false,                   # 硬锁标记
      "visibility": "public",            # 可见性
      "permitted_users": "[]",           # 指定可见用户（JSON 文本）
      "permission": "edit",              # 编辑权限
      "permitted_editors": "[]",         # 指定可编辑用户（JSON 文本）
      "editing_by": "",                  # 当前编辑者
      "editing_since": null,             # 编辑锁时间
      "steps": "1. [click] 输入用户名",  # 文本步骤
      "steps_data": [                    # 解析后的结构化步骤
        {"type": "click", "xpath": "//*[@text='登录']"}
      ],
      "watchers": [],                    # 弹窗处理规则
      "package_name": "com.example.app", # 应用包名
      "design_method": "场景流法",       # 设计方法（五法之一）
      "expected_result": "进入首页",     # 预期结果
      "metrics": "通过率 100%",          # 量化指标
      "permitted_users_list": [],        # permitted_users 解析数组
      "permitted_editors_list": []       # permitted_editors 解析数组
    }
  ]
}
```

### 4.2 用例新建接口：POST /api/cases/definitions/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**（共享字段见 §2.1；UI 特有字段如下）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| steps | string | 否 | 文本步骤 |
| steps_data_write | array | 否 | 结构化步骤数组（写，落库为 steps_json） |
| watchers | array | 否 | 弹窗处理规则 [{xpath, action}] |
| package_name | string | 否 | 应用包名 |
| design_method | string | 否 | 设计方法 |
| expected_result | string | 否 | 预期结果 |
| metrics | string | 否 | 量化指标 |

```json
{
  "title": "登录成功",
  "directory": 5,
  "category": "登录",
  "priority": "P1",
  "precondition": "已安装 App",
  "enabled": true,
  "steps_data_write": [{"type": "click", "xpath": "//*[@text='登录']"}],
  "package_name": "com.example.app",
  "design_method": "场景流法",
  "expected_result": "进入首页",
  "metrics": "通过率 100%"
}
```

**成功响应（201）**：返回新建用例完整对象（结构同 §4.1 单条）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 这个字段是必填项。 | title 缺失 |
| 400 | 目录「{目录名}」下已存在同名用例「{title}」 | 同目录重名 |
| 400 | 请求格式错误 | 请求体非合法 JSON |

### 4.3 用例详情接口：GET /api/cases/definitions/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。**成功响应（200）** 返回单条用例对象（结构同 §4.1）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 未找到。 | 用例不存在或无可见权限 |

### 4.4 用例整体更新接口：PUT /api/cases/definitions/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

请求体字段同 §4.2（全量更新，缺省字段回默认值）。**成功响应（200）** 返回更新后对象。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | 这个字段是必填项。 | title 缺失 |
| 400 | 目录下已存在「{title}」 | 同目录重名（字段级 title） |
| 404 | 未找到。 | 用例不存在或无可见权限 |

### 4.5 用例部分更新接口：PATCH /api/cases/definitions/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

请求体仅需传要更新的字段（部分字段）。**成功响应（200）** 返回更新后对象。错误码同 §4.4。

### 4.6 用例删除接口：DELETE /api/cases/definitions/{pk}/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。**成功响应（204）**：无响应体。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 403 | 该用例已被创建者锁定，禁止删除 | 用例被硬锁 |
| 403 | 没有删除权限 | hidden 且非创建者 |
| 404 | 未找到。 | 用例不存在 |

### 4.7 用例批量导入接口：POST /api/cases/definitions/batch/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**：整体为数组（或 {"items": [...]}），每项含 id（可选，存在则更新）、title（必填）、directory_id、steps_data、category、priority、enabled 等。

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {
    "created": 2,                        # 新建数量
    "updated": 1,                        # 更新数量
    "errors": [                          # 失败项
      {"item": {"title": ""}, "error": "标题不能为空"}
    ]
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | items is required | 未传数组且无 items 字段 |

---

## 5. Storage / 功能用例接口（DRF router，标准信封）

> 路由：storage/definitions（StorageCaseViewSet）。7 个动作与 §4 完全同构（列表/新建/详情/整体更新/部分更新/删除/批量），仅类型特有字段不同。以下仅列差异字段，其余（查询参数、错误码、信封）参见 §4。

**Storage 特有字段**（写入）：steps（文本）、steps_data_write（结构化步骤数组）、custom_columns（自定义列数组）、rows（表格行数组 [{key, values}]）、expected_result、design_method、metrics。

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| Storage 用例列表接口 | GET /api/cases/storage/definitions/ | 列表，响应为 {status,data:[...]} |
| Storage 用例新建接口 | POST /api/cases/storage/definitions/ | 新建 |
| Storage 用例详情接口 | GET /api/cases/storage/definitions/{pk}/ | 详情 |
| Storage 用例整体更新接口 | PUT /api/cases/storage/definitions/{pk}/ | 全量更新 |
| Storage 用例部分更新接口 | PATCH /api/cases/storage/definitions/{pk}/ | 部分更新 |
| Storage 用例删除接口 | DELETE /api/cases/storage/definitions/{pk}/ | 删除 |
| Storage 用例批量导入接口 | POST /api/cases/storage/definitions/batch/ | 批量导入 |

**新建请求体示例**

```json
{
  "title": "制冰机缺水保护",
  "directory": 3,
  "priority": "P1",
  "precondition": "水箱排空",
  "steps_data_write": [{"type": "action", "description": "启动制冰"}],
  "expected_result": "提示缺水并停机",
  "custom_columns": [{"key": "固件版本", "values": ["v1.0", "v1.1"]}],
  "rows": [{"key": "column1", "values": ["v1", "v2"]}]
}
```

> 重名报错文案为 目录「{目录名}」下已存在同名存储用例「{title}」（新建）/ 目录下已存在「{title}」（更新）；删除/权限语义同 §4.6。

---

## 6. API 接口测试用例接口（DRF router，标准信封）

> 路由：api-testing/definitions（ApiCaseViewSet）。7 个动作与 §4 同构。类型特有字段仅 config_json（统一 JSON 配置，native JSONField）。config_json 分两种格式：多接口 {case_info, steps, test_data, validation} 与单接口 {meta, request, cases}，保存前经 schema_config.validate_any_api_config 校验（自动探测格式）。

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| API 用例列表接口 | GET /api/cases/api-testing/definitions/ | 列表 |
| API 用例新建接口 | POST /api/cases/api-testing/definitions/ | 新建 |
| API 用例详情接口 | GET /api/cases/api-testing/definitions/{pk}/ | 详情 |
| API 用例整体更新接口 | PUT /api/cases/api-testing/definitions/{pk}/ | 全量更新 |
| API 用例部分更新接口 | PATCH /api/cases/api-testing/definitions/{pk}/ | 部分更新 |
| API 用例删除接口 | DELETE /api/cases/api-testing/definitions/{pk}/ | 删除 |
| API 用例批量导入接口 | POST /api/cases/api-testing/definitions/batch/ | 批量导入 |

**新建请求体示例（多接口格式）**

```json
{
  "title": "查询用户列表",
  "directory": 2,
  "priority": "P1",
  "config_json": {
    "case_info": {"title": "查询用户列表", "description": "", "precondition": ""},
    "steps": [
      {"name": "查询用户", "url": "/api/users", "method": "GET", "headers": {}, "assert": true}
    ],
    "test_data": [],
    "validation": [{"step_index": 0, "enabled": true}]
  }
}
```

**错误码与文案（config_json 校验，取自 schema_config 实际文案）**

| HTTP | message | 触发条件 |
|---|---|---|
| 400 | config_json 结构校验失败: {jsonschema.message} | 结构不合 Schema |
| 400 | case_info.title 不能为空 | 多接口格式 title 为空 |
| 400 | steps 不能为空（至少需要 1 个步骤） | 多接口格式无步骤 |
| 400 | meta.title 不能为空 | 单接口格式 title 为空 |
| 400 | cases 不能为空（至少需要 1 行测试数据） | 单接口格式无 cases |
| 400 | 无法识别 config_json 格式：缺少 meta（单接口）或 case_info（多接口） | 格式无法识别 |
| 400 | 目录「{目录名}」下已存在同名 API 用例「{title}」 | 同目录重名 |

---

## 7. Web 自动化用例接口（DRF router，标准信封）

> 路由：web/definitions（WebCaseViewSet）。7 个动作与 §4 同构。类型特有字段：url（目标 URL）、steps（文本）、steps_data_write（结构化步骤数组）、custom_columns、rows、expected_result、design_method、metrics。

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| Web 用例列表接口 | GET /api/cases/web/definitions/ | 列表 |
| Web 用例新建接口 | POST /api/cases/web/definitions/ | 新建 |
| Web 用例详情接口 | GET /api/cases/web/definitions/{pk}/ | 详情 |
| Web 用例整体更新接口 | PUT /api/cases/web/definitions/{pk}/ | 全量更新 |
| Web 用例部分更新接口 | PATCH /api/cases/web/definitions/{pk}/ | 部分更新 |
| Web 用例删除接口 | DELETE /api/cases/web/definitions/{pk}/ | 删除 |
| Web 用例批量导入接口 | POST /api/cases/web/definitions/batch/ | 批量导入 |

**新建请求体示例**

```json
{
  "title": "首页可访问",
  "directory": 4,
  "priority": "P1",
  "url": "https://example.com/home",
  "steps_data_write": [{"type": "goto", "url": "https://example.com/home"}],
  "expected_result": "页面加载成功"
}
```

> 重名报错文案为 目录「{目录名}」下已存在同名 Web 用例「{title}」（新建）/ 目录下已存在「{title}」（更新）。

---

## 8. 锁与可见性接口（DRF 手动注册，标准信封）

> 跨四类用例共用的 5 个锁/可见性端点，由 CaseActionsViewSet 手动注册（避免与 UiCaseViewSet 前缀冲突）。case_id 为四类用例任一 ID。**注意**：DRF 版本把 api_lock 的 423（锁定冲突）统一映射为 **403**（_raise_lock_error 中 404→NotFound、400→ValidationError、其余→PermissionDenied）；legacy 版本保留 423。锁变更后经 WS /ws/case-editing/{case_id} 推送 case_updated。

### 8.1 获取编辑锁接口：POST /api/cases/definitions/{case_id}/lock/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体（force 可选，body 传 {"force": true} 强制接管）。

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {
    "locked": true,                      # 是否已加锁
    "editing_by": "admin"                # 当前编辑者
  }
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 用例不存在 | case_id 不存在 |
| 403 | 此用例为只读模式，仅创建者可编辑 | permission=readonly 且非创建者 |
| 403 | 此用例仅限指定用户编辑 | permission=restricted 且不在 permitted_editors |
| 403 | 用例已被所有者锁定 | 被硬锁且非创建者 |
| 403 | 用例正被 {editing_by} 编辑中 | 他人持编辑锁且未超时 |

### 8.2 释放编辑锁接口：POST /api/cases/definitions/{case_id}/unlock/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**请求体**（可选）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| force | bool | 否 | true 时创建者强制踢出他人编辑锁 |

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {"unlocked": true}             # 是否已释放
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 用例不存在 | case_id 不存在 |
| 403 | 只有用例创建者可以强制解除编辑锁 | force=true 且非创建者 |
| 403 | 只有编辑者或创建者可以释放编辑锁 | 非编辑者且非创建者 |

### 8.3 硬锁接口：POST /api/cases/definitions/{case_id}/case-lock/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

无请求体。**成功响应（200）**：{status: true, data: {"locked": true}}（已锁定则 already_locked）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 用例不存在 | case_id 不存在 |
| 403 | 只有创建者可以锁定用例 | 非创建者 |

### 8.4 解除硬锁接口：POST /api/cases/definitions/{case_id}/case-unlock/

无请求体。**成功响应（200）**：{status: true, data: {"unlocked": true}}（已解锁则 already_unlocked）。

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 用例不存在 | case_id 不存在 |
| 403 | 只有创建者可以解除锁定用例 | 非创建者 |

### 8.5 可见性接口：POST /api/cases/definitions/{case_id}/visibility/

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |
| Content-Type | application/json |

**请求体**（字段 snake_case）

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| visibility | string | 否 | public/hidden/restricted，默认 public |
| permitted_users | array/string | 否 | 指定可见用户（restricted 时生效） |
| permitted_editors | array/string | 否 | 指定可编辑用户 |
| permission | string | 否 | edit/readonly/restricted |

**成功响应（200）**

```json
{
  "status": true,                        # 请求是否成功
  "data": {"visibility": "restricted"}   # 更新后的可见性
}
```

**错误码与文案**

| HTTP | message | 触发条件 |
|---|---|---|
| 404 | 用例不存在 | case_id 不存在 |
| 403 | 只有创建者可以修改可见性 | 非创建者 |
| 400 | 无效的可见性值，可选: public / hidden / restricted | visibility 取值非法 |

---

## 9. Legacy 平铺端点（分组简述）

> 以下为保留给旧前端的平铺路径（无尾斜杠），响应信封为平铺 {status, 业务字段...}，与 §3~§8 行为一致、字段与错误文案基本同源。详细字段/错误文案可对照上文对应端点。

### 9.1 目录 legacy（平铺 {status, tree|directory|result}）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| 目录树列表接口(legacy) | GET /api/cases/directories | 返回 {status:true, tree:[...]}，tree 含用例节点混入 children |
| 新建目录接口(legacy) | POST /api/cases/directories/create | 请求体 {name, parent_id, sort_order, case_type}，返回 {status:true, directory:{...}}；支持 parent_id 建子目录 |
| 目录批量移动接口(legacy) | POST /api/cases/directories/batch-move | 请求体 {items:[{type,id}], target_directory_id}，返回 {status:true, moved, errors} |
| 目录更新/删除接口(legacy) | POST /api/cases/directories/{dir_id} | 请求体 {action:"update"|"delete", name, parent_id, sort_order}，返回 {status:true, result:{...}} |
| 目录权限接口(legacy) | POST /api/cases/directories/{dir_id}/permission | 请求体 {allow_create, allow_delete}，返回 {status:true} |

**目录树响应示例（legacy）**

```json
{
  "status": true,                        # 请求是否成功
  "tree": [                              # 根级节点（目录与用例混排）
    {
      "id": 1, "name": "登录模块", "parent_id": null, "sort_order": 0,
      "node_type": "directory",          # 节点类型 directory/case
      "case_count": 2,                   # 用例数（含子目录）
      "created_by": "admin", "allow_create": true, "allow_delete": false,
      "children": [
        {"id": "case:TC-001", "name": "登录成功", "node_type": "case",
         "case_id": "TC-001", "case_type": "ui_automation", "enabled": true,
         "priority": "P1", "category": "登录", "step_count": 3, "children": []}
      ]
    }
  ]
}
```

> 目录 legacy 通用错误：目录名称不能为空、只支持两级目录，不能创建三级目录、父级目录不存在: {id}、该层级下已存在同名目录: {name}、目录下存在子目录或用例，请先清空后再删除、只有目录创建者（{created_by}）可以删除此目录。

### 9.2 UI 用例 legacy（平铺）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| UI 用例列表/保存接口(legacy) | GET/POST /api/cases/definitions | GET 返回 {status:true, definitions:[...]}；POST 保存，id 缺省自动生成 TC-...，返回 {status:true, id, updated_at} |
| UI 用例批量导入接口(legacy) | POST /api/cases/definitions/batch | 请求体 {cases:[...], overwrite, directory_id}，返回 {status:true, imported, skipped, failed} |
| UI 用例详情/删除接口(legacy) | GET/DELETE /api/cases/definitions/{case_id} | GET 返回 {status:true, definition:{...}}；DELETE 返回 {status:true} |

> 列表支持 directory_id 查询；可见性过滤同 §2。批量限制 BATCH_IMPORT_LIMIT=500。通用错误：无效的 JSON、cases 必须是非空数组、单次批量导入最多 500 条用例、not found(404)、用例已被所有者锁定(403)、Forbidden(403)。保存冲突（乐观锁/重名）经 api 层 ConflictError/ValueError 映射 409，文案如 用例「{title}」已被他人修改，请刷新后重试、目录「{dir}」下已存在同名用例「{title}」。

### 9.3 Storage 用例 legacy（平铺）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| Storage 列表/保存接口(legacy) | GET/POST /api/cases/storage/definitions | 同 9.2，返回 {status:true, definitions:[...]}；id 缺省生成 ST-... |
| Storage 批量导入接口(legacy) | POST /api/cases/storage/definitions/batch | 返回 {status:true, imported, skipped, failed} |
| Storage 详情/删除接口(legacy) | GET/DELETE /api/cases/storage/definitions/{case_id} | 同 9.2 |

### 9.4 API 用例 legacy（平铺）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| API 列表/保存接口(legacy) | GET/POST /api/cases/api-testing/definitions | 同 9.2；POST 支持 config_json 或平铺字段（method/url/headers/body 等）自动组装 config_json，并做 validate_any_api_config 校验（校验失败返回 400）；id 缺省生成 API-... |
| API 批量导入接口(legacy) | POST /api/cases/api-testing/definitions/batch | 平铺字段组装为多接口 config_json 后批量保存 |
| API 详情/删除接口(legacy) | GET/DELETE /api/cases/api-testing/definitions/{case_id} | 同 9.2；响应附带 method/url/headers 便捷字段（从 config_json 提取） |

### 9.5 Web 用例 legacy（平铺）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| Web 列表/保存接口(legacy) | GET/POST /api/cases/web/definitions | 同 9.2；id 缺省生成 WEB-... |
| Web 批量导入接口(legacy) | POST /api/cases/web/definitions/batch | 返回 {status:true, imported, skipped, failed} |
| Web 详情/删除接口(legacy) | GET/DELETE /api/cases/web/definitions/{case_id} | 同 9.2 |

### 9.6 锁与可见性 legacy（平铺，423 保留）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| 获取编辑锁接口(legacy) | POST /api/cases/definitions/{case_id}/lock | 成功 {status:true, editing_by, editing_since, created_by}；冲突 423 |
| 释放编辑锁接口(legacy) | POST /api/cases/definitions/{case_id}/unlock | body {force}；成功 {status:true, released|force_unlocked|already_unlocked} |
| 硬锁接口(legacy) | POST /api/cases/definitions/{case_id}/case-lock | 成功 {status:true, locked:true|already_locked} |
| 解除硬锁接口(legacy) | POST /api/cases/definitions/{case_id}/case-unlock | 成功 {status:true, locked:false|already_unlocked} |
| 可见性接口(legacy) | POST /api/cases/definitions/{case_id}/visibility | body snake_case {visibility, permitted_users, permitted_editors, permission}；成功 {status:true, visibility} |

> 未登录时这 5 个端点返回 401 未登录；其余错误文案同 §8（用例不存在 404、此用例为只读模式…/用例正被…编辑中/用例已被所有者锁定 423、只有创建者可以…/只有编辑者或创建者… 403、无效的可见性值… 400）。与 DRF 版区别：此处 **423（锁定冲突）保留为真实 HTTP 状态码**。

### 9.7 步骤类型接口：GET /api/cases/step-types

| 项 | 值 |
|---|---|
| 鉴权 | 需登录(Bearer) |

**查询参数**：target（android / web / api，默认 android）。**特例信封**：{status:true, data:{types:[...]}}。

```json
{
  "status": true,                        # 请求是否成功
  "data": {
    "types": [                           # 指定平台可用操作类型
      {"type": "click", "label": "点击", "fields": []}
    ]
  }
}
```

### 9.8 YAML 导出与下载（legacy）

| 接口 | 方法/路径 | 说明 |
|---|---|---|
| 导出 YAML 接口 | POST /api/cases/export/yaml | 请求体 {test_case_name, page_ids}；把 element_locator 测试点/流程导出为 YAML 并写文件，返回 {status:true, filename, yaml} |
| 导出文件列表接口 | GET /api/cases/exports | 返回 {status:true, files:[{name, size, time}]}；未登录 401 Unauthorized |
| 下载导出文件接口 | GET /api/cases/exports/{filename} | **FileResponse**（application/x-yaml），非 JSON；未登录 401 Unauthorized；不存在 404 not found |

**导出 YAML 响应示例**

```json
{
  "status": true,                        # 请求是否成功
  "filename": "test_20260821_153000.yaml",  # 生成的文件名
  "yaml": "name: auto_test\n..."         # YAML 文本内容
}
```

---

## 10. 附：WS 编辑锁推送（非 REST）

- 通道：/ws/case-editing/{case_id}；服务端单一事件 case_updated。
- 锁状态变更 → api_lock.py 写库 → 推送 case_updated，前端以推送驱动只读禁用。
- 写库仍走 api，consumer 不直接 ORM 写。
