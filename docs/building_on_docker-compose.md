# Build the Project using Docker-compose from Source
* 본 프로젝트를 Ubuntu 18.04에서 설치하기 위해서는 TensorRT 및 별도의 라이브러리를 설치하여야 하기때문에 docker와 docker-compose를 설치하신 후 아래에 따라 빌드하시기 바랍니다.
* [docker 설치 방법](https://velog.io/@jinhasong/Docker-install)
* [nvidia-docker2 설치 방법](https://velog.io/@jinhasong/Nvidia-docker2-install)
* [docker-compose 설치 방법](https://velog.io/@jinhasong/Docker-compose-install)

## Build using Docker-compose 
### Clone repository
```shell script
cd ${WORKSPACE}
git clone https://${PERSONAL_ACCESS_TOKEN}@github.com/Jinhasong/edge-analysis-module.git
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
### Install python requirements
```shell script
cd /workspace
pip3 install -r requirements.txt 
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
    --result_dir=./results/ \
    --video_path=videos/aihub_01_360p.mp4
```
- yolov4에서의 기본 필터링 score threshold는 0.1 미만으로 낮췄을 경우 속도저하가 매우 심하여 0.1이 기본값으로 설정되어 있습니다.
- argument에 대한 설명은 hyperparameter가 결정된 후 작성될 예정입니다.