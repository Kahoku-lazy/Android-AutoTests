<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { getToken } from '@/shared/api-client.js'

import {
  listBanks, createBank, updateBank, deleteBank, seedDefaultBank,
  listRuns, getRun, startRun, deleteRun, submitScore,
  kbSelfTest, listAgents, listFrameworks,
} from './evaluator-api.js'

// ── Sub-tabs ──
const subTab = ref('self')
const SUB_TABS = [
  { key: 'self', label: '答卷评分', desc: '自建 LLM-as-Judge 四维评分', available: true, kind: 'exam' },
  { key: 'kb', label: '知识库评测', desc: 'ChromaDB 检索质量自测', available: true, kind: 'kb' },
  { key: 'evalscope', label: 'EvalScope', desc: '模型基准跑分 + Arena 对战', available: false, kind: 'benchmark' },
  { key: 'deepeval', label: 'DeepEval', desc: 'Pytest 风格指标化评测', available: false, kind: 'metric' },
  { key: 'maseval', label: 'MASEval', desc: '多 Agent 系统级评测', available: false, kind: 'system' },
]

const curTab = computed(() => SUB_TABS.find(t => t.key === subTab) || SUB_TABS[0])

// ── Frameworks availability ──
async function loadFrameworks() {
  try {
    const { data } = await listFrameworks()
    if (data.ok) {
      const availMap = {}
      ;(data.frameworks || []).forEach(f => { availMap[f.key] = f.available })
      SUB_TABS.forEach(t => { if (availMap.hasOwnProperty(t.key)) t.available = availMap[t.key] })
    }
  } catch (_) {}
}

// ── Agents ──
const agents = ref([])
async function loadAgents() {
  try { const { data } = await listAgents(); if (data.ok) agents.value = data.agents || [] } catch (_) {}
}

// ── Banks ──
const banks = ref([])
async function loadBanks() {
  try { const { data } = await listBanks(); if (data.ok) banks.value = data.banks || [] } catch (_) {}
}

// ── Bank editor ──
const showBankEditor = ref(false)
const editingBank = ref(null)
const bankForm = ref({ name: '', description: '', questions: [] })
function openBankEditor(bank) {
  if (bank) { editingBank.value = bank; bankForm.value = { name: bank.name, description: bank.description || '', questions: [] } }
  else { editingBank.value = null; bankForm.value = { name: '', description: '', questions: [] } }
  showBankEditor.value = true
}
function addQuestionRow() { bankForm.value.questions.push({ content: '', expected_keywords: '', category: 'general' }) }
function removeQuestionRow(i) { bankForm.value.questions.splice(i, 1) }
async function saveBank() {
  if (!bankForm.value.name.trim()) { ElMessage.warning('请输入试卷名称'); return }
  try {
    if (editingBank.value) await updateBank(editingBank.value.id, bankForm.value)
    else await createBank(bankForm.value)
    showBankEditor.value = false; await loadBanks(); ElMessage.success('已保存')
  } catch (_) { ElMessage.error('保存失败') }
}
async function removeBank(id) { try { await deleteBank(id); await loadBanks() } catch (_) {} }
async function seedDefault() {
  try { await seedDefaultBank(); await loadBanks(); ElMessage.success('默认试卷已创建') } catch (_) {}
}

// ── Eval Run (shared) ──
const selectedAgentId = ref(null)
const selectedBankId = ref(null)
const judgeModel = ref('qwen-max')
const starting = ref(false)
const runs = ref([])

// Framework-specific: benchmark/metric selection
const evalMode = ref('custom')  // 'benchmark' | 'custom'
const selectedBenchmark = ref('')
const selectedMetrics = ref([])

