# ポリシーの env フィールドで環境変数参照をサポートする

## Labels
`enhancement`, `security`

## Description

`policy.yaml` の `env` フィールドに API キー等を平文で書くリスクがある。環境変数を参照する構文をサポートし、secrets の平文管理を回避する。

## Proposed Solution

```yaml
servers:
  my-server:
    command: node
    args: ["server.js"]
    env:
      API_KEY: "${API_KEY}"           # 環境変数から取得
      STATIC_VALUE: "hello"           # そのまま使用
      WITH_DEFAULT: "${DB_HOST:-localhost}"  # デフォルト値付き
```

### 実装

`policy.py` の `load_policy()` で `env` 値に対して `os.environ` からの展開処理を追加。

```python
import os, re

def _expand_env(value: str) -> str:
    def replacer(m):
        name, default = m.group(1), m.group(3)
        return os.environ.get(name, default or "")
    return re.sub(r'\$\{(\w+)(-([^}]*))?\}', replacer, value)
```

## Acceptance Criteria

- [ ] `${VAR}` 構文で環境変数を参照できる
- [ ] `${VAR:-default}` でデフォルト値を指定できる
- [ ] 未定義の環境変数を参照した場合に警告ログを出力
- [ ] ドキュメントに「env に secrets を直書きしない」旨の注意書き
