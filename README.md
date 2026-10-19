# Folio · Obsidian 主题

给「写技术笔记」的 Obsidian 主题。骨子里是**纸感书卷** —— 宋体正文、两端对齐、首行缩进两字、
居中书名、标题分隔线、朱批红；想换现代文档风，一键切成 **ChatGPT 网页端**那套中性灰 + 蓝色
强调色（配色、字体、排版一起换）。

独立仓库，独立版本管理。

![纸感模式](screenshot.png)

> 图里就是**开箱默认**的样子（纸感书卷）。想要现代文档风，`Style Settings → Folio →
> 配色 → ChatGPT 模式` 打开即整页切换；两套配色都按 WCAG 核过（见「配色与对比度」）。
> 截图由 `dev/screenshot/shot.py` 在真实 Obsidian 里生成，可复跑。

## 特性一览

| 领域 | 做了什么 |
| --- | --- |
| 书卷排版 | 宋体正文 + 两端对齐 + 首行缩进两字 + 居中书名 + H1–H3 标题分隔线；后四项都能单独关（默认全开） |
| 两套配色 | **纸感为默认**（暖白纸面 + 墨色）/ ChatGPT 可选（中性灰 + 蓝），各含浅色与深色；正文对比度 ≥ 7:1 |
| 标题层级 | H1 1.75em 递减到 H6 1.02em，始终大于正文 1em；独立墨色 + 字重，上下留白充足 |
| 标注块 | 七类语义 Callout（note / tip / important / warning / caution / example / quote）：3px 语义色竖线 + 极浅同色底，正文保持墨色 |
| 表格 | 占满栏宽、列宽平分（不随内容变化）、长内容换行；「每行最多列数」超出才横滚；两个视图的内边距与行高一致 |
| 编辑器 | 朱批红下划线（`Cmd/Ctrl+U`）、暖黄高亮、当前行浅底、可隐藏 Markdown 语法、光标行居中（插件）、选中浮出格式工具条（插件） |
| 聚焦模式 | 调暗非当前内容，鼠标悬停行与光标行亮起；配套插件让光标行始终停在视口中间 |
| 文件树 | 文件夹与文件各有 SVG 图标、缩进 22px、去掉缩进引导线；纸感模式下整棵树按「书的目录」重做 |
| 纯 CSS 做不到的 | 四个轻量插件：打字机滚动、红下划线命令、阅读视图表格横滚、选中文工具条（见「安装」） |
| 可调 | 接入 Style Settings：字体、行高、段距、栏宽、标题字号、表格列数、上面每一项开关 |

## 安装

### 装主题

**分享给别人（或自己用）**：把本仓库改名为 `Folio`，放进对方的 `<库>/.obsidian/themes/`，
然后在 `设置 → 外观 → 主题` 里选它。详细步骤见 [`INSTALL.md`](INSTALL.md)；
要打成 zip 就用 `./package.sh`（见「打包 · 分享 · 防覆盖」）。

**本机开发**：用软链，改完 CSS 直接生效，无需复制：

```bash
./install.sh                       # 默认链接到同级的 obsidian-library vault
./install.sh /path/to/your/vault   # 或指定 vault
```

> 新装了字体后，**需要完全退出并重启 Obsidian** 才会生效（Chromium 只在启动时枚举系统字体）。

### 配套插件（可选）

主题有四处「纯 CSS 做不到」的能力，各做成一个轻量插件；都是纯 DOM、无构建，`main.js` 就是最终产物：

| 插件 | 干什么 | 为什么必须用插件 |
| --- | --- | --- |
| `plugin/folio-typewriter` | 聚焦模式下让光标所在行**始终停在视口中间**（打字机滚动） | 浏览器只保证光标「不被裁掉」，主动居中必须由 JS 在每次光标/内容变化后重算 `scrollTop` |
| `plugin/folio-mark` | `Cmd/Ctrl+U` 给选中文字**加 / 去红色下划线**（见「朱笔」） | Obsidian 核心没有「下划线」命令，主题更绑不了快捷键 |
| `plugin/folio-table` | 让**阅读视图**里的宽表格能横向滚动（见「表格」） | Obsidian 只在实时预览里给表格包 `.table-wrapper` 容器，阅读视图里没有，纯 CSS 补不出来 |
| `plugin/folio-toolbar` | 选中文字后**浮出格式工具条**（加粗 / 链接 / 格式转换…，见「选中文工具条」） | 桌面端没有「选中即浮出格式条」这回事，要监听选区、算坐标、动态插 DOM |

```bash
./install-plugin.sh      # 一键把 plugin/ 下的插件都链进 vault 并登记
```

装完重启 Obsidian（或在 `设置 → 第三方插件` 里重载）即可。

四个插件各自有独立私有仓库（`obsidian-folio-typewriter` / `obsidian-folio-mark` /
`obsidian-folio-table` / `obsidian-folio-toolbar`，另有在 vault 里就地开发的 `obsidian-dashboard`）。开发仍在
`plugin/<id>/` 原地进行，改完镜像过去：

```bash
./sync-plugins.sh                 # 同步全部（含 vault 里的 dashboard）
./sync-plugins.sh folio-table     # 只同步一个
./sync-plugins.sh --dry-run       # 只看会改什么
```

仓库里的 `README.md` / `LICENSE` / `.gitignore` 属于「仓库自己」，同步时不会被覆盖或删除；
`node_modules/` 与运行时 `data.json` 不入库。

### 字体

配套三套字体，缺失的已下载安装到 `~/Library/Fonts/`：

| 用途 | 字体 | 来源 |
| --- | --- | --- |
| 正文 / 标题 | **Iowan Old Style**（西文）+ **思源宋体 Noto Serif CJK SC**（中文） | Iowan 系统自带；思源宋体已安装 |
| 目录 / 文件树 | GPT 模式：**Bear Sans UI** + **Noto Sans SC** + 苹方；纸感模式：改用正文那一副字（`--folio-tree-font-paper`） | 本机已有 |
| 代码 | **Maple Mono**（中文友好） | 本机已有 |

```
~/Library/Fonts/NotoSerifCJKsc-Regular.otf   思源宋体 常规
~/Library/Fonts/NotoSerifCJKsc-Bold.otf      思源宋体 粗体
~/Library/Fonts/LXGWWenKai-Regular.ttf       霞鹜文楷（备选「纸感」正文字体）
```

三套字体都可在 `Style Settings → Folio` 里一键切换（各有一组预设）。

