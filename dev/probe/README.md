# 真实 Obsidian 探针

`probe.py` 另起一个 Obsidian 实例（**独立 `--user-data-dir`，不碰你自己的 vault 与配置**），
打开一个只含测试笔记的临时 vault —— 主题直接用**当前工作区那份 `theme.css`**（每次运行都重拷），
然后用远程调试 + CDP 模拟真实点击，量真实 DOM。

```bash
python3 dev/probe/probe.py            # 跑一遍（跑完自动关掉探针实例）
python3 dev/probe/probe.py --keep     # 留着实例，方便自己接 DevTools 继续看
python3 dev/probe/probe.py --port 9444 --dir /tmp/folio-probe
```

退出码：全部一致 `0`，有不一致 `1`（可以直接串进脚本里）。

## 为什么需要它

`preview.html` + 无头 Chrome 只能验「阅读视图那种静态 HTML」；实时预览里的表格不是那回事：

- 表格组件是 `.cm-content` 的**直接子元素**，不在任何 `.cm-line` 里（继承关系跟想当然的不一样）；
- 单元格里层那个 CodeMirror **只在光标进去时才存在**，而且会被 Obsidian 自己的 `app.css` 抢权重
  （`.cm-table-widget th, td { padding: 0 }` 权重 0-4-1，盖得住主题的 `.markdown-rendered td`）；
- 里层编辑器还会漏进主题里按**后代**写的规则（内边距 / 首行缩进 / 两端对齐 / letter-spacing）。

`letter-spacing` 那条就栽过一次：静态复现页把表格组件放进了 `.cm-line` 里，量出来
「有光标没光标都是 0.16px，不用改」，真实 DOM 里其实是「没光标没有、光标进去才有」，
每字多 0.16px 正好把折行点顶过去。**所以表格/编辑器相关的改动，一律在这儿量一遍再下结论。**

## 它检查什么

| # | 检查 | 判定 |
| --- | --- | --- |
| 1 | 同一格「没光标 vs 有光标」 | 文本起点（相对单元格）、行高、逐条视觉行的字数与右缘，全部要一致（±0.1px） |
| 1 | 里层 `.cm-line` 的四个复位 | `letter-spacing: normal`、`text-indent: 0px`、`text-align: start`、`text-justify: auto` —— 检查时会**把 `folio-book-indent` / `folio-justify` 两个模式都打开**，复位失效立刻现形 |
| 2 | 「实时预览 vs 阅读视图」 | 短格的文本起点与单行行高要一致；顺带打印内边距落在哪个元素上（实时预览在 `.table-cell-wrapper`、阅读视图在 `td`） |
| 3 | 表格横向可滚量 + 「+」把手贴边 | 逐层 `scrollLeft = 99999`：**≤ 设定列数**必须每一层都 0px；**> 设定列数**必须真能滚，且滚到底能看到表格右缘 |

观测对象是 `fixtures/表格测试.md`：**最长的格**、**最短的格**各取一个（检查 1/2 只认
DOM 里第一张表，2 列），加上它后面两张给检查 3 用的表（4 列 = 设定值边界、6 列 = 该滚的一侧）。
长格那 33 个字是特意挑的 —— 正好卡在折行点上，字距一变折行就跳，检查 1 才灵敏。
换内容时请保持这个性质（或直接把探针的判定当「同等布局下前后比」，别动窗口大小）。

检查 3 是「≤ 设定列数也还能左右滑几像素」那类回归的守门人。它必须**逐层**量：
实时预览里真正的滚动盒是 `.cm-table-widget`，但主题给阅读视图写的
`.markdown-rendered .table-wrapper { overflow-x: auto }` 连实时预览那层 wrapper 也会命中
（表格组件自己带 `markdown-rendered` 类）。只量 `.cm-table-widget` 会得到「0px，不滚」的
假结论，而实际能滑的正是 `.table-wrapper` —— 滑的正好是里面那个「+」列把手
（`.table-col-btn`，`inset-inline-start: 100%; width: 16px`，而 wrapper 自己 `padding: 0`）。
（CodeMirror 只渲染视口附近的块，所以检查 3 会先把整篇滚一遍、滚到哪张量哪张；
检查 1 也会先把目标格 `scrollIntoView` 再点 —— 否则真实鼠标事件落到窗口外面，点了个空。）

