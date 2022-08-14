# Build the Project from Source on Jetson Nano
* 본 프로젝트를 Jetson Nano 및 Jetson Xavier NX에서 설치하기 위해서는 Jetson Nano 또는 Jetson Xavier NX에 Jetpack 4.4.1 이미지를 설치하신 후 아래에 따라 빌드하시기 바랍니다.
## Build from jetson-inference source code
```shell script
sudo apt-get update
sudo apt-get install git cmake libpython3-dev python3-numpy
git clone --recursive https://github.com/dusty-nv/jetson-inference
cd jetson-inference
mkdir build
cd build
cmake ../
make -j$(NPROC)
sudo make install
sudo ldconfig
```
## Build from EdgeAnalysisModule source code
### Export CUDA and LD_LIBRARY path
```shell script
# Add blow codes in "~/.bashrc" file
export CUDA_HOME=/usr/local/cuda
export LD_LIBRARY_PATH=${CUDA_HOME}/lib64
PATH=${CUDA_HOME}/bin:${PATH}
export PATH

# Apply
source ~/.bashrc
``` 
### Clone repository
```shell script
cd ${WORKSPACE}
git clone https://${PERSONAL_ACCESS_TOKEN}@github.com/Jinhasong/edge-analysis-module.git
```
### Install python requirements
```shell script
cd ${WORKSPACE}/edge-analysis-module
pip3 install -r requirements.txt 
``` 
### Install Protobuf, PyCUDA and ONNX
* Jetson Nano에서 해당 소스 코드를 사용하기 위해서는 protobuf-3.8.0 이 필요하며 apt를 이용해 기본으로 설치할 수 있는 protobuf는 이보다 하위 버전이기 때문에 별도의 빌드 및 설치가 필요합니다.
```shell script
cd ${WORKSPACE}/edge-analysis-module/scripts
chmod +x ./install_protobuf-3.8.0.sh
chmod +x ./install_pycuda.sh
./install_protobuf-3.8.0.sh
./install_pycuda.sh
```
### Build plugin for yolo layer
```shell script
cd ${WORKSPACE}/edge-analysis-module/detector/object_detection/yolov4/plugins
make ${NPROC}
```
### Download YOLOv4-obstacle model and Convert yolo to trt
```shell script
cd ${WORKSPACE}/edge-analysis-module/detector/object_detection/yolov4/yolo
chmod +x download_yolov4_416_obstacle.sh
chmod +x yolov4_obstacle_yolo_to_trt.sh
./download_yolov4_416_obstacle.sh
./yolov4_obstacle_yolo_to_trt.sh
```

### Install rtsp-simple-server
```shell
cd ${WORKSPACE}/edge-analysis-module/scripts
sh ./install_rtsp_simple_server.sh
```