# SSE / Streamable HTTP トランスポートへの対応

## Labels
`enhancement`, `core`

## Description

現在 mcp-fw は stdio トランスポートのみ対応。リモートの MCP サーバー（HTTP ベース）に接続するには SSE または Streamable HTTP トランスポートのサポートが必要。

## Proposed Solution

```yaml
servers:
  remote-server:
    transport: sse            # or "streamable-http"
    url: "https://example.com/mcp"
    headers:
      Authorization: "Bearer ${API_TOKEN}"
    allow: [IO, NET]
    deny: [PROC, FS]
```

### 実装ステップ

1. `ServerPolicy` に `transport`, `url`, `headers` フィールドを追加
2. `proxy.py` でトランスポートに応じた接続方式を選択
3. `mcp` ライブラリの SSE / HTTP クライアントを活用

## Acceptance Criteria

- [ ] `transport: sse` でリモート MCP サーバーに接続できる
- [ ] `transport: streamable-http` でリモート MCP サーバーに接続できる
- [ ] デフォルトは `stdio`（後方互換）
- [ ] `headers` で認証トークン等を渡せる
