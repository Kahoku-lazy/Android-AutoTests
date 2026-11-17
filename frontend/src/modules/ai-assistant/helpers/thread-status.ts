/**
 * 对话栏状态的中文标签：对话页页头与左栏共用一份，避免两处文案漂移。
 */

const STATUS_LABEL: Record<string, string> = {
  idle: "空闲",
  running: "进行中",
  done: "已完成",
  cancelled: "已取消",
  interrupted: "已中断",
}

/** 未知状态原样返回，便于排查后端新增的状态值。 */
export function threadStatusLabel(value: string): string {
  return STATUS_LABEL[value] || value
}
