#!/usr/bin/env python3
"""Integration tests for the AI agent system."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.client import Agent


async def run_tests():
    """Execute integration test suite."""
    print("=" * 50)
    print("Agent Integration Tests")
    print("=" * 50)
    
    agent = Agent()
    passed = 0
    failed = 0
    
    try:
        # Test 1: Connection
        print("\n[1] Testing server connection...")
        await agent.initialize()
        print(f"    ✓ Connected, {len(agent.tools)} tools discovered")
        passed += 1
        
        # Test 2: Tool discovery
        print("\n[2] Verifying tool discovery...")
        tool_names = [t['function']['name'] for t in agent.tools]
        expected = ['text_reversal', 'timestamp', 'sysinfo']
        found = all(name in tool_names for name in expected)
        if found:
            print(f"    ✓ Expected tools present: {expected}")
            passed += 1
        else:
            print(f"    ✗ Missing expected tools. Found: {tool_names}")
            failed += 1
        
        # Test 3: Direct tool invocation
        print("\n[3] Testing direct tool invocation...")
        result = await agent._bridge.invoke("text_reversal", {"text": "hello"})
        if result.get("ok") and result.get("data", {}).get("output") == "olleh":
            print(f"    ✓ text_reversal works: hello → olleh")
            passed += 1
        else:
            print(f"    ✗ Unexpected result: {result}")
            failed += 1
        
        # Test 4: Timestamp tool
        print("\n[4] Testing timestamp tool...")
        result = await agent._bridge.invoke("timestamp", {})
        if result.get("ok") and "iso" in result.get("data", {}):
            print(f"    ✓ timestamp works: {result['data']['iso']}")
            passed += 1
        else:
            print(f"    ✗ Unexpected result: {result}")
            failed += 1
        
        # Test 5: System info tool
        print("\n[5] Testing sysinfo tool...")
        result = await agent._bridge.invoke("sysinfo", {})
        if result.get("ok"):
            data = result.get("data", {})
            print(f"    ✓ sysinfo works: {data.get('os')} / Python {data.get('python')}")
            passed += 1
        else:
            print(f"    ✗ Unexpected result: {result}")
            failed += 1
        
    except Exception as e:
        print(f"\n✗ Test error: {e}")
        import traceback
        traceback.print_exc()
        failed += 1
    
    finally:
        await agent.shutdown()
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_tests())
    sys.exit(0 if success else 1)
