# Folio · Obsidian 主题

一款偏「现代文档」的 Obsidian 主题：默认是 ChatGPT 网页端那套**中性灰 + 蓝色强调色**，
也可以一键切回**纸感书卷**（宋体正文 + 首行缩进 + 标题居中）。

独立仓库，独立版本管理。

![预览](screenshot.png)

## 仓库结构

```
obsidian-theme-folio/
├── manifest.json     ← 主题元信息（Obsidian 读取）
├── theme.css         ← 主题全部样式 + Style Settings 配置
├── versions.json     ← 主题版本 → 最低 Obsidian 版本
├── INSTALL.md        ← 面向使用者的安装说明（分享时带上）
├── screenshot.png    ← 预览图（上架社区主题也需要）
├── package.sh        ← 打分享用的 zip 到 ~/Downloads
├── install.sh        ← 开发用：软链主题到某个 vault
├── install-plugin.sh ← 开发用：软链配套插件到某个 vault
├── plugin/           ← 配套插件（各自独立，见对应章节）
│   ├── folio-typewriter/{manifest.json, main.js}   ← 打字机滚动（见「聚焦模式」）
│   ├── folio-mark/{manifest.json, main.js}         ← 红色下划线（见「朱笔」）
│   └── folio-table/{manifest.json, main.js}        ← 阅读视图表格横滚（见「表格」）
├── preview.html      ← 开发用：浏览器里的排版预览页
├── palette.gen.py    ← 开发用：从 theme.css 生成四套配色的色卡
├── palette.html      ← 色卡（生成物，不入库；python3 palette.gen.py 生成）
├── LICENSE
└── README.md
```

主题以软链方式接入 vault：`<vault>/.obsidian/themes/Folio -> 本仓库`。
Obsidian 只认 `.obsidian/themes/<名字>/theme.css`，而 `.obsidian/` 通常被 vault 的
`.gitignore` 忽略；把主题独立成仓库再软链进去，就能脱离 vault 独立做版本管理、备份与发布。

## 安装

**开发时（本机）**：用软链，改完 CSS 直接生效。

```bash
./install.sh                       # 默认链接到同级的 obsidian-library vault
./install.sh /path/to/your/vault   # 或指定 vault
```

**配套插件（可选）**：主题有两处「纯 CSS 做不到」的能力，各做成一个轻量插件；
两个都是纯 DOM / 无构建，`main.js` 就是最终产物：

| 插件 | 干什么 | 为什么必须用插件 |
| --- | --- | --- |
| `plugin/folio-typewriter` | 聚焦模式下让光标所在行**始终停在视口中间**（打字机滚动） | 浏览器只保证光标「不被裁掉」，主动居中必须由 JS 在每次光标/内容变化后重算 `scrollTop` |
| `plugin/folio-mark` | `Cmd/Ctrl+U` 给选中文字**加 / 去红色下划线**（见「朱笔」） | Obsidian 核心没有「下划线」命令，主题更绑不了快捷键 |
| `plugin/folio-table` | 让**阅读视图**里的宽表格能横向滚动（见「表格」） | Obsidian 只在实时预览里给表格包 `.table-wrapper` 容器，阅读视图里没有，纯 CSS 补不出来 |

```bash
./install-plugin.sh                  # 一键把 plugin/ 下的插件都链进 vault 并登记
```

装完重启 Obsidian（或 `设置 → 第三方插件` 里重载）即可。

**分享给别人**：见 [`INSTALL.md`](INSTALL.md)。简要版是把本仓库改名为 `Folio`
放进对方的 `<库>/.obsidian/themes/`，然后在 `设置 → 外观 → 主题` 里选它。
（分享的主题只有 CSS，不含插件；对方若要打字机滚动或红色下划线，需另装上面的插件。）

> 新装了字体后，**需要完全退出并重启 Obsidian** 才会生效（Chromium 只在启动时枚举系统字体）。

## 分享给别人

```bash
./package.sh                # 生成 ~/Downloads/folio-obsidian-theme-v<版本>.zip
./package.sh /path/to/dir   # 或指定输出目录
```

zip 里只含使用者需要的文件（`theme.css` / `manifest.json` / `versions.json` /
`INSTALL.md` / `README.md` / `LICENSE` / `screenshot.png`），不含开发脚本。

想让别人**在 Obsidian 里直接搜到并安装**，需要上架社区主题列表，见文末「发布到社区主题」。

## 字体方案

配套三套字体，缺失的已下载安装到 `~/Library/Fonts/`：

