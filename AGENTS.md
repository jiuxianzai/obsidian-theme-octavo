# AGENTS.md · Folio Paper

给编码 Agent 的机器可读说明。人类使用说明见 [README.md](README.md) / [INSTALL.md](INSTALL.md)。

## 1. 这是什么

Folio Paper 是一个纯 CSS 的 Obsidian 主题，**零插件依赖**。仓库只包含：

```
theme.css        ← 全部样式 + Style Settings 配置块
manifest.json    ← 主题元信息
versions.json    ← 版本 → 最低 Obsidian 版本
screenshot.png   ← 社区市场展示图（512×288）
screenshots/     ← README 用的高清截图
```

没有构建步骤，没有 `node_modules`，没有插件源码。

## 2. 安装到用户的 vault

目标目录：

```
<vault>/.obsidian/themes/Folio Paper/
├── manifest.json
└── theme.css
```

推荐命令（macOS / Linux）：

```bash
VAULT="/path/to/vault"
mkdir -p "$VAULT/.obsidian/themes/Folio Paper"
cp theme.css manifest.json "$VAULT/.obsidian/themes/Folio Paper/"
```

然后让 Obsidian 启用它，二选一：

1. 用户在 `设置 → 外观 → 主题` 里选 **Folio Paper**（推荐，最稳）
2. 修改 `<vault>/.obsidian/appearance.json`，把 `"cssTheme"` 设为 `"Folio Paper"`。
   改 JSON 前先备份；保留其他字段；文件可能不存在，不存在就新建。

不要做这些事：

- 不要安装任何社区插件（包括 Style Settings；它只是可选调参）
- 不要改 `theme.css` 来实现用户的一次性偏好；写到
  `<vault>/.obsidian/snippets/folio-paper-overrides.css`，并在
  `<vault>/.obsidian/appearance.json` 的 `enabledCssSnippets` 里启用
- 不要新增 `@import`、远程字体、`url(http...)` 依赖
- 不要重命名 `theme.css` / `manifest.json`
- 不要删除 `manifest.json` 里的 `name` / `version` / `minAppVersion`

## 3. 主题契约

### 主题名与目录

- 显示名：`Folio Paper`
- 安装目录：`.obsidian/themes/Folio Paper/`
- 当前版本：见 `manifest.json`

### 默认外观（无插件）

默认是**纸感模式**，以下样式在没有任何 body 类时也生效：

- 正文两端对齐
- 段落首行缩进 2em
- 标题居中
- H1–H3 标题分隔线
- `<u>文字</u>` 朱红下划线
- 当前行浅底高亮
- 文件树按「书的目录」排版
- 表格 4 列上限，手机 3 列

### 可切换的 body 类

| 类 | 作用 | 默认 |
| --- | --- | --- |
| `folio-modern-mode` | 现代模式：中性灰 + 蓝、无衬线、左对齐 | 关 |
| `folio-no-justify` | 关闭两端对齐 | 不添加 |
| `folio-no-book-indent` | 关闭首行缩进 | 不添加 |
| `folio-no-title-centered` | 标题左对齐 | 不添加 |
| `folio-no-heading-rule` | 关闭标题分隔线 | 不添加 |
| `folio-no-u-red` | 关闭朱红下划线 | 不添加 |
| `folio-no-active-line` | 关闭当前行高亮 | 不添加 |
| `folio-free-width` | 正文占满全宽 | 关 |
| `folio-focus-dim` | 聚焦模式：调暗非当前内容 | 关 |
| `folio-hide-scrollbars` | 隐藏滚动条 | 关 |
| `folio-hide-status-bar` | 隐藏底部状态栏 | 关 |
| `folio-hide-markdown` | 隐藏 Markdown 语法标记 | 关 |
| `folio-tree-compact` | 文件树紧凑行高 | 关 |
| `folio-tree-lines` | 文件树缩进引导线 | 关 |

> `folio-no-*` 只用于 Style Settings 的「关」选项，或用户明确要求时手动加；
> 不要把它们当成常规配置入口。

### 主要 CSS 变量

变量都定义在 `theme.css` 的 `body { ... }` 顶部，片段里可直接覆盖：

```css
body {
  --folio-text-font: "Iowan Old Style", "Noto Serif CJK SC", "Songti SC", Georgia, serif;
  --folio-tree-font: "Bear Sans UI", "Noto Sans SC", "PingFang SC", -apple-system, sans-serif;
  --folio-mono-font: "Maple Mono", "JetBrainsMono NFM", ui-monospace, monospace;
  --folio-line-height: 1.75;
  --folio-para-spacing: 1.05em;
  --folio-content-width: 42rem;
  --folio-heading-spacing: 1.7em;
  --folio-table-cols: 4;
  --folio-table-cols-mobile: 3;
}
```

### Style Settings 配置

`theme.css` 顶部有一个 `/* @settings ... */` 块。它只在用户装了
[Style Settings](https://github.com/mgmeyers/obsidian-style-settings) 时生效；
没有插件时整块会被忽略，不影响默认样式。

- 默认开启的项用 `class-select` + `folio-no-*`
- 默认关闭的项用 `class-toggle`
- 新增设置项时保持这个约定，否则「零插件默认外观」会被破坏

## 4. 常见任务

### 改正文栏宽

优先让用户建片段：

```css
body { --folio-content-width: 46rem; }
```

不要直接改 `theme.css`，除非用户要求提交上游。

### 切换现代模式

装 Style Settings 时用面板；否则可以临时在开发者工具里：

```js
document.body.classList.add('folio-modern-mode');
```

持久化不要在主题里写死；让用户用 Style Settings 或片段。

### 检查是否生效

```js
// Obsidian 开发者工具 / 任意能执行 JS 的地方
document.body.classList.contains('theme-dark')        // 深色是否启用
getComputedStyle(document.body).getPropertyValue('--folio-content-width')
document.querySelector('.theme-light, .theme-dark')   // 主题是否加载
```

更直接：`设置 → 外观 → 主题` 里当前项应显示 **Folio Paper**。

## 5. 修改主题时的验证清单

1. `manifest.json` 的 `version` 与 `versions.json` 的键同步
2. 不新增插件依赖，不新增网络字体
3. 默认（无 body 类）仍是纸感模式
4. `folio-modern-mode` 下配色 / 字体 / 对齐都切换
5. 浅色 / 深色都检查
6. 桌面与手机视口都检查（至少 393px 宽）
7. 表格 ≤ 4 列不横滚，> 4 列可横滚
8. `@settings` 的 YAML 仍能被 Style Settings 解析

## 6. 参考

- Folio（elijahchan2019 / elijah7x，MIT）：名称与早期命名参考，独立实现，无代码派生
- Minimal（kepano，MIT）：隐藏 Markdown 语法的思路参考
- GitHub Alerts：标注块语义分级参考
- ChatGPT 网页端：现代模式的视觉参考，无隶属关系

完整说明见 [CREDITS.md](CREDITS.md)。

授权：MIT。详见 [README.md](README.md) 的「参考与致谢」。
