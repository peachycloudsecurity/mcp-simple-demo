#!/usr/bin/env python3
"""Unit tests for the tool registry."""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.tools import registry


def run_tests():
    """Test all registered tools."""
    print("=" * 50)
    print("Tool Registry Tests")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    # Test 1: text_reversal
    print("\n[1] text_reversal...")
    result = registry.execute("text_reversal", {"text": "python"})
    if result.get("ok") and result["data"]["output"] == "nohtyp":
        print(f"    ✓ Passed: python → nohtyp")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 2: timestamp
    print("\n[2] timestamp...")
    result = registry.execute("timestamp", {})
    if result.get("ok") and "iso" in result.get("data", {}):
        print(f"    ✓ Passed: {result['data']['iso']}")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 3: sysinfo
    print("\n[3] sysinfo...")
    result = registry.execute("sysinfo", {})
    if result.get("ok") and "os" in result.get("data", {}):
        print(f"    ✓ Passed: OS={result['data']['os']}")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 4: mkdir
    print("\n[4] mkdir...")
    result = registry.execute("mkdir", {"path": "data/test_dir"})
    if result.get("ok"):
        print(f"    ✓ Passed: Created {result['data']['created']}")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 5: file_write
    print("\n[5] file_write...")
    result = registry.execute("file_write", {"path": "data/test.txt", "content": "Hello!"})
    if result.get("ok"):
        print(f"    ✓ Passed: Wrote {result['data']['size']} bytes")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 6: jwt_decode
    print("\n[6] jwt_decode...")
    test_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U"
    result = registry.execute("jwt_decode", {"token": test_jwt})
    if result.get("ok") and result["data"]["payload"].get("sub") == "1234567890":
        print(f"    ✓ Passed: Decoded JWT payload")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 7: log_search
    print("\n[7] log_search...")
    result = registry.execute("log_search", {"ip": "192.168.1.1"})
    if result.get("ok"):
        print(f"    ✓ Passed: Found {result['data']['count']} matches")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 8: ticket_action
    print("\n[8] ticket_action...")
    result = registry.execute("ticket_action", {"ticket_id": "BUG-123", "action": "close"})
    if result.get("ok"):
        print(f"    ✓ Passed: {result['data']['result']}")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Test 9: Unknown tool
    print("\n[9] Unknown tool handling...")
    result = registry.execute("nonexistent", {})
    if not result.get("ok") and "not found" in result.get("error", ""):
        print(f"    ✓ Passed: Correctly reported missing tool")
        passed += 1
    else:
        print(f"    ✗ Failed: {result}")
        failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 50)
    
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
