# 参考与致谢 / Credits

Folio Paper 是一个独立实现的 Obsidian 主题。下面列出公开参考对象、使用范围与许可，
以便读者和原作者追溯。

## 主题与实现

### Folio · elijahchan2019 / elijah7x

- 仓库：https://github.com/elijahchan2019/obsidian-folio-theme
- 许可：MIT
- 关系：**名称与早期命名参考，独立实现，未复用其 CSS 代码。**
  本项目早期曾使用 `Folio` 作为主题名，并在本地与官方 Folio 同名同 ID；
  公开版已更名为 **Folio Paper**，以避免与官方主题混淆。
  本项目不是 elijahchan2019 / elijah7x 的官方版本，也不代表其立场。

### Minimal · kepano

- 仓库：https://github.com/kepano/obsidian-minimal
- 许可：MIT
- 关系：「隐藏 Markdown 语法」这一交互思路的参考。相关 CSS 为本项目自行编写，
  没有直接复制 Minimal 的样式表。

### GitHub Alerts

- 文档：https://docs.github.com/en/get-started/writing-on-github/getting-started-with-writing-and-formatting-on-github/basic-writing-and-formatting-syntax#alerts
- 关系：七类标注块（note / tip / important / warning / caution / example / quote）
  的语义分级参考。配色、竖线、底色与图标均按本主题的纸感语言重做。

### ChatGPT 网页端 · OpenAI

- 关系：现代模式（Modern）的配色与排版观感参考。
- 本项目与 OpenAI 无隶属、合作或背书关系，未使用其商标、字体文件或页面素材。

### 其他观感参考

- **中文书籍排版传统**：两端对齐、首行缩进、居中书名、朱批。
- **VS Code**：文件树的结构与紧凑行高。
- **Bear**：字体选择与写作界面的克制感。

这些属于公共设计惯例或观感参考，不涉及代码复制。

## 可选插件

### Style Settings · mgmeyers

- 仓库：https://github.com/mgmeyers/obsidian-style-settings
- 许可：MIT
- 关系：可选的调参面板。主题里的 `/* @settings */` 块遵循它的格式；
  不安装它时，主题默认外观完全不受影响。

## 字体

主题**不打包任何字体文件**，只在字体栈里按顺序引用候选字体：

| 字体 | 许可 / 来源 |
| --- | --- |
| Iowan Old Style | macOS 系统字体 |
| Noto Serif CJK SC / 思源宋体 | SIL Open Font License 1.1 |
| LXGW WenKai / 霞鹜文楷 | SIL Open Font License 1.1 |
| Maple Mono | SIL Open Font License 1.1 |
| Bear Sans UI | 仅作为字体名候选，不随主题分发 |

## 如果归属有误

如果你是本项目参考对象之一的作者，认为这里的署名、范围或许可有误，
请在本仓库开 Issue，我们会尽快修正或移除相关内容。
