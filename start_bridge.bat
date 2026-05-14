@echo off
start /min wsl -d Ubuntu bash -c "cd /home/dukcowlf/.hermes && nohup /home/dukcowlf/.hermes/hermes-agent/venv/bin/python3 hermes-bridge_server.py --port 8642 > /tmp/bridge.log 2>&1 &"
timeout /t 3 >nul
wsl -d Ubuntu ss -tlnp | findstr 8642
