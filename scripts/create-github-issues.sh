#!/usr/bin/env bash
# GitHub Issues を一括作成するスクリプト
# 使い方: gh auth login 後に実行
#   ./scripts/create-github-issues.sh
#
# 事前条件:
#   - gh CLI がインストール済み
#   - gh auth login で認証済み
#   - リポジトリのルートから実行

set -euo pipefail

REPO="zyom45/mcp-fw"
ISSUES_DIR="$(cd "$(dirname "$0")/../issues" && pwd)"

created=0
skipped=0

for file in "$ISSUES_DIR"/[0-9]*.md; do
  [ -f "$file" ] || continue

  # タイトル: 1行目の "# " を除去
  title=$(head -1 "$file" | sed 's/^# //')

  # ラベル: "## Labels" セクションから抽出
  labels=$(awk '/^## Labels/{getline; print; exit}' "$file" \
    | sed 's/`//g' | sed 's/, */,/g' | xargs)

  # ボディ: "## Labels" 行とその次の行を除いた "## Description" 以降
  body=$(awk 'BEGIN{skip=0} /^## Labels/{skip=1; next} skip==1{skip=0; next} /^## /{found=1} found{print}' "$file")

  # 既存 Issue チェック (タイトルの先頭20文字で検索)
  search_term="${title:0:30}"
  existing=$(gh issue list -R "$REPO" --search "$search_term" --json number --jq '.[0].number' 2>/dev/null || true)

  if [ -n "$existing" ]; then
    echo "SKIP: #$existing already exists - $title"
    skipped=$((skipped + 1))
    continue
  fi

  # Issue 作成
  label_args=""
  if [ -n "$labels" ]; then
    IFS=',' read -ra LABEL_ARRAY <<< "$labels"
    for l in "${LABEL_ARRAY[@]}"; do
      label_args="$label_args --label \"$l\""
    done
  fi

  echo "Creating: $title"
  eval gh issue create -R "$REPO" \
    --title "\"$title\"" \
    --body "\"$body\"" \
    $label_args \
    2>&1 || echo "  ERROR: Failed to create issue"

  created=$((created + 1))

  # Rate limit 回避
  sleep 1
done

echo ""
echo "Done: $created created, $skipped skipped"
