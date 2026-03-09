# nail-lang の Delegation チェック機能を活用する

## Labels
`enhancement`, `security`, `nail-upgrade`

## Description

nail-lang 0.9.2 で `check_delegation_call()` / `check_delegation_program()` が追加された。これにより、マルチエージェント構成で Agent A が Agent B のツールを呼ぶ際に、明示的な委譲許可を要求できる。

### ユースケース

```
Claude Desktop → mcp-fw (proxy) → MCP Server A → (delegates to) → MCP Server B
```

Agent A が `write_file`（`delegation: "explicit"`）を持つ Agent B のツールを呼ぶ場合、A のポリシーに `grants: ["FS:write_file"]` がないとブロックされる。

```yaml
servers:
  agent-a:
    command: ...
    allow: [IO]
    grants: ["FS:write_file"]  # B への委譲を明示許可
```

## Proposed Changes

1. `ServerPolicy` に `grants` フィールドを追加
2. ツール呼び出し時に `check_delegation_call()` を実行
3. `DelegationError` を `McpError` に変換してフロントエンドに返す

## Acceptance Criteria

- [ ] ポリシーで `grants` を指定できる
- [ ] 委譲違反時に明確なエラーメッセージが返される
- [ ] `grants` 未指定時は従来通りの動作（後方互換）
