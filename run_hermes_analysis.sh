#!/bin/bash
cd /home/dukcowlf/.hermes/hermes-agent
QUERY=$(cat /tmp/trading_analysis_prompt.txt)
/home/dukcowlf/.local/bin/hermes chat -q "$QUERY" -Q --yolo --max-turns 30
