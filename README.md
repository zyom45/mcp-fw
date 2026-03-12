# mcp-fw

[![CI](https://github.com/zyom45/mcp-fw/actions/workflows/ci.yml/badge.svg)](https://github.com/zyom45/mcp-fw/actions/workflows/ci.yml)
[![PyPI version](https://img.shields.io/pypi/v/mcp-fw)](https://pypi.org/project/mcp-fw/)
[![Python](https://img.shields.io/pypi/pyversions/mcp-fw)](https://pypi.org/project/mcp-fw/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[日本語版 README](README_ja.md)

**MCP servers can read your files, run processes, and access the network — all without asking.**

mcp-fw is a firewall proxy that sits between Claude Desktop and MCP servers.
It uses [NAIL](https://github.com/watari-ai/nail) effect labels to control exactly what each server can do.

By default, `mcp-fw` allows tools subject to effect policy, but blocks MCP `resources` and `prompts` unless you explicitly opt in with `allow_resources: true` / `allow_prompts: true`.

```
Claude Desktop  ←→  mcp-fw (proxy)  ←→  MCP Server
                     ↑
                  policy.yaml
                  allow: [FS, IO]
                  deny:  [NET]
```

## Why

MCP servers are powerful — but there's no built-in permission model.
A filesystem server could silently make network calls.
An "everything" server could spawn processes.

mcp-fw enforces boundaries:

| Effect | What it controls | Example |
|--------|-----------------|---------|
| `FS`   | File read/write | Read a file, list directory |
| `IO`   | General I/O | stdin/stdout, echo |
| `NET`  | Network access | HTTP requests, DNS |
| `PROC` | Process execution | Spawn subprocess, exec |
| `TIME` | Time/clock access | Get current time |
| `RAND` | Randomness | Generate random numbers |

## Quick Start

```bash
pip install mcp-fw
```

## Commands

Primary CLI:

```bash
mcp-fw run --config policy.yaml --server filesystem [--verbose] [--log-file /path/to/file.log]
mcp-fw inspect --config policy.yaml --server filesystem
mcp-fw status --server filesystem
mcp-fw stop --server filesystem
mcp-fw claude-remove [--server filesystem]
mcp-fw menubar --config policy.yaml
```

Legacy shorthand still supported:

```bash
mcp-fw --config policy.yaml --server filesystem [--verbose] [--log-file /path/to/file.log]
```

Dedicated menubar entry point:

```bash
mcp-fw-menubar --config policy.yaml
```

### 1. Write a policy

```yaml
# policy.yaml
servers:
  filesystem:
    command: npx
    args: ["@modelcontextprotocol/server-filesystem", "/tmp"]
    allow: [FS, IO]
    deny: [NET]
```

This lets the filesystem server read/write files (`FS`, `IO`) but **blocks all network access** (`NET`).
It also keeps MCP `resources` and `prompts` blocked unless you explicitly enable them.

### 2. Point Claude Desktop to the proxy

In `claude_desktop_config.json`:

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

That's it. Claude Desktop now talks to `mcp-fw`, which filters tools before forwarding to the real server.

If your server uses MCP `resources` or `prompts`, opt in explicitly:

```yaml
servers:
  filesystem:
    allow_resources: true
    allow_prompts: true
```

To remove mcp-fw entries later:

```bash
mcp-fw claude-remove
# or only one server
mcp-fw claude-remove --server filesystem
```

### 3. See what happened

```
$ mcp-fw --config policy.yaml --server filesystem --verbose
2025-01-15 10:00:01 [INFO] Filtered 5 → 3 tools (allowed effects: ['FS', 'IO'])
2025-01-15 10:00:05 [WARNING] Blocked tool call: fetch_url
```

To stop a running proxy process:

```bash
mcp-fw stop --server filesystem
```

To inspect how NAIL classified tools before changing policy:

```bash
mcp-fw inspect --config policy.yaml --server filesystem
```

The output shows inferred effects, effective effects after overrides, whether an override changed classification, and the final allowed/blocked result.

## Menubar App (macOS)

For a GUI experience:

```bash
pip install "mcp-fw[menubar]"
mcp-fw menubar --config policy.yaml
# or:
mcp-fw-menubar --config policy.yaml
```

A `[FW]` icon appears in your menubar:

```
[FW]
├── mcp-fw v0.2.5
├── ────────
├── ● filesystem
│   ├── Status: Running
│   ├── ────────
│   ├── [x] FS
│   ├── [x] IO
│   ├── [ ] NET          ← toggle effects live
│   ├── [ ] PROC
│   ├── Stop Proxy
│   └── ...
├── ○ everything
├── ────────
├── Edit Policy YAML
├── View Logs...
├── ────────
├── Sync to Claude Desktop
├── Remove from Claude Desktop
└── Quit
```

- **Toggle effects** with checkboxes — changes are written to `policy.yaml` instantly
- **Sync to Claude Desktop** generates `claude_desktop_config.json` entries automatically
- **Stop Proxy** terminates a running proxy process for a server
- **Remove from Claude Desktop** deletes generated `*-fw` entries from `claude_desktop_config.json`
- **View Logs** opens a live log viewer
- **Process monitor** shows ● running / ○ stopped status per server

## How It Works

```
1. Claude calls list_tools()
   → mcp-fw forwards to the real server
   → NAIL annotates each tool with effect labels
   → mcp-fw filters out tools that violate the policy
   → Claude only sees allowed tools

2. Claude calls a tool
   → mcp-fw checks if it's in the allowed set
   → Allowed: forward to server
   → Blocked: return error
```

The key insight: tools aren't just allowed or denied by name — they're classified by **what they do** (filesystem, network, process, etc.) using [NAIL's effect system](https://github.com/watari-ai/nail). This means mcp-fw can enforce policies on servers it has never seen before.

## Policy Reference

```yaml
servers:
  my-server:
    command: npx                    # server command
    args: ["@org/server", "/tmp"]   # command arguments
    allow: [FS, IO]                 # permitted effects (empty = all)
    deny: [NET]                     # blocked effects (overrides allow)
    allow_resources: false          # permit MCP resources API
    allow_prompts: false            # permit MCP prompts API
    tool_overrides:                 # per-tool effect corrections
      safe_fetch: [IO]             # override NAIL's auto-detection
```

**Rules:**
- `allow: []` (empty) = all effects permitted, then `deny` subtracts
- `allow: [FS, IO]` = only these effects, then `deny` subtracts
- `deny` always wins over `allow`
- `allow_resources` and `allow_prompts` are explicit opt-ins; by default they are blocked
- `tool_overrides` lets you correct NAIL's automatic effect detection for specific tools

## License

MIT
