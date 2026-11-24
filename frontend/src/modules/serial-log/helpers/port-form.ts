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

export type PortFormCheck =
  { kind: "ok"; payload: PortFormPayload } | { kind: "error"; error: string }

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
