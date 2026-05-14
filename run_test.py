#!/usr/bin/env python3
import sys
import os
import traceback

os.environ['PYTHONUTF8'] = '1'
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Redirect all output to a file
log_path = os.path.join(os.path.dirname(__file__), 'run_test.log')
with open(log_path, 'w', encoding='utf-8') as log:
    try:
        log.write("Starting test...\n")
        log.flush()
        
        os.chdir(os.path.dirname(__file__))
        log.write(f"Changed to directory: {os.getcwd()}\n")
        log.flush()
        
        # Remove lock file
        lock_file = os.path.join(os.path.dirname(__file__), '.monitor.lock')
        if os.path.exists(lock_file):
            os.remove(lock_file)
            log.write("Removed lock file\n")
            log.flush()
        
        log.write("Importing auto_monitor...\n")
        log.flush()
        
        import auto_monitor
        
        log.write("Calling main_loop...\n")
        log.flush()
        
        import signal
        def handler(signum, frame):
            log.write(f"Signal {signum} received!\n")
            log.flush()
        signal.signal(signal.SIGTERM, handler)
        
        try:
            auto_monitor.main_loop()
            log.write("main_loop completed normally\n")
        except BaseException as e:
            log.write(f"BaseException: {type(e).__name__}: {e}\n")
            log.write(traceback.format_exc())
        log.flush()
        
    except Exception as e:
        log.write(f"ERROR: {e}\n")
        log.write(traceback.format_exc())
        log.flush()

print(f"Log written to {log_path}")
