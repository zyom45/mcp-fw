# ツールキャッシュのリフレッシュ機構を追加する

## Labels
`enhancement`, `core`

## Description

現在 `FirewallProxy._ensure_allowed_names()` はツールリストを一度取得するとキャッシュしたまま。バックエンドの MCP サーバーがツールを動的に追加・削除した場合に追従できない。

## Proposed Solution

以下のいずれか（または両方）を実装：

1. **MCP 通知の購読**: `notifications/tools/list_changed` を購読し、通知を受けたらキャッシュを破棄
2. **TTL 付きキャッシュ**: 一定時間（例: 60秒）経過後にキャッシュを無効化

### 推奨: 方法1（MCP 通知ベース）

MCP プロトコルに組み込みの仕組みを活用するのが最も堅実。

```python
# 例: 通知ハンドラ
@self._backend_session.on_notification("notifications/tools/list_changed")
async def _on_tools_changed():
    self._allowed_names = None  # キャッシュ破棄
```

## Acceptance Criteria

- [ ] バックエンドサーバーのツール追加・削除がプロキシに反映される
- [ ] 既存テストが通る
- [ ] 新しいテストでキャッシュ破棄の動作を確認
