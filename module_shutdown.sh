#!/bin/bash
(exec sudo kill $(ps aux |awk '/main.py/ {print $2}')) 2>/dev/null
(exec sudo kill $(ps aux |awk '/celery/ {print $2}')) 2>/dev/null