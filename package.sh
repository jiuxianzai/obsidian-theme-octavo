#!/usr/bin/env bash
# 打一个可直接分享的主题 zip 到 ~/Downloads（或指定目录）
#
# 用法：
#   ./package.sh                # 输出到 ~/Downloads
#   ./package.sh /path/to/dir   # 输出到指定目录
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HOME/Downloads}"
VERSION="$(sed -n 's/.*"version"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p' "$SRC/manifest.json" | head -1)"
NAME="folio-obsidian-theme-v$VERSION"

if [ -z "$VERSION" ]; then
  echo "✗ 读不到 manifest.json 里的 version" >&2
  exit 1
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$NAME"

# 只放「使用者需要」的文件，不放 install.sh / preview.html 这类开发文件
cp "$SRC/theme.css" \
   "$SRC/manifest.json" \
   "$SRC/versions.json" \
   "$SRC/LICENSE" \
   "$SRC/INSTALL.md" \
   "$SRC/README.md" \
   "$SRC/screenshot.png" \
   "$STAGE/$NAME/"

rm -f "$OUT/$NAME.zip"
( cd "$STAGE" && zip -r -X "$OUT/$NAME.zip" "$NAME" >/dev/null )

echo "✅ 已生成： $OUT/$NAME.zip"
echo "   解压后把 $NAME 文件夹改名为 Folio，放进 <你的库>/.obsidian/themes/"
