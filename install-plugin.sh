#!/usr/bin/env bash
# 把 Folio 主题的配套插件「Folio Typewriter」装进某个 Obsidian vault。
#
# 用法：
#   ./install-plugin.sh                     # 默认装到同级的 obsidian-library vault
#   ./install-plugin.sh /path/to/your/vault # 或指定 vault
#
# 做了什么：
#   1. 把 plugin/folio-typewriter 软链到 <vault>/.obsidian/plugins/folio-typewriter
#   2. 把插件 id 写进 <vault>/.obsidian/community-plugins.json（幂等）
#
# 装完需要重启 Obsidian，或在「设置 → 第三方插件」里重载。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$(cd "$SRC/../obsidian-library" && pwd)}"
PLUGINS="$VAULT/.obsidian/plugins"
DEST="$PLUGINS/folio-typewriter"
ID="folio-typewriter"

if [ ! -f "$SRC/plugin/$ID/main.js" ]; then
  echo "✗ 找不到插件源文件：$SRC/plugin/$ID/main.js" >&2
  exit 1
fi

mkdir -p "$PLUGINS"
rm -rf "$DEST"
ln -s "$SRC/plugin/$ID" "$DEST"

REG="$VAULT/.obsidian/community-plugins.json"
python3 - "$REG" "$ID" <<'PY'
import json, os, sys

reg, plugin_id = sys.argv[1], sys.argv[2]
data = []
if os.path.exists(reg):
    try:
        with open(reg, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        data = []
if not isinstance(data, list):
    data = []
if plugin_id not in data:
    data.append(plugin_id)
with open(reg, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")
print("已登记到 community-plugins.json" + ("（新增）" if plugin_id in data else ""))
PY

echo "✅ 已安装： $DEST  ->  $SRC/plugin/$ID"
echo "   重启 Obsidian（或 设置 → 第三方插件 → 重载）后即可生效。"
echo "   聚焦模式打开时，光标所在行会停在视口中间。"
