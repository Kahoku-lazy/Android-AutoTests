/**
 * [P0] 必测 — 关键词表单校验（spec: serial-log-module 关键词维护接口）
 *
 * 目录：tests/serial-log/p0/
 * 断言：必填 / 长度 / 范围白名单 / 编号可选非负整数；通过时载荷口径（缺省不带编号）。
 */
import { describe, expect, it } from "vitest"
import { validateKeywordForm } from "@/modules/serial-log/helpers/keyword-form"

const BASE = {
  keyword: "h6601_boot",
  module: "设备开关",
  feature: "H6601开机完成",
  scope: "*",
  featureIdText: "",
}

describe("[P0] validateKeywordForm", () => {
  it("合法输入通过；编号缺省不带字段", () => {
    const check = validateKeywordForm(BASE)
    expect(check.kind).toBe("ok")
    if (check.kind === "ok") {
      expect(check.payload).toEqual({
        keyword: "h6601_boot",
        module: "设备开关",
        feature: "H6601开机完成",
        scope: "*",
      })
    }
  })

  it("去空白后提交；空范围按通用", () => {
    const check = validateKeywordForm({ ...BASE, keyword: "  kw  ", scope: "" })
    expect(check.kind).toBe("ok")
    if (check.kind === "ok") {
      expect(check.payload.keyword).toBe("kw")
      expect(check.payload.scope).toBe("*")
    }
  })

  it("编号给定时带入载荷", () => {
    const check = validateKeywordForm({ ...BASE, featureIdText: "56" })
    expect(check.kind).toBe("ok")
    if (check.kind === "ok") expect(check.payload.feature_id).toBe(56)
  })

  it.each([
    ["keyword", ""],
    ["module", "  "],
    ["feature", ""],
  ])("必填缺失：%s", (field, value) => {
    const check = validateKeywordForm({ ...BASE, [field]: value })
    expect(check.kind).toBe("error")
  })

  it.each([
    ["keyword", "x".repeat(201)],
    ["module", "x".repeat(101)],
    ["feature", "x".repeat(201)],
  ])("超长拒绝：%s", (field, value) => {
    const check = validateKeywordForm({ ...BASE, [field]: value })
    expect(check.kind).toBe("error")
  })

  it.each(["H6601专用", "../x", "a b"])("非法范围拒绝：%s", (scope) => {
    const check = validateKeywordForm({ ...BASE, scope })
    expect(check.kind).toBe("error")
  })

  it("合法 SKU 范围通过", () => {
    const check = validateKeywordForm({ ...BASE, scope: "H6601" })
    expect(check.kind).toBe("ok")
  })

  it.each(["abc", "-1", "1.5"])("非法编号拒绝：%s", (featureIdText) => {
    const check = validateKeywordForm({ ...BASE, featureIdText })
    expect(check.kind).toBe("error")
  })

  it("编号 0 合法", () => {
    const check = validateKeywordForm({ ...BASE, featureIdText: "0" })
    expect(check.kind).toBe("ok")
    if (check.kind === "ok") expect(check.payload.feature_id).toBe(0)
  })
})
