# ツール呼び出し時の「承認モード」(ask mode) を追加する

## Labels
`enhancement`, `security`

## Description

現在のポリシーは allow/deny のバイナリ判定のみ。「許可するかわからないが、ブロックまではしたくない」ツールについて、ユーザーに都度確認する中間モードがあると便利。

## Proposed Solution

ポリシーに `ask` エフェクトリストを追加：

```yaml
servers:
  filesystem:
    command: npx
    args: [...]
    allow: [FS, IO]
    deny: [PROC]
    ask: [NET]           # NET エフェクトのツールは都度確認
```

### 動作

1. `allow` に含まれるエフェクト → 自動許可
2. `deny` に含まれるエフェクト → 自動拒否
3. `ask` に含まれるエフェクト → ユーザーに確認（menubar 通知 or CLI プロンプト）

### 技術的考慮

- stdio トランスポートではプロンプト表示が困難（stdout は MCP プロトコル専用）
- Menubar アプリとの連携、もしくはログファイル経由での承認フローが必要
- MCP プロトコルの `sampling` 機能を活用できる可能性

## Acceptance Criteria

- [ ] `ask` で指定したエフェクトのツール呼び出し時にユーザー確認が発生する
- [ ] 承認/拒否の結果がログに記録される
- [ ] `ask` 未指定時は従来通りの動作