## 实现备查

- CDP 客户端是纯标准库写的（socket + base64 + 手搓 WebSocket 帧），不装任何依赖。
- Obsidian 路径写死 `/Applications/Obsidian.app/Contents/MacOS/Obsidian`（macOS 默认安装位置）。
- 探针实例由 `--user-data-dir` 隔离：跟你正在用的 Obsidian **并存**（单实例锁是按 user-data-dir 分的），
  退出时 `terminate()` 掉；`--keep` 留下的实例记得自己 `pkill -f folio-probe`。
- 测量都是「相对单元格边框盒」的坐标，跟窗口大小/缩放无关；比的是同一次运行里的两个状态。

---

# 手机视口探针（`mobile_probe.py`）

`probe.py` 量的是**桌面**；手机上的 `app.css` 有一整套挂在 `is-mobile` / `is-phone`
下面的规则（页边距、表格把手的槽、属性面板外扩……），桌面上量不到。`mobile_probe.py`
把真实 Obsidian 的视口用 CDP 压成手机尺寸（默认 393×852 @3x = iPhone 15/16 Pro），
再补上 `is-mobile is-phone is-ios` 三个类，量的还是真实 DOM。

```bash
python3 dev/probe/mobile_probe.py                     # 四组检查全跑
python3 dev/probe/mobile_probe.py --check table       # 只看表格单元格（逐格比有无光标）
python3 dev/probe/mobile_probe.py --check formats     # 只看各类格式体检
python3 dev/probe/mobile_probe.py --check clamp       # 只看阅读视图的横向夹取
python3 dev/probe/mobile_probe.py --check shell       # 只看手机外壳（顶栏透明度 / 日期框）
python3 dev/probe/mobile_probe.py --desktop           # 同一套检查跑桌面尺寸（对照用）
python3 dev/probe/mobile_probe.py --width 375         # 换机型宽度
python3 dev/probe/mobile_probe.py --theme old.css     # 拿另一份 theme.css 做前后对比
python3 dev/probe/mobile_probe.py --snippet snippets/folio-mobile.css
                                                      # 连 CSS 片段一起加载（可重复）
```

`--snippet` 走的是 Obsidian 真正加载片段的路径（拷进探针 vault 的 `.obsidian/snippets/`
并写进 `appearance.json` 的 `enabledCssSnippets`）。**片段是在主题之后加载的** ——
手机上那个「光标进单元格变成一个字一行」的 bug 就出在这条层叠上：
片段里 `body.is-mobile .markdown-source-view.mod-cm6 .cm-content { padding-inline: 14px }`
的权重是 0-4-1，正好比主题的复位（0-4-0）高一位，于是那 14px 连单元格里层编辑器一起改到。
复现：`--theme <旧的 theme.css> --snippet <那份片段>`；验收：换上带 `!important` 的复位。

## 一个前提：桌面外壳要补成手机的样子

桌面 App 里没有手机版的 `.mod-visible` 标记，而 app.css 有一条
`.is-phone .mod-root .workspace-split:not(.mod-visible) { display: none }` ——
不补这个类，主编辑区会被整块 `display:none`，量到的宽度全是 0。探针会补上它
（真机上 App 自己会加）。另外实时预览与阅读视图会在同一个叶子里并存，
所以每项检查都先问 App「现在是哪个模式」，只在那个模式的那棵子树里量。

## 它检查什么

