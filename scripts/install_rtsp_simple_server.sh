#!/bin/bash

set -e

version="v0.19.2"

echo "[INFO] Download rtsp-simple-server(${version})"
wget -nc https://github.com/aler9/rtsp-simple-server/releases/download/${version}/rtsp-simple-server_${version}_linux_armv7.tar.gz
echo "[INFO] Unzip rtsp-simple-server_${version}_linux_armv7.tar.gz"
tar xvf rtsp-simple-server_${version}_linux_armv7.tar.gz
echo "[INFO] Add to crontab to run rtsp-simple-server on reboot"
crontab ./crontab_rss_setting
echo "[INFO] rtsp-simple-server is successfully installed. Now when the system reboots, rtsp-simple-server will run automatically."
