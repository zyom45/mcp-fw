# 1プロセスで複数サーバーを同時プロキシする

## Labels
`enhancement`, `core`

## Description

現在 mcp-fw は `--server` オプションで1つのサーバーのみをプロキシする。Claude Desktop から複数の MCP サーバーを使う場合、サーバーごとに mcp-fw プロセスを起動する必要がある。

## Proposed Solution

```bash
# 現在: サーバーごとにプロセス
mcp-fw --config policy.yaml --server filesystem
mcp-fw --config policy.yaml --server everything

# 提案: 1プロセスで全サーバー
mcp-fw --config policy.yaml --all
```

### 実装方針

1. ポリシーの全サーバーを読み込み
2. 各サーバーに対して `FirewallProxy` インスタンスを生成
3. `asyncio.gather()` で並行実行
4. Claude Desktop の設定に1つのプロキシエンドポイントとして登録

## Considerations

- stdio ベースでは1プロセス = 1サーバーの制約があるため、SSE/HTTP トランスポート (#14) との組み合わせが前提になる可能性
- サーバー間のツール名衝突の解決（namespace prefix など）

## Acceptance Criteria

- [ ] 1プロセスで複数サーバーをプロキシできる
- [ ] サーバーごとに独立したポリシーが適用される
- [ ] ツール名衝突時の挙動が定義されている
