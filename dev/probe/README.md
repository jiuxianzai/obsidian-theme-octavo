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
| 3 | 表格横向可滚量 | 逐层 `scrollLeft = 99999`：**≤ 设定列数**必须每一层都 0px；**> 设定列数**必须真能滚，且滚到底能看到表格右缘 |

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