| 用途 | 字体 | 来源 |
| --- | --- | --- |
| 正文 / 标题 | **Iowan Old Style**（西文）+ **思源宋体 Noto Serif CJK SC**（中文） | Iowan 系统自带；思源宋体已安装 |
| 目录 / 文件树 | GPT 模式：**Bear Sans UI** + **Noto Sans SC** + 苹方；纸感模式：改用正文那一副字（`--folio-tree-font-paper`） | 本机已有 |
| 代码 | **Maple Mono**（中文友好） | 本机已有 |

新增字体文件：

```
~/Library/Fonts/NotoSerifCJKsc-Regular.otf   思源宋体 常规
~/Library/Fonts/NotoSerifCJKsc-Bold.otf      思源宋体 粗体
~/Library/Fonts/LXGWWenKai-Regular.ttf       霞鹜文楷（备选「纸感」正文字体）
```

三套字体都可在 `Style Settings → Folio` 里一键切换（各有一组预设）。

## 调参（Style Settings）

已接入 `obsidian-style-settings`。在 `Settings → Style Settings → Folio`：

- **排版**：正文字体、目录字体、代码字体、行高、段距、正文栏宽
- **配色**：ChatGPT 模式（默认开）
- **标题**：H1~H6 字号、标题上方留白
- **表格**：每行最多列数（超出就横向滚动）
- **版面**：取消居中栏宽、**标题居中**、**标题分隔线**、**两端对齐**、**首行缩进**
- **专注**：**聚焦模式**（调暗非当前内容、悬停行/光标行亮起，详见下节）、隐藏滚动条、隐藏状态栏
- **编辑器**：**当前行高亮**、**隐藏 Markdown 语法**（见下）
- **批注**：**红色下划线**（朱笔，见下）
- **文件树**：紧凑行高、显示缩进引导线

> 正文字号不在此处，请用 `Appearance → Font size`（推荐 17）。原因是 Obsidian 把字号写在
> `body` 的行内样式上，主题无法在不破坏原生滑杆的前提下覆盖它。

## 书籍排版（默认开启）

参考当代书籍排版，以下四项**默认开启**，都能在 `Style Settings → Folio → 版面` 一键关掉：

| 项 | 效果 |
| --- | --- |
| 标题居中（书名式） | 笔记标题（文件名）居中，像书页的章名 |
| 标题分隔线 | H1–H3 下方一条细线，**阅读视图与实时预览都生效** |
| 正文两端对齐 | 中文书籍常见的齐行 |
| 段落首行缩进两字 | 中文书籍正文的段落起首缩进（编辑区只对纯段落行生效） |

主题整体为**浅色**：浅白纸面（`#fcfbf8`）+ 墨色宋体。请在
`Appearance → Base color` 选择 **Light**。

## 隐藏 Markdown 语法

参考 Minimal 的 *Hide Markdown syntax*，在实时预览里隐藏 `**`、`*`、`~~`、`==`、`[[ ]]`、`#`
等标记（`cm-formatting-*`），让编辑区看起来更像成稿。

- 开启：`Style Settings → Folio → 隐藏 Markdown 语法`
- 注意：字符仍然存在，只是不显示；**光标所在那一行也照样隐藏**（与 Minimal 一致），
  且默认**不留占位**。唯一例外：当标记正好是该行最后一个元素时（例如刚打完 `##`
  的空标题），会保留标记宽度、只把字形变透明——否则光标没有落点会消失，后续输入
  也会跑到标记前面（标题打不出来）。因为它已在行尾，这点占位看不出来。

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

也就是说，**设 4 就是「4 列铺满，出现第 5 列才开始左右滑」**。

宽度是相对**表格的实际容器**算的（百分比），不是拿「正文栏宽」设置换算的绝对值 ——
所以面板比栏宽窄几像素时（窗口差一点、外边距、滚动条），≤ 设定值的列数也仍然是
正好 100%、不滚；窗口整体变窄时，各列只是跟着一起变窄，不会提前开始滚。

实现上靠一组 `table:has(tr > :nth-child(k))` 抬 `min-width`（CSS 数不出列数，只能
一个一个 k 写，靠层叠顺序取最大的那个 = 真实列数），**16 列封顶**；超过 16 列时
只有前 16 列撑开宽度，各列会被挤窄一点。

滚动条只出现在横向：容器上显式写了 `overflow-y: hidden`（容器一旦是滚动盒，
竖向会从 `auto` 派生，macOS「始终显示滚动条」下就会多出一条没用的竖条）。

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

## 配色与对比度

四套配色 = `body.theme-light/dark` × `folio-chatgpt-mode` 开关。所有色值都按 WCAG
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

## 设计取向（对应需求）

