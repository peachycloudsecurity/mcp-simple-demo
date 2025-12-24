# MCP Server Architecture - Explained

## What is MCP (Model Context Protocol)?

MCP is a protocol that allows AI assistants (LLMs) to use **tools** and access **external resources**. Think of it as a bridge between the LLM and the real world.

## Architecture Overview

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   LLM       │         │  MCP Client  │         │ MCP Server  │
│ (Ollama)    │◄───────►│              │◄───────►│             │
│             │         │              │  STDIO  │  (Tools)    │
└─────────────┘         └──────────────┘         └─────────────┘
     │                        │                        │
     │                        │                        │
     └────────────────────────┴────────────────────────┘
                    JSON-RPC Messages
```

## Components Breakdown

### 1. **MCP Server** (`mcp_server.py`)
The server **exposes tools** that the LLM can use.

**Key Concepts:**
- **STDIO Communication**: Server communicates via stdin/stdout (standard input/output)
- **Tool Registration**: Server defines what tools are available
- **Tool Execution**: Server executes tools when requested

**How it works:**
```python
# Server listens on STDIO
async with stdio_server() as (read_stream, write_stream):
    # Client sends requests via stdin
    # Server responds via stdout
    await self.server.run(read_stream, write_stream, ...)
```

**What the server does:**
1. **List Tools**: When client asks "what tools do you have?", server responds with tool list
2. **Execute Tools**: When client says "run calculator with 2+2", server executes and returns result

### 2. **MCP Client** (`mcp_client.py`)
The client **connects** to the server and **manages** the LLM.

**Key Concepts:**
- **Subprocess**: Client spawns server as a subprocess
- **STDIO Transport**: Client communicates via pipes (stdin/stdout)
- **Session Management**: Client maintains connection to server
- **Tool Discovery**: Client asks server "what tools do you have?"

**How it works:**
```python
# Client spawns server as subprocess
server_params = StdioServerParameters(
    command="python3",
    args=["src/mcp_server.py"]
)

# Connect via STDIO
stdio_transport = stdio_client(server_params)
read_stream, write_stream = stdio_transport

# Create session
session = ClientSession(read_stream, write_stream)
await session.initialize()  # Handshake
```

**What the client does:**
1. **Start Server**: Spawns `mcp_server.py` as subprocess
2. **Discover Tools**: Asks server for available tools
3. **Bridge LLM ↔ Server**: When LLM wants to use a tool, client forwards request to server
4. **Return Results**: Gets result from server and sends back to LLM

### 3. **LLM (Ollama)**
The AI that **decides** when to use tools.

**How it works:**
1. User asks: "What's 2+2?"
2. LLM sees it needs calculator tool
3. LLM requests tool via client
4. Client forwards to server
5. Server executes calculator
6. Result goes back: LLM → Client → Server → Client → LLM
7. LLM responds: "2+2 equals 4"

## Communication Flow

### Step 1: Initialization
```
Client → Server: "Initialize connection"
Server → Client: "OK, I'm ready"
Client → Server: "List your tools"
Server → Client: ["calculator", "get_current_time", ...]
```

### Step 2: Tool Execution
```
User → LLM: "What's 25 * 4?"
LLM → Client: "I need calculator tool with expression '25 * 4'"
Client → Server: "Call tool 'calculator' with {'expression': '25 * 4'}"
Server → Client: {"success": true, "result": 100}
Client → LLM: "Calculator returned 100"
LLM → User: "25 * 4 equals 100"
```

## STDIO Protocol Explained

**STDIO = Standard Input/Output**

Instead of HTTP/WebSocket, MCP uses:
- **stdin**: Client writes requests, Server reads requests
- **stdout**: Server writes responses, Client reads responses

**Why STDIO?**
- Simple: No network setup needed
- Secure: Direct process communication
- Portable: Works everywhere
- Efficient: No network overhead

**Example:**
```python
# Server reads from stdin
request = await read_stream.read()

