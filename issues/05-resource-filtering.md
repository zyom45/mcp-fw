# Resource / Prompt のフィルタリングを実装する

## Labels
`enhancement`, `security`, `core`

## Description

現在 `list_resources`, `read_resource`, `list_prompts`, `get_prompt` はバックエンドからの応答をフィルタリングせずそのまま素通ししている。

`read_resource` は任意のファイル内容や機密情報を返す可能性があり、ツールと同等のアクセス制御が望ましい。

## Proposed Solution

### Phase 1: Resource URI パターンマッチ

ポリシーに `resource_allow` / `resource_deny` を追加：

```yaml
servers:
  filesystem:
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
    allow: [FS, IO]
    deny: [NET]
    resource_allow:
      - "file:///tmp/**"
    resource_deny:
      - "file:///tmp/secret/**"
```

### Phase 2: Prompt のフィルタリング

必要に応じて prompt 名の allowlist/denylist を追加。

## Acceptance Criteria

- [ ] `resource_allow` / `resource_deny` でリソースのフィルタリングが可能
- [ ] ポリシーに記載がない場合は従来通り素通し（後方互換）
- [ ] テストカバレッジ