| 需求 | 落地方式 |
| --- | --- |
| 标题字号递减且大于正文 | `--h1-size`…`--h6-size` 用 `em`，均 > 1em；由 1.9em 递减到 1.02em |
| 标题颜色区分正文 | 独立的 `--folio-heading-*` 墨色，比正文更深/更亮 + 更重字重 |
| 标题上下留白 | `--heading-spacing`（默认 1.7em）+ 每级 `margin-block` |
| 复杂文档不费力 | 行高 1.75、段距 1.05em、栏宽 42rem（约 30~45 汉字/行） |
| 纸质书感 | 浅白纸面 + 墨色宋体正文、两端对齐、首行缩进、居中书名、标题分隔线、居中短分隔线 |
| 去除干扰 | 收敛侧栏/标签栏描边、可隐藏状态栏与滚动条、聚焦模式（调暗非当前内容 + 鼠标悬停行/光标行亮起 + 配套插件让光标行始终停在视口中间） |
| 文件树 | **文件夹与文件各有 SVG 图标**（都走 `mask`，颜色跟随主题）：文件夹是「开 / 关」两张切换，文件是一张折角纸；同样 15px + 7px 间距，所以两列图标对齐、文件夹名与文件名成列，层级一眼可辨；行距 / 圆角由 `--nav-item-*` 变量控制；字号 `--nav-item-size: 14px`（GPT 规范）；**缩进 22px** 让子项输出稳定落在父级之下 —— 这份缩进整份写进子级容器的 `padding-inline-start`、`margin` 归零，不走 `--nav-item-children-margin-start`（那条是 margin）：文件树的「无限滚动 / 虚拟化」会给每行套 inline 的 `margin` / `padding`（带 `!important`），走 margin 的那半会被折算掉，一级缩进只剩 ~6px、文件和上级目录就贴一起了；去掉缩进引导线；选中态 = 底色 + 字重（GPT 模式另有左侧强调竖条，挂在 `::after` 上，避免顶掉 `::before` 的文件图标；纸感模式去掉竖条，它是 App 的选中控件、不是纸上的记号）。**纸感模式**（关掉 ChatGPT 模式）整棵树按「书的目录」重做：换成正文衬线、图标降到 60% 不透明度（印刷符号而非 UI 控件）、行距放松一档、圆角收小、侧栏面板标题按页眉处理。全部包在 `body:not(.folio-chatgpt-mode)` 里，GPT 模式零影响 |
| ChatGPT 模式 | 一键切换「配色 + 字体 + 排版」：中性灰（浅色 `#ffffff` / `#f9f9f9` / `#f3f3f3`，主文字 `#212121`，次级 `#6b6b6b`，边框 `#e5e5e5`；深色 `#212121` 正文 / `#171717` 下沉侧栏 / `#262626` 浮出面板）+ 蓝色强调色 + **正文无衬线、标题沿用纸感衬线** + 左对齐 / 不缩进 / 标题不居中 / 标题无分隔线 |
| 字号层级 | 全局生效（两种模式都一样）：侧边栏 14px / 400、正文 16px / 行高 28px、H1 28px / 700、H2 22px / 700、代码块 13px、行内代码 0.88em、侧边栏分组标题 12px、标签标题 14px |
| 日历 | 给 Calendar 插件的 `.today` 加实心强调色底 + 反白文字，高亮当前日期 |
| 表格 | 默认全宽、列宽平分（`table-layout: fixed`，不随内容变化）、长内容换行；「每行最多列数」（默认 4）决定何时开始横滚：≤ 该值时正好占满可用宽度、**一点都不滚**，再多一列各列就守住「可用宽度 ÷ 列数」的下限不让位 → 表格整体变宽、容器横向滚动。宽度用百分比相对**实际容器**算（不是拿栏宽设置换算），所以面板比栏宽窄几像素也不会误滚；上限 16 列。滚动条只有横向（容器显式 `overflow-y: hidden`）。**两个视图给的滚动容器不一样**：实时预览里 Obsidian 自己把表格包进 `.table-wrapper`，主题给那个容器 `overflow-x: auto` 就够了；阅读视图里 Obsidian **不包**这层容器，纯 CSS 又补不出来 —— 置配套插件 `folio-table` 补上，两个视图就一致了（没装插件时，阅读视图会退回 Obsidian 的原生行为：表格撑破栏宽、由整个面板横滚）。另外「正文本身」两个视图都不横向滚动：阅读视图在栏容器上加 `overflow-x: clip`；实时预览把 Obsidian 表格组件那 16px 的「+」把手槽真让出来（`.cm-sizer` 上限 +32px、`.cm-content` 补 16px 内边距，代价是窄窗时正文会窄最多 32px） |
| 代码块 | 参考 ChatGPT 网页端：12px 圆角容器 + 细边框 + 内容内边距 16/18px + 13px / 行高 1.7 等宽。底色与纸面同温（**不是**中性灰）：纸感浅 `#f5f3ed` / 纸感深 `#232120`，GPT 浅 `#f6f6f6` / GPT 深 `#1a1a1a`。语法色统一走 `--code-*` 变量（阅读模式 Prism `.token.*` 与编辑器 `cm-*` 共用同一套）。编辑器里代码块是一串 `.cm-line`，中间行直角、只给首/末行圆角（不给围栏相邻行加圆角，否则留缺口） |
| 行内代码 | 半透明灰底 `rgba(127,127,127,0.13)` + 细边框 + 5px 圆角 |
| 当前行 / 加粗 | 光标所在行铺一层浅底，用一叠 `box-shadow`（每段平移量为行宽的 0.7 倍，保证互相咬合）横向铺满编辑区；底色不透明，避免半透明叠加出现色阶。加粗文字为朱批红（纸感 `#b03a2e` / 深色 `#e0736a`）—— 刻意与代码 keyword 的红拉开，避免「加粗」和「行内代码」共用同一支红笔、互相稀释强调 |
| 引用块 | 浅色圆角背景（`--folio-quote-bg`）+ 一条灰色左边线 + 上下内边距（`--folio-quote-pad`，默认 0.7em，可在 Style Settings 调）。编辑器里多行引用由逐行底拼成整段，**圆角与上下 padding 都只给首 / 末行** —— CM6 的引用是多个 `.cm-line`，padding 写进通用规则会把整段切成一块块；左边线改 `--blockquote-border-color` 且不再自加边框，避免与 Obsidian 默认的主体色竖线叠成两条 |
| 批注（红色下划线） | 原文 `<u>…</u>`，主题把 `u` / `ins` 渲染成朱红下划线：`text-decoration-color` 走 `--folio-u-color`，线比默认粗一档、往下压一点（`thickness` / `underline-offset`），并关掉 `text-decoration-skip-ink` 让整条线连成一笔。快捷键由配套插件 `folio-mark` 提供（`Cmd/Ctrl+U`）。**刻意不去动 `.cm-underline`** —— 那是内部链接的类，碰它会把所有链接一起染红 |
| 标注块（Callout） | 七个语义类型（note / tip / important / warning / caution / example / quote）各配一支色：左边 3px 语义色竖线 + 同色 7%（深色 10%）极浅底 + 语义色标题与图标，正文仍是墨色，圆角只留右侧 8px（与引用块对齐），左侧两角为直角。颜色收在 `--folio-co-*`（浅 / 深两套），语义强度照 GitHub Alerts 的排序；不列出的类型（info / success / danger…）统一落到 note 配色。**不碰 Obsidian 的 `--callout-color`**（1.13 起改了取值格式，依赖它会被钉死版本），改用自有的 `--folio-co` |

