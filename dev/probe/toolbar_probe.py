#!/usr/bin/env python3
"""真实 Obsidian 探针 —— 选中文工具条（folio-toolbar）的「浮出 / 定位 / 落笔」检查。

为什么要这个：工具条是**编辑器插件**，踩的坑全在真实 DOM 与真实事件里 ——
  · 选区是 CodeMirror 6 的原生 selection，工具条靠 `getClientRects()` 定位，
    静态页里量不出「上方放不下要翻到下方」「水平夹进视口」这类边界；
  · 按钮按下若不 preventDefault，编辑器会先失焦、选区塌掉，命令就没得作用 ——
    只有真机点一下才知道；
  · 按钮走的是 Obsidian 核心命令（editor:toggle-bold …），这些 id 只存在于
    真实实例的 `app.commands` 里，静态页无从验证。

做法与 `probe.py` 同：另起一个 Obsidian 实例（独立 `--user-data-dir`），开一个只含
测试笔记的临时 vault，**主题与插件都用当前工作区那份**（每次运行都重拷），再走 CDP。

检查：
  0. 每个按钮用到的核心命令 id 都真实存在
  1. 选中文字 → 工具条浮出，位置在选区上方且水平对齐，默认 7 个按钮、图标齐全
  2. 点「加粗」→ 正文变 `**…**`；点「清除格式」→ 还回来
  3. Esc → 收起
  4. 打开「格式转换」组 → 出现分隔线与标题按钮；点「标题 1」→ 该行变标题
  5. 阅读视图里选中同一段 → **不**出现工具条
  6. 「标注」按钮 → 类型菜单 7 项 → 包成 `> [!warning]`；同类型再点一次拆掉

用法：
    python3 dev/probe/toolbar_probe.py            # 跑一遍（跑完关掉探针实例）
    python3 dev/probe/toolbar_probe.py --keep     # 留着实例，方便接 DevTools
    python3 dev/probe/toolbar_probe.py --port 9444 --dir /tmp/folio-toolbar-probe
退出码：全部通过 → 0；有失败 → 1。
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
sys.path.insert(0, str(HERE))
from probe import CDP, OBSIDIAN, REPO, kill_stale, wait_ready  # noqa: E402

PLUGIN_SRC = REPO / 'plugin' / 'folio-toolbar'
NOTE = '工具条测试.md'
WORD = '选我'
# 目标词放在行中间，逼真一点：加粗后应得到「把**选我**这两个字…」
FIXTURE = '把选我这两个字加粗，再试链接与格式转换。\n'

# main.js 里 BUTTONS 用到的核心命令（检查 0 逐一核对）
EXPECTED_COMMANDS = [
    'editor:toggle-bold', 'editor:toggle-italics', 'editor:toggle-strikethrough',
    'editor:toggle-code', 'editor:toggle-highlight', 'editor:insert-link',
    'editor:clear-formatting', 'editor:set-heading-1', 'editor:set-heading-2',
    'editor:set-heading-3', 'editor:toggle-bullet-list', 'editor:toggle-numbered-list',
    'editor:toggle-blockquote', 'editor:insert-codeblock', 'editor:cycle-list-checklist',
]
DEFAULT_LABELS = ['加粗', '斜体', '删除线', '行内代码', '高亮', '链接', '清除格式']


# --------------------------------------------------------------------------- #
# 实例：临时 vault + 独立 profile（对比 probe.setup，多装了 folio-toolbar）
# --------------------------------------------------------------------------- #
def setup(workdir: Path) -> Path:
    vault = workdir / 'vault'
    profile = workdir / 'profile'
    obsidian = vault / '.obsidian'
    theme_dir = obsidian / 'themes' / 'Folio'
    plug_dir = obsidian / 'plugins' / 'folio-toolbar'
    for d in (theme_dir, plug_dir, profile):
        d.mkdir(parents=True, exist_ok=True)
    obsidian.mkdir(parents=True, exist_ok=True)

    # 主题与插件都用当前工作区那份 —— 测的就是你正在改的代码
    shutil.copyfile(REPO / 'theme.css', theme_dir / 'theme.css')
    for f in ('main.js', 'manifest.json'):
        shutil.copyfile(PLUGIN_SRC / f, plug_dir / f)

    (vault / NOTE).write_text(FIXTURE, encoding='utf-8')
    (obsidian / 'app.json').write_text(json.dumps({
        'legacyEditor': False, 'livePreview': True, 'defaultViewMode': 'source',
        'readableLineLength': True, 'showLineNumber': False, 'spellcheck': False,
        'attachmentFolderPath': './', 'promptDelete': False,
    }, ensure_ascii=False))
    (obsidian / 'appearance.json').write_text(json.dumps({
        'baseFontSize': 16, 'theme': 'moonstone', 'cssTheme': 'Folio',
        'translucency': False, 'nativeMenus': False, 'showViewHeader': True,
    }, ensure_ascii=False))
    # 留空 vault 的「限制模式」：写好社区插件清单，Obsidian 才会加载它
    (obsidian / 'community-plugins.json').write_text(
        json.dumps(['folio-toolbar']), encoding='utf-8')
    (profile / 'obsidian.json').write_text(json.dumps({
        'vaults': {'0123456789abcdef': {'path': str(vault), 'ts': int(time.time() * 1000), 'open': True}},
    }))
    return profile


# --------------------------------------------------------------------------- #
# 注入渲染进程的脚本
# --------------------------------------------------------------------------- #
OPEN_NOTE = r"""
(async () => {
  const f = app.vault.getAbstractFileByPath(%s);
  await app.workspace.getLeaf().openFile(f);
  await new Promise(r => setTimeout(r, 800));
  return !!document.querySelector('.markdown-source-view .cm-line');
})()
""" % json.dumps(NOTE)

CHECK_COMMANDS = r"""
(() => {
  const ids = %s;
  return { missing: ids.filter(id => !app.commands.commands[id]), total: ids.length };
})()
""" % json.dumps(EXPECTED_COMMANDS)

# 目标词的起讫坐标（放在行内第一段文字里），由 Python 侧发真实拖拽
WORD_COORDS = r"""
(() => {
  const word = %s;
  for (const line of document.querySelectorAll('.markdown-source-view .cm-line')) {
    const w = document.createTreeWalker(line, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = w.nextNode())) {
      const i = n.textContent.indexOf(word);
      if (i < 0) continue;
      const r1 = document.createRange(); r1.setStart(n, i); r1.setEnd(n, i + 1);
      const r2 = document.createRange(); r2.setStart(n, i + 1); r2.setEnd(n, i + 2);
      const b1 = r1.getBoundingClientRect(), b2 = r2.getBoundingClientRect();
      if (!b1.width || !b2.width) continue;
      return { ok: true, sx: +(b1.left + 1).toFixed(1), sy: +(b1.top + b1.height / 2).toFixed(1),
               ex: +(b2.right - 1).toFixed(1), ey: +(b2.top + b2.height / 2).toFixed(1) };
    }
  }
  return { ok: false };
})()
""" % json.dumps(WORD)

# 工具条 + 选区的几何与按钮清单
INSPECT = r"""
(() => {
  const sel = window.getSelection();
  const range = sel && sel.rangeCount ? sel.getRangeAt(0) : null;
  const r = range ? range.getBoundingClientRect() : null;
  const bar = document.querySelector('.folio-toolbar');
  const visible = !!(bar && bar.classList.contains('is-visible'));
  const btns = bar ? [...bar.querySelectorAll('.folio-toolbar-btn')] : [];
  return {
    sel: sel ? sel.toString() : null,
    selRect: r && r.width ? { top: r.top, bottom: r.bottom, cx: (r.left + r.right) / 2 } : null,
    visible,
    barRect: visible ? (b => ({ top: b.top, bottom: b.bottom, cx: (b.left + b.right) / 2 }))(bar.getBoundingClientRect()) : null,
    buttons: btns.map(b => ({ label: b.getAttribute('aria-label'), icon: !!b.querySelector('svg'),
                              w: +b.getBoundingClientRect().width.toFixed(1) })),
    seps: bar ? bar.querySelectorAll('.folio-toolbar-sep').length : 0,
  };
})()
"""

BUTTON_CENTER = r"""
(() => {
  const b = [...document.querySelectorAll('.folio-toolbar-btn')]
    .find(x => x.getAttribute('aria-label') === %s);
  if (!b) return null;
  const r = b.getBoundingClientRect();
  return { x: +(r.left + r.width / 2).toFixed(1), y: +(r.top + r.height / 2).toFixed(1) };
})()
"""

EDITOR_VALUE = r"""
(() => {
  const leaf = app.workspace.activeLeaf;
  const ed = leaf && leaf.view && leaf.view.editor;
  return ed ? ed.getValue() : null;
})()
"""

ENABLE_BLOCK = r"""
(() => {
  const p = app.plugins.plugins['folio-toolbar'];
  const extra = %s;
  p.settings.buttons = [...new Set(p.settings.buttons.concat(extra))];
  p.render();
  return p.settings.buttons;
})()
""" % json.dumps(['h1', 'ul', 'quote'])

SET_MODE = r"""
(async (mode) => {
  const leaf = app.workspace.getMostRecentLeaf();
  await leaf.setViewState({ type: 'markdown', state: { file: %s, mode: mode } });
  await new Promise(r => setTimeout(r, 800));
  return leaf.getViewState().state.mode;
})(%s)
""" % (json.dumps(NOTE), '%s')

# 在阅读视图里用程序选中同一段文字（读视图没有 CodeMirror，靠原生 Range）
SELECT_IN_PREVIEW = r"""
(() => {
  const root = document.querySelector('.markdown-preview-view');
  if (!root) return { ok: false };
  const w = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, { acceptNode(n) {
    return n.textContent.includes(%s) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
  }});
  const n = w.nextNode();
  if (!n) return { ok: false };
  const i = n.textContent.indexOf(%s);
  const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 2);
  const sel = window.getSelection(); sel.removeAllRanges(); sel.addRange(r);
  return { ok: true, text: sel.toString() };
})()
""" % (json.dumps(WORD), json.dumps(WORD))

# 重置笔记内容 / 打开「标注」按钮
RESET_CONTENT = r"""
(() => {
  const ed = app.workspace.activeLeaf.view.editor;
  ed.setValue(%s);
  ed.focus();
  return ed.getValue();
})()
""" % json.dumps(FIXTURE)

ENABLE_CALLOUT = r"""
(() => {
  const p = app.plugins.plugins['folio-toolbar'];
  p.settings.buttons = [...new Set(p.settings.buttons.concat(['callout']))];
  p.render();
  return p.settings.buttons;
})()
"""

# 类型菜单：是否打开、有哪几项、各项坐标（找得到才点得中）
MENU_STATE = r"""
(() => {
  const menu = document.querySelector('.menu');
  if (!menu) return { open: false };
  const items = [...menu.querySelectorAll('.menu-item')].map(i => {
    const r = i.getBoundingClientRect();
    return { title: i.textContent.trim(), icon: !!i.querySelector('svg'),
             x: +(r.left + r.width / 2).toFixed(1), y: +(r.top + r.height / 2).toFixed(1) };
  });
  return { open: true, items };
})()
"""


def drag(cdp: 'CDP', sx: float, sy: float, ex: float, ey: float, steps: int = 8):
    """真实拖拽选词：按下 → 分步移动 → 松开（跟用户手选同一条路径）。"""
    cdp.call('Input.dispatchMouseEvent', {
        'type': 'mousePressed', 'x': sx, 'y': sy, 'button': 'left',
        'buttons': 1, 'clickCount': 1, 'pointerType': 'mouse'})
    for i in range(1, steps + 1):
        cdp.call('Input.dispatchMouseEvent', {
            'type': 'mouseMoved', 'x': sx + (ex - sx) * i / steps,
            'y': sy + (ey - sy) * i / steps, 'button': 'left',
            'buttons': 1, 'pointerType': 'mouse'})
    cdp.call('Input.dispatchMouseEvent', {
        'type': 'mouseReleased', 'x': ex, 'y': ey, 'button': 'left',
        'buttons': 0, 'clickCount': 1, 'pointerType': 'mouse'})


def press_escape(cdp: 'CDP'):
    for kind in ('keyDown', 'keyUp'):
        cdp.call('Input.dispatchKeyEvent', {
            'type': kind, 'key': 'Escape', 'code': 'Escape',
            'windowsVirtualKeyCode': 27, 'nativeVirtualKeyCode': 27})


def select_word(cdp: 'CDP', word: str) -> bool:
    coords = cdp.eval(WORD_COORDS)
    if not coords or not coords.get('ok'):
        return False
    drag(cdp, coords['sx'], coords['sy'], coords['ex'], coords['ey'])
    return True


# --------------------------------------------------------------------------- #
def main() -> int:
    ap = argparse.ArgumentParser(description='真实 Obsidian 探针：选中文工具条')
    ap.add_argument('--dir', default='/tmp/folio-toolbar-probe', help='临时 vault / profile 放哪')
    ap.add_argument('--port', type=int, default=9334, help='远程调试端口（默认 9334）')
    ap.add_argument('--keep', action='store_true', help='跑完不关探针实例')
    args = ap.parse_args()

    if not OBSIDIAN.exists():
        raise SystemExit(f'找不到 Obsidian：{OBSIDIAN}')
    workdir = Path(args.dir)
    profile = setup(workdir)
    kill_stale(profile)

    proc = subprocess.Popen(
        [str(OBSIDIAN), f'--user-data-dir={profile}', f'--remote-debugging-port={args.port}'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    ok = True
    try:
        cdp = CDP(args.port)
        cdp.connect()
        if not wait_ready(cdp, NOTE):
            print('✗ 等不到 Obsidian 就绪')
            return 1

        # 等插件加载
        deadline = time.time() + 30
        while time.time() < deadline:
            if cdp.eval("!!(window.app && app.plugins && app.plugins.plugins && "
                        "app.plugins.plugins['folio-toolbar'])"):
                break
            time.sleep(0.5)
        else:
            print('✗ 插件没加载（限制模式没关？community-plugins.json 没生效？）')
            return 1

        if not cdp.eval(OPEN_NOTE, await_promise=True):
            print('✗ 测试笔记没打开')
            return 1

        # ---- 0：核心命令 id 都在 ------------------------------------------------
        cmd = cdp.eval(CHECK_COMMANDS)
        print(f'\n【0】核心命令可用性（共 {cmd["total"]} 个）')
        if cmd['missing']:
            print('  ✗ 缺失：' + '、'.join(cmd['missing']))
            ok = False
        else:
            print('  ✓ 全部存在')

        # ---- 1：选中浮出 + 定位 + 默认按钮 -------------------------------------
        print('\n【1】选中文字 → 工具条浮出、定位、默认按钮')
        if not select_word(cdp, WORD):
            print('  ✗ 找不到目标词坐标')
            return 1
        time.sleep(0.8)  # delay(200ms) + 稳定
        insp = cdp.eval(INSPECT)
        if not insp['visible']:
            print('  ✗ 工具条没浮出')
            ok = False
        else:
            labels = [b['label'] for b in insp['buttons']]
            good = labels == DEFAULT_LABELS
            print(f'  {"按钮清单":<14}{"✓" if good else "✗"} {labels}（应为 {DEFAULT_LABELS}）')
            ok &= good
            good = all(b['icon'] for b in insp['buttons'])
            print(f'  {"图标齐全":<14}{"✓" if good else "✗"} '
                  f'{"全部有 svg" if good else "缺：" + str([b["label"] for b in insp["buttons"] if not b["icon"]])}')
            ok &= good
            good = insp['seps'] == 0
            print(f'  {"无多余分隔线":<12}{"✓" if good else "✗"} {insp["seps"]} 条（默认组内应为 0）')
            ok &= good

            bar, sr = insp['barRect'], insp['selRect']
            good = bool(bar and sr) and bar['bottom'] <= sr['top'] + 0.5
            print(f'  {"在选区上方":<14}{"✓" if good else "✗"} '
                  f'bar.bottom={bar["bottom"]:.1f} 选区 top={sr["top"]:.1f}')
            ok &= good
            good = bool(bar and sr) and abs(bar['cx'] - sr['cx']) <= 1.5
            print(f'  {"水平居中于选区":<12}{"✓" if good else "✗"} '
                  f'bar.cx={bar["cx"]:.1f} 选区 cx={sr["cx"]:.1f}')
            ok &= good

        # ---- 2：加粗 / 清除格式 -------------------------------------------------
        print('\n【2】点「加粗」→ 变 **…**；点「清除格式」→ 还原')
        before = cdp.eval(EDITOR_VALUE)
        btn = cdp.eval(BUTTON_CENTER % json.dumps('加粗'))
        if not btn:
            print('  ✗ 找不到「加粗」按钮')
            ok = False
        else:
            cdp.click(btn['x'], btn['y'])
            time.sleep(0.6)
            after = cdp.eval(EDITOR_VALUE)
            good = f'**{WORD}**' in after
            print(f'  {"加粗落笔":<14}{"✓" if good else "✗"} {after.strip()}')
            ok &= good

            btn = cdp.eval(BUTTON_CENTER % json.dumps('清除格式'))
            if btn:
                cdp.click(btn['x'], btn['y'])
                time.sleep(0.6)
                cleared = cdp.eval(EDITOR_VALUE)
                good = f'**{WORD}**' not in cleared and cleared == before
                print(f'  {"清除格式还原":<12}{"✓" if good else "✗"} {cleared.strip()}')
                ok &= good
            else:
                print('  ✗ 找不到「清除格式」按钮')
                ok = False

        # ---- 3：Esc 收起 --------------------------------------------------------
        print('\n【3】Esc 收起')
        press_escape(cdp)
        time.sleep(0.3)
        insp = cdp.eval(INSPECT)
        good = not insp['visible']
        print(f'  {"已收起":<14}{"✓" if good else "✗"} visible={insp["visible"]}')
        ok &= good

        # ---- 4：打开「格式转换」组 + 标题落笔 -----------------------------------
        print('\n【4】启用「格式转换」组 → 分隔线 + 标题按钮 → 点「标题 1」')
        cdp.eval(ENABLE_BLOCK)
        cdp.eval("app.workspace.activeLeaf.view.editor.focus()")
        if not select_word(cdp, WORD):
            print('  ✗ 重新选中失败')
            ok = False
        else:
            time.sleep(0.8)
            insp = cdp.eval(INSPECT)
            good = insp['visible'] and insp['seps'] == 1
            print(f'  {"出现分隔线":<14}{"✓" if good else "✗"} seps={insp["seps"]} visible={insp["visible"]}')
            ok &= good
            labels = [b['label'] for b in insp['buttons']]
            good = '标题 1' in labels and '引用' in labels
            print(f'  {"出现段落按钮":<12}{"✓" if good else "✗"} {labels}')
            ok &= good

            btn = cdp.eval(BUTTON_CENTER % json.dumps('标题 1'))
            if btn:
                cdp.click(btn['x'], btn['y'])
                time.sleep(0.6)
                val = cdp.eval(EDITOR_VALUE) or ''
                good = val.lstrip().startswith('#')
                print(f'  {"标题 1 落笔":<12}{"✓" if good else "✗"} {val.strip()[:40]}')
                ok &= good
            else:
                print('  ✗ 找不到「标题 1」按钮')
                ok = False

        # ---- 5：阅读视图里不该出现 ---------------------------------------------
        print('\n【5】阅读视图里选中同一段 → 不出现工具条')
        cdp.eval(SET_MODE % json.dumps('preview'), await_promise=True)
        time.sleep(0.6)
        sel = cdp.eval(SELECT_IN_PREVIEW)
        time.sleep(0.8)
        insp = cdp.eval(INSPECT)
        good = bool(sel and sel.get('ok')) and not insp['visible']
        print(f'  {"不出现":<14}{"✓" if good else "✗"} 选中={sel} visible={insp["visible"]}')
        ok &= good
        cdp.eval(SET_MODE % json.dumps('source'), await_promise=True)

        # ---- 6：标注按钮 → 类型菜单 → 包成 callout，再点一次拆掉 ----------------
        print('\n【6】「标注」按钮 → 类型菜单（7 项）→ 包成 callout；同类型再点一次拆掉')
        cdp.eval(RESET_CONTENT)
        cdp.eval(ENABLE_CALLOUT)
        time.sleep(0.3)

        def open_menu_and_pick(needle):
            """点「标注」→ 等菜单 → 点标题含 needle 的那项；返回菜单快照。"""
            btn = cdp.eval(BUTTON_CENTER % json.dumps('标注'))
            if not btn:
                return None
            cdp.click(btn['x'], btn['y'])
            time.sleep(0.5)
            menu = cdp.eval(MENU_STATE)
            if menu.get('open'):
                item = next((i for i in menu['items'] if needle in i['title']), None)
                if item:
                    cdp.click(item['x'], item['y'])
                    time.sleep(0.6)
            return menu

        if not select_word(cdp, WORD):
            print('  ✗ 选中目标词失败')
            ok = False
        else:
            time.sleep(0.8)
            insp = cdp.eval(INSPECT)
            labels = [b['label'] for b in insp['buttons']]
            icon_ok = any(b['label'] == '标注' and b['icon'] for b in insp['buttons'])
            good = insp['visible'] and '标注' in labels and icon_ok
            print(f'  {"标注按钮就位":<12}{"✓" if good else "✗"} visible={insp["visible"]} 图标={icon_ok} {labels}')
            ok &= good

            menu = open_menu_and_pick('Warning')
            if not menu or not menu.get('open'):
                print('  ✗ 点了「标注」没弹出菜单')
                ok = False
            else:
                titles = [i['title'] for i in menu['items']]
                good = len(titles) == 7 and all(i['icon'] for i in menu['items'])
                print(f'  {"菜单七项+图标":<12}{"✓" if good else "✗"} {titles}')
                ok &= good
                val = cdp.eval(EDITOR_VALUE) or ''
                good = val.startswith('> [!warning]') and ('> ' + FIXTURE.strip()) in val
                print(f'  {"包成 warning":<12}{"✓" if good else "✗"} {val.strip()!r}')
                ok &= good

                # 同类型再点一次 → 拆掉。选区一般由插件保留；没保留就重选
                insp = cdp.eval(INSPECT)
                if not insp['visible'] and select_word(cdp, WORD):
                    time.sleep(0.8)
                    insp = cdp.eval(INSPECT)
                if not insp['visible']:
                    print('  （标注块上拿不到选区，跳过「拆掉」检查）')
                else:
                    menu = open_menu_and_pick('Warning')
                    val = cdp.eval(EDITOR_VALUE) or ''
                    if menu and menu.get('open'):
                        good = val.strip() == FIXTURE.strip()
                        print(f'  {"再点一次拆掉":<12}{"✓" if good else "✗"} {val.strip()!r}')
                        ok &= good
                    else:
                        print('  （菜单没再次打开，跳过「拆掉」检查）')

        print('\n结果：' + ('全部通过 ✓' if ok else '有失败 ✗'))
        return 0 if ok else 1
    finally:
        if args.keep:
            print(f'（--keep：探针实例留着，端口 {args.port}，profile {profile}）')
        else:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    sys.exit(main())
