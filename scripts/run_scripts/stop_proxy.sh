#!/bin/bash
process=$(ps -ef | grep 'ffmpeg -re -stream_loop')
pid=$(echo ${process} | cut -d " " -f2)

if [ -n "${pid}" ]
then
    result1=$(kill -9 ${pid})
    echo "Process is killed.(pid: ${pid})"
else
    echo "Running process not found."
fi