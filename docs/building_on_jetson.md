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
git clone https://${AUTH_KEY}@github.com/Jinhasong/edge-analysis-module.git
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

### Extract analysis results
```shell script
python3 extract_results.py \
    --event_model=assault,falldown,kidnapping,tailing,wanderer \
    --assault_score_th=0.1 \
    --falldown_score_th=0.5 \
    --kidnapping_score_th=0.5 \
    --tailing_score_th=0.5 \
    --wanderer_score_th=0.5 \
    --result_dir=./results/ \
    --video_path=videos/aihub_01_360p.mp4
```
- 4월 8일 업데이트 기준 이전 객체 검출 모델(yolov4)에서 score threshold로 필터링 하던 부분을 각 이벤트 검출 모델에서 필터링 가능하도록 업데이트했습니다
- extract_results.py 실행 시 각 모델별 필터링 기본값은 __0.5__ 이며 위와 같이 ${EVENT}_score_th 파라미터로 조절 가능합니다.
- yolov4에서의 기본 필터링 score threshold는 0.1 미만으로 낮췄을 경우 속도저하가 매우 심하여 0.1이 기본값으로 설정되어 있습니다. 