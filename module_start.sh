#!/bin/bash
nohup sh -- ./scripts/run_scripts/run_flask.sh > flask.log 2>&1 &
nohup sh -- ./scripts/run_scripts/run_celery.sh > celery.log 2>&1 &
echo "Start Server"