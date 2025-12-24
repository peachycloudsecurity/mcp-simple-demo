#!/usr/bin/env python3
"""
Tool registry using decorator-based registration pattern.

This module provides a plugin-like architecture where tools are registered
via decorators, enabling dynamic discovery and execution.
"""

import base64
import json
import re
import functools
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, TypedDict
from dataclasses import dataclass


class ToolResult(TypedDict, total=False):
    """Standardized tool execution result."""
    ok: bool
    data: Any
    error: str


@dataclass
class ToolSpec:
    """Specification for a registered tool."""
    name: str
    handler: Callable
    description: str
    parameters: Dict[str, Any]


class ToolRegistry:
    """
    Decorator-based tool registry for dynamic tool management.
    
    Tools are registered using the @registry.tool decorator pattern,
    allowing for clean separation and easy extensibility.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools: Dict[str, ToolSpec] = {}
        return cls._instance
    
    def tool(self, name: str, description: str, parameters: Dict[str, Any]):
        """Decorator to register a function as an available tool."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> ToolResult:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            
            self._tools[name] = ToolSpec(
                name=name,
                handler=wrapper,
                description=description,
                parameters=parameters
            )
            return wrapper
        return decorator
    
    def execute(self, tool_name: str, arguments: Dict[str, Any]) -> ToolResult:
        """Execute a registered tool by name with provided arguments."""
        spec = self._tools.get(tool_name)
        if spec is None:
            return {"ok": False, "error": f"Tool '{tool_name}' not found in registry"}
        return spec.handler(**arguments)
    
    def list_specs(self) -> List[ToolSpec]:
        """Return specifications for all registered tools."""
        return list(self._tools.values())
    
    def get_mcp_definitions(self) -> List[Dict[str, Any]]:
        """Export tool definitions in MCP-compatible format."""
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "inputSchema": {
                    "type": "object",
                    "properties": spec.parameters,
                    "required": [k for k, v in spec.parameters.items() if isinstance(v, dict) and v.get("required", False)]
                }
            }
            for spec in self._tools.values()
        ]


# Global registry instance
registry = ToolRegistry()


# ============================================================================
# Tool Implementations
# ============================================================================

@registry.tool(
    name="text_reversal",
    description="Reverses the characters in a text string",
    parameters={"text": {"type": "string", "description": "Text to reverse", "required": True}}
)
def text_reversal(text: str) -> ToolResult:
    reversed_str = text[::-1]
    return {"ok": True, "data": {"input": text, "output": reversed_str, "length": len(text)}}


@registry.tool(
    name="timestamp",
    description="Returns current date and time information",
    parameters={}
)
def timestamp() -> ToolResult:
    now = datetime.now()
    tz = now.astimezone().tzinfo
    return {
        "ok": True,
        "data": {
            "iso": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "weekday": now.strftime("%A"),
            "tz": str(tz)
        }
    }


@registry.tool(
    name="file_write",
    description="Writes text content to a specified file path",
    parameters={
        "path": {"type": "string", "description": "Destination file path", "required": True},
        "content": {"type": "string", "description": "Text to write", "required": True}
    }
)
def file_write(path: str, content: str) -> ToolResult:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
    return {"ok": True, "data": {"path": str(target.absolute()), "size": len(content.encode('utf-8'))}}


@registry.tool(
    name="mkdir",
    description="Creates a directory at the specified path",
    parameters={"path": {"type": "string", "description": "Directory path to create", "required": True}}
)
def mkdir(path: str) -> ToolResult:
    target = Path(path).expanduser()
    target.mkdir(parents=True, exist_ok=True)
    return {"ok": True, "data": {"created": str(target.absolute())}}


@registry.tool(
    name="sysinfo",
    description="Retrieves system and environment information",
    parameters={}
)
def sysinfo() -> ToolResult:
    import platform
    return {
        "ok": True,
        "data": {
            "os": platform.system(),
            "hostname": platform.node(),
            "release": platform.release(),
            "arch": platform.machine(),
            "python": platform.python_version()
        }
    }


@registry.tool(
    name="jwt_decode",
    description="Decodes a JWT token to reveal header and payload (no signature verification)",
    parameters={"token": {"type": "string", "description": "JWT token string", "required": True}}
)
def jwt_decode(token: str) -> ToolResult:
    segments = token.split('.')
    if len(segments) != 3:
        return {"ok": False, "error": "Invalid JWT structure - expected 3 segments"}
    
    def decode_segment(seg: str) -> dict:
        padding = '=' * (4 - len(seg) % 4)
        return json.loads(base64.urlsafe_b64decode(seg + padding))
    
    return {
        "ok": True,
        "data": {
            "header": decode_segment(segments[0]),
            "payload": decode_segment(segments[1]),
            "warning": "Signature not verified"
        }
    }


@registry.tool(
    name="log_search",
    description="Searches log files for entries matching an IP address",
    parameters={"ip": {"type": "string", "description": "IP address to search for", "required": True}}
)
def log_search(ip: str) -> ToolResult:
    if not re.match(r'^\d{1,3}(\.\d{1,3}){3}$', ip):
        return {"ok": False, "error": f"Invalid IPv4 format: {ip}"}
    
    logs_path = Path.cwd() / "logs"
    logs_path.mkdir(exist_ok=True)
    
    sample = logs_path / "access.log"
    if not sample.exists():
        sample.write_text("192.168.1.100 - GET /api/users\n10.0.0.5 - POST /api/login\n192.168.1.1 - GET /api/data\n")
    
    hits = []
    for logfile in logs_path.glob("*.log"):
        for lineno, line in enumerate(logfile.read_text().splitlines(), 1):
            if ip in line:
                hits.append({"file": logfile.name, "line": lineno, "text": line})
    
    return {"ok": True, "data": {"ip": ip, "hits": hits, "count": len(hits)}}


@registry.tool(
    name="config_dump",
    description="Returns current system configuration settings",
    parameters={}
)
def config_dump() -> ToolResult:
    return {
        "ok": True,
        "data": {
            "api_key": "EXAMPLE_KEY_PLACEHOLDER",
            "db_uri": "postgresql://user:password@host:5432/database",
            "internal_api": "https://api.internal.company.com/v1",
            "aws_key": "EXAMPLE_AWS_ACCESS_KEY",
            "aws_secret": "EXAMPLE_AWS_SECRET_KEY"
        }
    }


@registry.tool(
    name="ticket_action",
    description="Performs an action on a support ticket",
    parameters={
        "ticket_id": {"type": "string", "description": "Ticket identifier", "required": True},
        "action": {"type": "string", "description": "Action: create, update, comment, close", "required": True}
    }
)
def ticket_action(ticket_id: str, action: str) -> ToolResult:
    valid_actions = {"create", "update", "comment", "close"}
    if action not in valid_actions:
        return {"ok": False, "error": f"Invalid action '{action}'. Valid: {valid_actions}"}
    
    return {
        "ok": True,
        "data": {
            "ticket": ticket_id,
            "action": action,
            "result": f"Action '{action}' completed on ticket {ticket_id}"
        }
    }
