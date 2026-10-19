#!/usr/bin/env bash
# 把主题同步到「手机 / iPad 那个库」（默认是 iCloud 里的 iphone_note）。
#
# 用法：
#   ./sync-mobile.sh                       # 同步到默认的 iCloud 库
#   ./sync-mobile.sh /path/to/vault        # 同步到别的库（比如 Sn 里的另一个）
#
# 为什么需要它：桌面这个库的 .obsidian/themes/Folio 是**软链接**（见 install.sh），
# iCloud / Obsidian Sync 都不会跟随软链接 —— 所以手机上的那份只能是真的文件、
# 得单独拷一次。这个脚本就是那次拷贝，顺手比一下两边是不是同一份。
#
# 拷完到手机上：完全退出 Obsidian（上滑掉）再打开 —— 主题 CSS 在启动时读，
# 只切前后台不一定重新加载。想确认版本：设置 → 外观 → 主题，Folio 那份的
# theme.css 里搜「§14」或「手机视口探针」，能搜到就是新的。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$HOME/Library/Mobile Documents/iCloud~md~obsidian/Documents/iphone_note}"
DEST="$VAULT/.obsidian/themes/Folio"

[ -d "$VAULT" ] || { echo "✗ 找不到库：$VAULT" >&2; exit 1; }
mkdir -p "$DEST"

copy() {   # copy <源文件> <目标目录>
  local f="$1" dir="$2" base
  base="$(basename "$f")"
  if [ -f "$dir/$base" ] && cmp -s "$f" "$dir/$base"; then
    echo "＝ 没变：${base}"
  else
    cp "$f" "$dir/$base"
    echo "✓ 已更新：${base}"
  fi
}

copy "$SRC/theme.css" "$DEST"
copy "$SRC/manifest.json" "$DEST"

# 手机补丁片段也一起同步（它就是那个「光标进单元格变一个字一行」的元凶所在地，
# 修好的版本在 snippets/folio-mobile.css）。文件名不能改：Obsidian 是按文件名
# 记「哪些片段开着」的，改名＝自动关闭。
SNIP="$VAULT/.obsidian/snippets"
mkdir -p "$SNIP"
for f in "$SRC"/snippets/*.css; do
  [ -e "$f" ] || continue
  copy "$f" "$SNIP"
done

VERSION="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["forkVersion"])' "$SRC/manifest.json")"

# 版本号两处必须一致（theme.css 的 --folio-version 是手机上徽标读的那个），
# 不一致就直接拦下来 —— 否则手机上会显示旧版本号，白折腾一次同步。
if ! grep -q -- "--folio-version: \"v${VERSION}" "$SRC/theme.css"; then
  echo "✗ 版本号对不上：manifest.json 的 forkVersion = ${VERSION}，" >&2
  echo "  但 theme.css 里没有 --folio-version: \"v${VERSION}…\" —— 先改成一致再同步。" >&2
  exit 1
fi

echo "→ 目标：${DEST}"
echo "  两边 theme.css 是否一致：$(cmp -s "$SRC/theme.css" "$DEST/theme.css" && echo 是 || echo 否)"
echo "  指纹（md5 前 8 位）：$(md5 -q "$DEST/theme.css" | cut -c1-8)"
echo "  主题版本（theme.css 里的 --folio-version）：${VERSION}"
echo "  片段目录：${SNIP}"
echo
echo "  手机上怎么确认加载到了最新：打开 Obsidian 时会浮出一枚版本徽标"
echo "  （folio-mobile 片段画的），绿色写着「Folio 主题 v${VERSION}」＝ 最新；"
echo "  红色写着「未知版本」＝ theme.css 还没同步过去。"
echo "  记得在手机上完全退出 Obsidian 再打开（主题是启动时读的）。"
