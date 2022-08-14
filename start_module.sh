#!/bin/bash
nohup sh -- ./run_flask.sh > flask.log 2>&1 &
nohup sh -- ./run_celery.sh > celery.log 2>&1 &
echo "Start Server"