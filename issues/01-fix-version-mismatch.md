# pyproject.toml と __init__.py のバージョン不整合を修正する

## Labels
`bug`, `good first issue`

## Description

`pyproject.toml` では `version = "0.2.4"` だが、`src/mcp_fw/__init__.py` では `__version__ = "0.2.3"` となっており、バージョンが不整合。

リリース時に手動で2箇所を更新する運用ではずれが起きやすい。

## Proposed Solution

以下のいずれかで single source of truth にする：

1. **`hatch-vcs`** を導入し、git tag からバージョンを自動生成
2. **`importlib.metadata`** を使い、`__init__.py` で `importlib.metadata.version("mcp-fw")` を参照

## Acceptance Criteria

- [ ] `mcp_fw.__version__` と `pyproject.toml` の `version` が常に一致する仕組みになっている
- [ ] CI でバージョン不整合を検知するテスト、もしくはそもそも不整合が起きない仕組みが入っている