const BENCHMARKS_BY_FW = {
  evalscope: [
    { key: 'mmlu', label: 'MMLU', desc: '多任务语言理解（57学科）' },
    { key: 'ceval', label: 'C-Eval', desc: '中文综合能力评测' },
    { key: 'swe_bench', label: 'SWE-bench', desc: '软件工程任务' },
    { key: 'gaia', label: 'GAIA', desc: '通用多步推理' },
    { key: 'tau3_bench', label: 'τ³-bench', desc: '客服场景（零售/航空/银行）' },
  ],
  maseval: [
    { key: 'gaia', label: 'GAIA', desc: '通用多步推理' },
    { key: 'agent_bench', label: 'AgentBench', desc: '多环境 Agent 决策' },
  ],
}

const METRICS_BY_FW = {
  deepeval: [
    { key: 'answer_relevancy', label: 'AnswerRelevancy', desc: '回答相关性', selected: false },
    { key: 'faithfulness', label: 'Faithfulness', desc: '忠实度（幻觉检测）', selected: false },
    { key: 'geval', label: 'GEval', desc: '通用 LLM-as-Judge', selected: false },
    { key: 'hallucination', label: 'Hallucination', desc: '幻觉检测', selected: false },
    { key: 'task_completion', label: 'TaskCompletion', desc: '任务完成度', selected: false },
    { key: 'tool_correctness', label: 'ToolCorrectness', desc: '工具调用正确率', selected: false },
    { key: 'goal_accuracy', label: 'GoalAccuracy', desc: '目标准确性', selected: false },
    { key: 'plan_adherence', label: 'PlanAdherence', desc: '计划遵循度', selected: false },
  ],
}

async function loadRuns() {
  try { const { data } = await listRuns(); if (data.ok) runs.value = data.runs || [] } catch (_) {}
}

const filteredRuns = computed(() => runs.value.filter(r => (r.framework || 'self') === subTab.value))

async function doStartRun() {
  if (!selectedAgentId.value) { ElMessage.warning('请选择智能体'); return }
  if (curTab.value.kind === 'exam' && !selectedBankId.value) { ElMessage.warning('请选择试卷'); return }
  starting.value = true
  try {
    const extra = {}
    if (curTab.value.kind === 'benchmark' && evalMode.value === 'benchmark') {
      extra.benchmark = selectedBenchmark.value
    }
    if (curTab.value.kind === 'metric') {
      extra.metrics = selectedMetrics.value.filter(m => m.selected).map(m => m.key)
    }
    const { data } = await startRun(selectedAgentId.value, selectedBankId.value, judgeModel.value, subTab.value)
    if (data.ok) { ElMessage.success(data.message || '评测已开始'); await loadRuns(); pollRun(data.id) }
    else ElMessage.error(data.error || '启动失败')
  } catch (_) { ElMessage.error('启动失败') }
  starting.value = false
}

function pollRun(runId) {
  const timer = setInterval(async () => {
    try {
      const { data } = await getRun(runId)
      if (data.ok) {
        const idx = runs.value.findIndex(r => r.id === runId)
        if (idx >= 0) { runs.value[idx] = data.run; runs.value = [...runs.value] }
        if (data.run.status === 'completed' || data.run.status === 'failed') {
          clearInterval(timer); ElMessage.success('评测完成')
        }
      }
    } catch (_) {}
  }, 2000)
}

// ── Run Detail ──
const activeRunId = ref(null)
const runDetail = ref(null)
const loadingDetail = ref(false)
async function viewRun(runId) {
  activeRunId.value = runId; loadingDetail.value = true
  try { const { data } = await getRun(runId); if (data.ok) runDetail.value = data.run } catch (_) {}
  loadingDetail.value = false
}
async function doSubmitScore(resultId, field, value) {
  try { await submitScore(resultId, { [field]: value }); if (activeRunId.value) await viewRun(activeRunId.value) } catch (_) {}
}

// ── KB Self-Test & Interactive Query ──
const kbTestResult = ref(null); const kbTesting = ref(false)
const kbQuery = ref(''); const kbQueryResult = ref(null); const kbQuerying = ref(false)

async function doKbSelfTest() {
  kbTesting.value = true
  try { const { data } = await kbSelfTest(); if (data.ok) kbTestResult.value = data } catch (_) {}
  kbTesting.value = false
}

