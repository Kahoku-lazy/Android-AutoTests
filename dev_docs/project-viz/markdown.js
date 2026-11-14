/**
 * 极简 markdown 渲染：只覆盖 AGENTS.md 用到的语法。
 *
 * 支持的语法：ATX 标题、有序/无序列表、表格、围栏代码块、引用、**粗体**、`行内码`。
 * 不足：嵌套列表、图片、脚注会退化成普通段落——够读 AGENTS.md，不追求完整兼容。
 */
(function () {
  "use strict";
  /* 极简 markdown 渲染：只覆盖 AGENTS.md 用到的语法（标题/列表/表格/代码块/粗体/行内码） */
  function escapeHtml(text) {
    return String(text)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function inlineMd(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  }

  function renderMarkdown(source) {
    var lines = String(source || "").split(/\r?\n/);
    var html = [];
    var i = 0;
    var listTag = "";
    var closeList = function () {
      if (listTag) {
        html.push("</" + listTag + ">");
        listTag = "";
      }
    };
    var openList = function (tag) {
      if (listTag !== tag) {
        closeList();
        html.push("<" + tag + ">");
        listTag = tag;
      }
    };
    while (i < lines.length) {
      var line = lines[i];
      var trimmed = line.trim();

      /* 代码块 */
      if (trimmed.indexOf("```") === 0) {
        closeList();
        var code = [];
        i += 1;
        while (i < lines.length && lines[i].trim().indexOf("```") !== 0) {
          code.push(lines[i]);
          i += 1;
        }
        i += 1;
        html.push("<pre><code>" + escapeHtml(code.join("\n")) + "</code></pre>");
        continue;
      }

      /* 表格：| a | b | 后跟 |---|---| */
      if (trimmed.charAt(0) === "|" && i + 1 < lines.length && /^\|[\s:\-|]+\|$/.test(lines[i + 1].trim())) {
        closeList();
        var header = trimmed.replace(/^\|/, "").replace(/\|$/, "").split("|");
        i += 2;
        var rows = [];
        while (i < lines.length && lines[i].trim().charAt(0) === "|") {
          rows.push(lines[i].trim().replace(/^\|/, "").replace(/\|$/, "").split("|"));
          i += 1;
        }
        var table = ["<table><thead><tr>"];
        header.forEach(function (cell) {
          table.push("<th>" + inlineMd(cell.trim()) + "</th>");
        });
        table.push("</tr></thead><tbody>");
        rows.forEach(function (row) {
          table.push("<tr>");
          row.forEach(function (cell) {
            table.push("<td>" + inlineMd(cell.trim()) + "</td>");
          });
          table.push("</tr>");
        });
        table.push("</tbody></table>");
        html.push(table.join(""));
        continue;
      }

      /* 标题 */
      var heading = trimmed.match(/^(#{1,4})\s+(.*)$/);
      if (heading) {
        closeList();
        var level = heading[1].length;
        html.push("<h" + level + ">" + inlineMd(heading[2]) + "</h" + level + ">");
        i += 1;
        continue;
      }

      /* 无序列表 */
      if (/^[-*]\s+/.test(trimmed)) {
        openList("ul");
        html.push("<li>" + inlineMd(trimmed.replace(/^[-*]\s+/, "")) + "</li>");
        i += 1;
        continue;
      }

      /* 有序列表 */
      if (/^\d+\.\s+/.test(trimmed)) {
        openList("ol");
        html.push("<li>" + inlineMd(trimmed.replace(/^\d+\.\s+/, "")) + "</li>");
        i += 1;
        continue;
      }

      /* 引用 */
      if (/^>\s?/.test(trimmed)) {
        closeList();
        html.push("<blockquote>" + inlineMd(trimmed.replace(/^>\s?/, "")) + "</blockquote>");
        i += 1;
        continue;
      }
      if (trimmed === "") {
        closeList();
        i += 1;
        continue;
      }

      closeList();
      html.push("<p>" + inlineMd(trimmed) + "</p>");
      i += 1;
    }
    closeList();
    return html.join("\n");
  }


  window.SimpleMarkdown = { render: renderMarkdown };
})();
