#!/usr/bin/env bash
# 打一个可直接分享的主题 zip 到 ~/Downloads（或指定目录）
#
# 用法：
#   ./package.sh                # 输出到 ~/Downloads
#   ./package.sh /path/to/dir   # 输出到指定目录
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUT="${1:-$HOME/Downloads}"
VERSION="$(python3 - "$SRC/manifest.json" <<'PY'
import json, sys
print(json.load(open(sys.argv[1], encoding="utf-8"))["version"])
PY
)"
NAME="folio-paper-v$VERSION"
FOLDER="Folio Paper"

if [ -z "$VERSION" ]; then
  echo "✗ 读不到 manifest.json 里的 version" >&2
  exit 1
fi

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT
mkdir -p "$STAGE/$FOLDER"

# 只放「使用者需要」的文件，不放 install.sh 这类开发文件
cp "$SRC/theme.css" \
   "$SRC/manifest.json" \
   "$SRC/versions.json" \
   "$SRC/LICENSE" \
   "$SRC/CREDITS.md" \
   "$SRC/INSTALL.md" \
   "$SRC/README.md" \
   "$SRC/screenshot.png" \
   "$STAGE/$FOLDER/"

if [ -d "$SRC/screenshots" ]; then
  cp -R "$SRC/screenshots" "$STAGE/$FOLDER/"
fi

rm -f "$OUT/$NAME.zip"
( cd "$STAGE" && zip -r -X "$OUT/$NAME.zip" "$FOLDER" >/dev/null )

echo "✅ 已生成： $OUT/$NAME.zip"
echo "   解压后把 $FOLDER 文件夹放进 <你的库>/.obsidian/themes/"