| # | 检查 | 判定 |
| --- | --- | --- |
| A | 编辑器横向几何 | `.cm-scroller → sizer → content → 表格组件 → wrapper → table` 逐层的 x / 宽 / 内边距 / 能不能横滚；顺带报「正文左右各留白多少、每列多宽」 |
| B | 表格单元格逐格比 | 同一张表**每一格**「没光标 vs 有光标」的文本起点与逐行字数必须一致；不一致就打印里层编辑器逐层（盒宽 / clientW / 内边距 / overflow-x / 字号 / 行高）与光标位置 |
| C | 各类格式体检 | 标题 / 引用 / 标注块 / 代码块 / 表格 / 标签 / 行内代码 / 数学 / 脚注 / 嵌入 / 折叠箭头 / 属性面板 …… 逐个量：有没有伸出视口、被哪个祖先裁掉、内容比盒子宽而盒子又滚不动；阅读视图是分段懒渲染的，所以整篇滚一遍逐段扫（每类只报「问题最多」的那次） |
| E | 手机外壳 | 顶栏 / 状态栏那一条 / 按钮药丸必须是不透明纸底（正文不再从底下透出来）；属性面板的日期输入框要放得下数值（iOS 会把原生日历图标画在左端压字） |
| D | 阅读视图的横向夹取 | 栏容器必须是真 `clip`、面板横滚量 0、竖轴照旧能滚；**折叠箭头与属性面板的外扩必须还能命中**（`elementFromPoint` —— 被裁掉的东西点不到） |

检查 3 还量一条：列「+」把手与表格右缘的距离必须是 0（±1px）。把手是 `.table-wrapper`
的绝对定位子元素，wrapper 一不等于表格宽，它就会叠在表格内容上 —— 所以「撑开」必须
写在 wrapper 上（列数 > 设定值时才现形，手机上尤其明显）。

## 已经靠它定过的案

- **单元格里层编辑器比格子还宽**（`.cm-content` 的 flex `min-width: auto` 顶穿窄列）：手机上点进「2024.11.14」那格，
  没光标两行 [6,4] → 有光标一行 [10]，文字溢出格子。修法见 theme.css §5 第五条复位。
- **折行方式两端不一致**：单元格静态文本吃 `th/td` 的 `overflow-wrap: anywhere`，里层编辑器被 app.css 改成了
  `normal`，同一个格点进去就不折了。修法：同权重、排后地把 anywhere 写回去。
- **阅读视图的横向夹取夹错了地方**：夹在 `.markdown-preview-sizer` 上时，标题折叠箭头（`margin-inline-start: -22px`／手机 -20px）
  与手机版属性面板的外扩（`translateX(-12px)`）整根落在裁剪区外 —— 箭头不只是看不见，是点都点不到。
  修法：`overflow-clip-margin: 24px`（只放宽裁剪框，不产生滚动盒）。
- **横向滚动表格时，「+」把手叠在表格内容上**：`.table-col-btn` 挂在 `.table-wrapper` 的
  `inset-inline-start: 100%` 上，而主题原来把「撑开」写在表格上 → wrapper 还是 100%（容器宽），
  表格却已经 133% → 把手落在表格里侧（手机实测 -109.66px，正好压在「备注」列的字上）。
  修法：实时预览改撑 wrapper（表格那层 `min-width: 0` 兜住，不然会 (k ÷ 设定值)²），
  阅读视图照旧撑表格。
- **手机上正文比阅读视图窄 32px**、表格被压窄 32px：桌面那 16px 的 `.cm-content` 内边距在手机上纯属白窄
  （Obsidian 自己已经给了页边距）。修法见 theme.css §14。
- **「光标进单元格就一个字一行」，只在 iPhone 上出现**：不是 iOS 的 app.css 有什么特别，而是手机上的
  `folio-mobile` 片段（0-4-1）压过了主题的复位（0-4-0）—— 用 `--snippet` 把这层叠搬进探针，
  桌面尺寸下也能一模一样地复现（80px 的格子：没光标 12.5px、有光标 26.5px、每行一个字）。
  修法：片段不再写 `.cm-content` 内边距 + 主题复位加 `!important`。
