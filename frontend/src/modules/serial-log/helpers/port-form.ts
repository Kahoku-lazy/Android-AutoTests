/** port-form — 新增 / 编辑端口表单的纯校验（无状态、无 HTTP）
 *
 * 与后端口径一致：端口 1–65535 整数、不与已登记端口重号（编辑模式除外）、
 * SKU 必填 ≤100 字符、波特率正整数。弹窗提交前与 composable 提交前共用。
 */

import {
  PORT_ERR_BAUD_INVALID,
  PORT_ERR_PORT_DUPLICATE,
  PORT_ERR_PORT_REQUIRED,
  PORT_ERR_SKU_REQUIRED,
  PORT_ERR_SKU_TOO_LONG,
} from "../constants"

export interface PortFormInput {
  portText: string
  sku: string
  baudChoice: number | "custom"
  baudCustomText: string
}

export interface PortFormPayload {
  port: number
  sku: string
  baud: number
}

/** 校验结果：字符串判别（本仓 tsconfig 关闭 strictNullChecks，布尔字面量不收窄） */
export type PortFormCheck =
  { kind: "ok"; payload: PortFormPayload } | { kind: "error"; error: string }

/** 校验表单输入；编辑模式下端口号取 editPort，不做端口校验与重号检查。 */
export function validatePortForm(
  input: PortFormInput,
  opts: { editMode: boolean; editPort?: number; existingPorts: number[] },
): PortFormCheck {
  let port: number
  if (opts.editMode) {
    port = Number(opts.editPort)
  } else {
    port = Number(input.portText)
    if (!Number.isInteger(port) || port < 1 || port > 65535) {
      return { kind: "error", error: PORT_ERR_PORT_REQUIRED }
    }
    if (opts.existingPorts.includes(port)) {
      return { kind: "error", error: `端口 ${port} ${PORT_ERR_PORT_DUPLICATE}` }
    }
  }
  const sku = input.sku.trim()
  if (!sku) return { kind: "error", error: PORT_ERR_SKU_REQUIRED }
  if (sku.length > 100) return { kind: "error", error: PORT_ERR_SKU_TOO_LONG }
  const baud =
    input.baudChoice === "custom" ? Number(input.baudCustomText) : Number(input.baudChoice)
  if (!Number.isInteger(baud) || baud < 1) return { kind: "error", error: PORT_ERR_BAUD_INVALID }
  return { kind: "ok", payload: { port, sku, baud } }
}
