const STATUS_LABEL: Record<string, string> = {
  idle: "空闲",
  running: "进行中",
  done: "已完成",
  cancelled: "已取消",
  interrupted: "已中断",
}

export function threadStatusLabel(value: string): string {
  return STATUS_LABEL[value] || value
}