async function doKbQuery() {
  const q = kbQuery.value.trim()
  if (!q) { ElMessage.warning('请输入查询内容'); return }
  kbQuerying.value = true; kbQueryResult.value = null
  try {
    const { data } = await kbSelfTest() // reuse KB search API — pass single query
    // Actually, use a dedicated search: POST /api/evaluator/kb-search
    const resp = await fetch('/api/evaluator/kb-search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${getToken()}` },
      body: JSON.stringify({ query: q, top_k: 5 }),
    })
    const d = await resp.json()
    if (d.ok) kbQueryResult.value = d
  } catch (_) {
    // Fallback: use self-test result for now
    kbQueryResult.value = { ok: true, query: q, documents: [], note: '搜索暂不可用，请先重启服务' }
  }
  kbQuerying.value = false
}

// ── Init ──
onMounted(async () => { await Promise.all([loadAgents(), loadBanks(), loadRuns(), loadFrameworks()]) })

// Helpers
function scoreColor(s) { const v = parseFloat(s) || 0; if (v >= 4) return '#89CFF0'; if (v >= 3) return '#f7cd67'; if (v >= 2) return '#f7a8c4'; return '#e85f5f' }
function fwLabel(run) { const fw = SUB_TABS.find(f => f.key === (run.framework || 'self')); return fw ? fw.label : (run.framework || 'self') }
function prettyJson(raw) { try { return JSON.stringify(JSON.parse(raw), null, 2) } catch { return raw } }
</script>

