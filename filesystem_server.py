#!/usr/bin/env python3
"""
MCP File System Server - Sandboxed file operations via Model Context Protocol.

Provides secure file read/write/search operations with sandbox isolation,
path traversal prevention, and configurable access controls.
Built with FastMCP and the official MCP Python SDK.
"""

import sys
import os
import argparse
import hashlib
import logging
from pathlib import Path
from typing import Any
from datetime import datetime
from mcp.server.fastmcp import FastMCP, Context

logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                    format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("mcp-filesystem")

# ─── Global Config ─────────────────────────────────────────────────────
SANDBOX_PATH: str = ""
ALLOW_HIDDEN: bool = False
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB


def resolve_path(requested_path: str) -> Path:
    """Resolve and validate a file path within the sandbox.
    
    Raises ValueError if path escapes the sandbox or is hidden.
    """
    abs_path = Path(requested_path).resolve()
    sandbox = Path(SANDBOX_PATH).resolve()
    
    # Path traversal prevention
    try:
        abs_path.relative_to(sandbox)
    except ValueError:
        raise ValueError(f"❌ Path traversal blocked: {requested_path} is outside sandbox ({sandbox})")
    
    # Hidden files check
    if not ALLOW_HIDDEN:
        for part in abs_path.parts:
            if part.startswith('.') and part != '.':
                raise ValueError(f"❌ Hidden files blocked: {abs_path.name}. Use --allow-hidden to access.")
    
    return abs_path


# ─── FastMCP Server ────────────────────────────────────────────────────
mcp = FastMCP(
    "File System Server",
    description="Secure sandboxed file system operations through MCP",
    version="1.0.0",
)


# ─── Tools ─────────────────────────────────────────────────────────────
@mcp.tool(description="Read file contents as text")
def read_file(path: str, ctx: Context) -> str:
    """Read a file within the sandbox and return its contents.
    
    Args:
        path: Absolute or relative path within sandbox
        
    Returns:
        File contents with metadata
    """
    try:
        resolved = resolve_path(path)
        if not resolved.exists():
            return f"❌ File not found: {path}"
        if resolved.is_dir():
            return f"❌ Path is a directory: {path}"
        
        stat = resolved.stat()
        if stat.st_size > MAX_FILE_SIZE:
            return f"❌ File too large ({stat.st_size} bytes). Max: {MAX_FILE_SIZE} bytes. Use --max-size to increase."
        
        content = resolved.read_text(encoding="utf-8", errors="replace")
        summary = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        return f"📄 **File:** {resolved}\n**Size:** {stat.st_size:,} bytes\n**Modified:** {datetime.fromtimestamp(stat.st_mtime)}\n**SHA256:** {summary}...\n\n```\n{content}\n```"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"❌ Read error: {str(e)}"


