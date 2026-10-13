#!/usr/bin/env python3
"""由 theme.css 生成 palette.html —— 四套配色的可视色卡。

色卡里的每一个色块都直接引用主题自己的变量名（--folio-paper、--code-keyword…），
所以它不会和 theme.css 跑偏。改完配色重新跑一次即可：

    python3 palette.gen.py && open palette.html

同时会从 git HEAD 读一份旧配色，生成「改动前 → 改动后」对照。
"""

import re
import subprocess

SRC = "theme.css"
OUT = "palette.html"

SCHEMES = [
    ("纸感 · 浅", "s-paper-light", ["body", "body.theme-light"]),
    ("纸感 · 深", "s-paper-dark", ["body", "body.theme-dark"]),
    ("GPT · 浅", "s-gpt-light", ["body", "body.theme-light", "body.theme-light.folio-chatgpt-mode"]),
    ("GPT · 深", "s-gpt-dark", ["body", "body.theme-dark", "body.theme-dark.folio-chatgpt-mode"]),
]

# 色卡分组：(标题, [(变量名, 说明)])
GROUPS = [
    ("纸面 / 边框", [
        ("--folio-paper", "主背景"),
        ("--folio-paper-2", "次背景"),
        ("--folio-paper-3", "三级"),
        ("--folio-rule", "分隔线"),
        ("--folio-quote-bg", "引用底"),
        ("--folio-active-line-bg", "当前行底"),
    ]),
    ("墨色 / 标题", [
        ("--folio-ink-strong", "最强"),
        ("--folio-ink", "正文"),
        ("--folio-ink-soft", "次级"),
        ("--folio-ink-muted", "弱化"),
        ("--folio-ink-faint", "禁用/占位"),
        ("--folio-heading-strong", "H1/H2"),
        ("--folio-heading", "H3/H4"),
        ("--folio-heading-muted", "H5/H6"),
    ]),
    ("强调 / 选区 / 高亮 / 加粗", [
        ("--text-accent", "链接·标签"),
        ("--text-accent-hover", "链接 hover"),
        ("--interactive-accent", "填充（按钮/勾选）"),
        ("--text-on-accent", "填充上的文字"),
        ("--folio-bold-color", "加粗"),
    ]),
    ("代码块", [
        ("--folio-code-block-bg", "底"),
        ("--folio-code-block-border", "边框"),
        ("--folio-code-line-active", "当前行"),
    ]),
    ("语法色", [
        ("--code-normal", "normal"),
        ("--code-comment", "comment"),
        ("--code-keyword", "keyword"),
        ("--code-string", "string"),
        ("--code-function", "function"),
        ("--code-value", "value"),
        ("--code-property", "property"),
        ("--code-tag", "tag"),
        ("--code-punctuation", "punctuation"),
    ]),
]

# 改动对照里要高亮的 token
DIFF_TOKENS = [
    "--folio-ink-muted", "--folio-ink-faint", "--folio-bold-color",
    "--folio-code-block-bg", "--folio-code-block-border", "--folio-code-line-active",
    "--code-comment", "--text-accent", "--text-accent-hover", "--interactive-accent",
    "--text-on-accent", "--text-selection", "--text-highlight-bg",
    "--folio-paper-3", "--folio-active-line-bg",
]


# ---------------------------------------------------------------- 解析

def parse(text):
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    rules = re.findall(r"([^{}]+)\{([^{}]*)\}", text, flags=re.S)
    out = {}
    for sel, body in rules:
        sel = " ".join(sel.split())
        vals = {}
        for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", body):
            vals[m.group(1)] = m.group(2).strip()
        out.setdefault(sel, {}).update(vals)
    return rules, out


def resolve(rules, keys):
    v = {}
    for sel, body in rules:
        sel = " ".join(sel.split())
        if sel in keys:
            for m in re.finditer(r"(--[\w-]+)\s*:\s*([^;]+);", body):
                v[m.group(1)] = m.group(2).strip()
    return v


# ---------------------------------------------------------------- 颜色

