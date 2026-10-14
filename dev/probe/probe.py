#!/usr/bin/env python3
"""真实 Obsidian 探针 —— 表格单元格「有光标 / 没光标」「实时预览 / 阅读视图」一致性检查。

为什么要这个：theme.css 里表格那几条规则，很多坑只在真实 DOM 里才显形 ——
  · 表格组件是 `.cm-content` 的**直接子元素**，不在任何 `.cm-line` 里（继承关系跟猜的不一样）；
  · 单元格里层那个 CodeMirror 只在光标进去时才存在，且会被 Obsidian 的 app.css 抢权重；
  · Obsidian 自己的 `.cm-table-widget th, td { padding: 0 }` 会盖掉主题的 `th/td` 规则。
静态复现页（preview.html 那种）把 DOM 猜错一次，结论就会反 —— letter-spacing 那条
就曾被判成「不用改」，实际必须改。所以这类改动一律在这里量一遍。

做法：另起一个 Obsidian 实例（独立 `--user-data-dir`，不碰你自己的 vault 与配置），
开一个只含测试笔记的临时 vault，主题用**当前工作区的 theme.css**（每次运行都重新拷），
再用 CDP（纯标准库实现的 WebSocket 客户端）模拟真实点击、量 DOM。

用法：
    python3 dev/probe/probe.py              # 跑一遍全部检查（跑完关掉探针实例）
    python3 dev/probe/probe.py --keep       # 跑完留着实例，方便自己接 DevTools 玩
    python3 dev/probe/probe.py --port 9444  # 换端口（默认 9333）
退出码：所有检查一致 → 0；有不一致 → 1。
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import shutil
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OBSIDIAN = Path('/Applications/Obsidian.app/Contents/MacOS/Obsidian')
HERE = Path(__file__).resolve().parent
FIXTURE = HERE / 'fixtures' / '表格测试.md'
NOTE = '表格测试.md'


# --------------------------------------------------------------------------- #
# 极简 CDP 客户端（socket + base64，不依赖任何三方库）
# --------------------------------------------------------------------------- #
class CDP:
    def __init__(self, port: int):
        self.port = port
        self.sock: socket.socket | None = None

    def _page_ws(self) -> str:
        for _ in range(60):
            try:
                with urllib.request.urlopen(f'http://127.0.0.1:{self.port}/json', timeout=2) as r:
                    for t in json.load(r):
                        if t.get('type') == 'page' and t.get('url', '').startswith('app://obsidian.md'):
                            return t['webSocketDebuggerUrl']
            except (urllib.error.URLError, ConnectionError, TimeoutError, json.JSONDecodeError):
                pass
            time.sleep(0.5)
        raise SystemExit(f'等不到 {self.port} 端口上的 Obsidian 页面，探针实例没起来')

    def connect(self):
        url = self._page_ws()
        rest = url[len('ws://'):]
        hostport, path = rest.split('/', 1)
        host, port = hostport.split(':')
        self.sock = socket.create_connection((host, int(port)), timeout=60)
        key = base64.b64encode(os.urandom(16)).decode()
        self.sock.sendall((
            f"GET /{path} HTTP/1.1\r\nHost: {hostport}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        ).encode())
        buf = b''
        while b'\r\n\r\n' not in buf:
            buf += self.sock.recv(4096)
        head, _, rest = buf.partition(b'\r\n\r\n')
        if b' 101 ' not in head.split(b'\r\n')[0]:
            raise SystemExit('WebSocket 握手失败：' + head[:200].decode('latin1'))
        self.buf = rest
        self.next_id = 1

    def _recv_exact(self, n: int) -> bytes:
        while len(self.buf) < n:
            chunk = self.sock.recv(1 << 16)
            if not chunk:
                raise EOFError('探针实例把连接关了')
            self.buf += chunk
        out, self.buf = self.buf[:n], self.buf[n:]
        return out

    def _send(self, obj: dict):
        data = json.dumps(obj).encode()
        mask = os.urandom(4)
        n = len(data)
        head = bytearray([0x81])
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126)
            head += struct.pack('>H', n)
        else:
            head.append(0x80 | 127)
            head += struct.pack('>Q', n)
        head += mask
        self.sock.sendall(bytes(head) + bytes(b ^ mask[i % 4] for i, b in enumerate(data)))

    def _recv(self) -> tuple[int, bytes]:
        b1, b2 = self._recv_exact(2)
        ln = b2 & 0x7F
        if ln == 126:
            ln = struct.unpack('>H', self._recv_exact(2))[0]
        elif ln == 127:
            ln = struct.unpack('>Q', self._recv_exact(8))[0]
        mask = self._recv_exact(4) if b2 & 0x80 else None
        payload = self._recv_exact(ln)
        if mask:
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        return b1 & 0x0F, payload

    def call(self, method: str, params: dict | None = None):
        i = self.next_id
        self.next_id += 1
        self._send({'id': i, 'method': method, 'params': params or {}})
        while True:
            opcode, payload = self._recv()
            if opcode == 0x1:
                msg = json.loads(payload)
                if msg.get('id') == i:
                    if 'error' in msg:
                        raise RuntimeError(json.dumps(msg['error'], ensure_ascii=False))
                    return msg.get('result')
            elif opcode == 0x8:
                raise EOFError('探针实例结束了 WebSocket')

    def eval(self, expr: str, await_promise: bool = False):
        r = self.call('Runtime.evaluate', {
            'expression': expr, 'returnByValue': True,
            'awaitPromise': await_promise, 'userGesture': True,
        })
        if r.get('exceptionDetails'):
            raise RuntimeError(json.dumps(r['exceptionDetails'], ensure_ascii=False)[:1500])
        return r.get('result', {}).get('value')

    def click(self, x: float, y: float):
        for kind in ('mousePressed', 'mouseReleased'):
            self.call('Input.dispatchMouseEvent', {
                'type': kind, 'x': x, 'y': y, 'button': 'left',
                'clickCount': 1, 'pointerType': 'mouse',
            })


# --------------------------------------------------------------------------- #
# 注入到渲染进程里的测量脚本
# --------------------------------------------------------------------------- #
# 找到当前 markdown 视图里的第一张表，量「最长文本的格」和「最短文本的格」：
#   文本起点（相对 td 边框盒）、行高、每一条视觉行的字数与右缘；
# 若该格正处于编辑态，再带上里层 .cm-line 的几个关键计算值。
MEASURE = r"""
(() => {
  // 两个视图会同时在 DOM 里（藏着那个宽度为 0），只认可见的那张表
  const tables = [...document.querySelectorAll('.cm-table-widget table, .markdown-preview-view table')]
    .filter(t => t.getBoundingClientRect().width > 0);
  if (!tables.length) return { error: '没找到可见的表格' };
  const tbl = tables[0];
  const inPreview = !!tbl.closest('.markdown-preview-view');
  const cells = [...tbl.querySelectorAll('td')];
  if (!cells.length) return { error: '表格里没有 td' };
  const textOf = td => {
    const w = document.createTreeWalker(td, NodeFilter.SHOW_TEXT, { acceptNode(n) {
      const p = n.parentElement; if (!p) return NodeFilter.FILTER_REJECT;
      const cs = getComputedStyle(p);
      if (cs.display === 'none' || cs.visibility === 'hidden') return NodeFilter.FILTER_REJECT;
      return n.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    }});
    return w.nextNode();
  };
  const metrics = td => {
    const n = textOf(td);
    if (!n) return null;
    const box = td.getBoundingClientRect();
    const row = td.closest('tr').getBoundingClientRect();
    const rects = [];
    for (let i = 0; i < n.length; i++) {
      const r = document.createRange(); r.setStart(n, i); r.setEnd(n, i + 1);
      const b = r.getBoundingClientRect();
      rects.push({ top: Math.round(b.top), left: b.left, right: b.right });
    }
    const vlines = [];
    for (const r of rects) {
      const last = vlines[vlines.length - 1];
      if (last && Math.abs(last.top - r.top) < 3) { last.n++; last.right = Math.max(last.right, r.right); }
      else vlines.push({ top: r.top, n: 1, right: r.right });
    }
    const out = {
      chars: n.length,
      firstCharLeft: +(rects[0].left - box.left).toFixed(2),
      rowH: +row.height.toFixed(2),
      lines: vlines.map(v => ({ n: v.n, right: +(v.right - box.left).toFixed(1) })),
      focused: !!td.querySelector('.cm-editor'),
    };
    const line = td.querySelector('.cm-line');
    if (line) {
      const cs = getComputedStyle(line);
      out.line = {
        letterSpacing: cs.letterSpacing, textIndent: cs.textIndent,
        textAlign: cs.textAlign, textJustify: cs.textJustify, paddingLeft: cs.paddingLeft,
      };
    }
    const wrap = td.querySelector('.table-cell-wrapper:not([style*="display: none"])') || td;
    out.wrapperPadLeft = getComputedStyle(wrap).paddingLeft;
    out.tdPadLeft = getComputedStyle(td).paddingLeft;
    return out;
  };
  const byLen = [...cells].sort((a, b) => (textOf(b)?.length ?? 0) - (textOf(a)?.length ?? 0));
  const long = byLen[0], short = byLen[byLen.length - 1];
  return {
    mode: inPreview ? 'preview' : 'source',
    long: metrics(long), short: metrics(short),
    longText: (textOf(long)?.textContent || '').slice(0, 12),
    shortText: (textOf(short)?.textContent || '').slice(0, 12),
  };
})()
"""

# 点进「最长文本的格」：先问坐标，再由 Python 侧发真实鼠标事件（跟用户点击同一条路径）
CELL_CENTER = r"""
(() => {
  const tbl = document.querySelector('.cm-table-widget table');
  if (!tbl) return null;
  const cells = [...tbl.querySelectorAll('td')];
  const textOf = td => {
    const w = document.createTreeWalker(td, NodeFilter.SHOW_TEXT, { acceptNode(n) {
      const p = n.parentElement; if (!p) return NodeFilter.FILTER_REJECT;
      const cs = getComputedStyle(p);
      if (cs.display === 'none' || cs.visibility === 'hidden') return NodeFilter.FILTER_REJECT;
      return n.textContent.trim() ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    }});
    return w.nextNode();
  };
  const long = [...cells].sort((a, b) => (textOf(b)?.length ?? 0) - (textOf(a)?.length ?? 0))[0];
  const r = long.getBoundingClientRect();
  return { x: +(r.left + r.width / 2).toFixed(1), y: +(r.top + r.height / 2).toFixed(1) };
})()
"""

# 把两个「模式类」都打开，再读里层行的样式：复位若失效，这里立刻能看出来
LINE_WITH_MODES = r"""
(() => {
  document.body.classList.add('folio-book-indent', 'folio-justify');
  const line = document.querySelector('.cm-table-widget td .cm-editor .cm-line');
  if (!line) { document.body.classList.remove('folio-book-indent', 'folio-justify'); return null; }
  void line.offsetHeight;
  const cs = getComputedStyle(line);
  const out = { letterSpacing: cs.letterSpacing, textIndent: cs.textIndent,
                textAlign: cs.textAlign, textJustify: cs.textJustify, paddingLeft: cs.paddingLeft };
  document.body.classList.remove('folio-book-indent', 'folio-justify');
  return out;
})()
"""

OPEN_NOTE = r"""
(async () => {
  document.body.classList.add('folio-justify');           // 主题里这个模式默认开
  const f = app.vault.getAbstractFileByPath(%s);
  await app.workspace.getLeaf().openFile(f);
  await new Promise(r => setTimeout(r, 800));
  return !!document.querySelector('.cm-table-widget');
})()
""" % json.dumps(NOTE)

SET_MODE = r"""
(async (mode) => {
  const leaf = app.workspace.getMostRecentLeaf();
  await leaf.setViewState({ type: 'markdown', state: { file: %s, mode: mode } });
  await new Promise(r => setTimeout(r, 800));
  return leaf.getViewState().state.mode;
})(%s)
""" % (json.dumps(NOTE), '%s')


# --------------------------------------------------------------------------- #
# 探针实例：临时 vault + 独立 profile
# --------------------------------------------------------------------------- #
def setup(workdir: Path) -> Path:
    vault = workdir / 'vault'
    profile = workdir / 'profile'
    theme_dir = vault / '.obsidian' / 'themes' / 'Folio'
    theme_dir.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    # 主题永远用当前工作区那份（这样探针测的就是你正在改的代码）
    shutil.copyfile(REPO / 'theme.css', theme_dir / 'theme.css')
    shutil.copyfile(FIXTURE, vault / NOTE)
    (vault / '.obsidian' / 'app.json').write_text(json.dumps({
        'legacyEditor': False, 'livePreview': True, 'defaultViewMode': 'source',
        'readableLineLength': True, 'showLineNumber': False, 'spellcheck': False,
        'attachmentFolderPath': './', 'promptDelete': False,
    }, ensure_ascii=False))
    (vault / '.obsidian' / 'appearance.json').write_text(json.dumps({
        'baseFontSize': 16, 'theme': 'moonstone', 'cssTheme': 'Folio',
        'translucency': False, 'nativeMenus': False, 'showViewHeader': True,
    }, ensure_ascii=False))
    (vault / '.obsidian' / 'community-plugins.json').write_text('[]')
    (profile / 'obsidian.json').write_text(json.dumps({
        'vaults': {'0123456789abcdef': {'path': str(vault), 'ts': int(time.time() * 1000), 'open': True}},
    }))
    return profile


def kill_stale(profile: Path):
    subprocess.run(['pkill', '-f', f'user-data-dir={profile}'], check=False,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(0.5)


def wait_ready(cdp: 'CDP', timeout: float = 60) -> bool:
    """等 Obsidian 把 vault 和布局都load完 —— CDP 页面比 app 就绪早得多。"""
    expr = ("!!(window.app && app.workspace && app.workspace.layoutReady && app.vault && "
            "app.vault.getAbstractFileByPath(%s))" % json.dumps(NOTE))
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            if cdp.eval(expr):
                return True
        except (RuntimeError, EOFError):
            pass
        time.sleep(0.5)
    return False


# --------------------------------------------------------------------------- #
# 报告
# --------------------------------------------------------------------------- #
def fmt(ok: bool, now, want, unit: str = '') -> str:
    mark = '✓' if ok else '✗'
    return f'{mark} {now}{unit}（基准 {want}{unit}）'


def same(a, b, eps: float = 0.1) -> bool:
    return a is not None and b is not None and abs(a - b) <= eps


def same_lines(a, b) -> bool:
    if not a or not b or len(a) != len(b):
        return False
    return all(x['n'] == y['n'] and abs(x['right'] - y['right']) <= 0.1 for x, y in zip(a, b))


def main() -> int:
    ap = argparse.ArgumentParser(description='真实 Obsidian 探针：表格单元格一致性检查')
    ap.add_argument('--dir', default='/tmp/folio-probe', help='临时 vault / profile 放哪（默认 /tmp/folio-probe）')
    ap.add_argument('--port', type=int, default=9333, help='远程调试端口（默认 9333）')
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
        if not wait_ready(cdp):
            print('✗ 等不到 Obsidian 就绪（vault 没打开？）')
            return 1
        if not cdp.eval(OPEN_NOTE, await_promise=True):
            print('✗ 测试笔记里没等到表格组件（vault 或主题没加载？）')
            return 1

        # ---- 检查 1：同一个格，没光标 vs 有光标 -------------------------------
        base = cdp.eval(MEASURE)
        center = cdp.eval(CELL_CENTER)
        if not center:
            print('✗ 拿不到单元格坐标')
            return 1
        cdp.click(center['x'], center['y'])
        time.sleep(1.0)
        focused = cdp.eval(MEASURE)
        line = cdp.eval(LINE_WITH_MODES)

        print('\n【1】单元格：没光标 vs 有光标（文本 = %s…，%d 字）'
              % (base['longText'], base['long']['chars']))
        if not focused['long']['focused']:
            print('  ✗ 点进单元格后没看到里层编辑器，没法比')
            ok = False
        else:
            for label, key, unit in (('文本起点（相对单元格）', 'firstCharLeft', 'px'),
                                     ('行高', 'rowH', 'px')):
                good = same(base['long'][key], focused['long'][key])
                print(f'  {label:<22}{fmt(good, focused["long"][key], base["long"][key], unit)}')
                ok &= good
            good = same_lines(base['long']['lines'], focused['long']['lines'])
            print(f'  {"折行（每行字数/右缘）":<20}{"✓" if good else "✗"} '
                  f'{focused["long"]["lines"]}（基准 {base["long"]["lines"]}）')
            ok &= good
            if line:
                for label, key, want in (('letter-spacing', 'letterSpacing', 'normal'),
                                         ('text-indent', 'textIndent', '0px'),
                                         ('text-align', 'textAlign', 'start'),
                                         ('text-justify', 'textJustify', 'auto')):
                    good = line[key] == want
                    print(f'  里层行 {label:<16}{"✓" if good else "✗"} {line[key]}（应为 {want}；'
                          f'book-indent / justify 都已打开）')
                    ok &= good
            else:
                print('  ✗ 读不到里层 .cm-line 的样式')
                ok = False

        # ---- 检查 2：实时预览 vs 阅读视图 -------------------------------------
        cdp.eval(SET_MODE % json.dumps('preview'), await_promise=True)
        time.sleep(0.6)
        rv = cdp.eval(MEASURE)
        cdp.eval(SET_MODE % json.dumps('source'), await_promise=True)

        print('\n【2】实时预览 vs 阅读视图（短格 = %s，单元格内边距与单行行高）'
              % rv.get('shortText', ''))
        if rv.get('error'):
            print('  ✗ 阅读视图里没量到表格：' + rv['error'])
            ok = False
        else:
            for label, key, unit in (('文本起点（相对单元格）', 'firstCharLeft', 'px'),
                                     ('行高（短格所在行）', 'rowH', 'px')):
                good = same(rv['short'][key], base['short'][key])
                print(f'  {label:<22}{fmt(good, rv["short"][key], base["short"][key], unit)}')
                ok &= good
            print(f'  内边距落在谁身上      实时预览 td={base["short"]["tdPadLeft"]} / '
                  f'wrapper={base["short"]["wrapperPadLeft"]}；阅读视图 td={rv["short"]["tdPadLeft"]}')

        print('\n结果：' + ('全部一致 ✓' if ok else '有不一致 ✗'))
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
