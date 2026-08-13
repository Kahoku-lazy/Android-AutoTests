"""Default 30-question bank — covers the platform knowledge domains.

These questions are designed to test an agent's understanding of:
- Platform features & architecture (6 questions)
- Test case design & execution workflow (6)
- Device management (4)
- Element location & XPath (4)
- Knowledge base & RAG (3)
- Error handling & edge cases (4)
- General testing methodology (3)
"""

DEFAULT_QUESTIONS = [
    # ── 平台功能与架构 (6) ──
    {
        "content": "请介绍一下 Android-AutoTests 平台的整体架构，包括前端、后端、AI 引擎和设备控制四层。",
        "expected_keywords": "Vue,Django,AgentScope,uiautomator2,ADB,Redis",
        "category": "平台功能与架构",
        "order": 1,
    },
    {
        "content": "平台支持哪些模型提供商？如何配置 DeepSeek 模型？",
        "expected_keywords": "dashscope,openai,anthropic,deepseek,custom,API Key,base_url",
        "category": "平台功能与架构",
        "order": 2,
    },
    {
        "content": "请说明平台中 StepType 枚举的作用，并列举至少 5 种步骤类型。",
        "expected_keywords": "StepType,click,wait,verify_text,sleep,start_app,kill_app",
        "category": "平台功能与架构",
        "order": 3,
    },
    {
        "content": "请解释平台的「模块防火墙」规则。哪些跨模块操作是允许的，哪些是禁止的？",
        "expected_keywords": "跨App,import,Model,api.py,禁止直接ORM写",
        "category": "平台功能与架构",
        "order": 4,
    },
    {
        "content": "平台支持哪几种 XPath 定位策略？它们是如何生成和排序的？",
        "expected_keywords": "XPath,resource-id,text,content-desc,count,8种策略",
        "category": "平台功能与架构",
        "order": 5,
    },
    {
        "content": "AgentScope 服务和 Django 后端是如何协同工作的？请说明两者的职责边界。",
        "expected_keywords": "AgentScope,FastAPI,Django,同一进程,SSE流,Agent",
        "category": "平台功能与架构",
        "order": 6,
    },
    # ── 测试用例设计与执行 (6) ──
    {
        "content": "用户让你设计一个测试用例，你需要遵循什么样的 SOP 流程？请描述完整的四阶段工作流。",
        "expected_keywords": "需求分析,用例设计,元素准备,用例创建,调试,任务执行",
        "category": "测试流程",
        "order": 7,
    },
    {
        "content": "如何创建一个测试用例？你需要调用哪些工具，步骤中应该包含哪些字段？",
        "expected_keywords": "save_test_case,type,xpath,description,timeout",
        "category": "测试流程",
        "order": 8,
    },
    {
        "content": "在测试执行前，你需要如何准备设备？请描述完整的设备锁定和释放流程。",
        "expected_keywords": "get_online_devices,acquire_device,release_device,锁定",
        "category": "测试流程",
        "order": 9,
    },
    {
        "content": "如果测试用例调试失败，你应该如何排查和修复？",
        "expected_keywords": "debug_test_case,分析错误,调整steps,重新保存",
        "category": "测试流程",
        "order": 10,
    },
    {
        "content": "平台中的 loop_count 参数是什么作用？默认值是多少？",
        "expected_keywords": "loop_count,循环次数,默认3",
        "category": "测试流程",
        "order": 11,
    },
    {
        "content": "执行测试后如何获取结果？如果测试中途需要停止怎么办？",
        "expected_keywords": "get_run_results,stop_run,获取结果,停止执行",
        "category": "测试流程",
        "order": 12,
    },
    # ── 设备管理 (4) ──
    {
        "content": "平台中设备有哪些状态？每种状态代表什么含义？",
        "expected_keywords": "ONLINE,BUSY,OFFLINE,DISCONNECTED,设备状态",
        "category": "设备管理",
        "order": 13,
    },
    {
        "content": "如何查看当前有哪些在线设备？如果设备被其他人锁定了怎么办？",
        "expected_keywords": "get_online_devices,锁定,BUSY,排队",
        "category": "设备管理",
        "order": 14,
    },
    {
        "content": "设备锁的超时机制是怎样的？什么情况下设备会自动释放？",
        "expected_keywords": "timeout,超时,自动释放,心跳",
        "category": "设备管理",
        "order": 15,
    },
    {
        "content": "设备截图流是如何工作的？截图是通过什么协议推送到前端的？",
        "expected_keywords": "WebSocket,截图,2fps,screenshot",
        "category": "设备管理",
        "order": 16,
    },
    # ── 元素定位 (4) ──
    {
        "content": "如何查找某个页面上的 UI 元素？请描述元素定位的完整流程。",
        "expected_keywords": "fetch_page_elements,dump UI,XPath,层级",
        "category": "元素定位",
        "order": 17,
    },
    {
        "content": "如果 fetch_page_elements 返回的元素为空，可能是什么原因？如何解决？",
        "expected_keywords": "设备离线,dump失败,XML截断,ADB",
        "category": "元素定位",
        "order": 18,
    },
    {
        "content": "search_elements 和 fetch_page_elements 有什么区别？各适用于什么场景？",
        "expected_keywords": "search_elements,模糊搜索,fetch_page_elements,页面元素",
        "category": "元素定位",
        "order": 19,
    },
    {
        "content": "XPath 定位符中的 @bounds 属性是什么？它的精度和可靠性如何？",
        "expected_keywords": "@bounds,坐标,精确度,兜底",
        "category": "元素定位",
        "order": 20,
    },
    # ── 知识库与 RAG (3) ──
    {
        "content": "平台的知识库（RAG）是如何工作的？AI 什么时候应该使用它？",
        "expected_keywords": "ChromaDB,向量检索,RAG,语义搜索,search_knowledge_base",
        "category": "知识库",
        "order": 21,
    },
    {
        "content": "使用 search_knowledge_base 工具时需要注意什么？如何提高检索效果？",
        "expected_keywords": "query,top_k,自然语言,具体关键词",
        "category": "知识库",
        "order": 22,
    },
    {
        "content": "知识库中存储了哪些类型的文档？请列举至少 5 种。",
        "expected_keywords": "PRD,ARCH,步骤类型参考,开发清单,API参考",
        "category": "知识库",
        "order": 23,
    },
    # ── 异常处理 (4) ──
    {
        "content": "如果用户的提问需求不够明确，你应该如何处理？",
        "expected_keywords": "逐项询问,确认,不能跳过,设计方案",
        "category": "异常处理",
        "order": 24,
    },
    {
        "content": "当工具调用失败时（如设备不可用），你应该如何响应用户？",
        "expected_keywords": "如实告知,给出建议,不编造,具体原因",
        "category": "异常处理",
        "order": 25,
    },
    {
        "content": "用户要求你执行一个你没有权限的操作，你应该怎么做？",
        "expected_keywords": "拒绝,解释原因,替代方案",
        "category": "异常处理",
        "order": 26,
    },
    {
        "content": "如果测试执行过程中设备突然断开连接，你应该如何处理？",
        "expected_keywords": "OFFLINE,502,告知用户,释放设备",
        "category": "异常处理",
        "order": 27,
    },
    # ── 通用测试方法 (3) ──
    {
        "content": "在设计 Android UI 自动化测试用例时，应该遵循哪些最佳实践？",
        "expected_keywords": "等待,断言,异常处理,步骤描述,可读性",
        "category": "测试方法",
        "order": 28,
    },
    {
        "content": "为什么测试步骤中需要添加 wait 类型的步骤？不加会有什么后果？",
        "expected_keywords": "wait,页面加载,异步,稳定性,超时",
        "category": "测试方法",
        "order": 29,
    },
    {
        "content": "请说明测试用例中 description 字段的重要性，以及如何编写好的描述。",
        "expected_keywords": "description,可读性,维护,清晰描述,步骤意图",
        "category": "测试方法",
        "order": 30,
    },
]

VALID_CATEGORIES: list[str] = sorted({str(q["category"]) for q in DEFAULT_QUESTIONS})
