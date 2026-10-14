/*
 * Folio Table —— 阅读视图里让宽表格横向滚动（配套 Folio 主题）
 *
 * 主题的表格策略是「列宽平分（table-layout: fixed）+ 每行最多列数（默认 4）」：
 * 列数超过上限时，各列都守住「可用宽度 ÷ 列数」的下限不肯让位，表格整体变宽，
 * 由**容器**负责横向滚动。
 *
 * 问题在于两个视图给的容器不一样（Obsidian 1.11.7 实测）：
 *   · 实时预览：Obsidian 自己把表格包进 <div class="table-wrapper">，
 *     外层 .cm-table-widget 还有 overflow-x: auto —— 滚动天然可用；
 *   · 阅读视图：**根本没有这层容器**（app.js 里的 createDiv("table-wrapper")
 *     只出现在表格编辑器那条路径），表格是 .markdown-preview-sizer 的直接子元素。
 *     于是宽表格只会撑破栏宽、伸到栏外去，没有任何东西可以滚。
 *
 * 这里用 markdown 后处理器把阅读视图缺的那层容器补上，两个视图行为就一致了。
 * 只依赖 DOM，不 import CodeMirror，没有构建步骤，main.js 就是最终产物。
 */

const { Plugin } = require("obsidian");

class FolioTable extends Plugin {
  onload() {
    this.registerMarkdownPostProcessor((el) => {
      el.querySelectorAll("table").forEach((table) => {
        const parent = table.parentElement;
        // 幂等：已经包过（或 Obsidian 日后自己包了）就跳过
        if (!parent || parent.classList.contains("table-wrapper")) return;

        const wrapper = document.createElement("div");
        wrapper.className = "table-wrapper";
        parent.insertBefore(wrapper, table);
        wrapper.appendChild(table);
      });
    });
  }
}

module.exports = FolioTable;