def hex2rgb(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def lum(rgb):
    def f(c):
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def ratio(a, b):
    l1, l2 = lum(hex2rgb(a)), lum(hex2rgb(b))
    l1, l2 = max(l1, l2), min(l1, l2)
    return (l1 + 0.05) / (l2 + 0.05)


def split_alpha(s):
    m = re.match(r"rgba?\(\s*([\d.]+)\s*,\s*([\d.]+)\s*,\s*([\d.]+)\s*(?:,\s*([\d.]+)\s*)?\)", s)
    if not m:
        return s, 1.0
    hexv = "#%02x%02x%02x" % tuple(int(float(m.group(i))) for i in (1, 2, 3))
    return hexv, float(m.group(4) or 1)


def over(fg, bg):
    h, a = split_alpha(fg)
    if a >= 1:
        return h
    f, b = hex2rgb(h), hex2rgb(bg)
    return "#%02x%02x%02x" % tuple(round(f[i] * a + b[i] * (1 - a)) for i in range(3))


def grade(r):
    return "AAA" if r >= 7 else ("AA" if r >= 4.5 else ("AA-large" if r >= 3 else "fail"))


# ---------------------------------------------------------------- 生成

def swatch_grid(v, paper):
    parts = []
    for title, items in GROUPS:
        cells = []
        for name, desc in items:
            val = v.get(name, "—")
            shown = over(val, paper) if val.startswith("rgba") else val
            note = ""
            if val.startswith("rgba"):
                note = f'<span class="ratio">α{val.split(",")[-1].strip().rstrip(")")}</span>'
            elif shown.startswith("#") and name not in ("--text-on-accent",):
                note = f'<span class="ratio">{ratio(shown, paper):.2f}</span>'
            elif name == "--text-on-accent":
                acc = v.get("--interactive-accent", "#000")
                note = f'<span class="ratio">{ratio(shown, acc):.2f}</span>'
            cells.append(
                f'<div class="cell"><div class="chip" style="background:{shown}"></div>'
                f'<div class="meta"><code>{name.replace("--", "")}</code>'
                f'<span class="hex">{val}</span>'
                f'<span class="desc">{desc} {note}</span></div></div>'
            )
        parts.append(f'<div class="group"><h4>{title}</h4><div class="cells">{"".join(cells)}</div></div>')
    return "".join(parts)


def mock_note(v):
    return f"""
<div class="note">
  <div class="inline-title">配色改动后的样子</div>
  <h1>一级标题 H1</h1>
  <h2>二级标题 H2</h2>
  <h3>三级标题 H3</h3>
  <p>正文里混着 <strong>加粗的重点</strong>、<em>斜体</em>、<code>inline_code()</code>、
  一个 <a href="#">站内链接</a>、一个 <a class="unresolved" href="#">未解析链接</a>、
  一个 <span class="tag">#标签</span>，还有 <mark>被高亮标出的句子</mark>。</p>
  <p>再区分一次：<span class="sel">这是「我选中的文字」</span>，而
  <mark>这是「我标的重点」</mark> —— 两者不该长一样。</p>
  <blockquote>引用块：纸感模式下它是暖的，深色模式下它和「当前行」不是同一个颜色。</blockquote>
  <pre><code><span class="c">// 代码注释：深色下最容易糊掉的一档</span>
<span class="k">const</span> <span class="f">folio</span> = {{
  <span class="p">paper</span>: <span class="s">"#fcfbf8"</span>,
  <span class="p">radius</span>: <span class="n">12</span>,
  <span class="p">theme</span>: <span class="t">Theme</span>.<span class="f">of</span>(<span class="s">"folio"</span>),
}};</code></pre>
  <table>
    <thead><tr><th>角色</th><th>取值</th></tr></thead>
    <tbody><tr><td>正文</td><td>{v.get('--folio-ink', '')}</td></tr>
    <tr><td>次级</td><td>{v.get('--folio-ink-muted', '')}</td></tr></tbody>
  </table>
  <ul class="tasks">
    <li><input type="checkbox" checked> 已勾选的任务</li>
    <li><input type="checkbox"> 未勾选的任务（边框要看得见）</li>
  </ul>
  <hr>
  <p class="faintline">这一行故意用 faint 写：它只该出现在禁用态与占位符里。</p>
</div>"""


def scheme_css(sid, v):
    keep = [n for _, items in GROUPS for n, _ in items] + [
        "--text-selection", "--text-highlight-bg", "--folio-quote-bg"]
    lines = [f"#{sid}{{" + "".join(f"{n}:{v[n]};" for n in dict.fromkeys(keep) if n in v) + "}"]
    return "".join(lines)


def diff_rows(old, new, paper_old, paper_new):
    rows = []
    for name in DIFF_TOKENS:
        o, n = old.get(name), new.get(name)
        if not o or not n or o == n:
            continue
        o_show, n_show = over(o, paper_old), over(n, paper_new)
        ro = ratio(o_show, paper_old) if name != "--text-on-accent" else None
        rn = ratio(n_show, paper_new) if name != "--text-on-accent" else None
        delta = ""
        if ro and rn:
            arrow = "↑" if rn > ro else "↓"
            delta = f'<span class="delta">{ro:.2f} → {rn:.2f} {arrow}</span>'
        rows.append(
            f'<tr><td><code>{name.replace("--", "")}</code></td>'
            f'<td><span class="mini" style="background:{o_show}"></span>{o}</td>'
            f'<td><span class="mini" style="background:{n_show}"></span>{n}</td>'
            f'<td>{delta}</td></tr>'
        )
    return "".join(rows)


def main():
    cur_rules, _ = parse(open(SRC, encoding="utf-8").read())
    try:
        head = subprocess.run(["git", "show", "HEAD:theme.css"], capture_output=True, text=True,
                              check=True).stdout
        old_rules, _ = parse(head)
        has_old = True
    except Exception:
        old_rules, has_old = [], False

    blocks, css, diff_blocks = [], [], []
    for title, sid, keys in SCHEMES:
        v = resolve(cur_rules, keys)
        paper = v.get("--folio-paper", "#fff")
        css.append(scheme_css(sid, v))
        blocks.append(f"""
<section class="scheme" id="{sid}">
  <header class="scheme-head"><h2>{title}</h2>
    <span class="mono">{sid}</span></header>
  <div class="cols">
    <div class="left">{swatch_grid(v, paper)}</div>
    <div class="right">{mock_note(v)}</div>
  </div>
</section>""")
        if has_old:
            ov = resolve(old_rules, keys)
            rows = diff_rows(ov, v, ov.get("--folio-paper", "#fff"), paper)
            if rows:
                diff_blocks.append(
                    f'<details><summary>{title} 的改动（{rows.count("<tr>")} 处）</summary>'
                    f'<table class="diff"><thead><tr><th>token</th><th>旧</th><th>新</th>'
                    f'<th>对比度</th></tr></thead><tbody>{rows}</tbody></table></details>')

    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>Folio 配色色卡</title>
<style>
  :root {{ color-scheme: light dark; }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; padding:32px; background:#f2f2f0; color:#1a1a1a;
         font:14px/1.7 -apple-system,"PingFang SC","Noto Sans SC",sans-serif; }}
  h1 {{ font-size:22px; margin:0 0 4px; }}
  .lede {{ color:#666; margin:0 0 28px; }}
  .scheme {{ background:#fff; border-radius:14px; margin:0 0 28px; overflow:hidden;
             box-shadow:0 1px 3px rgba(0,0,0,.08); }}
  .scheme-head {{ display:flex; align-items:baseline; gap:12px; padding:14px 22px;
                  border-bottom:1px solid rgba(128,128,128,.25);
                  background:var(--folio-paper-2); }}
  .scheme-head h2 {{ font-size:16px; margin:0; color:var(--folio-heading-strong); }}
  .mono {{ font:12px ui-monospace,monospace; color:var(--folio-ink-muted); }}
  .cols {{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1fr); gap:0; }}
  @media (max-width:1100px) {{ .cols {{ grid-template-columns:1fr; }} }}
  .left {{ padding:18px 22px; background:var(--folio-paper); }}
  .right {{ padding:18px 22px; background:var(--folio-paper);
            border-left:1px solid var(--folio-rule); }}
  .group {{ margin-bottom:16px; }}
  .group h4 {{ font-size:12px; margin:0 0 8px; letter-spacing:.06em; text-transform:uppercase;
               color:var(--folio-ink-muted); font-weight:600; }}
  .cells {{ display:grid; grid-template-columns:repeat(auto-fill,minmax(168px,1fr)); gap:8px; }}
  .cell {{ display:flex; gap:8px; align-items:center; padding:6px; border-radius:8px;
           border:1px solid var(--folio-rule); background:var(--folio-paper); }}
  .chip {{ width:26px; height:34px; border-radius:5px; flex:0 0 auto;
           border:1px solid var(--folio-rule); }}
  .meta {{ min-width:0; display:flex; flex-direction:column; line-height:1.35; }}
  .meta code {{ font:11px ui-monospace,monospace; color:var(--folio-ink);
                white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
  .hex {{ font:11px ui-monospace,monospace; color:var(--folio-ink-soft); }}
  .desc {{ font-size:11px; color:var(--folio-ink-muted); }}
  .ratio {{ font:10px ui-monospace,monospace; color:var(--folio-ink-muted);
            border:1px solid var(--folio-rule); border-radius:4px; padding:0 3px; margin-left:3px; }}

  /* —— 模拟笔记 —— */
  .note {{ color:var(--folio-ink); }}
  .note .inline-title {{ font-size:24px; font-weight:700; color:var(--folio-heading-strong);
                         margin-bottom:14px; }}
  .note h1 {{ font-size:24px; margin:16px 0 8px; color:var(--folio-heading-strong); border:0; }}
  .note h2 {{ font-size:19px; margin:14px 0 8px; color:var(--folio-heading-strong); border:0; }}
  .note h3 {{ font-size:16px; margin:12px 0 8px; color:var(--folio-heading); border:0; }}
  .note p {{ margin:10px 0; }}
  .note strong {{ color:var(--folio-bold-color); font-weight:650; }}
  .note code {{ background:rgba(127,127,127,.13); border:1px solid rgba(127,127,127,.12);
                border-radius:5px; padding:.12em .35em; font-size:.88em;
                font-family:ui-monospace,monospace; color:var(--code-normal); }}
  .note a {{ color:var(--text-accent); text-decoration:none; }}
  .note a.unresolved {{ color:var(--folio-ink-muted);
                        border-bottom:1px dashed var(--folio-rule); }}
  .note .tag {{ color:var(--text-accent); font-size:.9em; }}
  .note mark {{ background:var(--text-highlight-bg); color:var(--folio-ink);
                padding:0 2px; }}
  .note .sel {{ background:var(--text-selection); }}
  .note blockquote {{ margin:12px 0; padding:.6em 1.1em; border-radius:8px; font-style:italic;
                      color:var(--folio-ink-soft); background:var(--folio-quote-bg);
                      border-left:3px solid var(--folio-rule); }}
  .note pre {{ background:var(--folio-code-block-bg); border:1px solid var(--folio-code-block-border);
               border-radius:12px; padding:14px 16px; overflow-x:auto; margin:12px 0; }}
  .note pre code {{ background:none; border:0; padding:0; font-size:13px; line-height:1.7;
                    color:var(--code-normal); }}
  .note .c {{ color:var(--code-comment); }}
  .note .k {{ color:var(--code-keyword); }}
  .note .s {{ color:var(--code-string); }}
  .note .f {{ color:var(--code-function); }}
  .note .n {{ color:var(--code-value); }}
  .note .p {{ color:var(--code-property); }}
  .note .t {{ color:var(--code-tag); }}
  .note table {{ width:100%; border-collapse:collapse; margin:12px 0; }}
  .note th {{ text-align:left; background:var(--folio-paper-2); color:var(--folio-heading);
              padding:6px 10px; border:1px solid var(--folio-rule); font-weight:600; }}
  .note td {{ padding:6px 10px; border:1px solid var(--folio-rule); }}
  .note ul.tasks {{ list-style:none; padding-left:2px; }}
  .note ul.tasks li {{ margin:6px 0; }}
  .note input[type=checkbox] {{ appearance:none; width:14px; height:14px; border-radius:4px;
                                border:1.5px solid var(--folio-ink-muted); vertical-align:-2px;
                                margin-right:6px; background:transparent; }}
  .note input[type=checkbox]:checked {{ background:var(--interactive-accent);
                                        border-color:var(--interactive-accent); }}
  .note hr {{ border:0; border-top:1px solid var(--folio-rule); width:38%; margin:22px auto; }}
  .note .faintline {{ color:var(--folio-ink-faint); font-size:12px; }}

  .diff {{ width:100%; border-collapse:collapse; margin-top:10px; font-size:13px; }}
  .diff th, .diff td {{ text-align:left; padding:5px 8px; border-bottom:1px solid #e5e5e5; }}
  .diff code {{ font:12px ui-monospace,monospace; }}
  .mini {{ display:inline-block; width:14px; height:14px; border-radius:3px;
           border:1px solid rgba(0,0,0,.15); vertical-align:-2px; margin-right:6px; }}
  .delta {{ font:12px ui-monospace,monospace; color:#0a7f3f; }}
  details {{ background:#fff; border-radius:10px; padding:12px 18px; margin:0 0 12px;
             box-shadow:0 1px 3px rgba(0,0,0,.06); }}
  summary {{ cursor:pointer; font-weight:600; }}
</style>
<style>
{chr(10).join(css)}
</style></head>
<body>
  <h1>Folio 配色色卡</h1>
  <p class="lede">由 <code>theme.css</code> 解析生成 · 色块上的小数字是该色压在
    <code>--folio-paper</code> 上的 WCAG 对比度（on-accent 例外，是和填充色比）·
    重新生成：<code>python3 palette.gen.py</code></p>
  {"".join(diff_blocks) if diff_blocks else ""}
  {"".join(blocks)}
</body></html>"""

    open(OUT, "w", encoding="utf-8").write(html)
    print(f"已生成 {OUT}（{len(html)} 字节，{len(SCHEMES)} 套配色）")


if __name__ == "__main__":
    main()
