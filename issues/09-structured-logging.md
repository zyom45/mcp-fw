# 構造化ログ（JSON ログ）のサポート

## Labels
`enhancement`

## Description

現在 `logging.basicConfig` によるプレーンテキストログのみ。運用環境でのデバッグやモニタリングツール連携には構造化ログ（JSON 形式）が望ましい。

## Proposed Changes

1. `--log-format` オプションを追加（`text` / `json`）
2. JSON フォーマッタの実装（標準ライブラリの `logging` + カスタムフォーマッタ、もしくは `structlog`）

```bash
mcp-fw --config policy.yaml --server fs --log-format json --log-file /var/log/mcp-fw.json
```

```json
{"timestamp": "2026-03-09T12:00:00Z", "level": "INFO", "message": "Filtered 10 → 7 tools", "allowed_effects": ["FS", "IO"]}
```

## Acceptance Criteria

- [ ] `--log-format json` でJSON形式のログが出力される
- [ ] デフォルトは従来通りテキスト形式（後方互換）
- [ ] 外部依存を増やさず標準ライブラリで実装可能であればそちらを優先