<template>
  <div class="evaluator-host">
    <!-- ═══════════════ SUB-TABS ═══════════════ -->
    <div style="display:flex;gap:8px;margin-bottom:20px;flex-wrap:wrap">
      <button v-for="tab in SUB_TABS" :key="tab.key"
              :class="['view-tab', { active: subTab===tab.key }]"
              :title="tab.desc" @click="subTab=tab.key">
        {{ tab.label }}
        <span v-if="!tab.available" style="font-size:10px;opacity:0.5;margin-left:4px">未安装</span>
      </button>
    </div>

    <!-- ═══════════════ COMMON: Agent Selector ═══════════════ -->
    <div v-if="subTab!=='kb'" class="doc-section">
      <div class="section-title">{{ curTab.label }} 评测</div>

      <!-- Description -->
      <div class="fw-desc" style="margin-bottom:16px;padding:12px 16px;background:#faf9f4;border-radius:8px;font-size:13px;color:#5c4b38">
        <template v-if="subTab==='self'">
          使用 <strong>Judge LLM</strong> 对智能体的答卷进行四维评分（相关性/准确性/完整性/简洁性），支持人工纠偏。适用于自定义测试题目的精准评估。
        </template>
        <template v-else-if="subTab==='evalscope'">
          <strong>阿里 ModelScope 一站式评测框架。</strong>内置 MMLU、C-Eval、SWE-bench、GAIA、τ³-bench 等标准基准，支持 Arena 多模型对战排名、Agent Trace 可视化。适合论文级别的模型能力评测与横向对比。
        </template>
        <template v-else-if="subTab==='deepeval'">
          <strong>类 Pytest 风格的 LLM 评测框架。</strong>50+ 内置指标（AnswerRelevancy、Faithfulness、Hallucination、TaskCompletion 等），支持 CI/CD 集成。适合持续集成流水线和指标驱动的精细化评测。
        </template>
        <template v-else-if="subTab==='maseval'">
          <strong>多 Agent 系统级评测框架（ACL 2026）。</strong>将整个 Agent 系统（而非单个模型）作为评测单元，框架无关设计。支持 GAIA、AgentBench 等基准。适合 Leader+Worker 多智能体协作场景的评测。
        </template>
      </div>

      <!-- Not installed warning -->
      <div v-if="!curTab.available" style="padding:12px 16px;background:#fff3e0;border-radius:8px;margin-bottom:16px;font-size:13px;color:#e65100">
        ⚠️ {{ curTab.label }} 未安装。请先执行 <code>pip install {{ subTab }}</code>，然后重启服务。
      </div>

      <!-- ── Self: Exam paper mode ── -->
      <template v-if="subTab==='self'">
        <el-form label-width="100px" inline>
          <el-form-item label="选择智能体">
            <el-select v-model="selectedAgentId" placeholder="选择智能体" style="width:240px" clearable>
              <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="选择试卷">
            <el-select v-model="selectedBankId" placeholder="选择题库试卷" style="width:200px" clearable>
              <el-option v-for="b in banks" :key="b.id" :label="`${b.name} (${b.question_count}题)`" :value="b.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="裁判模型">
            <el-input v-model="judgeModel" placeholder="qwen-max" style="width:150px" />
          </el-form-item>
        </el-form>
      </template>

      <!-- ── EvalScope: Benchmark + Custom ── -->
      <template v-else-if="subTab==='evalscope'">
        <el-form label-width="100px" inline>
          <el-form-item label="选择智能体">
            <el-select v-model="selectedAgentId" placeholder="选择智能体" style="width:240px" clearable>
              <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div style="display:flex;gap:8px;margin-bottom:12px">
          <button :class="['mode-btn', { active: evalMode==='benchmark' }]" @click="evalMode='benchmark'">📊 标准基准跑分</button>
          <button :class="['mode-btn', { active: evalMode==='custom' }]" @click="evalMode='custom'">📝 自定义试卷</button>
        </div>
        <template v-if="evalMode==='benchmark'">
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
            <div v-for="bm in BENCHMARKS_BY_FW.evalscope" :key="bm.key"
                 :class="['bench-card', { selected: selectedBenchmark===bm.key }]"
                 @click="selectedBenchmark=bm.key">
              <div class="bench-name">{{ bm.label }}</div>
              <div class="bench-desc">{{ bm.desc }}</div>
            </div>
          </div>
        </template>
        <template v-else>
          <el-form-item label="选择试卷" style="margin-top:8px">
            <el-select v-model="selectedBankId" placeholder="或选择题库试卷" style="width:200px" clearable>
              <el-option v-for="b in banks" :key="b.id" :label="`${b.name} (${b.question_count}题)`" :value="b.id" />
            </el-select>
          </el-form-item>
        </template>
      </template>

      <!-- ── DeepEval: Metric selection + Exam ── -->
      <template v-else-if="subTab==='deepeval'">
        <el-form label-width="100px" inline>
          <el-form-item label="选择智能体">
            <el-select v-model="selectedAgentId" placeholder="选择智能体" style="width:240px" clearable>
              <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="选择试卷">
            <el-select v-model="selectedBankId" placeholder="选择题库试卷" style="width:200px" clearable>
              <el-option v-for="b in banks" :key="b.id" :label="`${b.name} (${b.question_count}题)`" :value="b.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div style="font-size:13px;font-weight:600;color:#4a3a28;margin-bottom:8px">评测指标（勾选需要的）：</div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:12px">
          <el-checkbox v-for="m in METRICS_BY_FW.deepeval" :key="m.key" v-model="m.selected"
                       :label="m.label" size="small" border style="margin-right:0" />
        </div>
      </template>

      <!-- ── MASEval: Benchmark + System description ── -->
      <template v-else-if="subTab==='maseval'">
        <el-form label-width="100px" inline>
          <el-form-item label="选择智能体">
            <el-select v-model="selectedAgentId" placeholder="选择智能体" style="width:240px" clearable>
              <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
            </el-select>
          </el-form-item>
        </el-form>
        <div style="display:flex;gap:8px;margin-bottom:12px">
          <button :class="['mode-btn', { active: evalMode==='benchmark' }]" @click="evalMode='benchmark'">📊 标准基准</button>
          <button :class="['mode-btn', { active: evalMode==='custom' }]" @click="evalMode='custom'">📝 自定义试卷</button>
        </div>
        <template v-if="evalMode==='benchmark'">
          <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px">
            <div v-for="bm in BENCHMARKS_BY_FW.maseval" :key="bm.key"
                 :class="['bench-card', { selected: selectedBenchmark===bm.key }]"
                 @click="selectedBenchmark=bm.key">
              <div class="bench-name">{{ bm.label }}</div>
              <div class="bench-desc">{{ bm.desc }}</div>
            </div>
          </div>
          <div style="font-size:12px;color:#a0936e;margin-top:4px">
            MASEval 将整个 Agent 系统作为评测单元。支持 Leader+Worker 多智能体协作场景。
          </div>
        </template>
        <template v-else>
          <el-form-item label="选择试卷" style="margin-top:8px">
            <el-select v-model="selectedBankId" placeholder="或选择题库试卷" style="width:200px" clearable>
              <el-option v-for="b in banks" :key="b.id" :label="`${b.name} (${b.question_count}题)`" :value="b.id" />
            </el-select>
          </el-form-item>
        </template>
      </template>

      <!-- Start button -->
      <div style="margin-top:16px">
        <el-button type="primary" :loading="starting" :disabled="!curTab.available" @click="doStartRun">
          🚀 开始评测
        </el-button>
      </div>
    </div>

    <!-- ═══════════════ KB Eval ═══════════════ -->
    <div v-if="subTab==='kb'" class="doc-section">
      <div class="section-title">知识库评测</div>

      <!-- Agent selector for context-aware KB testing -->
      <el-form label-width="120px" style="margin-bottom:24px">
        <el-form-item label="测试智能体（可选）">
          <el-select v-model="selectedAgentId" placeholder="选择智能体（查看其知识库文档范围）" style="width:280px" clearable>
            <el-option v-for="a in agents" :key="a.id" :label="a.name" :value="a.id" />
          </el-select>
          <span style="font-size:12px;color:#a0936e;margin-left:8px">
            选择智能体后，可查看该智能体配置的知识库文档范围
          </span>
        </el-form-item>
      </el-form>

      <!-- Interactive query -->
      <div style="margin-bottom:20px">
        <div style="font-size:14px;font-weight:600;color:#4a3a28;margin-bottom:8px">🔍 交互式检索测试</div>
        <div style="display:flex;gap:8px">
          <el-input v-model="kbQuery" placeholder="输入查询（如：如何创建测试用例）" style="flex:1"
                    @keyup.enter="doKbQuery" />
          <el-button type="primary" :loading="kbQuerying" @click="doKbQuery">查询</el-button>
        </div>
        <div v-if="kbQueryResult" style="margin-top:12px">
          <div style="font-weight:600;color:#4a3a28;margin-bottom:6px">
            查询: "{{ kbQueryResult.query }}" → {{ kbQueryResult.total || 0 }} 条结果
          </div>
          <div v-for="(doc, i) in (kbQueryResult.documents||[])" :key="i"
               style="padding:8px 12px;background:#faf9f4;border-radius:6px;margin-bottom:4px;font-size:13px">
            <span style="color:#8a7b66;font-weight:600">{{ doc.source }}</span>
            <span style="margin-left:8px;color:#a0936e">score: {{ doc.score }}</span>
            <div style="color:#5c4b38;margin-top:4px;max-height:120px;overflow:auto">{{ doc.content }}</div>
          </div>
          <div v-if="!kbQueryResult.documents?.length" style="color:#a0936e;padding:12px">无匹配结果</div>
        </div>
      </div>

      <el-divider />

      <!-- Auto self-test -->
      <p style="color:#a0936e;margin-bottom:12px">
        使用 10 个预定义查询批量测试知识库检索覆盖率与相关性。
      </p>
      <el-button type="primary" :loading="kbTesting" @click="doKbSelfTest">🔍 自动批量自测</el-button>

      <div v-if="kbTestResult" style="margin-top:20px">
        <div style="display:flex;gap:20px;margin-bottom:16px">
          <div class="score-badge"><div class="score-num" :style="{color:scoreColor(kbTestResult.score.coverage/20)}">{{ kbTestResult.score.coverage }}%</div><div class="score-label">覆盖率</div></div>
          <div class="score-badge"><div class="score-num">{{ kbTestResult.score.avg_relevance }}</div><div class="score-label">平均相关度</div></div>
          <div class="score-badge"><div class="score-num">{{ kbTestResult.score.total_queries }}</div><div class="score-label">测试查询数</div></div>
        </div>
        <div v-for="d in kbTestResult.details" :key="d.query" style="margin-bottom:12px">
          <div style="font-weight:600;color:#4a3a28;margin-bottom:4px">
            [{{ d.total_hits }} hits] {{ d.query }}
            <el-tag size="small" :type="d.total_hits?'success':'danger'" style="margin-left:8px">{{ d.total_hits?'有结果':'无结果' }}</el-tag>
          </div>
          <div v-for="doc in d.documents" :key="doc.source" style="padding:6px 12px;background:#faf9f4;border-radius:6px;margin-bottom:4px;font-size:12px">
            <span style="color:#8a7b66">{{ doc.source }}</span>
            <span style="margin-left:8px;color:#a0936e">score: {{ doc.score }}</span>
            <div style="color:#5c4b38;margin-top:2px">{{ doc.content_preview?.slice(0, 200) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════ Paper Management (all tabs except kb) ═══════════════ -->
    <div v-if="subTab!=='kb'" style="display:flex;gap:12px;align-items:center;margin-bottom:16px">
      <el-button size="small" @click="openBankEditor(null)">+ 新建试卷</el-button>
      <el-button size="small" @click="seedDefault" :disabled="banks.some(b=>b.name==='默认30题试卷')">📋 创建默认30题试卷</el-button>
      <span style="font-size:12px;color:#a0936e">已有 {{ banks.length }} 份试卷，共 {{ banks.reduce((s,b)=>s+(b.question_count||0),0) }} 题</span>
    </div>

    <!-- ═══════════════ Run History ═══════════════ -->
    <div class="doc-section">
      <div class="section-title">评测记录 ({{ filteredRuns.length }})</div>
      <div v-if="!filteredRuns.length" style="padding:20px;text-align:center;color:#a0936e">暂无评测记录</div>
      <div v-for="r in filteredRuns" :key="r.id" class="run-card"
           style="display:flex;align-items:center;gap:14px;padding:12px 16px;background:#faf9f4;border-radius:10px;margin-bottom:8px;border:1px solid #e8e2d6">
        <el-tag :type="r.status==='completed'?'success':r.status==='running'?'warning':r.status==='failed'?'danger':'info'" size="small">{{ r.status }}</el-tag>
        <span style="font-weight:600;min-width:100px">{{ r.agent_name }}</span>
        <el-tag size="small" type="info">{{ fwLabel(r) }}</el-tag>
        <span style="color:#8a7b66;font-size:13px">{{ r.bank_name }} · {{ r.total_questions }}题</span>
        <span v-if="r.total_score>0" style="font-weight:700;color:#89CFF0;font-size:13px">总分 {{ r.total_score }}</span>
        <span v-if="r.status==='running'" style="color:#f7a8c4;font-size:13px">{{ r.completed_questions }}/{{ r.total_questions }}</span>
        <div style="margin-left:auto;display:flex;gap:8px">
          <el-button size="small" @click="viewRun(r.id)" :disabled="r.status==='running'">详情</el-button>
          <el-button size="small" type="danger" plain @click="removeBank(r.id)">删除</el-button>
        </div>
      </div>
    </div>

    <!-- ═══════════════ Run Detail ═══════════════ -->
    <div v-if="runDetail" class="doc-section">
      <div class="section-title">
        评测详情 — {{ runDetail.agent_name }} × {{ runDetail.bank_name }}
        <el-tag size="small" style="margin-left:8px">{{ fwLabel(runDetail) }}</el-tag>
        <el-button size="small" style="margin-left:12px" @click="runDetail=null;activeRunId=null">关闭</el-button>
      </div>
      <div v-if="loadingDetail" style="padding:20px;text-align:center;color:#a0936e">加载中...</div>
      <div v-else>
        <div style="display:flex;gap:20px;margin-bottom:16px;flex-wrap:wrap">
          <div class="score-badge"><div class="score-num" :style="{color:scoreColor(runDetail.total_score)}">{{ runDetail.total_score }}</div><div class="score-label">综合总分</div></div>
          <div v-if="runDetail.avg_relevance>0" class="score-badge"><div class="score-num" :style="{color:scoreColor(runDetail.avg_relevance)}">{{ runDetail.avg_relevance }}</div><div class="score-label">相关性</div></div>
          <div v-if="runDetail.avg_accuracy>0" class="score-badge"><div class="score-num" :style="{color:scoreColor(runDetail.avg_accuracy)}">{{ runDetail.avg_accuracy }}</div><div class="score-label">准确性</div></div>
          <div v-if="runDetail.avg_completeness>0" class="score-badge"><div class="score-num" :style="{color:scoreColor(runDetail.avg_completeness)}">{{ runDetail.avg_completeness }}</div><div class="score-label">完整性</div></div>
          <div v-if="runDetail.avg_conciseness>0" class="score-badge"><div class="score-num" :style="{color:scoreColor(runDetail.avg_conciseness)}">{{ runDetail.avg_conciseness }}</div><div class="score-label">简洁性</div></div>
        </div>
        <!-- Framework raw output -->
        <div v-if="runDetail.framework!=='self'" style="margin-bottom:16px">
          <div style="font-size:14px;font-weight:600;color:#4a3a28;margin-bottom:8px">评测原始输出</div>
          <pre style="background:#faf9f4;border-radius:8px;padding:12px;font-size:12px;max-height:400px;overflow:auto;white-space:pre-wrap">{{ prettyJson(runDetail.report_json) }}</pre>
        </div>
        <!-- Per-question (self evaluator only) -->
        <div v-if="runDetail.framework==='self'" v-for="r in (runDetail.results||[])" :key="r.id"
             style="background:#faf9f4;border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid #e8e2d6">
          <div style="font-weight:700;margin-bottom:8px;color:#4a3a28">{{ r.question_text }}</div>
          <div style="font-size:13px;color:#5c4b38;margin-bottom:8px;max-height:100px;overflow:auto"><strong>回答：</strong>{{ r.agent_response }}</div>
          <div style="font-size:12px;color:#a0936e;margin-bottom:8px">{{ r.judge_reasoning }}</div>
          <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
            <span style="font-size:12px;color:#8a7b66">机器:</span>
            <el-tag size="small" type="warning">相关 {{ r.relevance_score }}</el-tag>
            <el-tag size="small" type="warning">准确 {{ r.accuracy_score }}</el-tag>
            <el-tag size="small" type="warning">完整 {{ r.completeness_score }}</el-tag>
            <el-tag size="small" type="warning">简洁 {{ r.conciseness_score }}</el-tag>
            <el-divider direction="vertical" />
            <span style="font-size:12px;color:#8a7b66">人工:</span>
            <el-select v-for="dim in [{k:'human_relevance',l:'相关'},{k:'human_accuracy',l:'准确'},{k:'human_completeness',l:'完整'},{k:'human_conciseness',l:'简洁'}]"
                       :key="dim.k" size="small" style="width:100px"
                       :model-value="r[dim.k]" @change="v=>doSubmitScore(r.id, dim.k, v)" clearable placeholder="调整">
              <el-option v-for="s in [1,2,3,4,5]" :key="s" :label="`${s}分`" :value="s" />
            </el-select>
          </div>
        </div>
      </div>
    </div>

    <!-- ═══════════════ BANK EDITOR ═══════════════ -->
    <el-dialog v-model="showBankEditor" :title="editingBank?'编辑试卷':'新建试卷'" width="680px" destroy-on-close>
      <el-form label-width="80px">
        <el-form-item label="名称" required><el-input v-model="bankForm.name" placeholder="试卷名称" /></el-form-item>
        <el-form-item label="描述"><el-input v-model="bankForm.description" type="textarea" :rows="2" /></el-form-item>
      </el-form>
      <el-divider>题目列表 ({{ bankForm.questions.length }})</el-divider>
      <div v-for="(q,i) in bankForm.questions" :key="i" style="display:flex;gap:8px;margin-bottom:8px;align-items:flex-start">
        <el-input v-model="q.content" type="textarea" :rows="2" placeholder="问题内容" style="flex:1" />
        <el-input v-model="q.expected_keywords" placeholder="预期关键词" style="width:140px" />
        <el-select v-model="q.category" style="width:110px">
          <el-option value="平台功能与架构" /><el-option value="测试流程" /><el-option value="设备管理" />
          <el-option value="元素定位" /><el-option value="知识库" /><el-option value="异常处理" />
          <el-option value="测试方法" /><el-option value="general" label="通用" />
        </el-select>
        <el-button size="small" type="danger" plain @click="removeQuestionRow(i)">✕</el-button>
      </div>
      <el-button size="small" @click="addQuestionRow" style="margin-top:8px">+ 添加题目</el-button>
      <template #footer>
        <el-button @click="showBankEditor=false">取消</el-button>
        <el-button type="primary" @click="saveBank">保存试卷</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.evaluator-host { padding: 4px 0; }
.view-tab {
  padding: 10px 22px; border: 2px solid #e8e2d6; border-radius: 12px;
  background: #faf9f4; color: #8a7b66; font-size: 15px; font-weight: 700;
  font-family: inherit; cursor: pointer; transition: all 0.2s ease;
}
.view-tab:hover { border-color: #19c8b9; background: #e6f9f6; color: #158a80; }
.view-tab.active { background: #19c8b9; color: #fff; border-color: #19c8b9; box-shadow: 0 4px 14px rgba(25,200,185,0.3); }

/* Mode toggle */
.mode-btn {
  padding: 8px 18px; border: 1.5px solid #e8e2d6; border-radius: 8px;
  background: #fff; color: #8a7b66; font-size: 13px; font-weight: 600;
  font-family: inherit; cursor: pointer; transition: all 0.2s ease;
}
.mode-btn:hover { border-color: #b39ef3; background: #f3f0ff; color: #5b4aa8; }
.mode-btn.active { background: #b39ef3; color: #fff; border-color: #b39ef3; }

/* Benchmark cards */
.bench-card {
  padding: 12px 16px; border: 1.5px solid #e8e2d6; border-radius: 10px;
  background: #faf9f4; cursor: pointer; min-width: 140px; transition: all 0.2s ease;
}
.bench-card:hover { border-color: #b39ef3; background: #f3f0ff; }
.bench-card.selected { border-color: #b39ef3; background: #f3f0ff; box-shadow: 0 2px 8px rgba(179,158,243,0.25); }
.bench-name { font-size: 14px; font-weight: 700; color: #4a3a28; }
.bench-desc { font-size: 11px; color: #a0936e; margin-top: 4px; }

.doc-section { background: #fff; border-radius: 16px; padding: 24px; margin-bottom: 20px; border: 1px solid #f0ebe0; box-shadow: 0 2px 8px rgba(61,52,40,0.04); }
.section-title { font-size: 18px; font-weight: 700; color: #4a3a28; margin-bottom: 20px; padding-bottom: 12px; border-bottom: 2px solid #f0ebe0; display: flex; align-items: center; }
.score-badge { background: #faf9f4; border-radius: 12px; padding: 14px 22px; text-align: center; border: 1px solid #e8e2d6; min-width: 80px; }
.score-num { font-size: 28px; font-weight: 800; }
.score-label { font-size: 12px; color: #a0936e; margin-top: 4px; }
</style>
