# CI に mypy / pyright による静的型チェックを追加する

## Labels
`enhancement`, `ci`, `good first issue`

## Description

テストは充実しているが、静的型チェッカーが CI に入っていない。`dataclass` を多用しているプロジェクトなので型チェッカーとの相性が良く、型エラーを早期に検出できる。

## Proposed Changes

1. `pyproject.toml` に mypy 設定を追加
2. `.github/workflows/ci.yml` に `mypy src/` ステップを追加
3. 必要に応じて型アノテーションを補完

```toml
# pyproject.toml
[tool.mypy]
python_version = "3.10"
strict = true
```

## Acceptance Criteria

- [ ] CI で `mypy src/` が実行され、エラーなしで通る
- [ ] 新たな型エラーを導入した場合に CI が失敗する
