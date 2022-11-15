#!/bin/bash
nohup sh -- /media/nvidia/external/edge-analysis-module/scripts/run_scripts/run_flask.sh > flask.log 2>&1 &
nohup sh -- /media/nvidia/external/edge-analysis-module/scripts/run_scripts/run_celery.sh > celery.log 2>&1 &
echo "Start Server"