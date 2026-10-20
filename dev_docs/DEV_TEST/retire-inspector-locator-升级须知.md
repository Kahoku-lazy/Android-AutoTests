# 升级须知：设备检查器与元素定位退役

> 对应变更：`retire-inspector-and-element-locator`（已归档，2026-10-20）
> 影响版本：本次拉取代码后**必须执行数据库迁移**，否则旧代码会报表不存在。

## 一、本次去掉了什么

| 对象 | 状态 |
|---|---|
| 后端 `apps/device_inspector`、`apps/element_locator` | 已删除 |
| 接口 `/api/inspector/*`、`/api/elements/*` | 已下线（404） |
| 数据表 `di_snapshots`、`el_locator_projects`、`el_locator_directories`、`el_pages`、`el_elements`、`el_page_flows` | **已 drop，数据不保留、不可恢复** |
| 前端「设备检查器」「元素定位」两个模块与侧栏入口 | 已删除 |
| 页面流节点关联元素定位页面 / 元素端口 | 已删除；节点改为纯手工命名，起点只剩「启动 App」 |
| `utils/xpath.py`、`utils/element_layers.py` | 已删除 |
| 检查器媒体目录 `{MEDIA_ROOT}/inspector/` | 已删除（截图与缩略图） |

## 二、升级步骤（按顺序）

```bash
git pull
python manage.py migrate          # 必须：drop 6 张表 + 清理页面流文档的关联字段
python run.py stop && python run.py start
```

前端若单独部署，需要重新 `npm run build`（旧产物仍引用已删模块，会白屏）。

## 三、不可回滚提示

- 6 张表的数据在迁移时被 drop，**回滚代码也无法恢复**；如需留档，只能在升级前自行备份数据库。
- 页面流文档里的 `linked_elements` / `linked_page_domain` / `linked_page_id` / `linked_page_name` 四个键已被迁移清空，文档本身与其余节点属性保留。

## 四、升级后自查

1. 侧栏「数据」分组只剩「设备管理 / 页面流 / 串口日志」。
2. 打开一篇历史页面流文档：能正常渲染、能保存，起点显示「启动 App」。
3. 仪表盘「测试资产」章节不再出现「Android元素」。
4. `python manage.py check` 与 `python tools/gen_arch_stats.py --check-boundaries` 均通过。
