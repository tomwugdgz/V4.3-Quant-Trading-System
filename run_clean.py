#!/usr/bin/env python3
"""Wrapper to run auto_monitor.py with full error logging."""
import sys
import os
import traceback
from datetime import datetime

log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auto_monitor_run.log')

with open(log_path, 'w', encoding='utf-8') as f:
    def write(msg):
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")
        f.flush()
    
    try:
        write("Wrapper started")
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        write(f"Changed to: {os.getcwd()}")
        
        # Remove stale lock
        lock_path = os.path.join(os.getcwd(), '.monitor.lock')
        if os.path.exists(lock_path):
            try:
                os.remove(lock_path)
                write("Removed stale lock file")
            except Exception as e:
                write(f"Failed to remove lock: {e}")
        
        write("Importing auto_monitor module...")
        # Don't let the module rewrap stdout/stderr
        import importlib.util
        spec = importlib.util.spec_from_file_location("auto_monitor", "auto_monitor.py")
        am = importlib.util.module_from_spec(spec)
        
        # Preserve original stdout/stderr before module import
        orig_stdout = sys.stdout
        orig_stderr = sys.stderr
        
        write("Executing module...")
        spec.loader.exec_module(am)
        
        write("Calling main_loop...")
        am.main_loop()
        
        write("main_loop completed successfully")
        
    except Exception as e:
        write(f"ERROR: {e}")
        write(traceback.format_exc())

print(f"Log written to {log_path}")
