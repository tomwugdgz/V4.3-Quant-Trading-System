# -*- coding: utf-8 -*-
"""
MT5 Connection Fix
Steps to fix -6 Authorization error
"""

import subprocess
import os
import sys

def print_step(msg):
    print("\n" + "="*60)
    print(msg)
    print("="*60)

print_step("1. Killing all MT5 and Python processes")

# Kill all terminal64
subprocess.run(["taskkill", "/F", "/IM", "terminal64.exe"], 
               capture_output=True, text=True)
subprocess.run(["taskkill", "/F", "/IM", "python.exe"], 
               capture_output=True, text=True)

print("✓ Killed all processes")

print_step("2. Starting MT5 terminal")

# Start MT5
mt5_path = r"C:\Program Files\MetaTrader 5\terminal64.exe"
process = subprocess.Popen([mt5_path], 
                         creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

print("✓ MT5 starting... waiting 15 seconds")
import time
time.sleep(15)

print_step("3. Testing connection")

# Now test connection
import MetaTrader5 as mt5

result = mt5.initialize()
print(f"Initialize result: {result}")

if result:
    print("✓ Connection SUCCESS!")
    account = mt5.account_info()
    if account:
        print(f"Account: {account.login}")
        print(f"Balance: ${account.balance:.2f}")
        print(f"Equity: ${account.equity:.2f}")
    else:
        print("⚠️ Connected but no account info - check login")
else:
    error = mt5.last_error()
    print(f"✗ Connection FAILED: {error}")
    print("\nManual steps required:")
    print("1. Open MT5 → Tools → Options → Expert Advisors")
    print("2. Check ✓ 'Allow automated trading'")
    print("3. Check ✓ 'Allow DLL imports'")
    print("4. Uncheck ✗ 'Disable automated trading when account has changed'")
    print("5. Restart MT5 and run this script again")

mt5.shutdown()
