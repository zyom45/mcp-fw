# mcp-fw 改善提案 Issues

## バグ修正
| # | タイトル | 優先度 | Labels |
|---|---------|--------|--------|
| 01 | [バージョン不整合の修正](01-fix-version-mismatch.md) | 高 | `bug`, `good first issue` |

## nail-lang アップグレード (0.9.0 → 0.9.2)
| # | タイトル | 優先度 | Labels |
|---|---------|--------|--------|
| 02 | [validate_effects() の採用](02-nail-validate-effects.md) | 高 | `refactor`, `nail-upgrade` |
| 03 | [MUT エフェクト対応](03-mut-effect-support.md) | 高 | `enhancement`, `nail-upgrade` |
| 11 | [infer_effects() ログ活用](11-nail-infer-effects-logging.md) | 中 | `enhancement`, `nail-upgrade` |
| 12 | [get_tool_effects() 活用](12-nail-get-tool-effects.md) | 中 | `refactor`, `nail-upgrade` |
| 13 | [Delegation チェック](13-nail-delegation-check.md) | 中 | `security`, `nail-upgrade` |

## コア機能強化
| # | タイトル | 優先度 | Labels |
|---|---------|--------|--------|
| 04 | [ツールキャッシュのリフレッシュ](04-tool-cache-refresh.md) | 高 | `enhancement`, `core` |
| 05 | [Resource フィルタリング](05-resource-filtering.md) | 高 | `security`, `core` |
| 06 | [ポリシーのホットリロード](06-policy-hot-reload.md) | 中 | `enhancement`, `core` |
| 07 | [バックエンドエラーハンドリング](07-error-handling-backend.md) | 中 | `reliability` |
| 14 | [SSE/HTTP トランスポート](14-sse-streamable-http.md) | 低 | `enhancement`, `core` |
| 15 | [マルチサーバープロキシ](15-multi-server-proxy.md) | 低 | `enhancement`, `core` |
| 16 | [承認モード (ask mode)](16-ask-mode.md) | 低 | `security` |

## 開発体験・運用
| # | タイトル | 優先度 | Labels |
|---|---------|--------|--------|
| 08 | [静的型チェック (mypy)](08-static-type-checking.md) | 中 | `ci`, `good first issue` |
| 09 | [構造化ログ](09-structured-logging.md) | 低 | `enhancement` |
| 10 | [env の環境変数参照](10-env-secret-handling.md) | 中 | `security` |
