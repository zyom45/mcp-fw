# mcp-fw

[![CI](https://github.com/zyom45/mcp-fw/actions/workflows/ci.yml/badge.svg)](https://github.com/zyom45/mcp-fw/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/mcp-fw)](https://pypi.org/project/mcp-fw/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-fw)](https://pypi.org/project/mcp-fw/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**MCPサーバーはファイルの読み書き、プロセスの実行、ネットワークへのアクセスを — 確認なしで行えてしまいます。**

mcp-fw は Claude Desktop と MCP サーバーの間に入るファイアウォールプロキシです。
[NAIL](https://github.com/watari-ai/nail) のエフェクトラベルを使い、各サーバーが何をできるかを正確に制御します。

デフォルトでは、`mcp-fw` は effect policy に従って tools を許可しつつ、MCP の `resources` と `prompts` は `allow_resources: true` / `allow_prompts: true` を明示しない限りブロックします。

```
Claude Desktop  ←→  mcp-fw (プロキシ)  ←→  MCP Server
                     ↑
                  policy.yaml
                  allow: [FS, IO]
                  deny:  [NET]
```

## なぜ必要か

MCP サーバーは強力ですが、組み込みの権限モデルがありません。
ファイルシステムサーバーがこっそりネットワーク通信を行うこともできます。
「なんでもできる」サーバーがプロセスを起動することも可能です。

mcp-fw は境界を強制します:

| エフェクト | 制御対象 | 例 |
|-----------|---------|-----|
| `FS`   | ファイルの読み書き | ファイル読み込み、ディレクトリ一覧 |
| `IO`   | 一般的な I/O | stdin/stdout、echo |
| `NET`  | ネットワークアクセス | HTTPリクエスト、DNS |
| `PROC` | プロセス実行 | サブプロセス起動、exec |
| `TIME` | 時刻アクセス | 現在時刻の取得 |
| `RAND` | 乱数 | 乱数生成 |

## クイックスタート

```bash
pip install mcp-fw
```

## コマンド一覧

通常の CLI:

```bash
mcp-fw run --config policy.yaml --server filesystem [--verbose] [--log-file /path/to/file.log]
mcp-fw inspect --config policy.yaml --server filesystem
mcp-fw status --server filesystem
mcp-fw stop --server filesystem
mcp-fw claude-remove [--server filesystem]
mcp-fw menubar --config policy.yaml
```

旧形式も引き続き利用可能:

```bash
mcp-fw --config policy.yaml --server filesystem [--verbose] [--log-file /path/to/file.log]
```

menubar 専用エントリポイント:

```bash
mcp-fw-menubar --config policy.yaml
```

### 1. ポリシーを書く

```yaml
# policy.yaml
servers:
  filesystem:
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
    allow: [FS, IO]
    deny: [NET]
```

ファイルシステムサーバーにファイルの読み書き (`FS`, `IO`) を許可し、**ネットワークアクセスをすべてブロック** (`NET`) します。
MCP の `resources` と `prompts` も、明示的に許可しない限りブロックされたままです。

### 2. Claude Desktop をプロキシに向ける

`claude_desktop_config.json` に記述:

```json
{
  "mcpServers": {
    "filesystem-fw": {
      "command": "mcp-fw",
      "args": ["--config", "/path/to/policy.yaml", "--server", "filesystem"]
    }
  }
}
```

これだけです。Claude Desktop は `mcp-fw` と通信し、mcp-fw がツールをフィルタしてから実サーバーに転送します。

サーバーが MCP の `resources` や `prompts` を使う場合は、明示的に opt-in してください:

```yaml
servers:
  filesystem:
    allow_resources: true
    allow_prompts: true
```

あとで mcp-fw のエントリを削除したい場合:

```bash
mcp-fw claude-remove
# 1サーバーだけ消す場合
mcp-fw claude-remove --server filesystem
```

### 3. 動作を確認する

```
$ mcp-fw --config policy.yaml --server filesystem --verbose
2025-01-15 10:00:01 [INFO] Filtered 5 → 3 tools (allowed effects: ['FS', 'IO'])
2025-01-15 10:00:05 [WARNING] Blocked tool call: fetch_url
```

実行中プロキシを停止したい場合:

```bash
mcp-fw stop --server filesystem
```

ポリシーを変える前に NAIL の推定結果を確認したい場合:

```bash
mcp-fw inspect --config policy.yaml --server filesystem
```

出力には、推定エフェクト、override 適用後の最終エフェクト、override による分類変更の有無、最終的な allowed/blocked が表示されます。

## メニューバーアプリ (macOS)

GUI で操作したい場合:

```bash
pip install "mcp-fw[menubar]"
mcp-fw menubar --config policy.yaml
# または:
mcp-fw-menubar --config policy.yaml
```

メニューバーに `[FW]` アイコンが表示されます:

```
[FW]
├── mcp-fw v0.2.5
├── ────────
├── ● filesystem
│   ├── Status: Running
│   ├── ────────
│   ├── [x] FS
│   ├── [x] IO
│   ├── [ ] NET          ← エフェクトをライブ切り替え
│   ├── [ ] PROC
│   ├── プロキシを停止
│   └── ...
├── ○ everything
├── ────────
├── Edit Policy YAML
├── View Logs...
├── ────────
├── Sync to Claude Desktop
├── Claude Desktop設定から削除
└── Quit
```

- **チェックボックスでエフェクトを切り替え** — 変更は即座に `policy.yaml` に反映
- **Sync to Claude Desktop** で `claude_desktop_config.json` のエントリを自動生成
- **プロキシを停止** でサーバーごとの実行中プロセスを終了
- **Claude Desktop設定から削除** で `claude_desktop_config.json` の `*-fw` エントリを削除
- **View Logs** でライブログビューアを表示
- **プロセスモニター** でサーバーごとの ● 稼働中 / ○ 停止中 を確認

## 仕組み

```
1. Claude が list_tools() を呼ぶ
   → mcp-fw が実サーバーに転送
   → NAIL が各ツールにエフェクトラベルを付与
   → mcp-fw がポリシー違反のツールを除外
   → Claude には許可されたツールだけが見える

2. Claude がツールを呼ぶ
   → mcp-fw が許可リストを確認
   → 許可: サーバーに転送
   → ブロック: エラーを返す
```

重要なポイント: ツールは名前で許可・拒否されるのではなく、**何をするか** (ファイルシステム、ネットワーク、プロセスなど) で分類されます。これは [NAIL のエフェクトシステム](https://github.com/watari-ai/nail)を使っています。つまり mcp-fw は初めて見るサーバーに対してもポリシーを適用できます。

## ポリシーリファレンス

```yaml
servers:
  my-server:
    command: npx                    # サーバーコマンド
    args: ["@org/server", "/tmp"]   # コマンド引数
    allow: [FS, IO]                 # 許可するエフェクト (空 = すべて許可)
    deny: [NET]                     # ブロックするエフェクト (allow より優先)
    allow_resources: false          # MCP resources API を許可
    allow_prompts: false            # MCP prompts API を許可
    tool_overrides:                 # ツールごとのエフェクト補正
      safe_fetch: [IO]             # NAIL の自動検出を上書き
```

**ルール:**
- `allow: []` (空) = すべてのエフェクトを許可し、`deny` で除外
- `allow: [FS, IO]` = これらのエフェクトのみ許可し、`deny` で除外
- `deny` は常に `allow` より優先
- `allow_resources` と `allow_prompts` は明示 opt-in です。未指定時はブロックされます
- `tool_overrides` で NAIL の自動エフェクト検出を特定のツールに対して補正可能

## ライセンス

MIT
