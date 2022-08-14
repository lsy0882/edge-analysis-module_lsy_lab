#!/bin/bash
tmp_ip=$(hostname -I)
ip="${tmp_ip:0:-1}"
cam_rtsp_address=$(python3 utils/get_cam_rtsp_address.py)
proxy_rtsp_address="rtsp://$ip:8554/proxy"
proxy_hls_address="http://$ip:8888/proxy/index.m3u8"

echo "Start proxy."
echo "    Descriptions:"
echo "        Connected Camera RTSP Address: $cam_rtsp_address"
echo "        Proxy HLS Address: $proxy_hls_address"
echo "        Proxy RTSP Address: $proxy_rtsp_address"
ffmpeg -re -stream_loop -1 -i $cam_rtsp_address -c copy -f rtsp $proxy_rtsp_address 2> /dev/null &