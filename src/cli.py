#!/usr/bin/env python3
"""
Interactive command-line interface for the AI agent.

Uses Rich library for enhanced terminal output with a
command-based interaction model.
"""

import asyncio
import sys
import os
from enum import Enum, auto

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt
from rich.theme import Theme

from src.client import Agent
from src.config import get_config

# Custom theme for consistent styling
custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "red bold",
    "success": "green",
    "user": "green bold",
    "assistant": "blue bold"
})

console = Console(theme=custom_theme)
cfg = get_config()


class Command(Enum):
    """Available CLI commands."""
    QUIT = auto()
    RESET = auto()
    HELP = auto()
    TOOLS = auto()
    CHAT = auto()


def parse_input(text: str) -> tuple[Command, str]:
    """Parse user input into command and argument."""
    text = text.strip()
    
    if not text:
        return Command.CHAT, ""
    
    lower = text.lower()
    if lower in ('exit', 'quit', 'q', '/quit', '/exit'):
        return Command.QUIT, ""
    if lower in ('reset', '/reset', '/clear'):
        return Command.RESET, ""
    if lower in ('help', '/help', '?'):
        return Command.HELP, ""
    if lower in ('tools', '/tools'):
        return Command.TOOLS, ""
    
    return Command.CHAT, text


def show_banner():
    """Display welcome banner."""
    console.print(Panel(
        f"[bold]AI Agent Terminal[/bold]\n"
        f"Model: [info]{cfg.llm.model_name}[/info]\n\n"
        f"Commands: [dim]/help, /tools, /reset, /quit[/dim]",
        border_style="blue",
        padding=(1, 2)
    ))


def show_help():
    """Display help information."""
    table = Table(title="Available Commands", show_header=True)
    table.add_column("Command", style="cyan")
    table.add_column("Description")
    
    table.add_row("/help, ?", "Show this help message")
    table.add_row("/tools", "List available tools")
    table.add_row("/reset", "Clear conversation history")
    table.add_row("/quit, /exit", "Exit the application")
    table.add_row("[text]", "Send message to AI")
    
    console.print(table)


def show_tools(tools: list):
    """Display available tools in a table."""
    table = Table(title="Available Tools", show_header=True)
    table.add_column("Name", style="cyan")
    table.add_column("Description")
    
    for tool in tools:
        fn = tool.get("function", {})
        table.add_row(fn.get("name", "?"), fn.get("description", "")[:60])
    
    console.print(table)


async def run_session():
    """Main interaction loop."""
    agent = Agent()
    
    show_banner()
    
    # Initialize agent
    with console.status("[info]Connecting to tool server...[/info]"):
        try:
            await agent.initialize()
            console.print("[success]✓ Connected[/success]")
            console.print(f"[dim]{len(agent.tools)} tools available[/dim]\n")
        except Exception as e:
            console.print(f"[error]Failed to initialize: {e}[/error]")
            return
    
    try:
        while True:
            try:
                user_input = Prompt.ask("\n[user]You[/user]")
                cmd, arg = parse_input(user_input)
                
                if cmd == Command.QUIT:
                    console.print("[warning]Goodbye![/warning]")
                    break
                
                if cmd == Command.RESET:
                    agent.reset()
                    console.print("[info]Conversation cleared[/info]")
                    continue
                
                if cmd == Command.HELP:
                    show_help()
                    continue
                
                if cmd == Command.TOOLS:
                    show_tools(agent.tools)
                    continue
                
                if cmd == Command.CHAT and not arg:
                    continue
                
                # Process chat message
                with console.status("[dim]Thinking...[/dim]"):
                    response = await agent.chat(arg)
                
                console.print("\n[assistant]Assistant[/assistant]")
                console.print(Markdown(response))
                
            except KeyboardInterrupt:
                console.print("\n[warning]Use /quit to exit[/warning]")
            except Exception as e:
                console.print(f"[error]Error: {e}[/error]")
    
    finally:
        await agent.shutdown()


def main():
    """Entry point."""
    try:
        asyncio.run(run_session())
    except KeyboardInterrupt:
        console.print("\n[warning]Interrupted[/warning]")
        sys.exit(0)


if __name__ == "__main__":
    main()
