// dsh-plugin-arch-gate — 移植自 .claude/hooks/check-boundary.sh
//
// 在 tools/post-execute 观察文件写入：当写入目标匹配 apps/**/*.py 时，
// 运行 `python tools/gen_arch_stats.py --check-boundaries`；
// 检查未通过时把输出作为 additionalContexts 注入会话（模型下一步可见），
// 不阻塞写入本身（PostToolUse 同语义）。
//
// 事件/决策形态对齐官方 @deepseek-ai/dsh-repeat-tool-reminder。
//
// 设计说明：本插件不 import @deepseek-ai/*（运行时包不在工作区，从工作区
// 挂载时 bare specifier 解析不可靠），因此：
//   - 不导出 schemastery Config（cordis 会原样传入 patch.yml 的 config）
//   - 默认值在 apply() 内合并
//   - 类型为本地最小结构声明（见下）

import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

// ── 本地最小类型面（运行时由 cordis 宿主提供真实实现） ──

export interface ArchGateConfig {
  enabled?: boolean;
  workspaceRoot?: string;
  toolNames?: string[];
  pathGlobs?: string[];
  command?: string;
  args?: string[];
  timeoutMs?: number;
  throttleMs?: number;
  passMarker?: string;
  mode?: "inject" | "block";
  maxOutputChars?: number;
}

interface ToolExec {
  name: string;
  arguments?: Record<string, unknown>;
  agent?: object;
}

interface UserMessage {
  content: Array<{ type: "text"; text: string }>;
  source: Record<string, unknown>;
}

interface PostToolDecision {
  kind: "accept" | "block";
  content?: unknown;
  value?: unknown;
  feedback?: string;
  additionalContexts?: UserMessage[];
}

interface Logger {
  warn(...args: unknown[]): void;
  info(...args: unknown[]): void;
}

interface PluginContext {
  on(event: string, listener: (...args: any[]) => any): void;
  logger?: (name: string) => Logger;
}

const execFileAsync = promisify(execFile);

export const name = "arch-gate";

const DEFAULTS: Required<Omit<ArchGateConfig, "enabled">> & { enabled: boolean } = {
  enabled: true,
  workspaceRoot: ".",
  toolNames: ["write", "edit"],
  pathGlobs: ["apps/**/*.py"],
  command: "python",
  args: ["tools/gen_arch_stats.py", "--check-boundaries"],
  timeoutMs: 30000,
  throttleMs: 30000,
  passMarker: "零违规",
  mode: "inject",
  maxOutputChars: 4000,
};

const PLUGIN_SOURCE = { kind: "plugin", name: "dsh-plugin-arch-gate" };

/** glob → RegExp（支持 ** 与 *，路径统一为 / 分隔） */
function globToRegExp(glob: string): RegExp {
  let re = "^";
  for (let i = 0; i < glob.length; i += 1) {
    const c = glob[i];
    if (c === "*" && glob[i + 1] === "*") {
      re += ".*";
      i += 1;
    } else if (c === "*") {
      re += "[^/]*";
    } else if (c === "?") {
      re += "[^/]";
    } else {
      re += c.replace(/[.+^${}()|[\]\\]/g, "\\$&");
    }
  }
  return new RegExp(`${re}$`);
}

/** 从写入工具的 arguments 提取目标路径（write/edit 均为 file_path） */
function targetPath(arguments_: Record<string, unknown> | undefined): string | undefined {
  const p = arguments_?.file_path ?? arguments_?.path;
  return typeof p === "string" ? p : undefined;
}

function createNotice(text: string, summary: string): UserMessage {
  return {
    content: [{ type: "text", text }],
    source: { ...PLUGIN_SOURCE, form: "notice", summary },
  };
}

function prependContext(msg: UserMessage, arr?: UserMessage[]): UserMessage[] {
  return [msg, ...(arr ?? [])];
}

export function apply(ctx: PluginContext, raw: ArchGateConfig = {}): void {
  const config = { ...DEFAULTS, ...raw };
  if (!config.enabled) return;

  const logger: Logger = ctx.logger?.(name) ?? console;
  const root = path.resolve(config.workspaceRoot);
  const patterns = config.pathGlobs.map(globToRegExp);

  // 节流状态：per-agent 上次检查时间（agent/pre-step 出现用户消息时重置）
  const lastRun = new WeakMap<object, number>();

  function matches(exec: ToolExec): boolean {
    if (!config.toolNames.includes(exec.name)) return false;
    const p = targetPath(exec.arguments);
    if (!p) return false;
    const normalized = p.replaceAll("\\", "/");
    return patterns.some((re) => re.test(normalized));
  }

  async function runCheck(exec: ToolExec): Promise<UserMessage | undefined> {
    const now = Date.now();
    const prev = exec.agent ? lastRun.get(exec.agent) : undefined;
    if (prev !== undefined && now - prev < config.throttleMs) return undefined;
    if (exec.agent) lastRun.set(exec.agent, now);

    try {
      const { stdout, stderr } = await execFileAsync(config.command, config.args, {
        cwd: root,
        timeout: config.timeoutMs,
        maxBuffer: 1024 * 1024,
        windowsHide: true,
      });
      const output = `${stdout ?? ""}${stderr ?? ""}`.trim();
      if (output.includes(config.passMarker)) return undefined;
      return createNotice(
        `arch-gate：写入 ${targetPath(exec.arguments)} 后边界检查未通过。\n${output.slice(0, config.maxOutputChars)}`,
        `arch-gate 边界检查未通过（${exec.name}）`,
      );
    } catch (err) {
      const { code, killed } = err as { code?: string; killed?: boolean };
      if (code === "ETIMEDOUT" || killed) {
        return createNotice(
          `arch-gate：边界检查超时（${config.timeoutMs}ms），请手动运行 ${config.command} ${config.args.join(" ")}。`,
          "arch-gate 检查超时",
        );
      }
      logger.warn("arch-gate check failed:", (err as Error)?.message ?? err);
      return undefined; // 检查工具自身异常时不打扰会话
    }
  }

  ctx.on("tools/post-execute", async (exec: ToolExec, _result: unknown, next: () => Promise<PostToolDecision>) => {
    const downstream = await next();
    if (!matches(exec)) return downstream;
    const notice = await runCheck(exec);
    if (!notice) return downstream;
    if (config.mode === "block") {
      return {
        kind: "block",
        feedback: notice.content[0].text,
        additionalContexts: prependContext(notice, downstream.additionalContexts),
      };
    }
    if (downstream.kind === "block") {
      return {
        kind: "block",
        feedback: downstream.feedback,
        additionalContexts: prependContext(notice, downstream.additionalContexts),
      };
    }
    return { ...downstream, additionalContexts: prependContext(notice, downstream.additionalContexts) };
  });

  ctx.on("agent/pre-step", (payload: { agent: object; messages: Array<{ source?: { kind?: string } }> }, next: () => Promise<unknown>) => {
    if (payload.messages.some((message) => message.source?.kind === "user")) lastRun.delete(payload.agent);
    return next();
  });
}

export default apply;
