// 最小 Node 内建模块类型桩。
// 本插件不依赖外部类型包（工作区无 @types/node、npm registry 不可达），
// 仅声明本文件用到的极少数 API；运行时由 Node 提供真实实现。

declare module "node:child_process" {
  export interface ExecFileResult {
    stdout: string;
    stderr: string;
  }
  export function execFile(
    file: string,
    args: string[],
    options: Record<string, unknown>,
    callback: (err: Error | null, result: ExecFileResult) => void,
  ): void;
}

declare module "node:util" {
  export function promisify(fn: (...args: any[]) => void): (...args: any[]) => Promise<any>;
}

declare module "node:path" {
  const path: {
    resolve(...segments: string[]): string;
  };
  export default path;
}
