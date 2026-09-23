## 1. <!-- 任务组名 -->

- [ ] 1.1 <!-- 任务描述 -->
- [ ] 1.2 <!-- 任务描述 -->

## 2. <!-- 任务组名 -->

- [ ] 2.1 <!-- 任务描述 -->
- [ ] 2.2 <!-- 任务描述 -->

<!-- 编写约定（apply 阶段按 `- [ ]` 解析进度，任务必须是 checkbox）：
     1. 每个任务自带验证方式，写在任务描述里，按项目门禁选取：
        - 后端：python manage.py check && ruff check && pytest <路径>
        - 前端：npm run build 通过 + vue-frontend-check 门禁
        - 全链路：quality-gate 四齿轮审查
        - 架构红线：python tools/gen_arch_stats.py --check-boundaries
        - 文档同步：python tools/gen_arch_stats.py --check-md --doc <架构文档路径>
     2. 任务粒度 = 一个会话内可完成；按依赖排序。
     3. 跨模块写库必须走 api.py，禁止直接 ORM 写（模块防火墙）。 -->
