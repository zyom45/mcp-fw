# ポリシーのホットリロードに対応する

## Labels
`enhancement`, `core`

## Description

CLI モードでは起動時にポリシー YAML を一度読み込んだら、プロセスを再起動するまで変更が反映されない。Menubar アプリからポリシーを変更しても実行中のプロキシには効かない。

## Proposed Solution

以下の2方式を検討：

### 方式1: SIGHUP シグナル（推奨）

```python
import signal

def _reload_policy(signum, frame):
    logger.info("Reloading policy (SIGHUP)")
    self._policy = load_policy(self._config_path, self._server_name)
    self._allowed_names = None  # キャッシュ破棄

signal.signal(signal.SIGHUP, _reload_policy)
```

### 方式2: ファイル監視（watchdog）

`watchdog` ライブラリでポリシーファイルの変更を監視し、自動リロード。依存が増えるのが難点。

### 推奨: 方式1 + 方式2 オプション

SIGHUP はゼロ依存で実装可能。watchdog は Optional 依存として追加。

## Acceptance Criteria

- [ ] `SIGHUP` でポリシーが再読込される
- [ ] リロード後、次の `list_tools` / `call_tool` で新しいポリシーが適用される
- [ ] リロード失敗時（YAML パースエラー等）に旧ポリシーを維持し、エラーをログ出力
