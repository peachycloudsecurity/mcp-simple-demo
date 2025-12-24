#!/usr/bin/env python3
"""
LLM client with MCP tool integration.

This client uses a context manager pattern for resource management
and separates concerns between LLM interaction and tool execution.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

import ollama
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.config import get_config

cfg = get_config()
logging.basicConfig(
    level=getattr(logging, cfg.log_level),
    format='[%(levelname)s] %(name)s: %(message)s'
)
log = logging.getLogger("client")


@dataclass
class Message:
    """Represents a conversation message."""
    role: str
    content: str


@dataclass
class Conversation:
    """Manages conversation state and history."""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    def add(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})
    
    def add_raw(self, msg: Dict[str, Any]):
        self.messages.append(msg)
    
    def clear(self):
        self.messages.clear()
    
    def as_list(self) -> List[Dict[str, Any]]:
        return self.messages.copy()


class ToolBridge:
    """
    Bridges MCP server communication for tool execution.
    
    Manages the lifecycle of the MCP server subprocess and
    provides methods for tool discovery and invocation.
    """
    
    def __init__(self):
        self._session: Optional[ClientSession] = None
        self._tools: List[Dict[str, Any]] = []
        self._cleanup_tasks: List[Any] = []
    
    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self._tools
    
    @property
    def is_connected(self) -> bool:
        return self._session is not None
    
    async def connect(self):
        """Establish connection to the MCP tool server."""
        server_path = Path(__file__).parent / "server.py"
        params = StdioServerParameters(
            command="python3",
            args=[str(server_path)],
            env=None
        )
        
        log.info(f"Spawning tool server: {server_path}")
        
        # Create STDIO transport
        transport_ctx = stdio_client(params)
        transport = await transport_ctx.__aenter__()
        self._cleanup_tasks.append(transport_ctx)
        
        # Create session
        session_ctx = ClientSession(transport[0], transport[1])
        self._session = await session_ctx.__aenter__()
        self._cleanup_tasks.append(session_ctx)
        
        # Initialize and discover tools
        await self._session.initialize()
        await self._discover_tools()
        
        log.info(f"Connected with {len(self._tools)} tools available")
    
    async def _discover_tools(self):
        """Fetch and cache available tools from server."""
        result = await self._session.list_tools()
        self._tools = [
            {
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema
                }
            }
            for t in result.tools
        ]
    
    async def invoke(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        log.info(f"Invoking tool: {name}")
        result = await self._session.call_tool(name, args)
        
        if result.content and hasattr(result.content[0], 'text'):
            return json.loads(result.content[0].text)
        return {"ok": False, "error": "Empty response from tool"}
    
    async def disconnect(self):
        """Clean up server connection."""
        for ctx in reversed(self._cleanup_tasks):
            try:
                await ctx.__aexit__(None, None, None)
            except Exception as e:
                log.warning(f"Cleanup error: {e}")
        self._cleanup_tasks.clear()
        self._session = None
        log.info("Disconnected from tool server")


class Agent:
    """
    AI agent that combines LLM capabilities with tool execution.
    
    Orchestrates the interaction between user input, LLM reasoning,
    and tool execution through the MCP bridge.
    """
    
    def __init__(self):
        self._llm = ollama.Client(host=cfg.llm.api_endpoint)
        self._bridge = ToolBridge()
        self._conversation = Conversation()
    
    @property
    def tools(self) -> List[Dict[str, Any]]:
        return self._bridge.tools
    
    async def initialize(self):
        """Set up the agent and connect to tool server."""
        self._verify_llm()
        await self._bridge.connect()
    
    def _verify_llm(self):
        """Check LLM availability and model presence."""
        try:
            models = self._llm.list()
            available = [m['name'] for m in models.get('models', [])]
            if cfg.llm.model_name not in available:
                log.warning(f"Model {cfg.llm.model_name} not found. Available: {available}")
        except Exception as e:
            log.warning(f"Could not verify LLM: {e}")
    
    async def chat(self, user_input: str) -> str:
        """
        Process user input through the LLM with tool support.
        
        Handles the full cycle of:
        1. Sending user message to LLM
        2. Processing any tool calls
        3. Returning final response
        """
        self._conversation.add("user", user_input)
        
        try:
            response = self._llm.chat(
                model=cfg.llm.model_name,
                messages=self._conversation.as_list(),
                tools=self._bridge.tools
            )
            
            msg = response.get("message", {})
            
            # Handle tool calls if present
            if tool_calls := msg.get("tool_calls"):
                self._conversation.add_raw(msg)
                
                for call in tool_calls:
                    fn = call["function"]
                    print(f"\n[Tool: {fn['name']}]")
                    
                    result = await self._bridge.invoke(fn["name"], fn["arguments"])
                    self._conversation.add("tool", json.dumps(result))
                
                # Get final response after tool execution
                final = self._llm.chat(
                    model=cfg.llm.model_name,
                    messages=self._conversation.as_list()
                )
                final_msg = final["message"]
                self._conversation.add_raw(final_msg)
                return final_msg.get("content", "")
            
            # No tool calls - direct response
            self._conversation.add_raw(msg)
            return msg.get("content", "")
            
        except Exception as e:
            return self._format_error(e)
    
    def _format_error(self, error: Exception) -> str:
        """Generate helpful error messages based on error type."""
        msg = str(error).lower()
        error_str = str(error)
        
        if "memory" in msg:
            return f"Memory error: Try a smaller model like llama3.2:1b"
        if "tools" in msg and "support" in msg:
            return f"Model doesn't support tools. Use llama3.2:1b or llama3.2:3b"
        if "connection" in msg or "refused" in msg:
            return f"Connection error: Ensure Ollama is running (ollama serve)"
        if "not found" in msg:
            return f"Model not found: Run 'ollama pull {cfg.llm.model_name}'"
        if "tensors" in msg or "wrong number" in msg or "abort trap" in msg:
            return f"⚠️ Model corruption detected!\n\n" \
                   f"Your Ollama model '{cfg.llm.model_name}' is corrupted.\n" \
                   f"Fix it by running:\n" \
                   f"  ./fix_ollama.sh\n\n" \
                   f"Or manually:\n" \
                   f"  ollama rm {cfg.llm.model_name}\n" \
                   f"  ollama pull {cfg.llm.model_name}"
        if "500" in error_str or "internal server error" in msg:
            return f"Ollama server error (500). This usually means:\n" \
                   f"  1. Model is corrupted (run: ./fix_ollama.sh)\n" \
                   f"  2. Ollama needs restart (run: pkill ollama && ollama serve)\n" \
                   f"  3. Model file is incomplete (re-pull: ollama pull {cfg.llm.model_name})"
        
        return f"Error: {error}"
    
    def reset(self):
        """Clear conversation history."""
        self._conversation.clear()
        log.info("Conversation cleared")
    
    async def shutdown(self):
        """Clean up resources."""
        await self._bridge.disconnect()
