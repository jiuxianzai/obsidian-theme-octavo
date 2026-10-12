#!/usr/bin/env bash
# 把 Folio 主题链接到某个 Obsidian vault 的 .obsidian/themes/Folio
#
# 用法：
#   ./install.sh                          # 默认链接到同级的 obsidian-library vault
#   ./install.sh /path/to/your/vault      # 链接到指定 vault
#
# 为什么用软链：Obsidian 只认 .obsidian/themes/<名字>/theme.css，
# 而 .obsidian/ 通常被 vault 的 .gitignore 忽略。
# 把主题独立成仓库、再软链进去，主题就能独立做版本管理。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$(cd "$SRC/../obsidian-library" && pwd)}"
DEST="$VAULT/.obsidian/themes/Folio"

mkdir -p "$VAULT/.obsidian/themes"
rm -rf "$DEST"
ln -s "$SRC" "$DEST"

echo "✅ 已链接： $DEST  ->  $SRC"
echo "   打开 Obsidian → Settings → Appearance → Themes，选择 “Folio”"