> **手机上（iOS）没有中文衬线**：`Noto Serif CJK SC` / `Songti SC` 在 iOS 的 WKWebView 里
> 都命中不了，正文中文会回落到系统无衬线（苹方），西文仍是 Iowan 衬线 —— 看起来就是
> 「汉字黑体 + 数字衬线」这种混搭。想两端一致，要么在手机上装一款中文衬线
> （思源宋体 / Noto Serif SC / 宋体 SC，装了主题会自动命中），要么把「正文字体」
> 切成「系统无衬线」。

## 调参（Style Settings）

已接入 [`obsidian-style-settings`](https://github.com/mgmeyers/obsidian-style-settings)。
在 `Settings → Style Settings → Folio`：

| 分组 | 项 | 默认 |
| --- | --- | --- |
| 排版 | 正文字体 / 目录字体 / 代码字体 | 思源宋体 / Bear Sans UI / Maple Mono |
| 排版 | 正文行高 `--folio-line-height` | 1.75 |
| 排版 | 段落间距 `--folio-para-spacing` | 1.05 |
| 排版 | 引用块上下留白 `--folio-quote-pad` | 0.7 |
| 排版 | 正文栏宽 `--folio-content-width` | 42rem |
| 标题 | H1–H6 字号 | 1.75 / 1.375 / 1.32 / 1.18 / 1.08 / 1.02（em） |
| 标题 | 标题上方留白 | 1.7 |
| 表格 | 每行最多列数 | 4（超出才横向滚动）；手机上默认 3，见「移动端」一节 |
| 配色 | **ChatGPT 模式** | **关**（= 纸感书卷；打开即切到中性灰那套） |
| 版面 | 取消居中栏宽 / **标题居中** / **标题分隔线** / **两端对齐** / **首行缩进** / **聚焦模式** | 关 / 开 / 开 / 开 / 开 / 关 |
| 专注 | 隐藏滚动条 / 隐藏底部状态栏 | 关 / 关 |
| 编辑器 | 当前行高亮 / 隐藏 Markdown 语法 | 开 / 关 |
| 批注 | 红色下划线（朱笔） | 开 |
| 文件树 | 紧凑行高 / 显示缩进引导线 | 关 / 关 |

> 正文字号不在此处，请用 `Appearance → Font size`（推荐 17）。原因是 Obsidian 把字号写在
> `body` 的行内样式上，主题无法在不破坏原生滑杆的前提下覆盖它。

## 书卷排版（纸感模式的四件套）

参考当代书籍排版，以下四项**默认开启**，都能在 `Style Settings → Folio → 版面` 一键关掉：

| 项 | 效果 |
| --- | --- |
| 标题居中（书名式） | 笔记标题（文件名）居中，像书页的章名 |
| 标题分隔线 | H1–H3 下方一条细线，**阅读视图与实时预览都生效** |
| 正文两端对齐 | 中文书籍常见的齐行（`text-justify: inter-ideograph`，汉字之间拉开而不是只拉空格） |
| 段落首行缩进两字 | 编辑区只对纯段落行生效，标题 / 列表 / 引用 / 代码 / 表格行不缩进 |

主题整体为**浅色**：浅白纸面（`#fcfbf8`）+ 墨色宋体。请在 `Appearance → Base color` 选择 **Light**。

## 配色与对比度

四套配色 = `body.theme-light/dark` × `folio-chatgpt-mode` 开关（这个开关**默认关**，
也就是纸感书卷）。所有色值都按 WCAG
相对亮度核算过，取值原则：**正文 ≥ 7:1，次要信息 ≥ 4.5:1，禁用/占位 ≥ 3:1**。

| 角色 | 纸感·浅 | 纸感·深 | GPT·浅 | GPT·深 |
| --- | --- | --- | --- | --- |
| 正文 `--text-normal` | 15.4 | 12.1 | 16.1 | 13.6 |
| 次级 `--text-muted`（列表符 / 未解析链接 / 状态栏） | 5.2 | 5.3 | 4.8 | 5.0 |
| 弱化 `--text-faint`（仅禁用 / 占位） | 3.7 | 4.6 | 3.0 | 3.0 |
| 链接 / 标签 `--text-accent` | 5.7 | 7.9 | 5.2 | 5.8 |
| 加粗 `--bold-color` | 5.8 | 5.7 | 6.0 | 5.2 |
| 代码注释 `--code-comment` | 5.8 | 5.2 | 5.9 | 5.6 |
| 强调色底上的文字 `--text-on-accent` | 5.9 | 6.3 | 5.2 | 6.5 |

两套配色的底子：**纸感** = 暖白纸面 `#fcfbf8` / `paper-2 #f4f2ec` / `paper-3 #eae7df` + 墨色
`#26211a`，正文衬线、两端对齐、首行缩进；**ChatGPT** = 中性灰（浅 `#ffffff` / `#f9f9f9` /
`#f3f3f3`，正文 `#212121`，次级 `#6b6b6b`，边框 `#e5e5e5`；深色 `#212121` / `#171717` /
`#262626`）+ 蓝色强调，正文换无衬线、左对齐、不缩进、标题不居中也没有分隔线。

几条容易被改回去的约定：

- **`faint` 不给正文类信息用。** 它只服务禁用态与占位符；状态栏文字走 `muted`，
  未勾选的复选框边框也走 `muted` —— `faint` 在白底上只有 2.1:1，框子直接看不见。
- **选区和高亮必须是两种颜色。** 选区用强调色（「我正在操作」），高亮用暖黄
  （「我标的重点」）。两者曾经同值，等于选中文字和 `==高亮==` 在视觉上分不出来。
- **暗色的高亮额外带一条 2px 下划线**（theme.css §9）。暗底上半透明底的亮度差拉不开，
  只靠底色，「我标的」和「我选的」仍然难分。
- **蓝色分两个角色**：文字用深浅变体（GPT 浅 `#2563eb` / 深 `#5c9bff`），
  品牌亮蓝 `#3983f7` 只做填充与图标 —— 它压在白底上只有 3.64:1，排正文不够 AA。
- **`--text-on-accent` 必须显式定义。** 两套深色的强调色是浅金 / 亮蓝，只有压深字才安全
  （白字压 `#c89154` 仅 2.75:1，压 `#3983f7` 仅 3.64:1）。
- **代码块底色跟纸面同温，不用中性灰。** 暖纸上放冷蓝灰（原 `#f6f8fa`）会像贴了一张网页
  截图；深色下原来的 `#2b2b2b` 还与 `paper-3` 只差 1.02:1，边界全靠边框撑着。

## 标注块（Callout）

七个语义类型。做法借 **GitHub Alerts** 的骨架（NOTE / TIP / IMPORTANT / WARNING /
CAUTION），换成本主题的纸感语言：

- 左边一条 **3px 语义色竖线**（与引用块同宽），其余三边不封口
- 底色只铺同色 **7%**（深色 10%），比 GitHub 更淡，纸面仍是主角
- **只有标题与图标吃语义色**，正文保持墨色 —— 正文对比度完全不受影响
- 圆角只留右侧 8px（与引用块一致），左侧两角为直角 —— 让 3px 竖线贴齐上边

写法就是 Obsidian 原生语法（和 GitHub Alerts 同一套）：

```markdown
> [!note] 顺带一提
> 正文照常写，可以用 **加粗**、<u>红下划线</u>、==高亮==，互不打架。

> [!caution] 最重的一档
> 用朱批红 —— 和加粗、红下划线是同一支笔。
```

| 类型 | 语义 | 图标 | 别名 | 色相 |
| --- | --- | --- | --- | --- |
| `note` | 顺带一提 | 铅笔 | —（默认类型） | 靛蓝 |
| `tip` | 小技巧 | 灯泡 | `hint` | 松绿 |
| `important` | 必须知道 | 圆圈警示 | — | 紫 |
| `warning` | 当心 | 三角警示 | `attention` | 琥珀 |
| `caution` | 最重的一档 | 八边形警示 | — | 朱批红 |
| `example` | 举例 | 列表 | — | 石墨青 |
| `quote` | 引文 | 引号 | `cite` | 暖褐 |

> [!warning] 图标是特意换过的
> Obsidian 默认里 **tip 与 important 都是 `lucide-flame`、颜色还同为青色**，
> **warning 与 caution 都是 `lucide-alert-triangle`** —— 只靠颜色根本分不开。
> 主题只覆盖这三个撞车的：tip 换灯泡、important 换圆圈警示、caution 换八边形警示，
> 其余保留 Obsidian 自己的图标（note 铅笔、example 列表、quote 引号）。

语义强度参考 GitHub 的排序：`note` < `tip` < `important` < `warning` < `caution`。
GitHub 自己的建议也照搬了：**别滥用**（一节里最多一两个）、**别嵌套**、**标题别省**。

几条实现上的约定（都在 theme.css §12）：

- 颜色收在 `--folio-co-*` 变量里，浅 / 深各一套；类型 → 颜色的映射一并在 §12，换色只动变量。
- **没列出的类型不会掉样式**：`info`、`success`、`danger`、`bug` 这类会统一落到 `note`
  的配色，不会再冒出 Obsidian 默认那套彩色。
- **图标仍由 Obsidian 提供**（Lucide）。要换，给对应类型写一条 `--callout-icon: lucide-xxx`。
- **主题不碰 Obsidian 的 `--callout-color`**：它 1.13 起从「R, G, B 三元组」改成要求完整
  颜色值，主题若依赖它就会被钉死在某个版本上；这里用自己的 `--folio-co`。
  代价是凡是 Obsidian 拿 `--callout-color` 上色的地方都要单独接管一次 —— 目前有两处：
  `.callout-icon .svg-icon`（图标，它的选择器权重比 `.callout-icon` 高，必须再压一层）
  与标注块里的 `--table-border-color`。

## 表格

默认行为：**占满栏宽、列宽平分（不随内容变化）、长内容换行**。

「最多几列」由一个设置控制 —— `Style Settings → Folio → 表格 → 每行最多列数`
（`--folio-table-cols`，默认 **4**）：

| 列数 | 效果 |
| --- | --- |
| ≤ 设定值 | 各列平分可用宽度、正好铺满，**一点都不滚**（是正好 100%，不是「差几像素才滚」） |
| > 设定值 | 各列都守住「可用宽度 ÷ 设定值」这个下限，不肯再让 → 表格整体变宽 → **容器横向滚动** |

也就是说，**设 4 就是「4 列铺满，出现第 5 列才开始左右滑」**（手机上默认按 3 算，见「移动端」）。

「撑开」这件事写在**谁**身上有讲究：实时预览里先把 `.table-wrapper` 撑开（表格是
`width: 100%`，跟着走），阅读视图里撑表格自己。原因是实时预览的两个「+」把手
（列/行）是 **wrapper 的绝对定位子元素**（`app.css`：`.table-col-btn { inset-inline-start: 100% }`）——
wrapper 要是不等于表格宽，那把「+」就贴不到表格右缘，会**叠在表格内容上**。
手机上（设定 3 列 + 4 列表）实测：表格 438.66px、wrapper 329px，把手落在表格里侧
109.66px 处，正好压在「备注」那一列的字上；把 min-width 挪到 wrapper 上之后是 0px。
两个探针都把这条当验收项（`probe.py` 的检查 3、`mobile_probe.py` 的检查 A）。

滚的是哪一层，两个视图不一样 —— 而实时预览那一层**必须是四周留了 16px 槽的容器**：

- **实时预览**：滚动盒是 Obsidian 的 **`.cm-table-widget`**（`padding: 16px` +
  `margin: 0 -16px`，四周正好留出 16px 的槽，给它行/列那两个绝对定位的「+」把手用）。
  所以主题显式把 `.table-wrapper` 交回给外层（`overflow: visible`）：wrapper 自己的
  `padding` 是 0，兜不住 `inset-inline-start: 100%`、宽 16px 的「+」列把手 —— 它一旦成了
  滚动盒，这 16px 就成了**实打实可滚的余量**：表格只有 1 列、正好 100% 宽，容器照样能
  左右滑 16px，滑到底右边多一条空白，看起来就像表格没铺满。附带两个症状：每张表下面
  多一条 15px 的横向滚动条，`overflow-y: hidden` 还把下面的「+」行把手裁掉（点不到）。
- **阅读视图**：滚动盒就是配套插件补的那层 `.table-wrapper`（阅读视图没有把手，不需要留槽）。

> [!warning] `.markdown-rendered .table-wrapper` 那条不只作用于阅读视图
> 实时预览的表格组件**自己也带 `markdown-rendered` 类**（实测 `class="cm-embed-block
> cm-table-widget markdown-rendered"`），所以那条会连实时预览的 wrapper 一起命中。
> 主题靠 `.cm-table-widget .table-wrapper { overflow: visible }`（权重 0-4-0 > 0-2-0）
> 把它压回去。删掉那一条会立刻复发上面那 16px —— `dev/probe/probe.py` 的**检查 3**
> 就是守这个的（1/2/4/6 列，逐层强行滚一遍）。

宽度是相对**表格的实际容器**算的（百分比），不是拿「正文栏宽」设置换算的绝对值 ——
所以面板比栏宽窄几像素时（窗口差一点、外边距、滚动条），≤ 设定值的列数也仍然是
正好 100%、不滚；窗口整体变窄时，各列只是跟着一起变窄，不会提前开始滚。

实现上靠一组 `table:has(tr > :nth-child(k))` 抬 `min-width`（CSS 数不出列数，只能
一个一个 k 写，靠层叠顺序取最大的那个 = 真实列数），**16 列封顶**；超过 16 列时
只有前 16 列撑开宽度，各列会被挤窄一点。

另外，「正文本身」在两个视图里都不会横向滚动 —— 两处独立处理，都不是表格的事：

- **阅读视图**：Obsidian 给 `.markdown-preview-view` 只写了 `overflow-y: auto`，
  `overflow-x` 便从 `visible` 派生为 `auto`。正文里只要有什么东西宽出一丁点，
  整块面板就能左右滑几像素，看起来就像表格在滚。主题在**栏容器**上加了
  `overflow-x: clip` 把它夹住。（用 `clip` 而不是 `hidden`：夹在栏容器上时它的
  竖轴还是 `visible`，不会被降级；而 `hidden` 会变成「还能用触控板滑、只是没有
  滚动条」的滚动盒，等于没夹。实测夹在面板上会被降级成 `hidden`，没用。）
- **实时预览**：Obsidian 的表格组件是 `padding: 16px` + `margin: 0 -16px`，它的
  边框盒天生比文字行宽出 16px（那 16px 是给它行/列「+」把手留的槽），而 CodeMirror
  的 `.cm-scroller` 是 `overflow-x: auto` —— 面板只要比栏宽宽不到 32px，整个编辑器
  就能左右滑十几像素，**跟列数完全无关，只有 1 列也照样**。主题把这 32px 的槽在
  编辑器里真让出来（`.cm-sizer` 上限 +32px、`.cm-content` 补 16px 内边距），表格
  正好落进槽里：既不溢出，也不会裁掉把手。代价是窗口比「栏宽 + 32px」更窄时，
  正文会跟着窄最多 32px（总好过整个编辑器能横滑）。

滚动条只出现在横向：容器上显式写了 `overflow-y: hidden`（容器一旦是滚动盒，
竖向会从 `auto` 派生，macOS「始终显示滚动条」下就会多出一条没用的竖条）。

> [!warning] 阅读视图需要插件
> **实时预览**：Obsidian 自己会把表格包进 `<div class="table-wrapper">`，主题给那个
> 容器 `overflow-x: auto` 就够了，开箱即用。
> **阅读视图**：Obsidian **不包**这层容器（`app.js` 里的 `createDiv("table-wrapper")`
> 只出现在表格编辑器那条路径），表格直接挂在笔记栏下 —— 于是宽表格只会**撑破栏宽、
> 伸到栏外**，没有任何东西可以滚。这不是主题能靠 CSS 解决的（`overflow` 加在
> `display: table` 的元素上无效，改成 `display: block` 又会丢掉 `table-layout: fixed`
> 的平分与最小列宽）。
> 装配套插件 **`folio-table`** 即可补上这层容器，两个视图行为一致：
>
> ```bash
> ./install-plugin.sh
> ```
> 不装也不会坏，只是阅读视图退回 Obsidian 的原生行为（表格伸出栏外，表格比窗口还宽时
> 由整个面板横滚）。

**单元格内边距：两个视图写在两个不同的元素上，必须各写一遍。** 只写一处，另一个视图
就还是 Obsidian 的默认值：

| 视图 | 内边距由谁提供 | 主题写在哪 |
| --- | --- | --- |
| 阅读视图 | `th` / `td` 自己 | `.markdown-rendered th, .markdown-rendered td` |
| 实时预览 | 里层的 `.table-cell-wrapper` | `.cm-table-widget .table-cell-wrapper` |

实时预览为什么会跑到里层：Obsidian 把单元格的 padding 全归给了 `.table-cell-wrapper`
（`app.css` 的 `.cm-table-widget th, td { padding: 0 }`，权重 0-4-1，连主题那条
`.markdown-rendered td` 也盖得住）。两处都写 `0.45em 0.75em` 之后，两个视图的单元格
左内边距与行高完全一致（实测 12.5px / 40.17px）；行高不用另调，两个视图都用
`--table-line-height`。漏写实时预览那条时，单元格只有 8px / 4px、行高矮 6.4px
（33.8px），切个视图表格就像换了一份。

**光标进单元格就变形：里层编辑器会「漏」进主题里四条规则。** 点进某个单元格时，
Obsidian 会在那个 `<td>` 里**再挂一个 CodeMirror**（`app.js` 的 `editTableCell()`：
新建 `.table-cell-wrapper` → 原来的内容 wrapper 隐藏 → 里层编辑器塞进同一个 `<td>`）。
里层编辑器虽然被摘掉了 `markdown-source-view` 类，但它是**后代**，四条规则照样命中它
—— 症状都是「有光标 / 没光标两个样」：

- `.markdown-source-view.mod-cm6 .cm-content { padding-inline: 16px }`（给外层编辑器补的）
  → 激活的单元格凭空多出 16px 左内边距，正好是**一个汉字的宽度** → 那一行文字整体右移一个字；
- `body.folio-book-indent … .cm-line:not([class*="HyperMD-"]) { text-indent: 2em }`
  → 里层的行没有 `HyperMD-` 类，开着「书籍段落缩进」时错位从 1 个字变成 3 个字；
- `body.folio-justify … .cm-line { text-align: justify }`（默认开）→ 里层这一行被拉成
  两端对齐：单元格里折出来的前几行被撑满、汉字之间被拉开，最后一行照旧不撑
  （实测第 2 行字距 15.43 → 16.17px、行右缘 198 → 206px）—— 看起来就是「字间距不一样」。
  复位用 `inherit` 而不是 `left`：列的居中对齐（`| :---: |`）是 Obsidian 写在 td 的
  `align` 属性上的，认它才不会被复位掉；
- `.markdown-source-view.mod-cm6 .cm-line { letter-spacing: 0.01em }` → 里层这一行自带
  0.01em（16px 字号 = 0.16px/字），而**没光标**的单元格没有这条：表格组件是
  `.cm-content` 的**直接子元素**（祖先链实测 `.cm-table-widget → .cm-content →
  .cm-contentContainer → .cm-sizer → .cm-scroller`），根本不在任何 `.cm-line` 里。
  一行三四十字就差 5px 上下，正好把折行点顶过去：实测同一格（33 字）没光标时是
  16+17 两行、行高 64.98px，光标一进去变 16+16+1 三行、89.78px。

四条都已在 `.cm-table-widget` 范围内复位（`theme.css` 第 5 节）。**在真实 Obsidian 里
实测**（探针见 `dev/probe/`，一条命令可复跑）：激活格与同文本的未激活格现在逐项相同 ——
左内边距 12.5px、行高 64.98px、视觉行 16+17 字（行右缘 268.5 / 276.5px）全都一样。

## 朱笔 · 红色下划线

给「要盯着的句子」画一条红色下划线，和暖黄的 `==高亮==` 分工：一个是荧光笔，
一个是批注笔。

| 项 | 说明 |
| --- | --- |
| 原文写法 | `<u>要标红的文字</u>`（Obsidian 原生支持，阅读视图与实时预览都会渲染） |
| 快捷键 | **`Cmd/Ctrl+U`** 加 / 去（配套插件 `folio-mark`；忘了也能在编辑器右键菜单里找到） |
| 开关 | `Style Settings → Folio → 批注 → 红色下划线（朱笔）`，默认开 |
| 颜色 | 沿用加粗那支**朱批红**（浅 `#b03a2e` / 深 `#e0736a`）；想换色改 `--folio-u-color` |

插件的行为：选中一段文字按一次包上 `<u>`，再按一次去掉；没选中就插一对空标签、
光标落在中间；选区里如果有空行，会退化成**逐行包裹**（空行会截断 HTML 块）。

两条边界，先说清楚：

- **标签里不解析 Markdown。** `<u>**粗体**</u>`、`<u>[[链接]]</u>` 里的加粗和链接
  都不会生效——这是 Obsidian 的既定行为，不是主题的问题。要「红下划线 + 粗体」
  得另想办法。
- **实时预览里，光标停在那一行时标签按原文显示**，和「隐藏 Markdown 语法」的取舍一致。

## 选中文工具条（folio-toolbar）

在编辑器里选中一段文字、松手稍停（默认 200 ms），选区上方浮出一条格式工具条；点一下就作用，
`Esc` 或点别处收起。

| 组 | 按钮 | 走什么 |
| --- | --- | --- |
| 行内格式（默认开） | 加粗、斜体、删除线、行内代码、高亮、链接、清除格式 | Obsidian 核心命令（`editor:toggle-bold` / `editor:insert-link` / `editor:clear-formatting` …） |
| 行内格式（默认关） | 朱笔下划线 | `<u>…</u>`；装了 `folio-mark` 就复用它的命令，否则插件自带简版（见「朱笔」） |
| 格式转换（默认关） | 标题 1–3、无序 / 有序列表、引用、代码块、待办 | 核心命令（`editor:set-heading-1` / `editor:toggle-bullet-list` / `editor:toggle-blockquote` / `editor:insert-codeblock` / `editor:cycle-list-checklist`） |
| 标注（默认关） | 标注：**一个按钮，点开选类型**（note / tip / important / warning / caution / example / quote） | 核心只能插固定类型的空标注、且不认选区，所以按类型自己改写 `> [!type]`；同类型再点一次拆掉，换类型直接改 |

- **按钮尽量走核心命令**（标注、朱笔下划线除外）：切换语义、链接弹窗、多行行为都跟编辑器自带的一致。
- **标注**：点「标注」弹出类型菜单，图标与主题 §12 的语义映射一致（tip 灯泡、important 圆圈警示、caution 八边形警示）；把选中的段落包成标注，同类型再点一次拆掉。
- **可配置**：`设置 → Folio Toolbar` 里逐个开关按钮、改弹出延迟（0–800 ms）、选择是否在图标下显示名称。
- **只在实时预览 / 源码模式出现**：选区必须落在当前文档的主编辑器上。阅读视图不弹；
  表格单元格里那层里层编辑器也不弹（否则会把格式施加到外层文档）。
- **桌面端专用**：移动端 Obsidian 自带格式工具条，这里不重复造。外观写在 `theme.css` §13，
  跟随纸感 / ChatGPT 两套配色。

> [!note] 为什么必须用插件
> Obsidian 桌面端没有「选中即浮出格式条」这回事（移动端的原生工具条由 App 提供，桌面端没有）。
> 要监听选区、算坐标、动态插 DOM，纯 CSS 做不到。

## 聚焦模式

`Style Settings → Folio → 版面 → 聚焦模式`（默认关）。开启后：

| 行为 | 实现 |
| --- | --- |
| 把非当前内容调暗 | CSS：`.cm-line`、`.cm-embed-block` 一律 `opacity: .32` |
| **鼠标悬停行**亮起 | CSS：`.cm-line:hover` / `.cm-embed-block:hover` 恢复不透明 |
| **光标所在行**亮起 | CSS：`.cm-line.cm-active`（含 CM6 的 `.cm-activeLine`）恢复不透明 |
| 表格等块级部件也参与调暗 | CSS：实时预览里表格是 `div.cm-embed-block.cm-table-widget`，**不是** `.cm-line`，只调暗行会漏掉它、看起来像「没聚焦还挺亮」；现在 `.cm-embed-block` 一并调暗，悬停 / 正在编辑（`:focus-within` / `.is-selected`）时再亮起 |
| **光标所在行永远停在视口中间** | **插件** `folio-typewriter`（打字机滚动）。浏览器只保证光标「不被裁掉」，居中必须由 JS 在每次光标/内容变化后重算 `scrollTop`，CSS 做不到 |

打字机滚动只依赖 DOM（`.cm-scroller` / `.cm-line.cm-active`），不 import CodeMirror，
无构建步骤。默认**只在聚焦模式打开时生效**；在 `设置 → Folio Typewriter` 里可改成
「始终居中」（不开聚焦模式也居中）或打开「平滑滚动」。文档首/末端会自动钳制（顶不到
中间时就贴边），不会滚过头。

## 文件树

**文件夹与文件各有 SVG 图标**（都走 `mask`，颜色跟随主题）：文件夹是「开 / 关」两张切换，
文件是一张折角纸；同样 15px + 7px 间距，所以两列图标对齐、文件夹名与文件名成列。

几个自己踩出来的点：

- **图标必须显式写 `align-self: center`**。Obsidian 的 `.tree-item-self` 是
  `align-items: baseline`（不是 center），而 `::before` 里只有一个空字符串、基线落在
  自己底边上，不写就会「坐」在文字基线上、比文字中线高约 3px（拿截图量过：文件行
  2.9px、文件夹行 3.3px）。`preview.html` 里的树行 stub 曾经写的是 `center`，正好把这个
  错位盖住了 —— 现在 stub 跟 App 的真实值（baseline + `line-height-tight`）一致。
- **缩进 22px 整份写在子容器的 `padding-inline-start` 上，`margin` 归零。** 文件树的
  「无限滚动 / 虚拟化」会给每行套 inline 的 `margin` / `padding`（带 `!important`），
  走 `--nav-item-children-margin-start`（那是 margin）的那半会被折算掉，一级缩进只剩
  ~6px、文件和上级目录就贴一起了。
- 行距 / 圆角由 `--nav-item-*` 变量控制，字号 `--nav-item-size: 14px`；去掉缩进引导线。
- 选中态 = 底色 + 字重。GPT 模式另有左侧强调竖条，挂在 `::after` 上（避免顶掉 `::before`
  的文件图标）；纸感模式去掉竖条 —— 它是 App 的选中控件，不是纸上的记号。
- **纸感模式**（关掉 ChatGPT 模式）整棵树按「书的目录」重做：换成正文衬线、图标降到
  60% 不透明度（印刷符号而非 UI 控件）、行距放松一档、圆角收小、侧栏面板标题按页眉处理。
  全部包在 `body:not(.folio-chatgpt-mode)` 里，GPT 模式零影响。

## 隐藏 Markdown 语法

参考 Minimal 的 *Hide Markdown syntax*，在实时预览里隐藏 `**`、`*`、`~~`、`==`、`[[ ]]`、`#`
等标记（`cm-formatting-*`），让编辑区看起来更像成稿。

- 开启：`Style Settings → Folio → 隐藏 Markdown 语法`
- 注意：字符仍然存在，只是不显示；**光标所在那一行也照样隐藏**（与 Minimal 一致），
  且默认**不留占位**。唯一例外：当标记正好是该行最后一个元素时（例如刚打完 `##`
  的空标题），会保留标记宽度、只把字形变透明——否则光标没有落点会消失，后续输入
  也会跑到标记前面（标题打不出来）。因为它已在行尾，这点占位看不出来。

## 其它细节（代码块 / 引用 / 高亮 / 日历）

这些是「设计取向」那张表里原本逐条记着的实现细节，收在这里备查：

| 对象 | 做法 |
| --- | --- |
| 代码块 | 参考 ChatGPT 网页端：12px 圆角容器 + 细边框 + 内容内边距 16/18px + 13px / 行高 1.7 等宽。底色与纸面同温（**不是**中性灰）：纸感浅 `#f5f3ed` / 深 `#232120`，GPT 浅 `#f6f6f6` / 深 `#1a1a1a`。语法色统一走 `--code-*` 变量（阅读视图 Prism 的 `.token.*` 与编辑器 `cm-*` 共用同一套）。编辑器里代码块是一串 `.cm-line`：中间行直角、只给首/末行圆角（不给围栏相邻行加圆角，否则留缺口） |
| 行内代码 | 半透明灰底 `rgba(127,127,127,0.13)` + 细边框 + 5px 圆角，字号 0.88em |
| 引用块 | 浅色圆角背景（`--folio-quote-bg`）+ 一条灰色左边线 + 上下内边距（`--folio-quote-pad`，默认 0.7em，可在 Style Settings 调）。编辑器里多行引用由逐行底拼成整段，**圆角与上下 padding 都只给首 / 末行** —— CM6 的引用是多个 `.cm-line`，padding 写进通用规则会把整段切成一块块；左边线改 `--blockquote-border-color` 且不再自加边框，避免与 Obsidian 默认的主体色竖线叠成两条 |
| 当前行 / 加粗 | 光标所在行铺一层浅底，用一叠 `box-shadow`（每段平移量为行宽的 0.7 倍，保证互相咬合）横向铺满编辑区；底色不透明，避免半透明叠加出现色阶。加粗文字为朱批红（纸感 `#b03a2e` / 深 `#e0736a`）—— 刻意与代码 keyword 的红拉开，避免「加粗」和「行内代码」共用同一支红笔 |
| 标签 | 透明底 + 强调色文字 + 一条细分隔边框（`--tag-*`），不做成彩色药丸 |
| 日历 | 给 Calendar 插件的 `.today` 加实心强调色底 + 反白文字，高亮当前日期 |

## 移动端（手机 / 平板）

主题原本是照桌面端调的。手机上 Obsidian 有一整套挂在 `is-mobile` / `is-phone` 下的规则
（页边距、表格把手的槽、属性面板外扩……），所以窄屏下有几处得单独交代 —— 全部写在
`theme.css` §14，且只对 `body.is-mobile` 生效，桌面一个像素都不动。

| 现象 | 原因 | 处理 |
| --- | --- | --- |
| 手机上正文比阅读视图窄 32px，同一篇笔记切个视图就重排 | 桌面那 16px 的 `.cm-content` 内边距是给表格组件的「padding 16 + margin −16」让把手槽的；手机上 Obsidian 自己就给了页边距（`--file-margins-x`），再补 16px 纯属白窄（393px 视口：实时预览 313px vs 阅读视图 345px，表格也从 329px 被压到 297px） | ≤ 50rem 的窄屏撤掉这 16px：正文回到 345px、表格 329px，行/列把手仍在页边距的槽里 |
| 手机上 4 列表每列只有 ~82px，一行三四个字 | 列宽 = 容器宽 ÷ 「每行最多列数」（默认 4） | 手机上默认降到 **3 列**（列宽 ~110px，第 4 列起横向滚动）。想改回去：Style Settings 新增的「手机上每行最多列数」，或干脆把 `--folio-table-cols-mobile` 设成 4 |
| 阅读视图里标题旁边的小三角不见了、点也点不到 | 主题给栏容器夹了 `overflow-x: clip` 防正文横滚，而折叠箭头（`margin-inline-start: -22px`／手机 −20px）与手机版属性面板的外扩（`translateX(-12px)`）天生在文字左缘之外 —— 被一起裁掉了 | 裁剪框向外放 24px（`overflow-clip-margin: 24px`）：只放宽裁剪范围，不产生滚动盒，正文照样横滚不动 |
| 光标点进单元格，那一格突然不折行了（文字溢出格子、格子里自己横滚） | 里层编辑器的 `.cm-content` 是 flex 子项，`min-width` 默认 `auto` ＝「最长不可断词」的宽度；窄列里它比整个格子还宽（实测 74px 的格子被顶到 80px） | §5 第五条复位 `min-width: 0`；另外把 app.css 改掉的 `overflow-wrap` 改回 `anywhere`，让「有光标 / 没光标」折行完全一致 |
| 光标点进单元格，整格文字右移一小截、每行只剩一个字 | 手机上的 `folio-mobile` 片段写过一条 `body.is-mobile … .cm-content { padding-inline: 14px }`，权重 **0-4-1** 正好压过主题那条复位（0-4-0）—— 于是那 14px 连**单元格里层编辑器**一起改到（80px 的格子：wrapper 12.75 + 漏进来 14 = 26.75px，只剩一格字宽）。桌面上没有这个片段，所以怎么量都量不出来 | 两边都改：片段不再给 `.cm-content` 写内边距；主题的复位加 `!important`（不看权重，谁也别想再漏）。复现与验收用 `mobile_probe.py --snippet`（片段在主题之后加载，层叠跟手机一致） |
| 顶部（状态栏那一条 + 标题条 + 按钮药丸）是半透明的，正文往上滚会从底下透出来、和标题叠在一起 | Obsidian 手机悬浮导航条的设计：药丸底 `--raised-background` 是 65% 纸色 + 模糊，`.view-header` 自己写死 `transparent`（0-4-0） | §14 把药丸底、标题条、状态栏那一条都换成不透明纸底（顶栏那条用同权重选择器压回 app.css 的写法）。**不是系统限制，纯 CSS 可改**；想回到半透明就把 §14 末段删掉 |
| 属性面板里的日期输入框，左边有个小日历图标压在「2026/10/19」上 | iOS 把 `<input type="date">` 的原生日历图标画在框**左端**，而框只有 95px，塞不下「图标 + 数值」 | §14 藏掉该图标并给到 `min-width: 15ch`（实测 95 → 132px，数值不再被压）。桌面上图标在右端、不挡字，所以只改手机 |
| 手机上「宋体纸感」变成黑体 | iOS 没预装中文衬线：`Noto Serif CJK SC` 不存在，`Songti SC` 在 WKWebView 里命中不了，中文回落到系统无衬线（PingFang），只有西文是 Iowan 衬线（截图里「1027」还是 old-style 数字） | 装一款中文衬线（思源宋体 / Noto Serif SC / 宋体 SC）即可命中；不装就把「正文字体」切成「系统无衬线」，两端至少一致 |

### 怎么确认手机上加载的是哪一版

主题里带一个版本戳 `--folio-version`（`theme.css` 顶部与变量区各一处，与 `manifest.json`
的 `forkVersion` 同步），手机补丁片段 `snippets/folio-mobile.css` 会把它画成一枚徽标：

- **绿色**「Folio 主题 v0.5.2 · 2026-10-19」= 手机上加载的就是最新主题；
- **红色**「Folio 主题 未知版本（theme.css 没同步到最新）」= theme.css 没同步过去，
  去 iCloud 里看 `…/.obsidian/themes/Folio/theme.css` 的修改时间，或重跑 `./sync-mobile.sh`。

徽标 6 秒后自己淡出（`pointer-events: none`，不挡操作）；不想要就把片段里
「版本徽标」那一段删掉。片段文件名**不要改** —— Obsidian 是按文件名记「哪些片段开着」的，
改名等于自动关掉。

### 同步到手机

手机 / iPad 那个库**不是**软链接（iCloud、Obsidian Sync 都不跟随软链接），主题得单独拷过去：

```bash
./sync-mobile.sh                  # 主题 + manifest + snippets/ 一起拷到 iCloud 里的 iphone_note 库
./sync-mobile.sh /path/to/vault   # 或指定别的库
```

拷完在手机上**完全退出** Obsidian 再打开（主题 CSS 是启动时读的），然后看那枚徽标。

手机视口下的回归检查走 `dev/probe/mobile_probe.py`（393×852 + `is-mobile`，
四组检查：横向几何 / 单元格逐格比 / 各类格式体检 / 阅读视图夹取；
`--snippet snippets/folio-mobile.css` 会把片段按真路数一起加载，层叠与手机一致）。

### `snippets/folio-mobile.css`（手机补丁片段）

手机上那些「桌面主题管不到」的部分：17px 正文字号、文件树 36px 触控目标、
Dashboard 双栏改单栏、iOS 惯性滚动、Home 指示条留白，外加版本徽标。
它有两处**别改**的硬约束：

- 别给 `.cm-content` 写内边距（权重 0-4-1 会连单元格里层编辑器一起改到，就是上面那条 bug）；
- 别把 `--file-margins` 调到 22px 以下（表格组件的把手槽要 ≥16px；阅读视图的折叠箭头
  是 `-20px`，实测 18px 时箭头会探出屏幕左边 2~4px）。

## 注意

- 旧 snippet `hide-tree-lines.css` / `edit-css.css` 与主题的文件树样式重叠，建议在
  `Settings → Appearance → CSS snippets` 里**关闭这两个**，避免 `!important` 打架。
- 主题显式接管正文与代码字体（`--font-text` / `--font-monospace`），所以 `Appearance` 里的
  「Text font / Monospace font」下拉会被主题覆盖；改字体请用 Style Settings。
- 深色模式保留了一套配套的「炭墨」配色，但本主题以浅色为主；不切到深色就不会生效。

## 开发

改 `theme.css` 后，Obsidian 会自动重载（软链指向本仓库，无需复制）。四个就地工具：

| 工具 | 用途 |
| --- | --- |
| `preview.html` | 浏览器里直接看排版，或让无头 Chrome 截图 |
| `palette.gen.py` | 从 `theme.css` 生成四套配色的色卡（含 WCAG 对比度与改动对照） |
| `dev/probe/` | **真实 Obsidian 探针**：`probe.py` 量桌面下表格「有 / 无光标」「实时预览 / 阅读视图」是否一致、横向可滚量对不对；`mobile_probe.py` 把视口压成 393×852 并补上 `is-mobile`（`--snippet` 可把 CSS 片段按真路数一起加载），量手机下同一批东西外加各类格式体检；`toolbar_probe.py` 量选中文工具条的浮出 / 定位 / 按钮落笔 |
| `dev/screenshot/` | 生成 README 头图 `screenshot.png`（真实 Obsidian、纸感模式） |

```bash
# 排版预览（浏览器 / 无头截图）
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --screenshot=out.png \
  --window-size=900,1200 "file://$PWD/preview.html"

# 色卡（生成物不入库）
python3 palette.gen.py && open palette.html

# 表格 / 编辑器改动：真机量一遍（全部一致 → 退出码 0）
python3 dev/probe/probe.py

# 选中文工具条改动：真机量一遍（浮出 / 定位 / 落笔都对 → 退出码 0）
python3 dev/probe/toolbar_probe.py

# 重新生成头图
python3 dev/screenshot/shot.py
```

**为什么要有真机探针**：静态预览页只能验「阅读视图那种静态 HTML」，而实时预览里的表格
完全是另一回事 —— 表格组件是 `.cm-content` 的直接子元素、里层那个编辑器只在光标进去时
才存在、Obsidian 自己的 `app.css` 还会抢权重。静态页一旦把 DOM 猜错，结论就会反：
`letter-spacing` 那条就栽过（静态页量出「两边都是 0.16px，不用改」，真机里其实是
「没光标没有、光标进去才有」，每字 0.16px 正好把折行点顶过去）。细节见
[`dev/probe/README.md`](dev/probe/README.md)。

## 打包 · 分享 · 防覆盖

```bash
./package.sh                # 生成 ~/Downloads/folio-obsidian-theme-v<版本>.zip
./package.sh /path/to/dir   # 或指定输出目录
```

zip 里只含使用者需要的文件（`theme.css` / `manifest.json` / `versions.json` /
`INSTALL.md` / `README.md` / `LICENSE` / `screenshot.png`），不含开发脚本。

> [!warning] 别点主题市场里的「更新」
> 本仓库是从**官方 Folio 分叉**出来的自定义版本，和官方**同名同 ID**；又因为它是软链进
> vault 的（`.obsidian/themes/Folio -> 本仓库`），所以在 `设置 → 外观 → 主题` 里点一下
> `Folio` 的「更新」，Obsidian 会按社区市场的记录下载**官方 Folio**，直接覆盖本仓库的
> `theme.css` 与 `manifest.json` —— 自定义样式全部消失（`git status` 会看到这两个文件被改动）。
>
> 防护：`manifest.json` 的 `version` 被抬到 `9.9.9`（远高于官方版本）。Obsidian 只在
> 「已装版本 < 市场版本」时才提示更新，因此那个「更新」不会再出现。
>
> - **真实版本**记在 `manifest.json` 的 `forkVersion`（与 `versions.json` 的键保持一致）。
>   `package.sh` 打包时读 `forkVersion`，所以 zip 名字仍是 `folio-obsidian-theme-v0.4.0.zip`。
> - 改主题时照旧只改 `theme.css`；发新版时更新 `forkVersion` 与 `versions.json`，
>   **`version` 保持 `9.9.9` 不动**。
> - 万一还是被覆盖了，回滚一条命令：`git fetch && git checkout -- theme.css manifest.json`。

## 发布到社区主题

仓库根目录已具备上架所需文件：`manifest.json`、`theme.css`、`versions.json`、`README.md`、
`LICENSE`，以及一张 `screenshot.png`。还差：推到 GitHub，向
[obsidianmd/obsidian-releases](https://github.com/obsidianmd/obsidian-releases) 提 PR。
版本号同时更新 `manifest.json` 与 `versions.json`。

## 仓库结构

```
obsidian-theme-folio/
├── manifest.json     ← 主题元信息（Obsidian 读取；version 是防覆盖哨兵，见「打包 · 分享 · 防覆盖」）
├── theme.css         ← 主题全部样式 + Style Settings 配置
├── versions.json     ← 主题版本 → 最低 Obsidian 版本
├── INSTALL.md        ← 面向使用者的安装说明（分享时带上）
├── screenshot.png    ← 头图（纸感模式；dev/screenshot/shot.py 生成）
├── package.sh        ← 打分享用的 zip 到 ~/Downloads
├── install.sh        ← 开发用：软链主题到某个 vault
├── install-plugin.sh ← 开发用：软链配套插件到某个 vault
├── sync-plugins.sh   ← 把插件源码镜像到各自的私有仓库（见「安装」）
├── plugin/           ← 配套插件（各自独立，见对应章节）
│   ├── folio-typewriter/{manifest.json, main.js}   ← 打字机滚动（见「聚焦模式」）
│   ├── folio-mark/{manifest.json, main.js}         ← 红色下划线（见「朱笔」）
│   ├── folio-table/{manifest.json, main.js}        ← 阅读视图表格横滚（见「表格」）
│   └── folio-toolbar/{manifest.json, main.js}      ← 选中文工具条（见「选中文工具条」）
├── preview.html      ← 开发用：浏览器里的排版预览页
├── palette.gen.py    ← 开发用：从 theme.css 生成四套配色的色卡
├── palette.html      ← 色卡（生成物，不入库；python3 palette.gen.py 生成）
├── dev/probe/        ← 开发用：真实 Obsidian 探针（见「开发」）
├── dev/screenshot/   ← 开发用：头图生成脚本 + 演示笔记（见「开发」）
├── LICENSE
└── README.md
```

主题以软链方式接入 vault：`<vault>/.obsidian/themes/Folio -> 本仓库`。
Obsidian 只认 `.obsidian/themes/<名字>/theme.css`，而 `.obsidian/` 通常被 vault 的
`.gitignore` 忽略；把主题独立成仓库再软链进去，就能脱离 vault 独立做版本管理、备份与发布。

## 设计取向（对应最初的需求）

| 需求 | 落地方式 |
| --- | --- |
| 标题字号递减且大于正文 | `--h1-size`…`--h6-size` 走 `em`，从 1.75em 递减到 1.02em，均 > 1em |
| 标题颜色区分正文 | 独立的 `--folio-heading-*` 墨色，比正文更深/更亮，字重更重 |
| 标题上下留白 | `--heading-spacing`（1.7em）+ 每级 `margin-block` |
| 复杂文档不费力 | 行高 1.75、段距 1.05em、栏宽 42rem（约 30~45 汉字/行） |
| 纸质书感 | 浅白纸面 + 墨色宋体 + 两端对齐 + 首行缩进 + 居中书名 + 标题分隔线 |
| 去除干扰 | 收敛侧栏与标签栏描边、可隐藏状态栏与滚动条、聚焦模式 |
| 文件树要清楚 | 双列对齐的 SVG 图标 + 22px 缩进 + 选中底色；纸感模式按「书的目录」重做 |
| 现代文档风可选 | ChatGPT 模式一键切换配色 + 字体 + 排版 |
| 字号层级 | 两种模式一致：侧边栏 14px、正文 16px / 行高 28px、H1 28px / 700、H2 22px / 700、代码 13px |
