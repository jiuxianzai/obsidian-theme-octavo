#!/usr/bin/env bash
# 把 Folio Paper 链接到某个 Obsidian vault 的 .obsidian/themes/Folio Paper
#
# 用法：
#   ./install.sh /path/to/your/vault
#
# 为什么用软链：Obsidian 只认 .obsidian/themes/<名字>/theme.css，
# 而 .obsidian/ 通常被 vault 的 .gitignore 忽略。
# 把主题独立成仓库、再软链进去，主题就能独立做版本管理。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-}"

if [ -z "$VAULT" ]; then
  echo "用法：./install.sh /path/to/your/vault" >&2
  exit 1
fi

if [ ! -d "$VAULT/.obsidian" ]; then
  echo "✗ 这不像一个 Obsidian 库（找不到 $VAULT/.obsidian）" >&2
  exit 1
fi

DEST="$VAULT/.obsidian/themes/Folio Paper"

mkdir -p "$VAULT/.obsidian/themes"
if [ -e "$DEST" ] && [ ! -L "$DEST" ]; then
  echo "✗ $DEST 已经存在且不是软链接。请先备份或移走它，再重跑。" >&2
  exit 1
fi
rm -f "$DEST"
ln -s "$SRC" "$DEST"

echo "✅ 已链接： $DEST  ->  $SRC"
echo "   打开 Obsidian → Settings → Appearance → Themes，选择 “Folio Paper”"
