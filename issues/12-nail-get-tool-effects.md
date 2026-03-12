# nail-lang の get_tool_effects() / annotate_tool_effects() を活用する

## Labels
`enhancement`, `refactor`, `nail-upgrade`

## Description

`filtering.py` でエフェクト情報を `fc["function"]["effects"]` のように dict の内部構造に直接アクセスしている。nail-lang 0.9.2 の公式 API を使うことで、内部構造の変更に強くなる。

### 現状

```python
fn = fc.get("function", {})
logger.debug("Tool %r → effects %s", fn.get("name"), fn.get("effects", []))
```

### 改善後

```python
from nail_lang import get_tool_effects

effects = get_tool_effects(fc)
logger.debug("Tool %r → effects %s", fn.get("name"), effects)
```

## Proposed Changes

- `filtering.py` で `get_tool_effects()` を使用してエフェクト取得
- 必要に応じて `annotate_tool_effects()` でオーバーライド処理を明示化

## Acceptance Criteria

- [ ] dict の内部構造への直接アクセスが公式 API に置き換わっている
- [ ] 既存テストが通る
