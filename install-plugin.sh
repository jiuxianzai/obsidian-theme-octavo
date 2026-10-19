#!/usr/bin/env bash
# 把 Folio 主题的配套插件装进某个 Obsidian vault（会装 plugin/ 下的全部插件）。
#
# 用法：
#   ./install-plugin.sh                     # 默认装到同级的 obsidian-library vault
#   ./install-plugin.sh /path/to/your/vault # 或指定 vault
#
# 做了什么：
#   1. 把 plugin/<id> 逐个软链到 <vault>/.obsidian/plugins/<id>
#   2. 把插件 id 写进 <vault>/.obsidian/community-plugins.json（幂等）
#
# 装完需要重启 Obsidian，或在「设置 → 第三方插件」里重载。
set -euo pipefail

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${1:-$(cd "$SRC/../obsidian-library" && pwd)}"
PLUGINS="$VAULT/.obsidian/plugins"
REG="$VAULT/.obsidian/community-plugins.json"

mkdir -p "$PLUGINS"

installed=()
for dir in "$SRC"/plugin/*/; do
  [ -d "$dir" ] || continue
  ID="$(basename "$dir")"
  if [ ! -f "$dir/main.js" ]; then
    echo "✗ 跳过 $ID：缺 main.js" >&2
    continue
  fi

  DEST="$PLUGINS/$ID"
  rm -rf "$DEST"
  ln -s "${dir%/}" "$DEST"
  installed+=("$ID")
  echo "✅ 已安装： $DEST  ->  ${dir%/}"
done

if [ ${#installed[@]} -eq 0 ]; then
  echo "✗ plugin/ 下没有找到任何插件" >&2
  exit 1
fi

python3 - "$REG" "${installed[@]}" <<'PY'
import json, os, sys

reg, *plugin_ids = sys.argv[1:]
data = []
if os.path.exists(reg):
    try:
        with open(reg, encoding="utf-8") as f:
            data = json.load(f)
    except (ValueError, OSError):
        data = []
if not isinstance(data, list):
    data = []

added = [pid for pid in plugin_ids if pid not in data]
data.extend(added)
with open(reg, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
    f.write("\n")

print("已登记到 community-plugins.json：" + ("、".join(added) if added else "无新增"))
PY

echo "   重启 Obsidian（或 设置 → 第三方插件 → 重载）后即可生效。"
echo "   · folio-typewriter：聚焦模式打开时，光标所在行停在视口中间"
echo "   · folio-mark：Cmd/Ctrl+U 给选中文字加 / 去红色下划线"
echo "   · folio-toolbar：选中文字浮出格式工具条（加粗 / 链接 / 格式转换…）"
