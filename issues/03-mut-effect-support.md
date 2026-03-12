# 新エフェクト MUT への対応

## Labels
`enhancement`, `nail-upgrade`

## Description

nail-lang 0.9.2 で `VALID_EFFECTS` に `MUT`（ミューテーション）エフェクトが追加された。

```python
VALID_EFFECTS = frozenset({'FS', 'IO', 'MUT', 'NET', 'PROC', 'RAND', 'TIME'})
```

mcp-fw のドキュメント、サンプルポリシー、menubar UI のいずれにも `MUT` の記載がない。

## Proposed Changes

- [ ] `README.md` のエフェクト一覧に `MUT` を追加し、意味を説明
- [ ] `examples/policy.yaml` に `MUT` を使った例を追加
- [ ] menubar の i18n (`i18n.py`) に `MUT` のラベルを追加
- [ ] menubar の UI でエフェクトチェックボックスに `MUT` を表示

## Acceptance Criteria

- [ ] `MUT` エフェクトがドキュメント・UI で適切に扱われている
- [ ] ポリシーで `deny: [MUT]` と指定した場合に正しくフィルタリングされる
