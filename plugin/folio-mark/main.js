/*
 * Folio Mark —— 朱笔：红色下划线（配套 Folio 主题）
 *
 * 作用：给选中的文字套上 <u>…</u>，由主题渲染成一条红色下划线；再按一次去掉。
 * 原文始终是可读的纯文本，能进 git、能跨设备同步、离开 Obsidian 也看得懂。
 *
 * 为什么是插件：Obsidian 核心没有「下划线」命令，主题更绑不了快捷键，
 * 所以和 folio-typewriter 一样做成一个轻量插件 —— 只 require("obsidian")，
 * 不 import CodeMirror，没有构建步骤，main.js 就是最终产物。
 *
 * ⚠️ 边界：HTML 标签内不解析 Markdown，所以 <u>**粗体**</u> 里的加粗、
 *    <u>[[链接]]</u> 里的链接都不会生效。这是 Obsidian 的既定行为。
 */

const { Plugin } = require("obsidian");

const OPEN = "<u>";
const CLOSE = "</u>";

/** 选区本身就已经是 <u>…</u> 整段 */
function isSelfWrapped(text) {
  return text.startsWith(OPEN) && text.endsWith(CLOSE) && text.length >= OPEN.length + CLOSE.length;
}

/** 选区外侧正好贴着标签（前一个字符之后是 <u>，后一个字符之前是 </u>） */
function isTagWrapped(editor, from, to) {
  const first = editor.getLine(from.line);
  const last = editor.getLine(to.line);
  return first.slice(0, from.ch).endsWith(OPEN) && last.slice(to.ch).startsWith(CLOSE);
}

/** 去掉外侧标签：先删后面的闭合、再删前面的开始（从后往前，位置不漂移） */
function unwrap(editor, from, to) {
  editor.replaceRange(
    "",
    { line: to.line, ch: to.ch },
    { line: to.line, ch: to.ch + CLOSE.length }
  );
  editor.replaceRange(
    "",
    { line: from.line, ch: from.ch - OPEN.length },
    { line: from.line, ch: from.ch }
  );
  const singleLine = from.line === to.line;
  editor.setSelection(
    { line: from.line, ch: from.ch - OPEN.length },
    { line: to.line, ch: to.ch - (singleLine ? OPEN.length : 0) }
  );
}

/** 包上标签，并把选区还原到文字本身 */
function wrap(editor, from, to, text) {
  editor.replaceRange(OPEN + text + CLOSE, from, to);
  const singleLine = from.line === to.line;
  editor.setSelection(
    { line: from.line, ch: from.ch + OPEN.length },
    // 单行时闭合标签也在同一行，把结束点推后；多行时 <u> 只加在首行，末行不动
    { line: to.line, ch: to.ch + (singleLine ? OPEN.length : 0) }
  );
}

function toggleUnderline(editor) {
  const from = editor.getCursor("from");
  const to = editor.getCursor("to");
  const text = editor.getSelection();

  // 没有选区：插一对空标签，把光标放到中间
  if (!text) {
    editor.replaceSelection(OPEN + CLOSE);
    const c = editor.getCursor();
    editor.setCursor({ line: c.line, ch: c.ch - CLOSE.length });
    return;
  }

  // 已经包好 —— 三种「包好」的形态都认
  if (isSelfWrapped(text)) {
    const inner = text.slice(OPEN.length, text.length - CLOSE.length);
    editor.replaceSelection(inner);
    const singleLine = from.line === to.line;
    editor.setSelection(
      { line: from.line, ch: from.ch },
      { line: to.line, ch: to.ch - (singleLine ? OPEN.length + CLOSE.length : CLOSE.length) }
    );
    return;
  }
  if (isTagWrapped(editor, from, to)) {
    unwrap(editor, from, to);
    return;
  }

  // 单行：整体包一层
  if (from.line === to.line) {
    wrap(editor, from, to, text);
    return;
  }

  // 多行：空行会截断 HTML 块，有就退化成逐行包裹
  let hasBlank = false;
  for (let n = from.line + 1; n < to.line; n++) {
    if (editor.getLine(n).trim() === "") {
      hasBlank = true;
      break;
    }
  }

  if (!hasBlank) {
    wrap(editor, from, to, text);
    return;
  }

  // 逐行包裹：从后往前替换，前面行的位置才不会被带偏
  for (let n = to.line; n >= from.line; n--) {
    const line = editor.getLine(n);
    const startCh = n === from.line ? from.ch : 0;
    const endCh = n === to.line ? to.ch : line.length;
    const seg = line.slice(startCh, endCh);
    if (seg.trim() === "") continue;
    editor.replaceRange(
      OPEN + seg + CLOSE,
      { line: n, ch: startCh },
      { line: n, ch: endCh }
    );
  }
}

class FolioMark extends Plugin {
  async onload() {
    this.addCommand({
      id: "toggle-underline",
      name: "切换红色下划线",
      hotkeys: [{ modifiers: ["Mod"], key: "U" }],
      editorCallback: (editor) => toggleUnderline(editor),
    });

    // 右键菜单也放一份，忘了快捷键时能摸到
    this.registerEvent(
      this.app.workspace.on("editor-menu", (menu, editor) => {
        menu.addItem((item) =>
          item
            .setTitle("切换红色下划线")
            .setIcon("underline")
            .onClick(() => toggleUnderline(editor))
        );
      })
    );
  }
}

module.exports = FolioMark;
