// AI 工作流面板 HTML（从 index 拆出）
window.WORKFLOW_PANEL_HTML = `<div class="view-panel" id="workflow-panel" data-hash="ai-workflow">
      <nav class="wf-toc" id="wf-toc">
        <button type="button" data-scroll="wf-s1">① Stage-Gate</button>
        <button type="button" data-scroll="wf-s2">② Agent 配置与关联</button>
        <button type="button" data-scroll="wf-s3">③ 用 AI 做产品</button>
        <button type="button" data-scroll="wf-s4">④ 附录案例</button>
      </nav>

      <div class="wf-hero">
        <h2>AI 工作流总览</h2>
        <p>本页是文档体系的「鸟瞰图」：先讲 Stage-Gate 六阶段为何这样切、门禁如何卡住质量；再讲 Agent / Skill / Rules 如何配置与互相咬合；最后给出用 AI 做产品的操作路径。正文不跳转具体文件，便于一次读完建立心智模型。</p>
        <p>横切支撑：管理员（方法论与签发）· 智能体（运行时结构）· 文档平铺主目录（前缀分类 + README 索引）。</p>
      </div>

      <section class="wf-section" id="wf-s1">
        <h2><span class="n">1</span>Stage-Gate 六阶段 · 流程与设计思路</h2>
        <p class="wf-lead">设计目标不是「多几个文件夹」，而是把产品从想法到上线拆成可审计的阶段：每阶段有明确产出物，关键节点用 Gate 做 Go / No-Go，避免需求未清就写代码、架构未定就铺量、质量未过就发布。</p>

        <div class="wf-flow">
          <div class="wf-stage"><div class="sn" style="background:#6fba2c">1</div><div class="st">立项验证</div><div class="sd">定位 · 灵感 · 人群 · 竞品与价值。回答「值不值得做」。</div></div>
          <div class="wf-stage"><div class="sn" style="background:#11a89b">2</div><div class="st">PRD 需求</div><div class="sd">1 总 PRD + 7 子模块 PRD；方法论内嵌索引页。</div><span class="sg">Gate 1</span></div>
          <div class="wf-stage"><div class="sn" style="background:#185FA5">3</div><div class="st">设计与架构</div><div class="sd">技术栈 · 总架构 · 模块设计 · 原型 · 接口契约。</div><span class="sg">Gate 2</span></div>
          <div class="wf-stage"><div class="sn" style="background:#7c5cbf">4</div><div class="st">任务拆分</div><div class="sd">按角色：设定 / 计划 / 验收。把规格拆成可执行批次。</div></div>
          <div class="wf-stage"><div class="sn" style="background:#c7840a">5</div><div class="st">开发与测试</div><div class="sd">按模块：编程工作流 · 代码质量 · 测试报告。</div><span class="sg">Gate 3</span></div>
          <div class="wf-stage"><div class="sn" style="background:#e05a5a">6</div><div class="st">发布与复盘</div><div class="sd">上线记录 · 质量/闭环/工程复盘 · 行动项回流下一轮。</div></div>
        </div>

        <div class="wf-ideas">
          <div class="wf-idea">
            <h3>为什么是六阶段而不是「边做边改」</h3>
            <ul>
              <li><strong>信息单向变硬</strong>：越往后越贵；立项与 PRD 阶段把假设写清，后面少返工。</li>
              <li><strong>门禁可拒绝</strong>：Gate 不是仪式，是「材料不足则停」的否决权。</li>
              <li><strong>角色可并行</strong>：调研 / 产品 / 架构 / 开发 / 测试各有产出槽位，避免一人包办黑盒。</li>
              <li><strong>文档即状态机</strong>：主目录平铺 + 前缀命名，阶段状态一眼可读，不靠口头同步。</li>
            </ul>
          </div>
          <div class="wf-idea">
            <h3>三道 Gate 的设计意图</h3>
            <ul>
              <li><strong>Gate 1 · PRD 评审</strong>：用户故事、验收标准、边界清晰；矛盾需求先消解。</li>
              <li><strong>Gate 2 · 架构就绪</strong>：模块边界、契约、关键风险与 Issue 级拆分就绪。</li>
              <li><strong>Gate 3 · 上线评审</strong>：功能/回归证据、已知风险、回滚与发布说明齐备。</li>
            </ul>
            <p style="margin-top:8px">管理员保留签发权；执行角色准备材料，不代替 Go 决策。</p>
          </div>
        </div>

        <div class="wf-idea" style="margin-bottom:0">
          <h3>与文档目录的对应（心智映射）</h3>
          <p>立项验证 → PRD → 设计与架构 → 任务拆分 → 开发与测试 → 发布与复盘；另有「管理员 / 智能体」横切栏，不参与漏斗完备度，专管方法论与运行时配置。</p>
        </div>
      </section>

      <section class="wf-section" id="wf-s2">
        <h2><span class="n">2</span>Agent 智能体 · 如何配置与关联</h2>
        <p class="wf-lead">智能体不是聊天窗口，而是「可路由的角色 + 可触发的 Skill + 始终生效的 Rules」。配置分三层：入口文档定调度，Agent 定人设与工具，Skill/Rules 定能力与铁律。</p>

        <table class="wf-table">
          <thead><tr><th>层级</th><th>放什么</th><th>关联方式</th></tr></thead>
          <tbody>
            <tr><td><code>CLAUDE.md</code></td><td>路由表、身份、验证铁律、Rules/Skills 索引</td><td>会话总入口；决定「先找谁」</td></tr>
            <tr><td><code>AGENTS.md</code></td><td>项目架构、模块边界、API/DB、启动约定</td><td>所有 Agent 共享的「项目真相」</td></tr>
            <tr><td><code>.claude/agents/</code></td><td>6 个角色：prd-writer / architect / developer / reviewer / tester / test-automator</td><td>按任务类型路由；各有工具权限</td></tr>
            <tr><td><code>.claude/skills/</code></td><td>auto-dev、PRD、架构审查、质量关卡、功能测试等</td><td>Agent 或用户触发专项工作流</td></tr>
            <tr><td><code>.claude/rules/</code></td><td>前后端、安全、防火墙、设备控制等硬约束</td><td>始终加载，约束生成行为</td></tr>
            <tr><td><code>.agents/skills/</code></td><td>扩展能力：浏览器测试、Skill 锻造、辅导等</td><td>按需挂载，不污染主路由</td></tr>
            <tr><td>Memory / Hooks</td><td>教训沉淀、格式化、凭据保护、会话健康</td><td>跨会话学习与安全兜底</td></tr>
          </tbody>
        </table>

        <div class="wf-ideas">
          <div class="wf-idea">
            <h3>推荐调度优先级</h3>
            <ol style="margin:0;padding-left:18px;font-size:12px;color:var(--text-secondary);line-height:1.7">
              <li>有功能需求 → 先确认 PRD 是否已由产品角色同步</li>
              <li>跨模块 / 架构不确定 → 先架构角色出影响面</li>
              <li>日常实现 → 开发角色走 auto-dev（探索→方案→编码→审查→测试）</li>
              <li>交付前 → 审查 + 测试双角色把关</li>
            </ol>
          </div>
          <div class="wf-idea">
            <h3>与 Stage-Gate 的咬合</h3>
            <ul>
              <li>阶段 1–2：产品 / 调研向 Agent + PRD Skill</li>
              <li>阶段 3–4：架构 Agent + 模块设计 / 架构审查 Skill</li>
              <li>阶段 5：开发 / 审查 / 测试 Agent + auto-dev / 质量关卡 / 功能测试</li>
              <li>阶段 6：复盘与发布相关 Skill；行动项写回 Memory 与下轮计划</li>
            </ul>
          </div>
        </div>

        <p class="wf-note">配置原则：改行为改 Agent/Skill/Rules 源；文档索引栏只做结构说明，不复制源文件。权限收敛——跨模块写操作走契约，禁止绕过三道防火墙。</p>
      </section>

      <section class="wf-section" id="wf-s3">
        <h2><span class="n">3</span>如何用 AI 做产品</h2>
        <p class="wf-lead">把 AI 当成「带门禁的协作团队」，而不是「一次生成全部代码」。人负责目标与签发，AI 负责探索、起草、实现与证据收集；每阶段结束用 Gate 问一句：材料够不够过门？</p>

        <div class="wf-steps">
          <div class="wf-step"><div class="num">1</div><div><h3>立假设，不立功能清单</h3><p>用立项四问（定位 / 灵感 / 人群 / 竞品价值）写清「为谁解决什么问题」。AI 可帮扩写与对比，但 Go/No-Go 由人拍板。</p></div></div>
          <div class="wf-step"><div class="num">2</div><div><h3>PRD 先行，验收标准可测</h3><p>先总后分：总 PRD 定边界，子模块 PRD 定交互与验收。未过 Gate 1 不开大规模编码。矛盾需求用评审方法消解，而不是堆需求。</p></div></div>
          <div class="wf-step"><div class="num">3</div><div><h3>架构与契约再动手</h3><p>模块边界、API 契约、状态机/设备锁等关键路径先定。复杂改动先出影响面与 Issue 拆分，再进开发批次。</p></div></div>
          <div class="wf-step"><div class="num">4</div><div><h3>小批次 auto-dev，强制全栈验证</h3><p>每批：探索 → 方案确认 → 编码 → 审查 → 测试。验证铁律：编译通过 → 重启 → 浏览器看 UI → 核对 API/DB。禁止「curl 通了就算修好」。</p></div></div>
          <div class="wf-step"><div class="num">5</div><div><h3>证据进文档，复盘进行动项</h3><p>开发/测试记录、诊断报告、质量复盘写入对应阶段；行动项回流立项或任务拆分，形成闭环而不是一次性对话。</p></div></div>
        </div>

        <div class="wf-ideas">
          <div class="wf-idea">
            <h3>人机分工（建议）</h3>
            <ul>
              <li><strong>人</strong>：目标、优先级、Gate 签发、敏感决策、最终体验判断</li>
              <li><strong>AI</strong>：调研扩写、PRD 草稿、架构草案、实现、用例、诊断报告</li>
              <li><strong>共同</strong>：方案多选项时列出让人决策；不确定就停下来问</li>
            </ul>
          </div>
          <div class="wf-idea">
            <h3>三条原则（贯穿全程）</h3>
            <ul>
              <li><strong>知行合一</strong>：流程写了就要做，门禁不能只在文档里好看</li>
              <li><strong>三省吾身</strong>：门禁过了吗？选择器/API 确定吗？改动经审批了吗？</li>
              <li><strong>知之为知之</strong>：不确定就查证或追问，禁止猜测试错装懂</li>
            </ul>
          </div>
        </div>
      </section>

      <section class="wf-section" id="wf-s4">
        <h2><span class="n">4</span>附录 · 案例</h2>
        <p class="wf-lead">以下案例抽象自本平台已发生的工作方式，说明「阶段 × Agent × 产出」如何串起来。不指向具体文件路径。</p>

        <div class="wf-case">
          <div class="wf-case-h"><span class="tag">案例 A</span><span class="title">新功能：从一句话需求到可测 PRD</span></div>
          <div class="wf-case-b">
            <strong>场景</strong>：业务提出「任务详情要能看步骤实时进度」。<br>
            <strong>路径</strong>：立项侧补场景假设 → 产品角色起草子模块需求与验收标准 → Gate 1 确认范围（含 WebSocket 推送、未执行步骤展示策略）→ 架构确认前后端契约 → 任务拆分出开发/测试批次。<br>
            <strong>要点</strong>：先把「实时」定义成可验收行为（推送字段、UI 状态），再让开发 Agent 实现。
          </div>
        </div>

        <div class="wf-case">
          <div class="wf-case-h"><span class="tag">案例 B</span><span class="title">执行引擎「用不了」：根因在状态机被架空</span></div>
          <div class="wf-case-b">
            <strong>场景</strong>：任务状态与真实运行不一致，崩溃后留僵尸任务。<br>
            <strong>路径</strong>：测试/诊断产出全链路报告 → 架构角色定位「状态机未接入主路径 + u2 阻塞无超时」→ 出重构方案与协议（分阶段渐进）→ 开发按 P0 修复接入 → 审查与回归 → 复盘写入质量/闭环评估。<br>
            <strong>要点</strong>：复杂故障先架构与诊断，再编码；协议化拆分避免一次大爆炸重构。
          </div>
        </div>

        <div class="wf-case">
          <div class="wf-case-h"><span class="tag">案例 C</span><span class="title">文档体系 Stage-Gate 化</span></div>
          <div class="wf-case-b">
            <strong>场景</strong>：文档散落、旧路径与新阶段并存，索引难用。<br>
            <strong>路径</strong>：发布与复盘阶段沉淀分类方案与移植方案 → 确认范围 → 主目录平铺 + README 索引 → 索引页按六阶段 + 管理员/智能体横切重组 → 旧路径软链兼容。<br>
            <strong>要点</strong>：治理类工作也走「方案确认 → 落地 → 复盘」；索引是导航，真相仍在阶段产出里。
          </div>
        </div>

        <div class="wf-case">
          <div class="wf-case-h"><span class="tag">案例 D</span><span class="title">日常小改：按钮文案 / 样式</span></div>
          <div class="wf-case-b">
            <strong>场景</strong>：低风险 UI 微调。<br>
            <strong>路径</strong>：可压缩流程——仍建议一句话说明验收标准 → 开发 Agent 直接改 → 浏览器验证 → 必要时补一条开发记录。<br>
            <strong>要点</strong>：Stage-Gate 可按风险裁剪强度（Lite），但「浏览器验证」不可裁掉。
          </div>
        </div>

        <p class="wf-note">更多细节分布在各阶段文档与智能体结构说明中；本页只建立总览心智，便于新人与协作者对齐「我们如何用 AI 做产品」。</p>
      </section>
    </div>

    `;
