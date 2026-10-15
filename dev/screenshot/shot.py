#!/usr/bin/env python3
"""生成 `screenshot.png`（README 头图 / 社区主题展示图）—— 真实 Obsidian、纸感模式。

跟 `dev/probe/probe.py` 同一套路：另起一个独立 profile 的 Obsidian 实例，开一个临时
vault（主题用当前工作区这份 `theme.css`），把 body 上的模式类按主题默认值摆好
（ChatGPT 模式**关掉** → 纸感；标题居中 / 标题分隔线 / 两端对齐 / 首行缩进 开着），
再把 `dev/screenshot/demo.md` 渲染出来截图。

用法：
    python3 dev/screenshot/shot.py            # 覆盖仓库根目录的 screenshot.png
    python3 dev/screenshot/shot.py --keep     # 留着实例，自己接 DevTools 微调
    python3 dev/screenshot/shot.py --width 1280 --height 720
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(REPO / 'dev' / 'probe'))
from probe import CDP, kill_stale, wait_ready  # noqa: E402  复用极简 CDP 客户端

OBSIDIAN = Path('/Applications/Obsidian.app/Contents/MacOS/Obsidian')
VAULT_NAME = 'obsidian-library'          # 截图里显示成库名（跟之前那张保持一致）
DEMO = '用 Obsidian 写技术笔记.md'

# 纸感模式该有的模式类：主题 @settings 的默认值里，除了 chatgpt-mode（截图要关掉它），
# 其余默认开着的都加上；另外把底部状态栏隐掉，画面干净一点（截图道具，不是默认状态）。
BODY_CLASSES = ['folio-title-centered', 'folio-heading-rule', 'folio-justify',
                'folio-book-indent', 'folio-u-red']
# 截图道具：收掉标签栏 / 面包屑 / 文件树顶部按钮 / 底部库名行（App 外壳，不是主题的一部分）
SCREENSHOT_SNIPPET = '_screenshot'
CHROME_OFF = '''/* 只给截图用：把 Obsidian 的外壳收掉，画面里只剩主题 */
.workspace-tab-header-container,
.workspace-leaf-content[data-type="markdown"] > .view-header,
.nav-buttons-container,
.workspace-sidedock-vault-profile,
.status-bar,
.sidebar-toggle-button,
.code-block-flair {          /* 代码块右上角那个语言标签 */
  display: none !important;
}
'''

# 顺带铺几行文件树，免得侧栏空得像没装东西（内容随便，纯截图道具）
TREE = [
    '技术文档/CSS 变量速查.md',
    '技术文档/Obsidian 主题开发.md',
    '技术文档/Rust/所有权与借用.md',
    '技术文档/Rust/生命周期.md',
    '电子政务/一网通办.md',
    '收集箱.md',
    '备忘录.md',
]


def setup(workdir: Path) -> Path:
    vault = workdir / VAULT_NAME
    profile = workdir / 'profile'
    theme_dir = vault / '.obsidian' / 'themes' / 'Folio'
    theme_dir.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(REPO / 'theme.css', theme_dir / 'theme.css')
    shutil.copyfile(HERE / 'demo.md', vault / DEMO)
    for rel in TREE:
        p = vault / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.exists() or p.write_text(f'# {p.stem}\n\n（截图道具，空文件即可。）\n')
    (vault / '.obsidian' / 'app.json').write_text(json.dumps({
        'legacyEditor': False, 'livePreview': True, 'defaultViewMode': 'source',
        'readableLineLength': True, 'showLineNumber': False, 'spellcheck': False,
        'showInlineTitle': True,           # 纸感的「居中书名」是 .inline-title，得让它出来
        'attachmentFolderPath': './', 'promptDelete': False,
    }, ensure_ascii=False))
    (vault / '.obsidian' / 'appearance.json').write_text(json.dumps({
        'baseFontSize': 16, 'theme': 'moonstone', 'cssTheme': 'Folio',
        'translucency': False, 'nativeMenus': False, 'showViewHeader': True,
        'showRibbon': False,
        'enabledCssSnippets': [SCREENSHOT_SNIPPET],
    }, ensure_ascii=False))
    # 截图道具：把 App 外壳收干净（作者原来那张是 hider 插件做的，这里用一个只对截图生效的 snippet）
    snip = vault / '.obsidian' / 'snippets' / f'{SCREENSHOT_SNIPPET}.css'
    snip.parent.mkdir(parents=True, exist_ok=True)
    snip.write_text(CHROME_OFF, encoding='utf-8')
    (vault / '.obsidian' / 'community-plugins.json').write_text('[]')
    (profile / 'obsidian.json').write_text(json.dumps({
        'vaults': {'0123456789abcdef': {'path': str(vault), 'ts': int(time.time() * 1000), 'open': True}},
    }))
    return profile


def main() -> int:
    ap = argparse.ArgumentParser(description='生成 screenshot.png（真实 Obsidian、纸感模式）')
    ap.add_argument('--dir', default='/tmp/folio-screenshot', help='临时 vault / profile 放哪')
    ap.add_argument('--port', type=int, default=9335, help='远程调试端口（默认 9335）')
    ap.add_argument('--width', type=int, default=1600, help='视口宽（默认 1600 → 输出 3200px 宽）')
    ap.add_argument('--height', type=int, default=900, help='视口高（默认 900 → 输出 1800px 高）')
    ap.add_argument('--out', default=str(REPO / 'screenshot.png'), help='输出文件')
    ap.add_argument('--keep', action='store_true', help='跑完不关实例')
    args = ap.parse_args()

    if not OBSIDIAN.exists():
        raise SystemExit(f'找不到 Obsidian：{OBSIDIAN}')
    profile = setup(Path(args.dir))
    kill_stale(profile)
    proc = subprocess.Popen(
        [str(OBSIDIAN), f'--user-data-dir={profile}', f'--remote-debugging-port={args.port}'],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    try:
        cdp = CDP(args.port)
        cdp.connect()
        if not wait_ready(cdp, note=DEMO):
            raise SystemExit('✗ 等不到 Obsidian 就绪（vault 没打开？）')

        # 窗口先按尺寸摆一遍（摆不上也无所谓，下面还有视口模拟兜底）
        try:
            win = cdp.call('Browser.getWindowForTarget')
            cdp.call('Browser.setWindowBounds', {'windowId': win['windowId'],
                                                 'bounds': {'width': args.width, 'height': args.height}})
        except Exception as e:                                    # noqa: BLE001
            print(f'（窗口尺寸没设上，只用视口模拟：{str(e)[:80]}）')
        cdp.call('Emulation.setDeviceMetricsOverride', {
            'width': args.width, 'height': args.height, 'deviceScaleFactor': 2, 'mobile': False,
        })

        # 摆好模式类 + 打开 demo 笔记（等字体/渲染稳定）
        cdp.eval(r"""
        (async () => {
          document.body.classList.remove('folio-chatgpt-mode');
          document.body.classList.add(%s);
          const f = app.vault.getAbstractFileByPath(%s);
          await app.workspace.getLeaf().openFile(f);
          await new Promise(r => setTimeout(r, 1200));
          return true;
        })()
        """ % (', '.join(json.dumps(c) for c in BODY_CLASSES), json.dumps(DEMO)), await_promise=True)
        time.sleep(1.2)

        shot = cdp.call('Page.captureScreenshot', {'format': 'png'})
        import base64
        out = Path(args.out)
        out.write_bytes(base64.b64decode(shot['data']))
        print(f'✓ 已生成 {out}（{out.stat().st_size / 1024:.0f} KB，视口 {args.width}×{args.height} @2x）')
        return 0
    finally:
        if args.keep:
            print(f'（--keep：实例留着，端口 {args.port}）')
        else:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == '__main__':
    sys.exit(main())
