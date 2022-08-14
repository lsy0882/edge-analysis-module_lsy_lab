#!/bin/bash
WORKSPACE=/media/nvidia/external/edge-analysis-module
cd $WORKSPACE
celery -A tasks worker --loglevel=info --autoscale=2,2