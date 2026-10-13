/*
 * Folio Typewriter —— 打字机滚动（配套 Folio 主题）
 *
 * 作用：让「光标所在行」始终停在编辑器视口的垂直中心。
 * 这是 CSS 做不到的事：浏览器只保证光标不被裁掉，不会主动把它滚到中间，
 * 必须由 JS 在每次光标/内容变化后重新计算 scrollTop，所以做成一个轻量插件。
 *
 * 逻辑刻意只依赖 DOM（.cm-scroller / .cm-line.cm-active），不 import CodeMirror，
 * 因此不需要任何构建步骤，main.js 就是最终产物。
 */

const { Plugin, MarkdownView, PluginSettingTab, Setting } = require("obsidian");

const FOCUS_CLASS = "folio-focus-dim";

const DEFAULT_SETTINGS = {
  // 未开启 Folio「聚焦模式」时是否也居中
  alwaysCenter: false,
  // 居中时用平滑滚动（光标快速移动时会略有迟滞）
  smooth: false,
};

class FolioTypewriter extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.pending = false;

    // 内容变化 / 光标移动 / 点击定位：都重新居中
    this.registerEvent(
      this.app.workspace.on("editor-change", () => this.schedule())
    );
    this.registerDomEvent(document, "selectionchange", () => this.schedule());
    this.registerDomEvent(document, "click", () => this.schedule());
    this.registerDomEvent(document, "keyup", () => this.schedule());

    // 「聚焦模式」是 Style Settings 的 class-toggle，开关时会改 <body> 的 class。
    // 监听它，好在聚焦模式关掉的那一刻停止居中。
    this.classObserver = new MutationObserver(() => this.schedule());
    this.classObserver.observe(document.body, {
      attributes: true,
      attributeFilter: ["class"],
    });
    this.register(() => this.classObserver.disconnect());

    this.addSettingTab(new FolioTypewriterSettingTab(this.app, this));
  }

  /** 当前是否应当居中：总是居中，或仅在聚焦模式打开时居中 */
  isEnabled() {
    return (
      this.settings.alwaysCenter ||
      document.body.classList.contains(FOCUS_CLASS)
    );
  }

  /** 把多次触发合并到下一帧——避免每次按键都同步测量、计算 */
  schedule() {
    if (this.pending) return;
    this.pending = true;
    requestAnimationFrame(() => {
      this.pending = false;
      this.center();
    });
  }

  center() {
    if (!this.isEnabled()) return;

    const view = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (!view) return;

    const scroller = view.containerEl.querySelector(".cm-scroller");
    if (!scroller) return;

    const line =
      scroller.querySelector(".cm-line.cm-active") ||
      scroller.querySelector(".cm-line.cm-activeLine");
    if (!line) return;

    const lineRect = line.getBoundingClientRect();
    const scRect = scroller.getBoundingClientRect();
    const delta =
      lineRect.top + lineRect.height / 2 - (scRect.top + scRect.height / 2);

    const max = scroller.scrollHeight - scroller.clientHeight;
    const target = Math.max(0, Math.min(max, scroller.scrollTop + delta));

    // 已经在中心（误差 < 1px）就别写 scrollTop，省掉无谓的重绘
    if (Math.abs(target - scroller.scrollTop) < 1) return;

    if (this.settings.smooth) {
      scroller.scrollTo({ top: target, behavior: "smooth" });
    } else {
      scroller.scrollTop = target;
    }
  }
}

class FolioTypewriterSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Folio Typewriter" });

    new Setting(containerEl)
      .setName("始终居中")
      .setDesc(
        "即使没有开启 Folio 主题的「聚焦模式」，也让光标所在行保持在视口中间。"
      )
      .addToggle((t) =>
        t.setValue(this.plugin.settings.alwaysCenter).onChange(async (v) => {
          this.plugin.settings.alwaysCenter = v;
          await this.plugin.saveData(this.plugin.settings);
        })
      );

    new Setting(containerEl)
      .setName("平滑滚动")
      .setDesc("居中时用动画过渡。光标快速移动时可能略有迟滞，默认关闭。")
      .addToggle((t) =>
        t.setValue(this.plugin.settings.smooth).onChange(async (v) => {
          this.plugin.settings.smooth = v;
          await this.plugin.saveData(this.plugin.settings);
        })
      );
  }
}

module.exports = FolioTypewriter;
