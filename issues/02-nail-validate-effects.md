# nail-lang の validate_effects() を採用し、自前バリデーションを置換する

## Labels
`enhancement`, `refactor`, `nail-upgrade`

## Description

`policy.py` に自前の `_validate_effects()` 関数があるが、nail-lang 0.9.2 で公式の `validate_effects()` が追加された。

```python
# 現在の自前実装
def _validate_effects(effects, context):
    invalid = set(effects) - VALID_EFFECTS
    if invalid:
        raise ValueError(...)

# nail-lang 公式
from nail_lang import validate_effects
validate_effects(["FS", "IO"])  # → OK or ValueError
```

公式APIに置き換えることで、nail-lang 側のエフェクト追加に自動追従でき、保守コストが下がる。

## Proposed Changes

- `policy.py` の `_validate_effects()` を `nail_lang.validate_effects()` で置換
- エラーメッセージのフォーマットが変わる場合はテストを調整

## Acceptance Criteria

- [ ] `_validate_effects()` が削除され、`nail_lang.validate_effects()` を使用している
- [ ] 既存テストが通る（エラーメッセージの検証がある場合は調整）
