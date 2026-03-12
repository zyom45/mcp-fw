# バックエンド接続のエラーハンドリングを改善する

## Labels
`enhancement`, `reliability`

## Description

`proxy.py` でバックエンド MCP サーバーへの接続失敗やタイムアウト時の挙動が不明瞭。サーバーが起動しない場合やクラッシュした場合の復旧パスがない。

## Proposed Changes

1. **起動失敗の明確なエラー**: バックエンドの `command` が見つからない・起動に失敗した場合に、わかりやすいエラーメッセージを返す
2. **接続リトライ**: リトライ回数・間隔をポリシーで設定可能にする
3. **ヘルスチェック**: バックエンドの生存確認（optional）

```yaml
servers:
  filesystem:
    command: npx
    args: [...]
    retry:
      max_attempts: 3
      backoff_seconds: 2
```

## Acceptance Criteria

- [ ] バックエンド起動失敗時に明確なエラーメッセージが表示される
- [ ] 設定可能なリトライが実装されている
- [ ] 既存テストが通る