@mcp.tool(description="Write content to a file (creates/overwrites)")
def write_file(path: str, content: str, ctx: Context) -> str:
    """Write content to a file within the sandbox.
    
    Creates parent directories if needed. Overwrites existing files.
    
    Args:
        path: File path within sandbox
        content: Text content to write
    """
    try:
        resolved = resolve_path(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(content, encoding="utf-8")
        return f"✅ Written {len(content):,} bytes to {resolved}"
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"❌ Write error: {str(e)}"


@mcp.tool(description="List files and directories")
def list_directory(path: str, ctx: Context) -> str:
    """List contents of a directory within the sandbox.
    
    Args:
        path: Directory path within sandbox
        
    Returns:
        Directory listing with file sizes and types
    """
    try:
        resolved = resolve_path(path)
        if not resolved.exists():
            return f"❌ Path not found: {path}"
        if not resolved.is_dir():
            return f"❌ Not a directory: {path}"
        
        entries = sorted(resolved.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        result = f"📂 **{resolved}/**\n\n"
        total_size = 0
        
        for entry in entries:
            display = entry.name
            if not ALLOW_HIDDEN and display.startswith('.'):
                continue
            
            if entry.is_dir():
                result += f"  📁 **{display}/**\n"
            else:
                size = entry.stat().st_size
                total_size += size
                size_str = f"{size:,}B" if size < 1024 else f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                result += f"  📄 {display} ({size_str})\n"
        
        result += f"\n**{len([e for e in entries if not (e.name.startswith('.') and not ALLOW_HIDDEN)])} items** — Total: {total_size/1024:.1f} KB"
        return result
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"❌ List error: {str(e)}"


@mcp.tool(description="Search files by glob pattern")
def search_files(pattern: str, base_path: str = "", ctx: Context = None) -> str:
    """Search for files matching a glob pattern within the sandbox.
    
    Args:
        pattern: Glob pattern (e.g., '*.py', '**/*.md', 'data_*.csv')
        base_path: Starting directory (defaults to sandbox root)
        
    Returns:
        Matching files with metadata
    """
    try:
        base = resolved = resolve_path(base_path) if base_path else Path(SANDBOX_PATH)
        sandbox = Path(SANDBOX_PATH)
        
        matches = []
        for entry in sandbox.rglob(pattern):
            try:
                entry.relative_to(sandbox)
                if not ALLOW_HIDDEN and any(p.startswith('.') for p in entry.parts[1:] if p != '.'):
                    continue
                matches.append(entry)
            except ValueError:
                continue
        
        if not matches:
            return f"🔍 No files matching `{pattern}` in sandbox."
        
        result = f"🔍 **{len(matches)} file(s)** matching `{pattern}`:\n\n"
        for m in sorted(matches):
            rel = m.relative_to(sandbox)
            if m.is_dir():
                result += f"  📁 {rel}/\n"
            else:
                size = m.stat().st_size
                result += f"  📄 {rel} ({size:,} bytes)\n"
        
        return result
    except Exception as e:
        return f"❌ Search error: {str(e)}"


@mcp.tool(description="Get file metadata")
def get_file_info(path: str, ctx: Context) -> str:
    """Get detailed metadata about a file or directory.
    
    Args:
        path: Path within sandbox
    """
    try:
        resolved = resolve_path(path)
        if not resolved.exists():
            return f"❌ Path not found: {path}"
        
        stat = resolved.stat()
        is_dir = resolved.is_dir()
        
        result = f"{'📁' if is_dir else '📄'} **{resolved.name}**\n\n"
        result += f"**Full path:** {resolved}\n"
        result += f"**Type:** {'Directory' if is_dir else 'File'}\n"
        result += f"**Size:** {stat.st_size:,} bytes\n"
        result += f"**Created:** {datetime.fromtimestamp(stat.st_ctime)}\n"
        result += f"**Modified:** {datetime.fromtimestamp(stat.st_mtime)}\n"
        result += f"**Permissions:** {oct(stat.st_mode)[-3:]}\n"
        
        if not is_dir:
            with open(resolved, 'rb') as f:
                content_start = f.read(512)
            result += f"**Magic bytes:** {content_start[:8].hex()}\n"
            result += f"**Is text:** {_is_text(content_start)}\n"
        
        return result
    except ValueError as e:
        return str(e)
    except Exception as e:
        return f"❌ Info error: {str(e)}"


@mcp.resource("file://{path}")
def get_file_resource(path: str) -> str:
    """Read a file and return its contents via resource URI."""
    try:
        resolved = resolve_path(path)
        if not resolved.exists() or resolved.is_dir():
            return f"Error: Path not found or is a directory: {path}"
        return resolved.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"Error: {str(e)}"


def _is_text(data: bytes) -> str:
    """Heuristic check if bytes represent text content."""
    try:
        data.decode("utf-8")
        return "✅ Likely text"
    except UnicodeDecodeError:
        return "❌ Likely binary"


# ─── CLI Entry Point ───────────────────────────────────────────────────
def main():
    global SANDBOX_PATH, ALLOW_HIDDEN, MAX_FILE_SIZE
    
    parser = argparse.ArgumentParser(description="MCP File System Server")
    parser.add_argument("--sandbox", required=True, help="Sandbox root directory (required)")
    parser.add_argument("--allow-hidden", action="store_true",
                        help="Allow access to hidden files (.*)")
    parser.add_argument("--max-size", type=int, default=10,
                        help="Max file size in MB (default: 10)")
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--port", type=int, default=8002)
    args = parser.parse_args()
    
    SANDBOX_PATH = os.path.abspath(args.sandbox)
    ALLOW_HIDDEN = args.allow_hidden
    MAX_FILE_SIZE = args.max_size * 1024 * 1024
    
    if not os.path.isdir(SANDBOX_PATH):
        os.makedirs(SANDBOX_PATH, exist_ok=True)
        logger.info(f"Created sandbox directory: {SANDBOX_PATH}")
    
    logger.info(f"Starting MCP File System Server (sandbox={SANDBOX_PATH}, "
                f"hidden={'✅' if ALLOW_HIDDEN else '❌'}, max_size={args.max_size}MB)")
    
    if args.transport == "streamable-http":
        mcp.run(transport="streamable-http", host="0.0.0.0", port=args.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
