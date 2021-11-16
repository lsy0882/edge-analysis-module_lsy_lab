#!/usr/bin/env bash
(exec kill $(ps aux |awk '/python3 main.py/ {print $2}')) 2>/dev/null &
echo "Shutdown Server"
/usr/bin/env bash