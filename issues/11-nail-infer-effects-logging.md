# nail-lang の infer_effects() を活用したデバッグログの改善

## Labels
`enhancement`, `nail-upgrade`

## Description

nail-lang 0.9.2 で `infer_effects()` が単体で利用可能になった。現在のデバッグログではアノテーション後のエフェクトしか表示されないが、推論過程を明示することでデバッグ性が向上する。

```python
from nail_lang import infer_effects

# ツールごとに推論結果をログ出力
for tool in backend_tools:
    inferred = infer_effects(tool.name, tool.description or "")
    logger.debug("Tool %r: inferred effects = %s", tool.name, inferred)
```

## Proposed Changes

- `filtering.py` の `build_allowed_tools()` に推論結果のログを追加
- `tool_overrides` がある場合は「推論値 → オーバーライド値」の差分をログ表示

## Acceptance Criteria

- [ ] `--verbose` 時にツールごとの推論エフェクトがログに出力される
- [ ] `tool_overrides` による変更が明示される
