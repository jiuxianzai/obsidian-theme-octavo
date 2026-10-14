#!/usr/bin/env bash
# 把插件源码镜像到各自的私有仓库（单一开发源 → 多个发布仓库）
#
# 开发仍然在原地，本脚本只负责「同步过去」：
#   plugin/folio-mark       → github.com/jiuxianzai/obsidian-folio-mark
#   plugin/folio-table      → github.com/jiuxianzai/obsidian-folio-table
#   plugin/folio-typewriter → github.com/jiuxianzai/obsidian-folio-typewriter
#   <vault>/.obsidian/plugins/dashboard → github.com/jiuxianzai/obsidian-dashboard
#
# 用法：
#   ./sync-plugins.sh                    # 同步全部
#   ./sync-plugins.sh folio-table        # 只同步指定插件（可写多个）
#   ./sync-plugins.sh --dry-run          # 只报告会改什么，不提交不推送
#   ./sync-plugins.sh -m "提交信息"       # 自定义提交信息
#
# 环境变量：
#   PLUGIN_OWNER       默认 jiuxianzai
#   PLUGIN_REMOTE_BASE 默认 https://github.com/${PLUGIN_OWNER}（测试时可指向本地 bare 仓库）
#   PLUGIN_SYNC_CACHE  默认 ~/.cache/folio-plugin-sync（每个仓库的本地镜像）
#   VAULT_DIR          默认 ../obsidian-library
#
# 说明：仓库里的 README.md / LICENSE / .gitignore 属于「仓库自己」，同步时既不覆盖也不删除。
set -euo pipefail

OWNER="${PLUGIN_OWNER:-jiuxianzai}"
REMOTE_BASE="${PLUGIN_REMOTE_BASE:-https://github.com/$OWNER}"
CACHE="${PLUGIN_SYNC_CACHE:-$HOME/.cache/folio-plugin-sync}"

THEME_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT_DIR="${VAULT_DIR:-$(cd "$THEME_DIR/../obsidian-library" && pwd)}"

DRY_RUN=0
MSG=""
ONLY=()
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run)     DRY_RUN=1; shift ;;
    -m|--message)  MSG="${2:?-m 需要跟一个提交信息}"; shift 2 ;;
    -h|--help)     sed -n '2,26p' "$0"; exit 0 ;;
    -*)            echo "未知参数：$1" >&2; exit 2 ;;
    *)             ONLY+=("$1"); shift ;;
  esac
done

# id | 源目录 | 仓库名 | 额外排除（逗号分隔）
PLUGINS=(
  "folio-mark|$THEME_DIR/plugin/folio-mark|obsidian-folio-mark|"
  "folio-table|$THEME_DIR/plugin/folio-table|obsidian-folio-table|"
  "folio-typewriter|$THEME_DIR/plugin/folio-typewriter|obsidian-folio-typewriter|"
  "dashboard|$VAULT_DIR/.obsidian/plugins/dashboard|obsidian-dashboard|node_modules,data.json"
)

command -v rsync >/dev/null || { echo "✗ 需要 rsync" >&2; exit 1; }
mkdir -p "$CACHE"

changed=0
for entry in "${PLUGINS[@]}"; do
  IFS='|' read -r id src repo extra <<<"$entry"

  if [ ${#ONLY[@]} -gt 0 ]; then
    want=1
    for o in "${ONLY[@]}"; do [ "$o" = "$id" ] && want=0; done
    [ "$want" = 1 ] && continue
  fi

  if [ ! -d "$src" ]; then
    echo "✗ ${id}：源目录不存在 → $src"
    continue
  fi

  work="$CACHE/$repo"
  if [ ! -d "$work/.git" ]; then
    echo "· ${id}：首次克隆 $REMOTE_BASE/$repo.git"
    git clone -q "$REMOTE_BASE/$repo.git" "$work" 2>/dev/null || {
      mkdir -p "$work"
      git -C "$work" init -q -b main
      git -C "$work" remote add origin "$REMOTE_BASE/$repo.git"
    }
  fi
  git -C "$work" fetch -q origin 2>/dev/null || true
  if git -C "$work" rev-parse --verify -q origin/main >/dev/null; then
    git -C "$work" checkout -q main 2>/dev/null || git -C "$work" checkout -q -b main origin/main
    git -C "$work" reset -q --hard origin/main
  else
    # 远端还是空仓库（gh repo create 刚建出来就是这种）
    echo "· ${id}：远端为空，按首次推送处理"
    git -C "$work" checkout -q -B main
  fi

  # 仓库自己的文件不动；源里的这些也不带过去
  excludes=(--exclude=.git --exclude=.DS_Store --exclude=README.md --exclude=LICENSE --exclude=.gitignore)
  if [ -n "$extra" ]; then
    IFS=',' read -ra xs <<<"$extra"
    for x in "${xs[@]}"; do excludes+=(--exclude="$x"); done
  fi
  rsync -a --delete "${excludes[@]}" "$src"/ "$work"/

  git -C "$work" add -A
  if git -C "$work" diff --cached --quiet; then
    echo "· ${id}：已是最新"
    continue
  fi

  echo "· ${id}：有变化 →"
  git -C "$work" diff --cached --stat | sed 's/^/    /'

  if [ "$DRY_RUN" = 1 ]; then
    git -C "$work" rev-parse --verify -q origin/main >/dev/null && git -C "$work" reset -q --hard origin/main || git -C "$work" reset -q --hard
    echo "    （--dry-run：未提交、未推送）"
    changed=1
    continue
  fi

  git -C "$work" commit -q -m "${MSG:-同步 $id 源码}"
  if GIT_TERMINAL_PROMPT=0 git -C "$work" push -q origin main; then
    echo "    ✓ 已推送 $(git -C "$work" rev-parse --short HEAD)"
    changed=1
  else
    echo "    ✗ 推送失败（网络/代理？）—— 本地镜像已提交，重跑本脚本即可重试：$work" >&2
    exit 1
  fi
done

[ "$changed" = 0 ] && echo "✅ 全部已是最新" || echo "✅ 同步完成"