# Server writes to stdout
await write_stream.write(response)
```

## Your Current Architecture

### Files Structure:
```
mcp-basic/
├── src/
│   ├── mcp_server.py    # MCP Server (exposes tools)
│   ├── mcp_client.py    # MCP Client (bridges LLM ↔ Server)
│   ├── tools.py         # Tool implementations
│   └── config.py        # Configuration
├── main.py              # Entry point
└── start.sh             # Startup script
```

### Flow in Your Code:

1. **Start** (`start.sh`):
   ```bash
   python3 main.py
   ```

2. **Main** (`main.py`):
   ```python
   cli = ChatInterface()
   await cli.start()
   ```

3. **CLI** (`cli.py`):
   ```python
   client = MCPClient()
   await client.connect()  # Spawns server, connects via STDIO
   ```

4. **Client** (`mcp_client.py`):
   ```python
   # Spawns: python3 src/mcp_server.py
   # Connects via STDIO
   # Discovers tools
   # Ready for LLM
   ```

5. **Server** (`mcp_server.py`):
   ```python
   # Listens on STDIO
   # Exposes 8 tools
   # Executes when requested
   ```

## Understanding Your Error

### Error 1: "llama runner process has terminated: signal: killed"
**What this means:**
- Ollama model process was killed (likely by OS)
- **Cause**: Out of memory (OOM killer)
- Model needs more RAM than available

**Why it happens:**
- `llama3.2:3b` needs ~2.3GB RAM
- System doesn't have enough free memory
- OS kills the process to prevent system crash

### Error 2: "Server disconnected without sending a response"
**What this means:**
- MCP server connection was lost
- **Cause**: Server subprocess crashed or was killed
- Could be related to memory issue or server error

**Why it happens:**
- If Ollama crashes, client might lose connection
- Server subprocess might have issues
- Memory pressure affects all processes

## Key MCP Concepts

### 1. **Tool Definition**
```python
TOOL_DEFINITIONS = [
    {
        "name": "calculator",
        "description": "Evaluate math expressions",
        "inputSchema": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            }
        }
    }
]
```

### 2. **Tool Execution**
```python
@self.server.call_tool()
async def call_tool(name: str, arguments: Dict) -> list[TextContent]:
    if name == "calculator":
        result = self.tools.calculator(arguments["expression"])
    return [TextContent(text=json.dumps(result))]
```

### 3. **Client Tool Discovery**
```python
tools_result = await self.session.list_tools()
# Returns: [Tool(name="calculator", ...), Tool(name="get_current_time", ...), ...]
```

### 4. **LLM Tool Calling**
```python
# LLM sees tools and decides to use one
response = ollama_client.chat(
    model=OLLAMA_MODEL,
    messages=conversation_history,
    tools=self.tools  # LLM knows about these tools
)
# LLM response includes: {"tool_calls": [{"name": "calculator", ...}]}
```

## Debugging Tips

### Check if server is running:
```bash
ps aux | grep mcp_server
```

### Check Ollama status:
```bash
ollama list
curl http://localhost:11434/api/tags
```

### Check memory:
```bash
free -h  # Linux
vm_stat  # macOS
```

### Test server directly:
```bash
python3 src/mcp_server.py
# Should wait for STDIO input
```

### Test client connection:
```python
# In Python
from src.mcp_client import MCPClient
client = MCPClient()
await client.connect()
print(client.tools)  # Should show 8 tools
```

## Next Steps to Fix Your Issue

1. **Memory Issue**: Use smaller model (`llama3.2:1b`)
2. **Check Server**: Verify server subprocess is stable
3. **Error Handling**: Add retry logic for disconnections
4. **Monitoring**: Add health checks for Ollama and server

## Summary

- **MCP Server**: Exposes tools, communicates via STDIO
- **MCP Client**: Bridges LLM and server, manages connection
- **LLM**: Decides when to use tools
- **STDIO**: Communication protocol (stdin/stdout)
- **Tools**: Functions that LLM can call (calculator, file ops, etc.)

The error you're seeing is likely a **memory issue** causing Ollama to crash, which then causes the MCP connection to fail.

