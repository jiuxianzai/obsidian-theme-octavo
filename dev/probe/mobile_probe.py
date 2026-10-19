#!/usr/bin/env python3
"""手机视口探针 —— 把真实 Obsidian 的视口压到 393×852（iPhone 15/16 Pro）、
补上 `is-mobile is-phone is-ios` 三个类，量「手机版 app.css + 主题」叠加之后的真实布局。

为什么不是静态复现页：手机上真正变的不只是窗口宽度 —— Obsidian 的移动端 CSS
（`--file-margins-x: 24px`、`.cm-table-widget { --table-drag-handle-size: 24px }`、
属性面板的 `translateX(-12px)` 等等）都挂在 `is-mobile` / `is-phone` 这两个类下，
静态页很难同时对上「类 + 宽度 + 真实 DOM」三件事。这里直接开真 App、用 CDP
的 `Emulation.setDeviceMetricsOverride` 改视口，DOM 与 app.css 都是真的。

用法：
    python3 dev/probe/mobile_probe.py                 # 全部检查
    python3 dev/probe/mobile_probe.py --check geo     # 只看编辑器横向几何
    python3 dev/probe/mobile_probe.py --check table   # 只看表格单元格（有/无光标）
    python3 dev/probe/mobile_probe.py --check formats # 只看各类 markdown 格式
    python3 dev/probe/mobile_probe.py --width 375     # 换机型宽度
    python3 dev/probe/mobile_probe.py --keep          # 留着实例自己接 DevTools
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE))
import probe  # noqa: E402  （复用 CDP 客户端与临时 vault 搭法）

PORT = 9344
WORKDIR = Path('/tmp/folio-mobile-probe')
NOTE_TABLE = '手机表格.md'          # 复刻用户截图里那张 4 列表（表格检查用）
NOTE_PROBE_TABLE = '表格测试.md'    # 仓库原有的表格 fixture（长格/短格/4 列/6 列）
NOTE_FORMATS = '移动端格式测试.md'

# --------------------------------------------------------------------------- #
# 注入渲染进程的量测脚本
# --------------------------------------------------------------------------- #
# 手机视口：只加类、不改 DOM。宽度用 CDP 的 deviceMetrics 改。
MOBILE_CLASSES = r"""
(() => {
  document.body.classList.add('is-mobile', 'is-phone', 'is-ios', 'mod-ios');
  document.body.classList.remove('is-tablet');
  // 桌面外壳里没有手机版的 .mod-visible 标记，而 app.css 有一条
  // `.is-phone .mod-root .workspace-split:not(.mod-visible) { display: none }`
  // —— 不补这个类，主编辑区会被整块 display:none（量到的宽度全是 0）。
  // 手机 App 是真会加这个类的，所以这只是把桌面外壳补齐成手机的样子，
  // 不算改主题的观测对象。
  document.querySelectorAll('.mod-root .workspace-split, .mod-root .workspace-tabs')
    .forEach(el => el.classList.add('mod-visible'));
  return document.body.className;
})()
"""

OPEN = r"""
(async (name) => {
  document.body.classList.add('folio-justify');
  const f = app.vault.getAbstractFileByPath(name);
  if (!f) return 'no-file';
  await app.workspace.getLeaf().openFile(f);
  await new Promise(r => setTimeout(r, 900));
  return 'ok';
})(%s)
"""

SET_MODE = r"""
(async (mode) => {
  const leaf = app.workspace.getMostRecentLeaf();
  await leaf.setViewState({ type: 'markdown', state: { file: %s, mode: mode } });
  await new Promise(r => setTimeout(r, 900));
  return leaf.getViewState().state.mode;
})(%s)
"""

# —— 检查 A：编辑器横向几何 —— 从 .cm-scroller 一路到表格，每一层的
#     宽度 / 内边距 / 外边距 / 可否横滚都列出来。手机上的「正文两边留白」
#     是这几层加出来的，表格还有自己的把手槽（手机 24px，桌面 16px）。
GEO = r"""
(() => {
  const r2 = n => +(+n).toFixed(2);
  const vw = document.documentElement.clientWidth;
  const cs = getComputedStyle(document.body);
  const out = {
    viewport: vw,
    bodyClass: document.body.className,
    vars: {
      fileMarginsX: cs.getPropertyValue('--file-margins-x').trim(),
      fileMarginsY: cs.getPropertyValue('--file-margins-y').trim(),
      dragHandle: cs.getPropertyValue('--table-drag-handle-size').trim(),
      tableCols: cs.getPropertyValue('--folio-table-cols').trim(),
      version: cs.getPropertyValue('--folio-version').trim(),
      contentWidth: cs.getPropertyValue('--folio-content-width').trim(),
    },
    chain: [],
  };
  const scroller = document.querySelector('.markdown-source-view.mod-cm6 .cm-scroller');
  if (!scroller) return { error: '找不到 .cm-scroller' };
  const chain = [scroller, scroller.querySelector('.cm-sizer'), scroller.querySelector('.cm-contentContainer'),
                 scroller.querySelector('.cm-content')].filter(Boolean);
  const widget = scroller.querySelector('.cm-table-widget');
  if (widget) chain.push(widget, widget.querySelector('.table-wrapper'), widget.querySelector('table'));
  for (const el of chain) {
    const c = getComputedStyle(el);
    const b = el.getBoundingClientRect();
    out.chain.push({
      sel: (el.className.toString().split(/\s+/).filter(Boolean).slice(0, 3).join('.')) || el.tagName,
      x: r2(b.left), w: r2(b.width), cw: el.clientWidth, sw: el.scrollWidth,
      pad: c.padding, mar: c.margin, ovx: c.overflowX,
      canScroll: (() => { const s = el.scrollLeft; el.scrollLeft = 99999; const a = el.scrollLeft; el.scrollLeft = s; return r2(a - s); })(),
    });
  }
  const line = scroller.querySelector('.cm-content .cm-line');
  if (line) out.textX = r2(line.getBoundingClientRect().left);
  // 表格的两个「+」把手：列把手挂在 .table-wrapper 的 inset-inline-start: 100% 上，
  // 所以 wrapper 一旦不等于表格宽（列数 > 设定值时就是这样），它就会叠在表格内容上。
  const wrap = scroller.querySelector('.cm-table-widget .table-wrapper');
  const btn = scroller.querySelector('.cm-table-widget .table-col-btn');
  if (wrap && btn) {
    const wb = wrap.getBoundingClientRect(), bb = btn.getBoundingClientRect();
    out.colBtn = { x: r2(bb.left), w: r2(bb.width),
                   wrapRight: r2(wb.right), wrapW: r2(wb.width) };
  }
  const tbl = scroller.querySelector('.cm-table-widget table');
  if (tbl) {
    const b = tbl.getBoundingClientRect();
    const tr = tbl.querySelector('tr');
    const wid = scroller.querySelector('.cm-table-widget');
    out.table = { x: r2(b.left), w: r2(b.width), cols: tr ? tr.children.length : 0,
                  colW: tr ? r2(tr.children[0].getBoundingClientRect().width) : null,
                  widgetX: wid ? r2(wid.getBoundingClientRect().left) : null,
                  widgetW: wid ? r2(wid.getBoundingClientRect().width) : null };
  }
  return out;
})()
"""

# —— 检查 B：单元格「没光标 / 有光标」——手机上真正出问题的地方。
#     除了 probe.py 那几项，这里把里层编辑器每一层的宽度与内边距都摊开，
#     再看光标（.cm-cursor）到底落在哪个 x 上 —— 「一格一行」的成因就在这几行里。
CELL = r"""
(() => {
  const r2 = n => +(+n).toFixed(2);
  const tbl = [...document.querySelectorAll('.cm-table-widget table')]
    .filter(t => t.getBoundingClientRect().width > 0)[0];
  if (!tbl) return { error: '没找到表格' };
  const scroller = document.querySelector('.markdown-source-view .cm-scroller');
  const content = scroller ? scroller.querySelector('.cm-content') : null;
  const textOf = td => {
    const w = document.createTreeWalker(td, NodeFilter.SHOW_TEXT, { acceptNode(n) {
      const p = n.parentElement; if (!p) return NodeFilter.NULL;
      const cs = getComputedStyle(p);
      if (cs.display === 'none' || cs.visibility === 'hidden') return NodeFilter.FILTER_REJECT;
      return n.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    }});
    return w.nextNode();
  };
  const metrics = td => {
    const n = textOf(td);
    const box = td.getBoundingClientRect();
    const o = { text: (n?.textContent || '').trim(), tdW: r2(box.width), focused: !!td.querySelector('.cm-editor') };
    if (n) {
      const rects = [];
      for (let i = 0; i < n.length; i++) {
        const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
        const b = r.getBoundingClientRect();
        rects.push({ top: Math.round(b.top), left: r2(b.left), right: r2(b.right) });
      }
      const vlines = [];
      for (const r of rects) {
        const last = vlines[vlines.length - 1];
        if (last && Math.abs(last.top - r.top) < 3) { last.n++; last.right = Math.max(last.right, r.right); }
        else vlines.push({ top: r.top, n: 1, right: r.right });
      }
      o.firstCharLeft = r2(rects[0].left - box.left);
      o.lines = vlines.map(v => v.n);
      o.lastRight = r2(vlines[vlines.length - 1].right - box.left);
    }
    const c = td.querySelector('.cm-editor');
    if (c) {
      const layers = [];
      const walk = e => {
        const cs = getComputedStyle(e);
        layers.push({ sel: e.tagName.toLowerCase() + '.' + (e.className.toString().split(/\\s+/)[0] || ''),
                      w: r2(e.getBoundingClientRect().width), cw: e.clientWidth, sw: e.scrollWidth,
                      padL: cs.paddingLeft, padR: cs.paddingRight, ovx: cs.overflowX,
                      letterSpacing: cs.letterSpacing, textIndent: cs.textIndent,
                      textAlign: cs.textAlign, textJustify: cs.textJustify,
                      fontSize: cs.fontSize, lineHeight: cs.lineHeight });
        [...e.children].forEach(walk);
      };
      walk(c);
      o.layers = layers;
      const cur = td.querySelector('.cm-cursor');
      o.cursor = cur ? { x: r2(cur.getBoundingClientRect().left - box.left),
                         w: r2(cur.getBoundingClientRect().width),
                         h: r2(cur.getBoundingClientRect().height) } : null;
      const line = td.querySelector('.cm-line');
      if (line) {
        const cs = getComputedStyle(line);
        o.lineStyle = { letterSpacing: cs.letterSpacing, textIndent: cs.textIndent,
                        textAlign: cs.textAlign, textJustify: cs.textJustify,
                        paddingLeft: cs.paddingLeft, fontSize: cs.fontSize, lineHeight: cs.lineHeight };
        o.lineBox = { w: r2(line.getBoundingClientRect().width), h: r2(line.getBoundingClientRect().height) };
      }
    }
    const wrap = td.querySelector('.table-cell-wrapper:not([style*="display: none"])') || td;
    o.wrapperPad = getComputedStyle(wrap).paddingLeft + ' / ' + getComputedStyle(wrap).paddingRight;
    o.tdPad = getComputedStyle(td).paddingLeft + ' / ' + getComputedStyle(td).paddingRight;
    return o;
  };
  const rows = [...tbl.querySelectorAll('tr')];
  const cells = [];
  rows.forEach((tr, ri) => [...tr.children].forEach(td => cells.push(Object.assign(metrics(td), { row: ri }))));
  return { viewport: document.documentElement.clientWidth,
           scrollerPadX: scroller ? getComputedStyle(scroller).paddingLeft + ' / ' + getComputedStyle(scroller).paddingRight : null,
           contentPadX: content ? getComputedStyle(content).paddingLeft + ' / ' + getComputedStyle(content).paddingRight : null,
           tableW: r2(tbl.getBoundingClientRect().width),
           cols: rows.length ? rows[0].children.length : 0,
           cells };
})()
"""
# CodeMirror 只渲染视口附近的块：表格在笔记中段时压根不在 DOM 里，
# 必须先把它滚进视口（否则量到的全是「没有表格」）。
SCROLL_TO_TABLE = r"""
(async () => {
  const sc = document.querySelector('.markdown-source-view.mod-cm6 .cm-scroller');
  if (!sc) return 'no-scroller';
  const hit = () => [...document.querySelectorAll('.cm-table-widget table')]
        .find(t => t.getBoundingClientRect().width > 0) || null;
  if (!hit()) {
    const step = Math.max(200, sc.clientHeight * 0.6);
    let guard = 0;
    for (let top = 0; top <= sc.scrollHeight && guard++ < 60; top += step) {
      sc.scrollTop = top;
      await new Promise(r => requestAnimationFrame(() => setTimeout(r, 60)));
      if (hit()) break;
    }
  }
  const t = hit();
  if (!t) return 'no-table';
  t.scrollIntoView({ block: 'center' });
  await new Promise(r => requestAnimationFrame(() => setTimeout(r, 120)));
  return 'ok';
})()
"""

CELL_CENTER = r"""
((needle) => {
  const tbl = document.querySelector('.cm-table-widget table');
  if (!tbl) return null;
  const cells = [...tbl.querySelectorAll('td')];
  if (!cells.length) return null;
  const pick = cells.find(td => (td.textContent || '').includes(needle)) || cells[0];
  pick.scrollIntoView({ block: 'center' });
  const r = pick.getBoundingClientRect();
  return { x: +(r.left + r.width / 2).toFixed(1), y: +(r.top + r.height / 2).toFixed(1),
           text: (pick.textContent || '').trim() };
})(%s)
"""

# —— 检查 C：各类格式在手机视口下的体检 ——
#     1) 元素有没有伸出视口 / 被哪个祖先裁掉（overflow hidden|clip）/ 要横滚多少
#     2) 该横向滚的（代码块、宽表格）到底能不能滚
#     3) 几个只在手机上才有的位移：标题折叠箭头（-20px）、属性面板（-12px 加宽）
#
#     阅读视图是**分段懒渲染**的：不在视口里的段落压根不在 DOM 里，所以这里把整篇
#     从上到下滚一遍，每段都扫一次，最后按「问题最多」的那次报。
FORMATS = r"""
(async () => {
  const r2 = n => +(+n).toFixed(2);
  const vw = document.documentElement.clientWidth;
  // 只认**当前这个叶子**里的元素：DOM 里同时存在别的叶子（上一个笔记的视图、
  // 隐藏的阅读/编辑视图），全局 querySelector 会挑到它们，量出一堆假的「缺元素」。
  const LEAF = document.querySelector('.workspace-leaf.mod-active') || document;
  // 一个叶子里可能同时挂着实时预览与阅读视图（切模式后旧的那个还在 DOM 里），
  // 所以先问 App 当前是哪个模式，再只在这个模式的那棵子树里量。
  let mode = 'source';
  try { mode = app.workspace.getMostRecentLeaf().getViewState().state.mode || 'source'; } catch (e) {}
  const isPreview = mode === 'preview';
  const ROOT = LEAF.querySelector(isPreview ? '.markdown-preview-view' : '.markdown-source-view.mod-cm6') || LEAF;
  const scroller = ROOT.querySelector('.cm-scroller') || ROOT;
  const visible = el => { const b = el.getBoundingClientRect(); return b.width > 0 && b.height > 0; };

  // 只看**最近**的那个非 visible 祖先：auto/scroll 说明滚得到，不算问题；
  // hidden/clip 才是真裁掉。远层祖先不用管 —— 中间那层已经把它夹住了。
  const nearestOverflow = el => {
    let p = el.parentElement;
    while (p && p !== document.body) {
      const cs = getComputedStyle(p);
      if (cs.overflowX !== 'visible' || cs.overflowY !== 'visible')
        return { el: p, ox: cs.overflowX, oy: cs.overflowY };
      p = p.parentElement;
    }
    return null;
  };

  const measure = (label, el) => {
    const b = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const o = { label, x: r2(b.left), w: r2(b.width), right: r2(b.right),
                fontSize: cs.fontSize, lineHeight: cs.lineHeight,
                outLeft: r2(-b.left), outRight: r2(b.right - vw),
                scrollX: r2(el.scrollWidth - el.clientWidth), ovx: cs.overflowX,
                text: (el.textContent || '').trim().slice(0, 16), issues: [] };
    const near = nearestOverflow(el);
    const reachable = near && (near.ox === 'auto' || near.ox === 'scroll' || near.oy === 'auto' || near.oy === 'scroll');
    if (o.outLeft > 0.5 || o.outRight > 0.5) {
      if (reachable) o.notes = [`超出视口（左 ${o.outLeft} / 右 ${o.outRight}px），由 .${near.el.className.toString().split(/\s+/)[0]} 横滚可达`];
      else o.issues.push(`伸出视口左缘 ${o.outLeft}px / 右缘 ${o.outRight}px，且没有任何可滚的祖先`);
    }
    if (near && near.ox !== 'visible' && !reachable) {
      // 裁剪框可以靠 overflow-clip-margin 往外放（主题就用它给折叠箭头留位置），
      // 判定时必须把这个外扩量算进去，否则会把「本来就没裁掉」的东西报成被裁。
      const pb = near.el.getBoundingClientRect();
      const margin = parseFloat(getComputedStyle(near.el).overflowClipMargin) || 0;
      const overL = r2(pb.left - b.left - margin), overR = r2(b.right - pb.right - margin);
      if (overL > 0.5 || overR > 0.5)
        o.issues.push(`✂ 被 .${near.el.className.toString().split(/\s+/).slice(0, 2).join('.')} 裁掉`
                      + `（overflow-x: ${near.ox}${margin ? `，裁剪框外扩 ${margin}px` : ''}，左右超出 ${overL} / ${overR}px）`);
    }
    // 盒子本身不是滚动盒（overflow-x: visible）时，「内容比盒子宽」只是它的
    // 子元素按设计外扩（属性面板就会左右各外扩 12px），不算问题，记一笔即可。
    if (o.scrollX > 2 && el.tagName !== 'INPUT') {
      const msg = `内容比盒子宽 ${o.scrollX}px（overflow-x: ${o.ovx}）`;
      const margin = parseFloat(getComputedStyle(el).overflowClipMargin) || 0;
      if (o.ovx === 'visible' || o.ovx === 'auto' || o.ovx === 'scroll'
          || (o.ovx !== 'visible' && o.scrollX <= margin)) {
        // visible：子元素按设计外扩（属性面板左右各 12px）；
        // auto / scroll：本来就是给人滚的（代码块、宽表格）；
        // clip/hidden 但裁剪框外扩得比溢出还多：没裁着。
        (o.notes = o.notes || []).push(msg);
      } else {
        o.issues.push(msg);
      }
    }
    return o;
  };

  const list = [
    ['属性面板', '.metadata-container'],
    ['属性内容', '.metadata-content'],
    ['行内标题', '.inline-title'],
    ['H1', 'h1, .HyperMD-header-1'],
    ['H3', 'h3, .HyperMD-header-3'],
    ['正文段', 'p, .cm-line:not([class*="HyperMD-"])'],
    ['引用块', 'blockquote, .HyperMD-quote'],
    ['标注块', '.callout'],
    ['标注块标题', '.callout-title'],
    ['标注块内容', '.callout-content'],
    ['代码块', 'pre'],
    ['代码块内层', 'pre > code'],
    ['复制按钮', 'button.copy-code-button'],
    ['列表', 'ul, ol, .HyperMD-list-line'],
    ['任务框', 'input[type=checkbox]'],
    ['表格外层', '.table-wrapper'],
    ['表格', 'table'],
    ['分隔线', 'hr, .cm-hr'],
    ['标签', '.tag, .cm-hashtag'],
    ['行内代码', 'code:not(pre code)'],
    ['数学块', '.math-block, .math'],
    ['脚注', '.footnotes, .footnote-ref'],
    ['嵌入', '.internal-embed, .markdown-embed'],
    ['折叠箭头', '.heading-collapse-indicator, .collapse-indicator, .cm-fold-indicator'],
    ['编辑器滚动盒', '.cm-scroller'],
    ['栏容器', '.cm-sizer, .markdown-preview-sizer'],
  ];

  const best = new Map();     // label -> 最差的一次
  const seen = new Map();     // label -> 见过几个
  const scrollers = new Map();
  const scan = () => {
    for (const [label, sel] of list) {
      for (const el of ROOT.querySelectorAll(sel)) {
        if (!visible(el)) continue;
        seen.set(label, (seen.get(label) || 0) + 1);
        const m = measure(label, el);
        const cur = best.get(label);
        if (!cur || m.issues.length > cur.issues.length) best.set(label, m);
      }
    }
    ROOT.querySelectorAll('pre > code, .callout-content, table, .table-wrapper, .cm-table-widget, .markdown-preview-view')
      .forEach(el => {
        if (!visible(el)) return;
        const can = (() => { const s = el.scrollLeft; el.scrollLeft = 99999; const a = el.scrollLeft; el.scrollLeft = s; return r2(a - s); })();
        const over = r2(el.scrollWidth - el.clientWidth);
        if (over > 0.5 || can > 0.5) {
          const key = el.tagName.toLowerCase() + '.' + (el.className.toString().split(/\s+/)[0] || '');
          const cur = scrollers.get(key);
          if (!cur || over > cur.over) scrollers.set(key, { key, over, can, ovx: getComputedStyle(el).overflowX });
        }
      });
  };

  if (scroller) {
    const step = Math.max(200, scroller.clientHeight * 0.6);
    let top = 0, guard = 0;
    while (top <= scroller.scrollHeight + step && guard++ < 200) {
      scroller.scrollTop = top;
      await new Promise(r => requestAnimationFrame(() => setTimeout(r, 70)));
      scan();
      top += step;
    }
    scroller.scrollTop = 0;
    await new Promise(r => requestAnimationFrame(() => setTimeout(r, 70)));
    scan();
  } else {
    scan();
  }
  return { viewport: vw, mode: isPreview ? 'preview' : 'source',
           items: list.map(([label]) => best.get(label) ? Object.assign(best.get(label), { seen: seen.get(label) })
                                                        : { label, missing: true }),
           scrollers: [...scrollers.values()] };
})()
"""


# —— 检查 D：阅读视图的「横向夹取」夹对地方了没有 ——
#     主题把正文的横向夹取从 .markdown-preview-sizer 挪到了 .markdown-preview-view，
#     这一组断言就是那次挪动的验收：面板横滚不动、竖向照滚、折叠箭头与属性面板
#     不再被裁。
CLAMP = r"""
(async () => {
  const r2 = n => +(+n).toFixed(2);
  const leaf = document.querySelector('.workspace-leaf.mod-active');
  const pv = leaf.querySelector('.markdown-preview-view');
  if (!pv) return { error: '当前不是阅读视图' };
  const sizer = pv.querySelector('.markdown-preview-sizer');
  const cs = getComputedStyle(pv);
  const scs = getComputedStyle(sizer);
  const tryScroll = (el, axis) => {
    const key = axis === 'x' ? 'scrollLeft' : 'scrollTop';
    const before = el[key];
    el[key] = 99999;
    const after = el[key];
    el[key] = before;
    return r2(after - before);
  };
  // 命中测试：被裁掉的东西 elementFromPoint 点不到。折叠箭头默认 opacity: 0，
  // 但 opacity 不影响命中 —— 这里量的正是「有没有被裁掉」。
  // 只有落在**视口内**的元素才谈得上命中（elementFromPoint 对视口外的点一律
  // 返回 null）；所以这里返回 null 表示「滚出视口了，没测」，不是被裁。
  const hit = el => {
    const b = el.getBoundingClientRect();
    const cx = b.left + b.width / 2, cy = b.top + b.height / 2;
    // 贴边（尤其最后 1~2px）时 elementFromPoint 会返回 null，那不是被裁，是没测到
    if (cy < 2 || cy > document.documentElement.clientHeight - 2) return null;
    // 手机上的标题条是 position: fixed 的不透明条：落在它下面的东西是「被顶栏盖住」
    // （往下滚一点就出来了），跟「被祖先裁掉」不是一回事，这里不测。
    const hdr = document.querySelector('.workspace-leaf.mod-active .view-header');
    if (hdr) {
      const hb = hdr.getBoundingClientRect();
      if (hb.height > 0 && cy < hb.bottom) return null;
    }
    const t = document.elementFromPoint(cx, cy);
    const mine = !!(t && (t === el || el.contains(t) || t.contains(el)));
    if (!mine && t) {
      // 上面漂着一层手机 UI（顶栏 / 侧栏开关那个药丸按钮）—— 那是「被盖住」，
      // 不是「被祖先裁掉」：往下滚一屏就出来了，不判失败。
      let p = t;
      while (p && p !== document.body) {
        const cs = getComputedStyle(p);
        if (cs.position === 'fixed' || cs.position === 'absolute') return null;
        p = p.parentElement;
      }
    }
    return mine;
  };
  const box = el => { const b = el.getBoundingClientRect(); return { l: r2(b.left), r: r2(b.right), w: r2(b.width) }; };
  const pvBox = box(pv);
  const out = {
    mode: 'preview',
    panel: { cls: pv.className.toString().split(/\s+/).slice(0, 2).join('.'),
             ovx: cs.overflowX, ovy: cs.overflowY,
             canScrollX: tryScroll(pv, 'x'), canScrollY: tryScroll(pv, 'y'),
             scrollH: pv.scrollHeight, clientH: pv.clientHeight,
             xOverflow: r2(pv.scrollWidth - pv.clientWidth) },
    sizer: { ovx: scs.overflowX, clipMargin: scs.overflowClipMargin, ...box(sizer) },
    arrows: [], meta: null,
  };
  sizer.querySelectorAll('.heading-collapse-indicator, .list-collapse-indicator').forEach(el => {
    const b = el.getBoundingClientRect();
    if (!b.width) return;
    const sb = sizer.getBoundingClientRect();
    out.arrows.push({ cls: el.className.toString().split(/\s+/)[0],
                      x: r2(b.left), w: r2(b.width),
                      outLeftOfSizer: r2(sb.left - b.left),
                      outLeftOfPanel: r2(pvBox.l - b.left),
                      hit: hit(el) });
  });
  const m = sizer.querySelector('.metadata-content');
  if (m) {
    const b = m.getBoundingClientRect();
    const sb = sizer.getBoundingClientRect();
    out.meta = { x: r2(b.left), w: r2(b.width),
                 outsideSizer: [r2(sb.left - b.left), r2(b.right - sb.right)],
                 hit: hit(m),
                 insidePanel: b.left >= pvBox.l - 0.5 && b.right <= pvBox.r + 0.5 };
  }
  return out;
})()
"""


# --------------------------------------------------------------------------- #
def setup(workdir: Path, theme: Path | None = None, snippets: list[Path] | None = None) -> Path:
    """probe.setup 只拷表格 fixture，这里补上格式 fixture；theme / snippets 可另指定。

    snippets 走的是 Obsidian 真正加载片段的路径（拷进 .obsidian/snippets/ 并写进
    appearance.json 的 enabledCssSnippets）—— 片段在主题**之后**加载，手机上的
    folio-mobile.css 就是靠这个顺序压过主题规则的，所以必须按真路数来。"""
    profile = probe.setup(workdir)
    if theme is not None:
        shutil.copyfile(theme, workdir / 'vault' / '.obsidian' / 'themes' / 'Folio' / 'theme.css')
    if snippets:
        snip_dir = workdir / 'vault' / '.obsidian' / 'snippets'
        snip_dir.mkdir(parents=True, exist_ok=True)
        names = []
        for s in snippets:
            shutil.copyfile(s, snip_dir / s.name)
            names.append(s.stem)   # appearance.json 里存的是**不带扩展名**的名字
        app = workdir / 'vault' / '.obsidian' / 'appearance.json'
        cfg = json.loads(app.read_text()) if app.exists() else {}
        cfg['enabledCssSnippets'] = names
        app.write_text(json.dumps(cfg, ensure_ascii=False))
    vault = workdir / 'vault'
    for name in (NOTE_FORMATS, NOTE_TABLE):
        shutil.copyfile(HERE / 'fixtures' / name, vault / name)
    return profile


def boot(cdp: 'probe.CDP', width: int, height: int, dpr: int = 3):
    cdp.call('Emulation.setDeviceMetricsOverride', {
        'width': width, 'height': height, 'deviceScaleFactor': dpr, 'mobile': True,
        'screenWidth': width, 'screenHeight': height})
    cdp.call('Emulation.setTouchEmulationEnabled', {'enabled': True, 'maxTouchPoints': 5})
    time.sleep(1.2)
    cdp.eval(MOBILE_CLASSES)
    time.sleep(0.6)


def open_note(cdp: 'probe.CDP', name: str):
    r = cdp.eval(OPEN % json.dumps(name), await_promise=True)
    if r != 'ok':
        raise SystemExit(f'✗ 打不开 {name}：{r}')
    time.sleep(0.8)


def hr(title: str):
    print('\n' + '─' * 72)
    print(title)
    print('─' * 72)


# --------------------------------------------------------------------------- #
def check_geo(cdp: 'probe.CDP') -> bool:
    print('  滚动到表格：', cdp.eval(SCROLL_TO_TABLE, await_promise=True))
    time.sleep(0.6)
    d = cdp.eval(GEO)
    hr('【A】编辑器横向几何（手机视口）')
    if d.get('error'):
        print('  ✗', d['error'])
        return False
    print(f"  视口 {d['viewport']}px   body: {d['bodyClass']}")
    print(f"  变量：--file-margins-x={d['vars']['fileMarginsX']}  --table-drag-handle-size={d['vars']['dragHandle']}  "
          f"--folio-table-cols={d['vars']['tableCols']}  --folio-content-width={d['vars']['contentWidth']}")
    print(f"  主题版本：{d['vars'].get('version') or '（没有 --folio-version ＝ 旧版 theme.css）'}")
    print(f"  {'层':<26}{'x':>7}{'宽':>8}{'clientW':>8}{'可滚':>6}   padding")
    for l in d['chain']:
        print(f"  {l['sel'][:25]:<26}{l['x']:>7}{l['w']:>8}{l['cw']:>8}{l['canScroll']:>6}   {l['pad']}")
    if d.get('table'):
        t = d['table']
        print(f"  表格：x={t['x']} 宽={t['w']} 列数={t['cols']} 列宽={t['colW']}；"
              f"表格组件（把手槽那层）x={t.get('widgetX')} 宽={t.get('widgetW')}")
        if d.get('textX') is not None:
            print(f"  → 正文左边留白 {d['textX']}px（占视口 {round(d['textX'] / d['viewport'] * 100)}%）；"
                  f"表格每列 {t['colW']}px")
        cb = d.get('colBtn')
        if cb:
            # 表格右缘（＝「+」本该贴着的那条线）＝ 表格 x + 宽
            table_right = t['x'] + t['w']
            gap = round(cb['x'] - table_right, 2)
            print(f"  列「+」把手：x={cb['x']}（wrapper 右缘 {cb['wrapRight']}，wrapper 宽 {cb['wrapW']}）；"
                  f"表格右缘 {round(table_right, 2)}")
            if abs(gap) <= 1:
                print(f"    ✓ 贴着表格右缘（差 {gap}px）")
            else:
                print(f"    ✗ 没贴着表格右缘：差 {gap}px —— 表格比 wrapper 宽时，"
                      f"把手会叠在表格内容上（wrapper 宽 {cb['wrapW']} vs 表格宽 {t['w']}）")
                d['colBtnBad'] = True
        if t.get('widgetX') is not None and t['widgetX'] < 0:
            print(f"  ⚠️ 表格组件的把手槽左缘 x={t['widgetX']} 已经在屏幕外 —— "
                  f"页边距（--file-margins）小于 16px 时会这样，行/列把手会被切掉")
    return not d.get('colBtnBad')


def check_table(cdp: 'probe.CDP') -> bool:
    hr('【B】表格单元格：没光标 vs 有光标（手机视口，逐格比）')
    print('  滚动到表格：', cdp.eval(SCROLL_TO_TABLE, await_promise=True))
    time.sleep(0.6)
    base = cdp.eval(CELL)
    if base.get('error'):
        print('  ✗', base['error'])
        return False
    print(f"  视口 {base['viewport']}  表格宽 {base['tableW']}px（{base['cols']} 列）  "
          f".cm-scroller 内边距 {base['scrollerPadX']}  .cm-content 内边距 {base['contentPadX']}")

    def dump(cells, tag):
        for c in cells:
            lay = c.get('lineBox')
            print(f"    [{tag}] 行{c['row']} 「{c['text'][:12]}」 td {c['tdW']}px 起点 {c.get('firstCharLeft')}px "
                  f"每行字数 {c.get('lines')}（{len(c.get('lines') or [])} 行）右缘 {c.get('lastRight')}"
                  + (f" 行盒 {lay}" if lay else ''))

    dump(base['cells'], '无光标')

    ok = True
    for target in ('满月酒合购金', '2024.11.14'):
        center = cdp.eval(CELL_CENTER % json.dumps(target))
        if not center:
            print('  ✗ 拿不到单元格坐标')
            return False
        time.sleep(0.6)
        cdp.click(center['x'], center['y'])
        time.sleep(1.2)
        foc = cdp.eval(CELL)
        print(f"\n  点进「{center['text'][:12]}」这一格（坐标 {center['x']},{center['y']}）：")
        dump(foc['cells'], '有光标')
        print(f"    {'':<2}{'格':<12}{'起点（无/有光标）':>22}{'折行（每行字数）':>24}")
        for b, f in zip(base['cells'], foc['cells']):
            same_start = b.get('firstCharLeft') is not None and f.get('firstCharLeft') is not None \
                and abs(b['firstCharLeft'] - f['firstCharLeft']) <= 0.1
            same_lines = b.get('lines') == f.get('lines')
            good = same_start and same_lines
            ok &= good
            mark = '✓' if good else '✗'
            print(f"    {mark} 「{b['text'][:8]}」{b.get('firstCharLeft'):>12} / {f.get('firstCharLeft'):<8}"
                  f"{str(b.get('lines')):>12} / {f.get('lines')}")
    for c in foc['cells']:
        if c.get('layers'):
            print(f"    里层编辑器逐层（「{c['text'][:8]}」）：")
            for l in c['layers']:
                print(f"      {l['sel'][:32]:<34} 盒宽 {l['w']:>7} clientW {l['cw']:>7} 内边距 {l['padL']}/{l['padR']} "
                      f"overflow-x {l['ovx']:<8} 字号 {l['fontSize']} 行高 {l['lineHeight']}")
            if c.get('cursor'):
                print(f"      光标：x={c['cursor']['x']} 宽 {c['cursor']['w']} 高 {c['cursor']['h']}")
    return ok


# —— 检查 E：手机外壳（顶部导航条不透明 / 属性面板日期框不被图标压住）——
SHELL = r"""
(() => {
  const r2 = n => +(+n).toFixed(2);
  const leaf = document.querySelector('.workspace-leaf.mod-active');
  const hdr = leaf.querySelector('.view-header');
  const strip = getComputedStyle(document.body, '::before');
  const date = document.querySelector('input.metadata-input[type="date"]');
  const dcs = date ? getComputedStyle(date) : null;
  const opaque = c => {
    const m = c.match(/rgba?\(([^)]+)\)/) || c.match(/color\(srgb ([\d.]+) ([\d.]+) ([\d.]+)(?: \/ ([\d.]+))?\)/);
    if (!m) return c === 'transparent' ? false : true;
    const parts = c.startsWith('color(') ? [m[1], m[2], m[3], m[4]] : m[1].split(/[,\/ ]+/).filter(Boolean);
    if (parts.length < 3) return false;
    const a = parts.length >= 4 && parts[3] !== undefined ? parseFloat(parts[3]) : 1;
    return a >= 0.99;
  };
  return {
    headerBg: hdr ? getComputedStyle(hdr).backgroundColor : null,
    headerOpaque: hdr ? opaque(getComputedStyle(hdr).backgroundColor) : null,
    headerBorder: hdr ? getComputedStyle(hdr).borderBottomColor : null,
    stripContent: strip.content || 'none',
    stripPos: strip.position,
    stripH: strip.height,
    stripBg: strip.backgroundColor,
    stripOpaque: opaque(strip.backgroundColor),
    raisedBg: getComputedStyle(document.body).getPropertyValue('--raised-background').trim(),
    date: date ? { w: r2(date.getBoundingClientRect().width), clientW: date.clientWidth,
                   scrollW: date.scrollWidth, minW: dcs.minWidth,
                   fits: date.clientWidth >= date.scrollWidth } : null,
  };
})()
"""


def check_clamp(cdp: 'probe.CDP') -> bool:
    hr('【D】阅读视图的横向夹取（夹在栏容器上 + 裁剪框外扩 24px）')
    cdp.eval(SET_MODE % (json.dumps(NOTE_FORMATS), json.dumps('preview')), await_promise=True)
    time.sleep(1.2)
    d = cdp.eval(CLAMP, await_promise=True)
    if d.get('error'):
        print('  ✗', d['error'])
        return False
    ok = True
    p, sz = d['panel'], d['sizer']
    print(f"  面板 .{p['cls']}：overflow-x = {p['ovx']} / overflow-y = {p['ovy']}")
    good = sz['ovx'] == 'clip'
    print(f"    {'✓' if good else '✗'} 栏容器是真 clip（overflow-x = {sz['ovx']}，裁剪框外扩 {sz['clipMargin']}）")
    ok &= good
    good = p['canScrollX'] <= 0.5 and p['xOverflow'] <= 0.5
    print(f"    {'✓' if good else '✗'} 正文横滚不动：试滚 99999 动了 {p['canScrollX']}px，"
          f"scrollWidth - clientWidth = {p['xOverflow']}px")
    ok &= good
    good = p['scrollH'] > p['clientH'] and p['canScrollY'] > 0.5
    print(f"    {'✓' if good else '✗'} 竖向照旧能滚：{p['canScrollY']}px（内容 {p['scrollH']} / 视口 {p['clientH']}）")
    ok &= good
    if d['arrows']:
        tested = [a for a in d['arrows'] if a['hit'] is not None]
        bad = [a for a in tested if a['hit'] is False]
        s = d['arrows'][0]
        print(f"    折叠箭头 {len(d['arrows'])} 个（视口内测到 {len(tested)} 个）：第一个 x={s['x']} 宽 {s['w']}，"
              f"在栏容器左缘外 {s['outLeftOfSizer']}px（正常位置），面板左缘内 {s['outLeftOfPanel']}px")
        good = not bad and bool(tested)
        print(f"    {'✓' if good else '✗'} 视口内的箭头全部还能命中（＝没被裁掉）"
              + ('' if good else f'：{len(bad)} 个点不到，例 {bad[:2]}'))
        ok &= good
    if d['meta']:
        m = d['meta']
        print(f"    属性面板：x={m['x']} 宽 {m['w']}，比栏容器左右各外扩 {m['outsideSizer']}px")
        good = m['hit'] and m['insidePanel']
        print(f"    {'✓' if good else '✗'} 外扩部分没被裁（命中 {m['hit']}／在面板内 {m['insidePanel']}）")
        ok &= good
    return ok


def check_shell(cdp: 'probe.CDP') -> bool:
    hr('【E】手机外壳：顶部不透明 / 日期框不被图标压住')
    open_note(cdp, NOTE_FORMATS)
    time.sleep(0.6)
    d = cdp.eval(SHELL)
    ok = True
    print(f"  标题条背景 {d['headerBg']}（不透明 {d['headerOpaque']}），下边框 {d['headerBorder']}")
    good = bool(d['headerOpaque'])
    print(f"    {'✓' if good else '✗'} 标题条是不透明纸底（正文不会再从底下透出来）")
    ok &= good
    print(f"  状态栏那一条：::before content={d['stripContent']} position={d['stripPos']} "
          f"高 {d['stripH']} 背景 {d['stripBg']}")
    good = d['stripPos'] == 'fixed' and d['stripOpaque']
    print(f"    {'✓' if good else '✗'} 状态栏那一条也铺了不透明底"
          f"{'（本机安全区为 0，高度会显成 12px 的 --view-header-top-offset）' if d['stripH'] in ('12px', '0px') else ''}")
    ok &= good
    print(f"  药丸底 --raised-background = {d['raisedBg']}")
    good = d['raisedBg'] not in ('', 'transparent', 'rgba(0, 0, 0, 0)')
    print(f"    {'✓' if good else '✗'} 按钮药丸也是不透明纸底"
          + ('' if good else '（还是 transparent / 半透明）'))
    ok &= good
    if d['date']:
        dd = d['date']
        print(f"  日期输入框：宽 {dd['w']}（min-width {dd['minW']}）clientW {dd['clientW']} "
              f"scrollW {dd['scrollW']}")
        good = dd['fits']
        print(f"    {'✓' if good else '✗'} 数值放得下（不会再被图标压住）")
        ok &= good
    else:
        print('  （这篇笔记里没有日期属性，跳过）')
    return ok


def check_formats(cdp: 'probe.CDP') -> bool:
    ok = True
    for mode, title in (('source', '实时预览'), ('preview', '阅读视图')):
        cdp.eval(SET_MODE % (json.dumps(NOTE_FORMATS), json.dumps(mode)), await_promise=True)
        time.sleep(0.8)
        d = cdp.eval(FORMATS, await_promise=True)
        hr(f'【C】各类格式体检 —— {title}（视口 {d["viewport"]}px）')
        print(f"  {'元素':<10}{'x':>7}{'宽':>8}{'字号':>7}{'行高':>9}  诊断")
        for it in d['items']:
            if it.get('missing'):
                # 某个视图里见不到某类元素很常见（实时预览不渲染 <pre>、脚注
                # 只在阅读视图成块），记一笔就好，不算不一致。
                print(f"  {it['label']:<10}{'—':>7}{'—':>8}{'—':>7}{'—':>9}  （这个视图里没见到）")
                continue
            diag = it['issues']
            extra = ('  ℹ ' + '；'.join(it['notes'])) if it.get('notes') else ''
            print(f"  {it['label']:<10}{it['x']:>7}{it['w']:>8}{it['fontSize']:>7}{it['lineHeight']:>9}  "
                  + ('；'.join(diag) if diag else '✓') + extra)
            if diag:
                ok = False
        if d['scrollers']:
            print('  可横滚的内层：')
            for s in d['scrollers']:
                print(f"    {s['key']:<28} 内容超出 {s['over']}px，实际能滚 {s['can']}px（overflow-x: {s['ovx']}）")
    cdp.eval(SET_MODE % (json.dumps(NOTE_FORMATS), json.dumps('source')), await_promise=True)
    return ok


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description='手机视口探针（393×852 + is-mobile/is-phone）')
    ap.add_argument('--check', default='all',
                    choices=['all', 'geo', 'table', 'formats', 'clamp', 'shell'])
    ap.add_argument('--desktop', action='store_true', help='不改视口、不加手机类（当桌面探针用）')
    ap.add_argument('--width', type=int, default=393)
    ap.add_argument('--height', type=int, default=852)
    ap.add_argument('--dpr', type=int, default=3)
    ap.add_argument('--dir', default=str(WORKDIR))
    ap.add_argument('--port', type=int, default=PORT)
    ap.add_argument('--theme', default=None, help='用另一份 theme.css 跑（默认 = 工作区那份）')
    ap.add_argument('--snippet', action='append', default=None,
                    help='启用某个 CSS 片段（可重复；片段在主题之后加载，用来复现手机上的层叠）')
    ap.add_argument('--keep', action='store_true')
    args = ap.parse_args()

    if not probe.OBSIDIAN.exists():
        raise SystemExit(f'找不到 Obsidian：{probe.OBSIDIAN}')
    workdir = Path(args.dir)
    profile = setup(workdir, Path(args.theme) if args.theme else None,
                    [Path(s) for s in args.snippet] if args.snippet else None)
    probe.kill_stale(profile)
    proc = subprocess.Popen(
        [str(probe.OBSIDIAN), f'--user-data-dir={profile}', f'--remote-debugging-port={args.port}'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        cdp = probe.CDP(args.port)
        cdp.connect()
        # 「各类格式体检」要把整篇从上到下滚一遍（阅读视图分段懒渲染），
        # 慢的时候会超过 CDP 默认那 60 秒 —— 放宽到 5 分钟，免得偶发超时。
        cdp.sock.settimeout(300)
        if not probe.wait_ready(cdp, note=NOTE_FORMATS, timeout=90):
            print('✗ 等不到 Obsidian 就绪')
            return 1
        if args.desktop:
            cdp.call('Emulation.setDeviceMetricsOverride', {
                'width': args.width, 'height': args.height, 'deviceScaleFactor': 2, 'mobile': False})
            time.sleep(1)
            print(f'桌面视口：{args.width}×{args.height}（不加 is-mobile）')
        else:
            boot(cdp, args.width, args.height, args.dpr)
            print(f'手机视口：{args.width}×{args.height} @{args.dpr}x   '
                  f'internal={cdp.eval("window.innerWidth")}×{cdp.eval("window.innerHeight")} '
                  f'dpr={cdp.eval("devicePixelRatio")}')

        ok = True
        if args.check in ('all', 'geo'):
            open_note(cdp, NOTE_TABLE)
            ok &= check_geo(cdp)
        if args.check in ('all', 'table'):
            open_note(cdp, NOTE_TABLE)
            ok &= check_table(cdp)
        if args.check in ('all', 'formats'):
            ok &= check_formats(cdp)
        if args.check in ('all', 'clamp'):
            open_note(cdp, NOTE_FORMATS) if args.check == 'clamp' else None
            ok &= check_clamp(cdp)
        if args.check in ('all', 'shell'):
            ok &= check_shell(cdp)
        print('\n结果：' + ('没有发现问题 ✓' if ok else '有可疑之处 ✗'))
        return 0 if ok else 1
    finally:
        if args.keep:
            print(f'（--keep：实例留着，端口 {args.port}，profile {profile}）')
        else:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    sys.exit(main())
