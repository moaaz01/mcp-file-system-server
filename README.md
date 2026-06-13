# 📁 MCP File System Server

> A **secure, sandboxed file system server** for the **Model Context Protocol**. Read, write, search, and manage files through any MCP-compatible AI client — with **path traversal protection**, **hidden file controls**, and **size limits**.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## ✨ Features

- **🔧 5 Tools**: `read_file`, `write_file`, `list_directory`, `search_files`, `get_file_info`
- **📄 1 Resource**: `file://{path}` — read files via MCP resource URIs
- **🛡️ Security-First Architecture**: Sandbox isolation, path traversal prevention, max size limits
- **🔥 Hidden File Control**: Block `.hidden` files by default, opt-in with `--allow-hidden`
- **🔍 Glob-Based Search**: Search by pattern (`*.py`, `*.md`, `data_*.csv`)
- **📊 Rich Metadata**: File size, timestamps, permissions, text/binary detection
- **🖥️ Dual Transport**: stdio and Streamable HTTP

---

## 🚀 Quick Start

```bash
# 1. Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Create sandbox and run
mkdir -p /tmp/mcp-sandbox
python filesystem_server.py --sandbox /tmp/mcp-sandbox
```

---

## 🛠️ Tools Reference

### `read_file(path: str) -> str`
Read a file and return its contents with metadata (size, modified time, SHA256).

### `write_file(path: str, content: str) -> str`
Write content to a file. Creates parent directories automatically.

### `list_directory(path: str) -> str`
List files and directories with sizes and type indicators.

### `search_files(pattern: str, base_path: str = "") -> str`
Search by glob pattern across the entire sandbox.

### `get_file_info(path: str) -> str`
Get detailed metadata: type, size, timestamps, permissions, text/binary detection.

---

## 🛡️ Security Controls

```
--sandbox PATH          # Required: root directory (all operations restricted)
--allow-hidden          # Allow access to .hidden files and directories
--max-size N            # Max file size in MB (default: 10)
```

| Attack Vector | Protection |
|---------------|------------|
| `../../../etc/passwd` | ❌ Path traversal prevented |
| `~/.ssh/id_rsa` | ❌ Outside sandbox |
| `.env` files | ❌ Blocked by default |
| 100GB file read | ❌ Size limit (configurable) |
| Hidden directory listing | ❌ Filtered by default |

---

## 📄 Resources

### `file://{path}`
Read a file's raw content via MCP resource protocol.

---

## 🔌 Connecting to Clients

### Claude Desktop

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "args": ["/ABSOLUTE/PATH/mcp-file-system-server/filesystem_server.py", "--sandbox", "/tmp/mcp-sandbox"]
    }
  }
}
```

### Cursor

Settings → Features → MCP → Add Server:
- **Name**: `filesystem`
- **Type**: `command`
- **Command**: `python /ABSOLUTE/PATH/mcp-file-system-server/filesystem_server.py --sandbox /tmp/mcp-sandbox`

---

## 📁 Project Structure

```
mcp-file-system-server/
├── filesystem_server.py   # Main server (FastMCP + security)
├── requirements.txt
├── setup.sh
├── README.md
└── .gitignore
```

---

## 🧪 Example Usage

```python
# Read a file
read_file("/tmp/mcp-sandbox/data.txt")
# → "📄 File: /tmp/mcp-sandbox/data.txt\nSize: 1,234 bytes\n..."

# Write a file
write_file("/tmp/mcp-sandbox/output/report.md", "# Report\n\nHello world!")
# → "✅ Written 28 bytes to /tmp/mcp-sandbox/output/report.md"

# Search for Python files
search_files("**/*.py")
# → "🔍 5 file(s) matching **/*.py:\n  📄 scripts/process.py (1,234 bytes)\n..."
```

---

## 📜 License

MIT