## 注意

- 旧 snippet `hide-tree-lines.css` / `edit-css.css` 与主题的文件树样式重叠，建议在
  `Settings → Appearance → CSS snippets` 里**关闭这两个**，避免 `!important` 打架。
- 主题显式接管正文与代码字体（`--font-text` / `--font-monospace`），所以 `Appearance` 里的
  「Text font / Monospace font」下拉会被主题覆盖；改字体请用 Style Settings。
- 深色模式保留了一套配套的「炭墨」配色，但本主题以浅色为主；不切到深色就不会生效。

## 开发

改 `theme.css` 后，Obsidian 会自动重载（软链指向本仓库，无需复制）。
`preview.html` 可直接用浏览器打开看排版，或用无头 Chrome 截图：

```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --screenshot=out.png \
  --window-size=900,1200 "file://$PWD/preview.html"
```

**改配色时用色卡**：`palette.gen.py` 从 `theme.css` 解析出四套配色的全部变量，
连同 WCAG 对比度和「改动前 → 改动后」对照渲染成一张 HTML 色卡。色块直接引用
主题自己的变量名，不会和 `theme.css` 跑偏：

```bash
python3 palette.gen.py && open palette.html
```

## 发布到社区主题

仓库根目录已具备上架所需文件：`manifest.json`、`theme.css`、`versions.json`、`README.md`、`LICENSE`。
还差：

1. 一张 `screenshot.png`（Obsidian 社区页展示图）
2. 推到 GitHub，向 [obsidianmd/obsidian-releases](https://github.com/obsidianmd/obsidian-releases) 提 PR

版本号同时更新 `manifest.json` 与 `versions.json`。
