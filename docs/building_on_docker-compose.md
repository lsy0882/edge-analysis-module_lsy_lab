# Build the Project using Docker-compose from Source
* 본 프로젝트를 Ubuntu 18.04에서 설치하기 위해서는 TensorRT 및 별도의 라이브러리를 설치하여야 하기때문에 docker와 docker-compose를 설치하신 후 아래에 따라 빌드하시기 바랍니다.
* [docker 설치 방법](https://velog.io/@jinhasong/Docker-install)
* [nvidia-docker2 설치 방법](https://velog.io/@jinhasong/Nvidia-docker2-install)
* [docker-compose 설치 방법](https://velog.io/@jinhasong/Docker-compose-install)

## Build using Docker-compose 
### Clone repository
```shell script
cd ${WORKSPACE}
git clone https://github.com/Jinhasong/edge-analysis-module.git
```
### build Cocker Container using Docker-compose
```shell script
cd ${WORKSPACE}
docker-compose up -d
```
### Access inside the Docker Container
```shell script
# Any where
docker attach edge-analysis-module_main_1
```

## Build Project from Source inside Docker Container
### Reinstall pip
* 해당 이미지의 pip가 정상적으로 동작하지 않기 때문에 git-pip.py를 이용하여 재설치 해줍니다.
```shell script
cd /workspace/scripts
python3 get-pip.py --force-reinstall
```
### Install python requirements
```shell script
cd /workspace
pip3 install -r requirements.txt 
``` 

### Install Protobuf, PyCUDA and ONNX
* Jetson Nano에서 해당 소스 코드를 사용하기 위해서는 protobuf-3.8.0 이 필요하며 apt를 이용해 기본으로 설치할 수 있는 protobuf는 이보다 하위 버전이기 때문에 별도의 빌드 및 설치가 필요합니다.
```shell script
cd /workspace/scripts
chmod +x ./install_protobuf-3.8.0_root.sh
chmod +x ./install_pycuda_root.sh
./install_protobuf-3.8.0_root.sh
./install_pycuda_root.sh
```
### Build plugin for yolo layer
```shell script
cd /workspace/detector/object_detection/yolov4/plugins
make -j${NPROC}
```
### Download YOLOv4-obstacle model and Convert yolo to trt
```shell script
cd /workspace/detector/object_detection/yolov4/yolo
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