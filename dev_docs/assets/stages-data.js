const STAGE_COLORS = {
  1: { bg: 'var(--s1)', border: 'var(--s1b)', hex: '#6fba2c' },
  2: { bg: 'var(--s2)', border: 'var(--s2b)', hex: '#11a89b' },
  3: { bg: 'var(--s3)', border: 'var(--s3b)', hex: '#185FA5' },
  4: { bg: 'var(--s4)', border: 'var(--s4b)', hex: '#7c5cbf' },
  5: { bg: 'var(--s5)', border: 'var(--s5b)', hex: '#c7840a' },
  6: { bg: 'var(--s6)', border: 'var(--s6b)', hex: '#e05a5a' },
  x: { bg: 'var(--sx)', border: 'var(--sxb)', hex: '#8a7b66' },
  a: { bg: 'var(--sa)', border: 'var(--sab)', hex: '#4a6cf7' },
  t: { bg: 'var(--st)', border: 'var(--stb)', hex: '#f5a623' },
};

const STAGES = [
  {
    id: 1, hash: 'stage-1', short: '立项', title: '立项验证',
    subtitle: '主目录平铺 · 见 README 索引 · 产品定位 / 灵感 / 人群 / 竞品 / 参考资料',
    agents: ['pm-assistant'], skills: ['feishu-docs'], gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sections: [
      {
        title: '产出文档', dir: '立项验证/',
        empty: null,
        md: [],
        html: [
          { title: '产品定位', path: '立项验证/产品定位.html', desc: '一句话定位 What/For Whom/Why Now · 核心价值主张 · 产品边界 · 差异化分析 · 平台能力全景。', badge: '主文档', emphasis: true },
          { title: '用户人群分析', path: '立项验证/用户人群分析.html', desc: '3 角色画像（测试工程师/QA负责人/产品经理）· 用户旅程 · 痛点与成功标准 · 非目标用户排除。', badge: '主文档', emphasis: true },
          { title: '灵感分析', path: '立项验证/灵感分析.html', desc: 'TestHub 灵感来源 · 4 大痛点链 · 4 项关键假设及验证状态 · 能力迁移矩阵 · 5 条设计原则。', badge: '主文档' },
          { title: '竞品调研与价值评估', path: '立项验证/竞品调研与价值评估.html', desc: '市场定位四象限 · 4 竞品对比 · 13 维功能矩阵 · 效率/差异化价值 · Go/No-Go 决策。', badge: '主文档', emphasis: true },
        ],
      },
      {
        title: '参考资料', dir: '立项验证/',
        empty: null, md: [],
        html: [
          { title: 'PM-Project Stage-Gate 工作流', path: '立项验证/pm-project-workflow.html', desc: '6 阶段 · 3 Gate 全生命周期流程参考。', badge: 'PM' },
          { title: 'PM-Project 架构总览', path: '立项验证/pm-project-architecture.html', desc: '13 Agent + 3 Gate 体系结构图。', badge: 'PM' },
          { title: 'PM-Project Demo Case', path: '立项验证/pm-project-demo.html', desc: '从立项到上线的完整 walkthrough。', badge: 'Demo' },
        ],
      },
    ],
  },
  {
    id: 2, hash: 'stage-2', short: 'PRD', title: 'PRD 需求',
    subtitle: '主目录平铺 · 1 总 PRD + 7 子模块（按模块分栏）+ README · 方法论内嵌本页',
    agents: [], skills: ['requirement-doc'], gate: 'Gate 1 — PRD 评审',
    mdEmpty: null, htmlEmpty: '待 gate-review Agent 产出 Gate 1 评审报告',
    md: [], html: [],
    sectionTone: 's2',
    sections: [
      {
        title: '产品总需求', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '实际需求文档（总 PRD v1.0）', path: '02-PRD需求/实际需求文档.md', desc: '平台定位、用户故事地图、非功能需求与七模块全景。' }],
        html: [],
      },
      {
        title: '元素定位', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-01-element-locator.md', desc: '截图流、Dump、XPath、页面/元素资产库。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-01-element-locator-全功能需求.html', desc: '现网 13 REST + WS 截图流；业务/技术/差距。', badge: '现网' }],
      },
      {
        title: '设备管理', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-02-device-pool.md', desc: '设备池、锁定/释放、排队、局域网 WIFI。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-02-device-pool-全功能需求.html', desc: '现网 13 REST；含局域网连接已交付。', badge: '现网' }],
      },
      {
        title: '用例管理', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-03-case-manager.md', desc: '两级目录、步骤编排、YAML 导出、用例 CRUD。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-03-case-manager-全功能需求.html', desc: '现网 10 REST；步骤类型与 executor 对齐说明。', badge: '现网' }],
      },
      {
        title: '执行引擎', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-04-test-runner.md', desc: '任务调度、状态机、WebSocket 实时进度。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-04-test-runner-全功能需求.html', desc: '现网 12 REST + WS；任务卡/排队/TREP。', badge: '现网' }],
      },
      {
        title: '测试报告', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-05-report-generator.md', desc: '执行记录聚合、在线详情、文件下载。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-05-report-generator-全功能需求.html', desc: '现网 4 REST；列表主源 tr_test_runs。', badge: '现网' }],
      },
      {
        title: 'AI 助手', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-06-ai-assistant.md', desc: '智能体配置、SSE、Tool、HITL、JWT。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-06-ai-assistant-全功能需求.html', desc: '现网 31 REST + SSE；Tool≈24+4。', badge: '现网' }],
      },
      {
        title: '仪表盘', dir: '02-PRD需求/',
        empty: null,
        md: [{ title: '子 PRD Markdown', path: '02-PRD需求/子PRD-07-dashboard.md', desc: '跨模块只读聚合、KPI、趋势、快捷入口。' }],
        html: [{ title: '全功能需求规格', path: '02-PRD需求/html/子PRD-07-dashboard-全功能需求.html', desc: 'F-01～F-05 只读聚合规格。', badge: '现网' }],
      },
      {
        title: '方法论（内嵌 · 无本地文件）', dir: 'index.html',
        empty: null, md: [], html: [],
        inlineHtml: `
<div class="prd-inline">
  <div class="prd-inline-block" id="prd-contradiction">
    <h3>需求矛盾分析方法 <span class="tag">Gate 1 辅助</span></h3>
    <p class="lead">文档迭代后自动执行的一致性校验流程。不落 <code>02-PRD需求/</code> 本地 md，以本页为唯一入口。</p>
    <h4>一、触发条件</h4>
    <table class="wf-table">
      <thead><tr><th>时机</th><th>触发</th></tr></thead>
      <tbody>
        <tr><td>PRD 版本递增后</td><td>✅</td></tr>
        <tr><td>技术代码结构更新后</td><td>✅</td></tr>
        <tr><td>新增/删除/重命名模块后</td><td>✅</td></tr>
        <tr><td>基础架构方案修改后</td><td>✅</td></tr>
        <tr><td>每日工作结束前（兜底）</td><td>✅</td></tr>
      </tbody>
    </table>
    <h4>二、检查维度（8 维）</h4>
    <ul>
      <li><strong>架构一致性</strong>：架构风格、目录结构、通信规则是否与基础方案一致</li>
      <li><strong>模块一致性</strong>：7 个子 PRD 齐全；中英文/编号与代码目录一致；状态标注一致</li>
      <li><strong>技术栈一致性</strong>：总 PRD §5 ↔ 架构方案前端/后端/DB 版本</li>
      <li><strong>版本路线一致性</strong>：里程碑 Phase、功能归属 v2/v3/v4、工作量误差 ≤20%</li>
      <li><strong>数据库一致性</strong>：表前缀/表名/表数量（约 18 ± 2）</li>
      <li><strong>API 一致性</strong>：端点数量与路径前缀 <code>/api/{domain}/*</code></li>
      <li><strong>规则一致性</strong>：Agent 约束、代码 Review 条款互相覆盖</li>
      <li><strong>跨文档引用</strong>：链接目标存在；模块编号 01~07 一致；PRD 版本号不超前</li>
    </ul>
    <h4>三、严重等级</h4>
    <table class="wf-table">
      <thead><tr><th>等级</th><th>定义</th><th>处理</th></tr></thead>
      <tbody>
        <tr><td><span class="prd-sev p0">P0</span></td><td>表名不同 / API 端点差 &gt; 5 / 模块名不同</td><td>立即修复，代码不可继续</td></tr>
        <tr><td><span class="prd-sev p1">P1</span></td><td>功能归属版本不同 / 规则缺失 / 工作量差 &gt; 30%</td><td>当次迭代修复</td></tr>
        <tr><td><span class="prd-sev p2">P2</span></td><td>表数量差 1~2 / 个别路径不一致</td><td>下次迭代修复</td></tr>
        <tr><td><span class="prd-sev p3">P3</span></td><td>措辞差异 / 链接旧路径</td><td>记录，不阻塞</td></tr>
      </tbody>
    </table>
    <h4>四、执行流程</h4>
    <p>前置：变更文档先跑单份 Gate 评审（PRD→Gate 1，架构→Gate 2），再做跨文档扫描，避免「两份都错」的假阴性。</p>
    <ol style="margin:0 0 8px;padding-left:18px;font-size:12px;color:var(--text-secondary);line-height:1.65">
      <li>前置评审 → 确定范围 → 8 维全量扫描 → 分级标注 P0~P3</li>
      <li>输出报告（存 <code>06-发布与复盘/</code>，命名 <code>一致性分析报告-{YYYYMMDD}.md</code>）</li>
      <li>修复：P0/P1 必须修，P2 记录</li>
    </ol>
    <h4>五、报告模板要点</h4>
    <p>标题、触发原因、检查范围、P0~P3 数量汇总、矛盾详情表（矛盾 / 文档A / 文档B / 修复建议）、修复追踪表。</p>
  </div>
  <div class="prd-inline-block" id="prd-excellent-design">
    <h3>优秀设计 <span class="tag">收束约定</span></h3>
    <p class="lead">标杆需求与优秀交互范例的收录约定。不单独建本地文档目录；范例产出后挂到对应阶段索引，并在本栏目补充说明。</p>
    <h4>本栏目应包含</h4>
    <ul>
      <li>优秀 PRD / 功能规格范例（可对标、可复用结构）</li>
      <li>优秀交互与信息架构设计参考（与需求验收相关）</li>
      <li>平台内已验证的「标杆功能」设计说明</li>
    </ul>
    <h4>产出约定</h4>
    <ul>
      <li>正式范例放入对应 Stage 主目录（如设计原型进 <code>03-设计与架构/</code>），命名清晰可检索</li>
      <li>完成后更新本 <code>index.html</code> 对应阶段卡片索引</li>
      <li><strong>禁止</strong>在 <code>02-PRD需求/</code> 再建「优秀设计」子目录或占位 md</li>
    </ul>
  </div>
</div>`,
      },
    ],
  },
  {
    id: 3, hash: 'stage-3', short: '设计', title: '设计与架构',
    subtitle: '先读主文档 → 再看图册/审查 → 模块原型仅示意 · 冲突以现网代码为准',
    agents: ['designer', 'architect'], skills: ['architect-doc', 'prototype-design', 'architecture-review'],
    gate: 'Gate 2 — 架构 + Issues 就绪门',
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 's3',
    toc: [
      { label: '怎么读', target: 'arch-how' },
      { label: '总设计', target: 'arch-core' },
      { label: '技术栈', target: 'arch-stack' },
      { label: '按模块', target: 'arch-modules' },
    ],
    guideHtml: `
<div class="arch-guide" id="arch-how">
  <p class="lead">文件很多，但日常只需认清角色——不要平行读 9 份「总架构」。</p>
  <ol>
    <li><strong>主文档</strong>：<code>当前实现架构方案.md</code>（基于代码的真相）</li>
    <li><strong>角色裁决</strong>：打开「同主题对比」，看主 / 参考 / 原型 / 已删</li>
    <li><strong>图册与审查</strong>：需要图或历史结论时再点；不与主文档抢真相</li>
    <li><strong>模块区</strong>：多数是低保真原型；执行引擎 / 测试报告另有「主」审查或 UI</li>
  </ol>
  <div class="arch-quick">
    <a class="primary" href="03-设计与架构/当前实现架构方案.md"><span class="q-tag">主</span>当前实现架构方案</a>
    <a href="03-设计与架构/html/对比-同主题文档差异.html"><span class="q-tag">对比</span>同主题文档差异</a>
    <a href="03-设计与架构/README.md"><span class="q-tag">索引</span>目录 README</a>
  </div>
</div>`,
    sections: [
      {
        id: 'arch-core',
        title: '总设计', dir: '03-设计与架构/',
        empty: null, md: [], html: [],
        hint: '同一主题拆成三层：主真相 → 参考/快照 → 图册。冲突以主文档 + 现网代码为准。',
        subsections: [
          {
            title: '主真相', dir: '03-设计与架构/',
            md: [{ title: '当前实现架构方案', path: '03-设计与架构/当前实现架构方案.md', desc: '通道 · 分层 · 模式 · 技术栈。Agent / 日常查阅优先读这份。', badge: '主文档', emphasis: true }],
            html: [],
          },
          {
            title: '参考 · 快照 · 指标', dir: '03-设计与架构/html/',
            md: [],
            html: [
              { title: '模块化架构设计方案', path: '03-设计与架构/html/总设计-模块化架构设计方案.html', desc: '理想架构 + 差距 + 路线图。', badge: '参考' },
              { title: '模块化架构分析报告', path: '03-设计与架构/html/总设计-模块化架构分析报告_20260709.html', desc: '耦合与防火墙快照（2026-07-09）。', badge: '快照' },
              { title: '架构审查报告（历史）', path: '03-设计与架构/html/总设计-架构审查报告_20260705.html', desc: '与设计方案同族的历史基线。', badge: '快照' },
              { title: '模块代码复杂度', path: '03-设计与架构/html/总设计-模块代码复杂度分析报告_20260709.html', desc: '行数与圈复杂度指标。', badge: '指标' },
            ],
          },
          {
            title: '图册 · 对标', dir: '03-设计与架构/html/',
            layout: 'grid',
            md: [],
            html: [
              { title: '系统架构图', path: '03-设计与架构/html/总设计-system-architecture.html', desc: '五层一页图。', badge: '图册' },
              { title: '数据模型图', path: '03-设计与架构/html/总设计-data-model.html', desc: '表 ER。', badge: '图册' },
              { title: '前端模块边界图', path: '03-设计与架构/html/结构-frontend-architecture.html', desc: '7 模块目录。', badge: '图册' },
              { title: 'TestHub 对标', path: '03-设计与架构/html/总设计-testhub-architecture.html', desc: '参考架构，非现网。', badge: '对标' },
            ],
          },
        ],
      },
      {
        id: 'arch-stack',
        title: '技术栈 · 工具', dir: '03-设计与架构/',
        empty: null,
        hint: '命名、动森素材、报告提示词、前后端契约——写代码 / 出 HTML 报告时用。',
        md: [
          { title: '技术栈说明', path: '03-设计与架构/技术栈-README.md', desc: '技术选型与素材约定。' },
          { title: '命名统一标准', path: '03-设计与架构/技术栈-命名统一标准.md', desc: '前后端 / API / DB 命名。' },
          { title: 'animal-island-ui 设计素材', path: '03-设计与架构/技术栈-animal-island-ui设计素材.md', desc: '动森 design token。' },
          { title: 'animal-island-ui 一键提示词', path: '03-设计与架构/技术栈-PROMPT-animal-island-ui一键提示词.md', desc: 'HTML 报告生成提示词。' },
          { title: 'VUE API CONTRACT', path: '03-设计与架构/工具-VUE_API_CONTRACT.md', desc: '前后端接口契约。' },
        ],
        html: [],
      },
      {
        id: 'arch-modules',
        title: '按模块（设计 / 审查 / 原型）', dir: '03-设计与架构/',
        empty: null, md: [], html: [],
        hint: '带「主」的是该模块优先文档；标「原型」的只是早期 UI 示意，不代表现网。',
        subsections: [
          {
            title: '执行引擎', dir: '03-设计与架构/html/',
            md: [],
            html: [
              { title: '设备执行控制管线审查', path: '03-设计与架构/html/模块-执行引擎-架构审查报告_设备执行控制管线_20260705.html', desc: '三层管线 · 本模块主审查。', badge: '主', emphasis: true },
              { title: '测试执行流程', path: '03-设计与架构/html/模块-执行引擎-execution-flow.html', desc: '步骤时序与 WS。', badge: '流程图' },
              { title: '低保真原型', path: '03-设计与架构/html/模块-执行引擎-runner.html', desc: '早期 UI 示意。', badge: '原型' },
            ],
          },
          {
            title: '测试报告', dir: '03-设计与架构/html/',
            md: [],
            html: [
              { title: 'Report Redesign', path: '03-设计与架构/html/模块-测试报告-report-generator-redesign.html', desc: '列表→详情重设计 · 本模块主 UI。', badge: '主', emphasis: true },
              { title: '早期原型', path: '03-设计与架构/html/模块-测试报告-reports.html', desc: '低保真对照。', badge: '原型' },
            ],
          },
          {
            title: 'AI 助手', dir: '03-设计与架构/',
            md: [{ title: '技术架构与功能设计', path: '03-设计与架构/模块-AI助手-技术架构与功能设计.md', desc: '页面 / API / 能力边界。', badge: '主', emphasis: true }],
            html: [],
          },
          {
            title: '元素定位', dir: '03-设计与架构/',
            md: [{ title: '元素管理页 UI 改动总结', path: '03-设计与架构/模块-元素定位-元素管理页UI改动总结.md', desc: '元素管理页设计迭代。' }],
            html: [{ title: '低保真原型', path: '03-设计与架构/html/模块-元素定位-elements.html', desc: '早期 UI 示意。', badge: '原型' }],
          },
          {
            title: '其它原型（设备 / 用例 / 仪表盘 / 登录）', dir: '03-设计与架构/html/',
            layout: 'grid',
            md: [],
            html: [
              { title: '设备管理', path: '03-设计与架构/html/模块-设备管理-devices.html', desc: '早期 UI 示意。', badge: '原型' },
              { title: '用例管理', path: '03-设计与架构/html/模块-用例管理-cases.html', desc: '早期 UI 示意。', badge: '原型' },
              { title: '仪表盘', path: '03-设计与架构/html/模块-仪表盘-dashboard.html', desc: '早期 UI 示意。', badge: '原型' },
              { title: '登录页', path: '03-设计与架构/html/模块-登录认证-login.html', desc: '早期 UI 示意。', badge: '原型' },
              { title: '产品原型导航', path: '03-设计与架构/html/结构-产品原型导航页.html', desc: '低保真入口索引。', badge: '导航' },
            ],
          },
        ],
      },
    ],
  },
  {
    id: 4, hash: 'stage-4', short: '拆分', title: '任务拆分',
    subtitle: '主目录平铺 · 角色前缀：市场调研- / 产品设计- / 架构师- / 全栈开发- / 测试-',
    agents: [], skills: ['requirement-to-issues'], gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 's4',
    sections: [
      {
        title: '市场调研', dir: '04-任务拆分/',
        empty: null,
        md: [
          { title: '角色设定', path: '04-任务拆分/市场调研-角色设定.md', desc: 'AI 可直接使用的 system prompt：项目约束 · 竞品基线 · 职责边界 · 管理文件 · 工作流程 · 输出模板。', badge: 'AI Prompt', emphasis: true },
          { title: '负责事项与任务清单', path: '04-任务拆分/市场调研-详细任务计划.md', desc: '文档资产清单 · 竞品跟踪频率 · 用户验证任务 · 只读参考范围 · Memory 沉淀。', badge: '清单' },
          { title: '验收评审结果', path: '04-任务拆分/市场调研-验收评审结果.md', desc: '调研结论评审（待填）。' },
        ],
        html: [],
      },
      {
        title: '产品设计', dir: '04-任务拆分/',
        empty: null,
        md: [
          { title: '角色设定', path: '04-任务拆分/产品设计-角色设定.md', desc: 'AI 可直接使用的 system prompt：PRD 结构 · 8 维矛盾分析 · 全功能 HTML 规格 · Gate 1 材料。', badge: 'AI Prompt', emphasis: true },
          { title: '负责事项与任务清单', path: '04-任务拆分/产品设计-详细任务计划.md', desc: '总 PRD + 7 子模块 + 7 HTML 规格 · 代码对齐检查项 · 8 维矛盾分析 · 关联规则索引。', badge: '清单' },
          { title: '验收评审结果', path: '04-任务拆分/产品设计-验收评审结果.md', desc: 'Gate 1 评审（待填）。' },
          { title: 'AI 任务卡片实施方案', path: '04-任务拆分/产品设计-AI任务卡片实施方案.md', desc: '任务卡片产品实施方案（自 PRD 迁入）。' },
        ],
        html: [],
      },
      {
        title: '架构师', dir: '04-任务拆分/',
        empty: null,
        md: [
          { title: '角色设定', path: '04-任务拆分/架构师-角色设定.md', desc: 'AI 可直接使用的 system prompt：五层架构 · 三道防火墙 · 架构审查清单 · ADR · Gate 2 材料。', badge: 'AI Prompt', emphasis: true },
          { title: '负责事项与任务清单', path: '04-任务拆分/架构师-详细任务计划.md', desc: '设计文档清单 · 7 App + 7 前端模块审查矩阵 · AgentScope Tool 审查 · 行数自检命令。', badge: '清单' },
          { title: '验收评审结果', path: '04-任务拆分/架构师-验收评审结果.md', desc: 'Gate 2 评审（待填）。' },
        ],
        html: [
          { title: '执行引擎架构重构方案', path: '04-任务拆分/架构师-详细任务计划-执行引擎架构重构方案.html', desc: 'Issue 级改造路径。', badge: '方案' },
          { title: 'TREP v1.0 协议', path: '04-任务拆分/架构师-详细任务计划-TREP-v1.0-protocol.html', desc: '执行引擎拆分契约。', badge: '协议' },
        ],
      },
      {
        title: '全栈开发', dir: '04-任务拆分/',
        empty: null,
        md: [
          { title: '角色设定', path: '04-任务拆分/全栈开发-角色设定.md', desc: 'AI 可直接使用的 system prompt：全栈铁律 · 组件陷阱 · auto-dev 五阶段 · 管理文件清单 · 安全红线。', badge: 'AI Prompt', emphasis: true },
          { title: '负责事项与任务清单', path: '04-任务拆分/全栈开发-详细任务计划.md', desc: '7 App × 7 前端模块全部文件清单 · AgentScope 10 文件 · 共享层 · 4 文件注册清单。', badge: '清单' },
          { title: '验收评审结果', path: '04-任务拆分/全栈开发-验收评审结果.md', desc: 'PR/功能批次评审（待填）。' },
        ],
        html: [
          { title: 'AI助手解决方案', path: '04-任务拆分/全栈开发-AI助手解决方案.html', desc: '联调功能-AI助手模块问题记录 · AI助手模块化重构方案 的综合解决方案：问题核实 · 安全热修 · 分阶段重构。', badge: '方案', emphasis: true },
        ],
      },
      {
        title: '测试', dir: '04-任务拆分/',
        empty: null,
        md: [
          { title: '角色设定', path: '04-任务拆分/测试-角色设定.md', desc: 'AI 可直接使用的 system prompt：五层测试 · 环境降级 · UI 截图 · Gate 3 质量输入 · 测试方案模板。', badge: 'AI Prompt', emphasis: true },
          { title: '负责事项与任务清单', path: '04-任务拆分/测试-详细任务计划.md', desc: '7 模块 × 5 层测试覆盖矩阵 · 安全清单 · 回归范围 · 环境降级表 · 端点状态码矩阵。', badge: '清单' },
          { title: '验收评审结果', path: '04-任务拆分/测试-验收评审结果.md', desc: 'Gate 3 质量输入（待填）。' },
        ],
        html: [],
      },
      {
        title: '管理员（签发留空）', dir: '04-任务拆分/',
        empty: null,
        md: [{ title: '管理员说明', path: '04-任务拆分/管理员-说明.md', desc: 'AI 可直接使用的 system prompt：Gate 签发清单 · 流程管理 · Memory 管理规范 · 争议裁决 · 四本手册。', badge: 'AI Prompt', emphasis: true }],
        html: [],
      },
      {
        title: '问题管理', dir: '04-任务拆分/',
        empty: null, md: [], html: [],
        subsections: [
          { title: '前端', dir: '04-任务拆分/问题管理/', empty: null, md: [
            { title: '报告页滚动失效', path: '04-任务拆分/问题管理/前端-报告页滚动失效.md', desc: 'App.vue :deep(> *) 选择器过宽 + doc-body min-height:0 → 内容截断不可滚动。', badge: '已修复' },
            { title: 'Tabs 内容区无法滚动', path: '04-任务拆分/问题管理/前端-Tabs内容区无法滚动.md', desc: '【常见问题】doc-body min-height:0 + animal-tabs flex 链锁死高度 → BUG 汇总/失败明细超出视口不可滚动。', badge: '常见问题', emphasis: true },
            { title: '表格右侧留白', path: '04-任务拆分/问题管理/前端-表格列宽固定导致右侧留白.md', desc: '报告/元素管理/用例管理三页面：列宽固定像素 vs 容器窄 → 表格未撑满，右侧留白。统一改百分比。', badge: '已修复' },
            { title: '报告图表横向滚动失效', path: '04-任务拆分/问题管理/前端-报告图表横向滚动失效.md', desc: '一月/一季趋势图：Chart.js responsive 缩回视口 + Grid min-width:auto 撑破卡片 → 无法固定显示5天并滑动浏览。', badge: '已修复' },
          ], html: [] },
          { title: '后端', dir: '04-任务拆分/问题管理/', empty: '暂无后端问题记录', md: [], html: [] },
          { title: '数据库', dir: '04-任务拆分/问题管理/', empty: '暂无数据库问题记录', md: [], html: [] },
          { title: '联调功能', dir: '04-任务拆分/问题管理/', empty: null, md: [
            { title: '执行引擎模块问题记录', path: '04-任务拆分/问题管理/联调功能-执行引擎模块问题记录.md', desc: '26 项风险与设计缺陷（6 竞态 + 4 泄漏 + 5 数据完整性 + 10 设计），2026-07-13 已全部修复。', badge: '已修复' },
            { title: 'AI助手模块问题记录', path: '04-任务拆分/问题管理/联调功能-AI助手模块问题记录.md', desc: '43 项风险与设计缺陷（7 CRITICAL + 9 HIGH + 14 MEDIUM + 13 设计），2026-07-13 代码审查。', badge: '43 项', emphasis: true },
            { title: 'AI助手模块化重构方案', path: '04-任务拆分/问题管理/联调功能-AI助手模块化重构方案.md', desc: '三层解耦：Django views 6→子模块 + ChatView 2800行→1+8+4 + Tool工厂按agent注入 + 公共代码去重。', badge: '方案' },
          ], html: [] },
        ],
      },
    ],
  },
  {
    id: 5, hash: 'stage-5', short: '开发', title: '开发与测试',
    subtitle: '按平台模块子目录 · 每模块：编程工作流 / 代码质量分析 / 质量与验收手册（测试方案暂缓）',
    agents: ['tdd-developer', 'code-testing', 'code-review'], skills: ['tdd-coder'],
    gate: 'Gate 3 — 上线评审',
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 's5',
    sections: [
      {
        title: '仪表盘', dir: '05-开发与测试/仪表盘/',
        empty: null, md: [],
        html: [
          { title: '编程工作流', path: '05-开发与测试/仪表盘/编程工作流.html', desc: '需求分析 → 改动评估 → 编码 → Review。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/仪表盘/代码质量分析.html', desc: '模块化设计与规范诊断（现网重扫）。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/仪表盘/质量与验收手册.html', desc: 'Review · 分析流程 · 报错诊断 · 功能验收。', badge: '手册' },
          { title: '测试报告', path: '05-开发与测试/仪表盘/测试报告.html', desc: '功能测试报告（已跑过）。', badge: '测试' },
        ],
      },
      {
        title: '设备管理', dir: '05-开发与测试/设备管理/',
        empty: null,
        md: [{ title: '测试方案（既有）', path: '05-开发与测试/设备管理/测试方案-02-device-pool.md', desc: 'HTML 测试方案暂缓。' }],
        html: [
          { title: '编程工作流', path: '05-开发与测试/设备管理/编程工作流.html', desc: '设备池改动全链路。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/设备管理/代码质量分析.html', desc: '现网结构盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/设备管理/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
        ],
      },
      {
        title: '元素定位', dir: '05-开发与测试/元素定位/',
        empty: null,
        md: [
          { title: '截图流故障手册', path: '05-开发与测试/元素定位/截图流故障手册.md', desc: 'WS 截图流排查。' },
          { title: '测试方案（既有）', path: '05-开发与测试/元素定位/测试方案-03-element-locator.md', desc: 'HTML 测试方案暂缓。' },
        ],
        html: [
          { title: '编程工作流', path: '05-开发与测试/元素定位/编程工作流.html', desc: 'Dump / XPath / 截图流。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/元素定位/代码质量分析.html', desc: '现网结构盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/元素定位/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
        ],
      },
      {
        title: '用例管理', dir: '05-开发与测试/用例管理/',
        empty: null,
        md: [{ title: '测试方案（既有）', path: '05-开发与测试/用例管理/测试方案-04-case-manager.md', desc: 'HTML 测试方案暂缓。' }],
        html: [
          { title: '编程工作流', path: '05-开发与测试/用例管理/编程工作流.html', desc: '14 种步骤编排。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/用例管理/代码质量分析.html', desc: '现网结构盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/用例管理/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
        ],
      },
      {
        title: '执行引擎', dir: '05-开发与测试/执行引擎/',
        empty: null,
        md: [{ title: '测试方案（既有）', path: '05-开发与测试/执行引擎/测试方案-05-test-runner.md', desc: 'HTML 测试方案暂缓。' }],
        html: [
          { title: '编程工作流', path: '05-开发与测试/执行引擎/编程工作流.html', desc: '状态机 / WS / 调度。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/执行引擎/代码质量分析.html', desc: '高复杂度现网盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/执行引擎/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
          { title: '全链路诊断（既有）', path: '05-开发与测试/执行引擎/test-runner-diagnosis-report.html', desc: '历史诊断报告。', badge: '诊断' },
          { title: '全面理解（既有）', path: '05-开发与测试/执行引擎/test-runner-comprehensive-understanding.html', desc: '历史理解报告。', badge: '理解' },
        ],
      },
      {
        title: '测试报告模块', dir: '05-开发与测试/测试报告/',
        empty: null,
        md: [{ title: '测试方案（既有）', path: '05-开发与测试/测试报告/测试方案-06-report-generator.md', desc: 'HTML 测试方案暂缓。' }],
        html: [
          { title: '编程工作流', path: '05-开发与测试/测试报告/编程工作流.html', desc: '报告生成与导出。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/测试报告/代码质量分析.html', desc: '现网结构盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/测试报告/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
        ],
      },
      {
        title: 'AI 助手', dir: '05-开发与测试/AI助手/',
        empty: null,
        md: [{ title: '测试方案（既有）', path: '05-开发与测试/AI助手/测试方案-07-ai-assistant.md', desc: 'HTML 测试方案暂缓。' }],
        html: [
          { title: '编程工作流', path: '05-开发与测试/AI助手/编程工作流.html', desc: '智能体 / SSE / Tool。', badge: '工作流' },
          { title: '代码质量分析', path: '05-开发与测试/AI助手/代码质量分析.html', desc: '现网结构盘点。', badge: '质量' },
          { title: '质量与验收手册', path: '05-开发与测试/AI助手/质量与验收手册.html', desc: 'Review · 诊断 · AC。', badge: '手册' },
        ],
      },
      {
        title: '平台级横切', dir: '05-开发与测试/平台级/',
        empty: null,
        md: [
          { title: '代码 Review 规则', path: '05-开发与测试/平台级/代码Review规则.md', desc: '审查标准与分级。' },
          { title: 'BUGS 追踪', path: '05-开发与测试/平台级/BUGS.md', desc: '已知 Bug 与修复状态。' },
          { title: '报错诊断手册', path: '05-开发与测试/平台级/报错诊断手册.md', desc: '常见错误速查。' },
          { title: '环境配置教程', path: '05-开发与测试/平台级/环境配置教程.md', desc: '环境搭建指南。' },
          { title: '平台测试方案', path: '05-开发与测试/平台级/平台测试方案.md', desc: '全平台分层测试规划。' },
          { title: 'E2E', path: '05-开发与测试/平台级/08-e2e.md', desc: '端到端用例。' },
          { title: '平台认证方案', path: '05-开发与测试/平台级/平台认证-01-platform-auth.md', desc: 'JWT / 鉴权。' },
        ],
        html: [],
      },
    ],
  },
  {
    id: 6, hash: 'stage-6', short: '复盘', title: '发布与复盘',
    subtitle: '主目录平铺 · 上线 / 质量 / 闭环 / 工程 / 流程 / 行动项',
    agents: ['pr-review-submit', 'post-launch-review', 'pm-workflow-evaluator'],
    skills: ['github-publish'], gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 's6',
    sections: [
      {
        title: '上线与行动', dir: '06-发布与复盘/',
        empty: null,
        md: [
          { title: '上线与发布记录', path: '06-发布与复盘/上线与发布记录.md', desc: 'Gate 3 / Release / PR 摘要。' },
          { title: '行动项与下轮迭代', path: '06-发布与复盘/行动项与下轮迭代.md', desc: '可执行改进项。' },
          { title: '治理横切说明（已归档）', path: '06-发布与复盘/治理横切说明-已归档.md', desc: '归档说明。' },
        ],
        html: [],
      },
      {
        title: '质量 · 闭环 · 工程 · 流程', dir: '06-发布与复盘/',
        empty: null,
        md: [{ title: 'Harness + Loop Engineering', path: '06-发布与复盘/Harness_Loop_Engineering_方案.md', desc: 'AI 工程化改进总方案。' }],
        html: [
          { title: '平台质量全面评估', path: '06-发布与复盘/平台质量全面评估报告_20260709.html', desc: '十维度 · B- 74/100。', badge: 'B-', grade: 'g-bm' },
          { title: 'AI 开发闭环符合度', path: '06-发布与复盘/AI开发闭环符合度评估报告_20260709.html', desc: '闭环符合度 C+ 66/100。', badge: 'C+', grade: 'g-c' },
          { title: 'Agent 工作流全景', path: '06-发布与复盘/Agent工作流全景报告.html', desc: 'Agent/Skill 与 auto-dev。', badge: '全景' },
          { title: '项目文件体系评估', path: '06-发布与复盘/项目文件体系评估报告_20260709.html', desc: '文档 B+，工程化 C。', badge: 'B+', grade: 'g-bp' },
          { title: 'PM-Project → .agents 移植', path: '06-发布与复盘/PM-Project移植到agents目录方案_20260709.html', desc: '移植方案（已确认）。', badge: '已确认', grade: 'g-ok', extra: 'b-ok' },
          { title: '文档分类方案', path: '06-发布与复盘/文档分类方案_Stage-Gate_20260710.html', desc: 'Stage-Gate 分类依据。', badge: '分类' },
        ],
      },
    ],
  },
  {
    id: 'x', hash: 'stage-x', short: '管理员', title: '管理员',
    subtitle: '主目录平铺 · 四本手册：智能体 · 项目 · 代码 · 验收 AI 输出',
    agents: [], skills: [], gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 'sx',
    sections: [
      {
        title: '目录索引', dir: '00-管理员/',
        empty: null,
        md: [{ title: 'README 索引', path: '00-管理员/README.md', desc: '四本手册平铺清单。' }],
        html: [],
      },
      {
        title: '四本手册', dir: '00-管理员/',
        empty: null,
        md: [
          { title: '管理智能体手册', path: '00-管理员/管理智能体-手册.md', desc: '灵感 → 设计 → 实践 → 总结 → 成果模型。' },
          { title: '管理项目手册', path: '00-管理员/管理项目-手册.md', desc: 'Stage-Gate 项目管理方法论。' },
          { title: '管理代码手册', path: '00-管理员/管理代码-手册.md', desc: '审查、边界与验收证据。' },
          { title: '验收 AI 输出手册', path: '00-管理员/验收AI输出-手册.md', desc: '验收流程、否决权与验收包。' },
        ],
        html: [],
      },
    ],
  },
  {
    id: 'a', hash: 'stage-a', short: '智能体', title: '智能体',
    subtitle: '我的实际工作方式 · 能力与工具 · Rules/Memory 体系 · 平台管理方案 · 源文件只读',
    agents: [], skills: [], gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 'sa',
    sections: [
      {
        title: '体系设计图册（主入口）', dir: '00-智能体/',
        empty: null,
        hint: '视觉与结构对齐 agent-workflow-report：多图画清双体系、路由、Auto-Dev 7 阶段、三档强度、SOP。',
        md: [{ title: '栏目 README', path: '00-智能体/README.md', desc: '本栏文档与只读目录索引。' }],
        html: [{ title: '智能体体系设计', path: '00-智能体/智能体体系设计.html', desc: '双体系 · 六角色泳道 · Auto-Dev 7 阶段流水线 · 三档强度 · 反馈下钻 · Stage-Gate · AgentScope SOP。', badge: '主', emphasis: true }],
      },
      {
        title: '一句话：我怎么干活', dir: '../CLAUDE.md',
        empty: null, md: [], html: [],
        inlineHtml: `
<div class="wf-hero">
  <h2>我是这个平台的产品负责人 + 全栈开发者 + 测试工程师</h2>
  <p>不是一个只写代码的 AI——我负责从需求理解到交付验证的<strong>完整生命周期</strong>。收到任务后先探索代码理解现状，用 <strong>Plan Mode</strong> 出方案等你审批，批准后全栈实现（前端 Vue → API Django → DB → 设备层），最后<strong>打开浏览器验证</strong>。所有规则（15 份 .claude/rules/）和教训沉淀（memory/）在每次执行中强制生效。</p>
  <p>核心配置文件在仓库根 <code>.claude/</code>，只读、不复制到文档目录。</p>
</div>
<div class="wf-steps">
  <div class="wf-step"><div class="num">1</div><div><h3>理解任务</h3><p>你提需求——「加个停止按钮」「写仪表盘 PRD」「测设备锁定」。我先 grep/Read 探索代码，搞清影响面和现状，不是猜。</p></div></div>
  <div class="wf-step"><div class="num">2</div><div><h3>Plan Mode 方案</h3><p>非简单任务自动进入 Plan Mode：探索代码 → 设计方案 → 写 plan 文件 → 等你审批。审批通过才开始写代码。</p></div></div>
  <div class="wf-step"><div class="num">3</div><div><h3>全栈执行</h3><p>改 Vue/Django/Python/JS，并行启动子 agent 做搜索、审查、测试。编译过才继续，失败自动修复（最多 3 次）。</p></div></div>
  <div class="wf-step"><div class="num">4</div><div><h3>浏览器验证</h3><p>不只是 curl API——打开 Playwright 浏览器看页面实际渲染，确认 UI、API、DB 三层数据一致。禁止「curl 通了就当修好了」。</p></div></div>
  <div class="wf-step"><div class="num">5</div><div><h3>沉淀教训</h3><p>每次发现新模式、踩坑、用户纠正 → 写 memory 到 <code>.claude/memory/</code>，更新索引。同类错误不犯第二次。</p></div></div>
</div>`,
      },
      {
        title: '我的能力与工具箱', dir: '../.claude/',
        empty: null, md: [], html: [],
        inlineHtml: `
<div class="wf-ideas">
  <div class="wf-idea">
    <h3>🛠 直接工具（我每次都能用）</h3>
    <ul>
      <li><strong>Bash</strong>：运行命令、启动服务、git 操作、编译检查</li>
      <li><strong>Read / Write / Edit</strong>：读代码、写文件、精确替换</li>
      <li><strong>Grep / Glob / LSP</strong>：全文搜索、文件匹配、代码智能跳转</li>
      <li><strong>Playwright MCP</strong>：打开浏览器看页面、截图、点按钮、填表单</li>
      <li><strong>filesystem MCP</strong>：目录浏览、文件信息、批量读取</li>
      <li><strong>github MCP</strong>：Issue/PR/分支/review/文件管理</li>
    </ul>
  </div>
  <div class="wf-idea">
    <h3>🧩 子 Agent（并行干活用）</h3>
    <p>这些是<strong>我的工具</strong>，不是独立角色。我根据任务需要 spawn 它们并行跑，结果汇总到我这里：</p>
    <table class="wf-table" style="margin-top:8px">
      <thead><tr><th>子 Agent</th><th>我什么时候用</th></tr></thead>
      <tbody>
        <tr><td><code>Explore</code></td><td>需要并行搜索多个目录/模式时，派它去做只读探索</td></tr>
        <tr><td><code>Plan</code></td><td>复杂实现前，派它设计实施方案供我审查</td></tr>
        <tr><td><code>developer</code></td><td>大改动时派它走 auto-dev 全流程（探索→方案→编码→审查→测试）</td></tr>
        <tr><td><code>reviewer</code></td><td>交付前派它做多维度审查（P0-P3 分级）</td></tr>
        <tr><td><code>tester</code></td><td>验收时派它环境探测→分层测试→出报告</td></tr>
        <tr><td><code>test-automator</code></td><td>需要把用例写成自动化脚本时派它</td></tr>
        <tr><td><code>prd-writer</code></td><td>写/改需求文档时派它，确保 PRD 是唯一真相来源</td></tr>
        <tr><td><code>architect</code></td><td>跨模块架构分析、状态机设计、协议定义时派它</td></tr>
      </tbody>
    </table>
  </div>
</div>
<div class="wf-ideas" style="margin-top:16px">
  <div class="wf-idea">
    <h3>📋 Skill = 我触发的专项工作流</h3>
    <p>按步骤做完一个完整流程，不是百科条目。比如：</p>
    <ul>
      <li><code>auto-dev</code>：Phase -1→0→1→2→3→4→5 全流程开发编排</li>
      <li><code>prd-writer</code> / <code>architecture-review</code> / <code>module-design</code></li>
      <li><code>quality-gate</code> / <code>code-health-check</code> / <code>functional-testing</code></li>
      <li><code>html-report</code> / <code>github-manager</code> / <code>feature-analysis</code></li>
      <li><code>code-review</code> / <code>simplify</code> / <code>verify</code> / <code>security-review</code></li>
    </ul>
    <p style="margin-top:8px;font-size:11px;color:var(--text-muted)">还有 <code>deep-research</code>（深度研究）、<code>dataviz</code>（数据可视化）、<code>loop</code>（定时循环）、<code>run</code>（启动验证）等内置 skill。</p>
  </div>
  <div class="wf-idea">
    <h3>📐 Plan Mode + Worktree</h3>
    <p><strong>Plan Mode</strong>：非简单任务自动进入——探索代码 → 写 plan 文件 → 等你审批。审批通过前<strong>一行代码不改</strong>。</p>
    <p style="margin-top:8px"><strong>Worktree 隔离</strong>：并行改多个文件互不冲突——每个子 agent 在独立 git worktree 中工作，改完自动合并。</p>
    <p style="margin-top:8px"><strong>Memory 系统</strong>：跨会话持久化——你的偏好、项目约定、排障教训都存在 <code>.claude/memory/</code>，每次对话自动加载。同类错误不会犯两次。</p>
  </div>
</div>`,
      },
      {
        title: 'Rules / Memory 怎么约束我', dir: '../.claude/',
        empty: null, md: [], html: [],
        inlineHtml: `
<table class="wf-table">
  <thead><tr><th>层级</th><th>位置</th><th>作用</th><th>示例</th></tr></thead>
  <tbody>
    <tr><td><strong>身份 + 铁律</strong></td><td><code>CLAUDE.md</code></td><td>定义我是谁、必须遵守什么</td><td>产品负责人+全栈+测试；PRD先行、编译必过、浏览器验证</td></tr>
    <tr><td><strong>项目事实</strong></td><td><code>AGENTS.md</code> + rules/</td><td>架构、API、DB、模块边界——写代码的依据</td><td>20 张表、50 REST + 2 WS、三道防火墙</td></tr>
    <tr><td><strong>专项规则</strong></td><td><code>.claude/rules/*.md</code>（15 份）</td><td>每份覆盖一个领域：前端/后端/安全/设备/AI引擎/数据库等</td><td>前端禁止硬编码数据、写操作 catch 必须报错、API Key 脱敏</td></tr>
    <tr><td><strong>子 Agent 定义</strong></td><td><code>.claude/agents/*.md</code>（8 个）</td><td>每个子 agent 的 system prompt 和工具权限</td><td>developer 走 auto-dev，reviewer 按 P0-P3 分级</td></tr>
    <tr><td><strong>Skill 流程</strong></td><td><code>.claude/skills/*/SKILL.md</code></td><td>专项工作流的步骤定义</td><td>auto-dev 五阶段、quality-gate 四齿轮</td></tr>
    <tr><td><strong>Memory</strong></td><td><code>.claude/memory/</code>（15 条）</td><td>跨会话持久化教训与偏好</td><td>animal-island-ui API 陷阱、CSS 调试三步法、UI 测试失败必须截图</td></tr>
  </tbody>
</table>
<p class="wf-note" style="margin-top:12px">这些不是"建议"——<strong>是硬约束</strong>。Rules 在每次会话中自动加载，不靠我"记得"。如果我违反了某条 rule，说明那条 rule 没写清楚或加载时机不对，需要修正 rule 本身。</p>
<div class="wf-ideas" style="margin-top:16px">
  <div class="wf-idea">
    <h3>🔴 跟平台内 AI 助手的区别</h3>
    <ul>
      <li><strong>我（Claude Code Agent）</strong>：帮你<strong>做产品</strong>——写 PRD、改代码、测平台、管文档。跑在 Claude Code CLI，操作的是<strong>代码仓库</strong></li>
      <li><strong>平台 AI 助手（AgentScope Agent）</strong>：帮测试同学<strong>用平台</strong>——对话搜元素、写用例、跑任务。跑在 AgentScope :8000，操作的是<strong>业务数据库</strong></li>
      <li>两者都叫"智能体"，但入口、Tool、SOP 完全不同。我是建造者，它是建造出来的产物。</li>
    </ul>
  </div>
  <div class="wf-idea">
    <h3>🔄 我覆盖所有 Stage-Gate 阶段</h3>
    <p>不局限某一个阶段——从立项到复盘我都在：</p>
    <ul>
      <li><strong>立项</strong>：调研扩写、竞品对比</li>
      <li><strong>PRD</strong>：写子 PRD、全功能 HTML、矛盾分析</li>
      <li><strong>设计</strong>：架构审查、模块化设计、协议定义</li>
      <li><strong>开发</strong>：全栈编码、编译验证、浏览器验证</li>
      <li><strong>测试</strong>：分层测试、功能验收、自动化脚本</li>
      <li><strong>复盘</strong>：质量评估、闭环符合度、行动项</li>
    </ul>
    <p style="margin-top:8px;font-size:11px;color:var(--text-muted)">Gate 签发权在人——我准备材料，人做 Go/No-Go 决策。</p>
  </div>
</div>`,
      },
      {
        title: '平台管理：我怎么管这个项目', dir: '../.claude/',
        empty: null, md: [], html: [],
        inlineHtml: `
<div class="wf-ideas">
  <div class="wf-idea" style="grid-column:1/-1">
    <h3>🔍 全栈验证铁律（每次修改后强制执行）</h3>
    <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;padding:12px 0;font-size:13px;font-family:monospace;color:var(--text-body)">
      <span style="background:var(--primary-bg);padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--primary)">改代码</span>
      <span style="color:var(--primary);font-weight:900">→</span>
      <span style="background:#edf7e7;padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--success)">编译通过</span>
      <span style="color:var(--primary);font-weight:900">→</span>
      <span style="background:#fef9e7;padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--claude)">重启服务</span>
      <span style="color:var(--primary);font-weight:900">→</span>
      <span style="background:#eef1fb;padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--device)">浏览器看 UI</span>
      <span style="color:var(--primary);font-weight:900">→</span>
      <span style="background:#f3eefb;padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--tool-purple)">API 数据正确</span>
      <span style="color:var(--primary);font-weight:900">→</span>
      <span style="background:#fef0f3;padding:6px 12px;border-radius:var(--r-sm);border:1.5px solid var(--agentscope)">DB 数据一致</span>
    </div>
  </div>
</div>
<div class="wf-ideas">
  <div class="wf-idea">
    <h3>🛡 三道防火墙（跨模块写操作硬约束）</h3>
    <div style="font-size:12px;line-height:1.8">
      <div style="padding:8px 12px;background:rgba(25,200,185,.06);border-radius:var(--r-sm);margin-bottom:6px;border-left:3px solid var(--primary)"><strong>#1</strong> service.py 互不 import · 跨 App 只调 Model（读）和 api.py（写）</div>
      <div style="padding:8px 12px;background:rgba(111,186,44,.06);border-radius:var(--r-sm);margin-bottom:6px;border-left:3px solid var(--success)"><strong>#2</strong> 读放开（跨 App SELECT 直接 ORM），写收敛（INSERT/UPDATE/DELETE 必须走 api 函数）</div>
      <div style="padding:8px 12px;background:rgba(136,157,240,.06);border-radius:var(--r-sm);border-left:3px solid var(--device)"><strong>#3</strong> 外部只走 API：Vue→HTTP→Django API→ORM / AgentScope→Tool→ORM（同进程）/ Admin→ORM</div>
    </div>
  </div>
  <div class="wf-idea">
    <h3>📊 文档管理方案</h3>
    <ul>
      <li><strong>Stage-Gate 六阶段</strong>：立项→PRD→设计→拆分→开发→复盘，每阶段有产出物，关键节点 Gate 做 Go/No-Go</li>
      <li><strong>主目录平铺</strong>：每个阶段目录下文件直接放，README 做索引，不建深层嵌套</li>
      <li><strong>index.html 门户</strong>：本文档索引页——ECharts 可视化 + 全量文档卡片 + 一键跳转</li>
      <li><strong>Memory 沉淀</strong>：每次排障/纠正/新模式 → 写 memory 文件，下次自动加载。同类错不犯两次</li>
      <li><strong>PRD 先行</strong>：收到功能需求先确认 PRD 是否同步，不跳过需求直接写代码</li>
    </ul>
  </div>
</div>
<div class="wf-case" style="margin-top:16px">
  <div class="wf-case-h"><span class="tag">案例</span><span class="title">实际工作流：从「任务详情要实时步骤」到上线</span></div>
  <div class="wf-case-b">
    <strong>1. 理解</strong>：grep 搜索 runner 模块代码，Read 相关文件，搞清 TaskCard/WebSocket/状态机现状。<br>
    <strong>2. Plan Mode</strong>：出方案——确认 consumer / TaskCard / 前端订阅契约，写 plan 文件等你审批。<br>
    <strong>3. 实现</strong>：改 runner.py + TaskDetail.vue + WS consumer，每步 npx vite build 编译验证。<br>
    <strong>4. 浏览器验证</strong>：python run.py restart → Playwright 打开页面 → 点任务 → 看步骤实时跳动 → 确认 WS 帧格式正确 → 检查 DB 数据一致。<br>
    <strong>5. 沉淀</strong>：写 memory 记录状态机接入要点，更新测试方案标注实现状态。
  </div>
</div>`,
      },
      {
        title: '三条原则（贯穿每次会话）', dir: '../CLAUDE.md',
        empty: null, md: [], html: [],
        inlineHtml: `
<div class="wf-ideas">
  <div class="wf-idea">
    <h3>知行合一</h3>
    <p>知道流程就必须做到。五阶段 + 审核门禁 + 验证铁律不是装饰，是每次任务必须执行的。知道但跳过 = 不知道。</p>
  </div>
  <div class="wf-idea">
    <h3>三省吾身</h3>
    <p>动手前自问：①审核门禁过了吗？②这个选择器/API/方案我确定对吗？③改动经你审批了吗？任一为否 → 停下来确认。</p>
  </div>
  <div class="wf-idea" style="grid-column:1/-1">
    <h3>知之为知之，不知为不知</h3>
    <p>不确定就查 DevTools / 读代码 / grep 搜索 / 追问。方案多选项时列出让你决策。<strong>禁止猜测、试错、假装理解。</strong></p>
  </div>
</div>`,
      },
      {
        title: '查阅入口（源文件只读）', dir: '00-智能体/',
        empty: null,
        md: [
          { title: '结构总览', path: '00-智能体/结构总览.md', desc: '目录树与全量索引（需要翻文件时用）。' },
          { title: 'CLAUDE.md', path: '../CLAUDE.md', desc: '我的身份定义 · 铁律 · 规则索引。', badge: '只读' },
          { title: 'AGENTS.md', path: '../AGENTS.md', desc: '项目架构 · 防火墙 · API/DB 事实。', badge: '只读' },
        ],
        html: [
          { title: '智能体体系设计', path: '00-智能体/智能体体系设计.html', desc: '本栏主图册。', badge: '主' },
          { title: 'Agent 工作流全景报告（参考）', path: 'tests/functional/dashboard/reports/agent-workflow-report.html', desc: '双 Agent 详细报告 · 设计视觉来源。', badge: '参考' },
        ],
      },
    ],
  },
  {
    id: 't', hash: 'stage-t', short: '测试报告', title: '一览平台测试报告',
    subtitle: '按模块分组的自动化测试报告 · 直接引用 tests/ 实际产出 · 点击查看详情',
    agents: ['tester', 'test-automator'], skills: ['functional-testing'],
    gate: null,
    mdEmpty: null, htmlEmpty: null, md: [], html: [],
    sectionTone: 'st',
    sections: [
      {
        title: '测试总览', dir: 'tests/functional/',
        empty: null,
        md: [{ title: '功能测试 README', path: 'tests/functional/README.md', desc: '功能测试目录结构与运行说明。' }],
        html: [],
      },
      {
        title: '前端测试', dir: 'tests/frontend/',
        empty: null,
        html: [{ title: '前端测试报告', path: 'tests/frontend/report.html', desc: 'Vue 前端组件与路由测试。', badge: '前端' }],
        md: [],
      },
      {
        title: '用例管理', dir: 'tests/functional/case-manager/reports/',
        empty: null,
        html: [
          { title: '最新测试报告', path: 'tests/functional/case-manager/reports/report_latest.html', desc: '用例管理模块最新功能测试。', badge: '最新' },
          { title: '目录交付报告', path: 'tests/functional/case-manager/reports/case-directory-delivery.html', desc: '用例目录功能交付测试。', badge: '交付' },
          { title: '目录规划报告', path: 'tests/functional/case-manager/reports/case-directory-plan.html', desc: '用例目录规划方案测试。', badge: '规划' },
          { title: '编辑器分析', path: 'tests/functional/case-manager/reports/case-editor-analysis.html', desc: '用例编辑器交互分析。', badge: '分析' },
        ],
        md: [],
      },
      {
        title: '仪表盘', dir: 'tests/functional/dashboard/reports/',
        empty: null,
        html: [
          { title: '最新测试报告', path: 'tests/functional/dashboard/reports/report_latest.html', desc: '仪表盘模块最新功能测试。', badge: '最新' },
          { title: 'Agent 工作流', path: 'tests/functional/dashboard/reports/agent-workflow-report.html', desc: '双 Agent 工作流详细报告。', badge: '参考' },
          { title: 'AI 编码工作流', path: 'tests/functional/dashboard/reports/dashboard-ai-coding-workflow.html', desc: 'AI 编码工作流分析。', badge: '工作流' },
          { title: '模块分析', path: 'tests/functional/dashboard/reports/dashboard-module-analysis.html', desc: '仪表盘模块结构分析。', badge: '分析' },
          { title: '统计概览', path: 'tests/functional/dashboard/reports/dashboard-stats-overview.html', desc: '平台统计数据概览。', badge: '统计' },
          { title: '趋势追踪', path: 'tests/functional/dashboard/reports/dashboard-trend-trace.html', desc: '趋势追踪分析。', badge: '趋势' },
        ],
        md: [],
      },
      {
        title: '设备管理', dir: 'tests/functional/',
        empty: null,
        html: [
          { title: '设备池测试报告', path: 'tests/functional/device-pool/reports/report_latest.html', desc: '设备池模块功能测试。', badge: '最新' },
          { title: '需求验证报告', path: 'tests/functional/device-pool-requirements/reports/report_latest.html', desc: '设备池需求验收测试。', badge: '需求' },
        ],
        md: [],
      },
      {
        title: '代码审查 & 质量', dir: 'tests/functional/',
        empty: null,
        html: [
          { title: '代码审查报告', path: 'tests/functional/code-review/reports/report_latest.html', desc: '代码审查最新报告。', badge: '审查' },
          { title: '质量关卡', path: 'tests/functional/quality-gate/reports/agent_factory_quality_gate.html', desc: 'Agent 工厂质量门禁报告。', badge: '质量' },
        ],
        md: [],
      },
    ],
  },
];
