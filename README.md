# edge-analysis-module

## Introduce
본 프로젝트는 Jetson Nano 및 Jetson Xavier NX에서 object detection 결과를 입력으로 받아 각 분석 엔진의 결과를 종합하여 관제 서버에 전송하는 서비스를 제공합니다.

본 프로젝트에서의 모델 테스트는 아래에 설명된 __분석 모델 테스트__([링크](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%B6%84%EC%84%9D-%EB%AA%A8%EB%8D%B8-%ED%85%8C%EC%8A%A4%ED%8A%B8))에 걸쳐 테스트를 하길 권장합니다.

Jetson Nano 및 Jetson Xavier NX에 설치될 예정이기 때문에 Ubuntu 18.04 환경에서 테스트하시길 권장하며, 만약 다른 환경에서 테스트를 진행하시려면 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 메일로 문의해주시기 바랍니다.

또한 입력 json의 형식은 각 연구실에서 필요한 입력에 따라 데이터가 추가될 수 있으니 참고하시기 바랍니다.

## Installation
설치 방법은 Jetson Nano & Jetson Xavier NX에서 진행하는 방법과 docker-compose 상에서 실행하는 방법으로 구성됩니다.

분석 모델에서 필요한 python requirement가 있을 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/1))에 명시된 예시와 같이 코멘트를 추가해주시기 바랍니다. 

추가적으로 FFmpeg이 requeirements에 추가되었으니 아래 링크를 참고하여 ffmpeg 4.2를 설치해주시기 바랍니다.

* [FFmpeg](https://velog.io/@jinhasong/Install-FFmpeg-4)
* [Jetson Nano & Jetson Xavier NX](https://github.com/JinhaSong/edge-analysis-module/blob/master/docs/building_on_jetson.md)
* [docker-compose](https://github.com/JinhaSong/edge-analysis-module/blob/master/docs/building_on_docker-compose.md)

## 분석 모델 정의
모든 설치가 끝났다면 이벤트 검출기 모델을 정의하기위해 detector/event/ 디렉토리로 이동합니다.

detector/event/ 디렉토리 내에는 기존에 정의하셨던 모델들을 rename하여 업로드 해놓았으니 각 연구실에서 담당하는 모델들을 수정하시고 테스트를 진행하시면 됩니다.

작성하셔야 하는 부분은 각 이벤트(assault, falldown, kidnapping, obstacle, reid, wanderer) 디렉토리 내의 main.py을 참고하여 작성하시기 바랍니다.

변경된 이벤트 디렉토리 이름 및 클래스 이름은 다음과 같습니다.
* FightDetection -> assault, AssaultEvent
* FalldownDetection -> falldown, FalldownEvent
* Tailing_Kidnapping -> kidnapping, KidnappingEvent & tailing, TailingEvent
* Obstacle -> obstacle, ObstacleEvent
* ReID -> reid, ReidEvent
* WandererDetection -> wanderer, WandererEvent

### 모델 수정(${PROJECT_DIR}/detector/event/${MODEL_NAME}/main.py)
해당 파트에서는 수정하셔야 할 부분을 언급합니다.
```python
class ...Event(Event):
```
* 필요한 이벤트의 클래스는 이미 정의 되어있으며 모델을 불러오는 부분과 inference 함수만 수정하시면 됩니다.  
```python
    def __init__(self, debug=False):
        super().__init__(debug)
        self.analysis_time = 0
        self.debug = debug
        self.result = False
        self.model_name = "${MODEL_Name}"

        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.
```
* 해당 함수는 필요한 경우 분석 전에 필요한 모듈이나 모델을 불러오기 및 대기 상태 유지를 위한 코드를 작성하는 부분입니다.
* self.model_name은 모든 분석 모델의 결과를 종합할 때 분석 모델의 구분자로 쓰여지기 떄문에 되도록 class이름과 동일하게 해주시길 바랍니다.
* TODO 하위의 주의사항에 유념하셔서 개발을 진행하시기 바랍니다. 

```python
        def inference(self, detection_result):
        start = 0
        end = 0
        if self.debug :
            start = time.time()

        # TODO: analysis
        # - 분석에 필요한 내용을 작성해주실 부분입니다.
        # - 마지막 라인(return self.result)는 테스트 코드에서 확인하기 위한 코드이며 실제로는 thread에서 사용하지 않습니다.
        #   따라서 반드시 결과 값은 self.result에 저장하시기 바라며, 마지막 라인은 변경하지 마시기 바랍니다.
        # - 이전 프레임의 결과를 사용해야하는 모듈들의 경우 self.history에 저장한 후 사용하시기 바랍니다.
        # - self.result에는 True 또는 False 값으로 이벤트 검출 결과를 저장해주시기 바랍니다. 

        if self.debug :
            end = time.time()
            self.analysis_time = end - start
            
        return self.result
```
* 분석에 필요한 입력 데이터가 없을 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/2))에 코멘트로 추가하여 주시면 해당 데이터를 정의하고 추가하도록 하겠습니다.
* 분석 결과의 경우 각 연구실별로 분석 내용이 다르고 분석 결과의 형식이 정해지지 않았기 때문에 분석 결과 형식의 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/3))에 작성하여 주시기 바랍니다.
* 분석에 필요한 입력 데이터와 분석 결과 형식이 관련 이슈에 작성된 내용가 많이 상이하여 해당 형식을 이용하지 못할 경우 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 메일로 기

## 분석 모델 테스트
#### 테스트 코드 실행 방법
```shell script
cd ${PROJECT_DIR}
python3 extract_results.py \ 
    --od_model_name=yolov4-416 \                                    # 객체 검출(Object Detection) 모델 이름(생략가능)
    --score_threshold=0.1 \                                         # 객체 검출 모델 score threshold(생략가능)
    --nms_threshold=0.5 \                                           # 객체 검출 모델 nms threshold(생략가능)
    --byte_tracker_params=0.1,0.5,30,0.8,10,20 \                    # Byte Tracker 파라미터(생략가능)
    --sort_params=0.5,2,20 \                                        # Sort Tracker 파라미터(생략가능)
    --event_model=assault,falldown,kidnapping,tailing,wanderer \    # 테스트하고자 하는 이벤트 모델 이름(생략가능)
    --event_model_score_threshold=0,0.5,0.5,0,0 \                   # 테스트하고자 하는 이벤트 모델의 score threshold(생략가능)
    --result_dir=${RESULT_DIR} \                                    # 분석 결과 저장 디렉토리 경로
    --video_path=${VIDEO_PATH} \                                    # 분석할 동영상 경로
    --save_frame_result \                                           # 옵션 추가 시 프레임 결과 저장(생략 시 저장X)
    --process_time                                                  # 옵션 추가 시 분석 처리 시간 표시(생략 시 처리 시간 미표시)
```
* 파라미터 값을 별토로 설정하지 않고 실행하고 싶을 경우 단순히 분석결과 저장 디렉토리(```--result_dir```)와 동영상 경로(```--video_path```)만 입력으로 주고 실행하면 됩니다.
  * example: ```python3 extract_results.py --result_dir=./result --video_path=./video.mp4```
### edge-analysis-module 사용 방법
#### 모듈 실행
```shell script
sh module_initialize.sh   # 모듈 초기화(기존 로그삭제)
sh module_start.sh        # 모듈 시작
```
* 모듈 시작 후 웹브라우저를 통해 ```http://${MODULE_IP}:8000/```로 접속하면 현재 모듈 상태를 확인할 수 있습니다.
#### Proxy 실행 및 모듈과 연결된 CCTV 화면 모니터링
```shell
bash scripts/run_scripts/run_proxy.sh  # streaming proxy 실행
```
* 모듈과 연결된 CCTV 카메라의 화면을 보고 싶을 경우 위 명령어를 이용해 proxy 서버를 별도로 실행 해줘야 모니터링 가능합니다.
* RTSP는 웹브라우저에서는 단독으로 스트리밍이 불가능하며, 별도의 proxy 서버를 실행 해줘야 스트리밍이 가능하기 때문에 proxy를 실행해주는 스크립트가 모듈에 추가되어 있습니다.
* 위 스크립트를 실행 후 모니터링 페이지에서 가져오기 → 재생 버튼을 차례로 누르면 재생이 됩니다.
  * 만약 run_proxy.sh를 이용해 proxy를 실행하지 않았다면 브라우저에서 에러메시지를 확인할 수 있습니다.
* 터미널에서 proxy를 종료하고 싶을 경우 ```scripts/run_scripts/stop_proxy.sh``` 쉘스크립트를 이용해 종료할 수 있습니다.
#### 모듈 종료
```shell script
sh module_shutdown.sh     # 모듈 종료
```

## 분석 엔진 반영 방법
각 연구실에서는 해당 소스 코드를 fork하여 개발을 진행해주시기 바라며, 각 연구실의 분석 모듈이 완성될 경우 을${PROEJCT_DIR}/detector/event 내에 수정하신 분석 모듈만을 pull request 해주시길 바랍니다.

pull request를 통해 소스 코드를 업데이트 하시기 전 테스트를 위한 주석 코드들은 모두 삭제하시고 pull request를 보내주시기 바랍니다.

해당 사항에 대하여 문의하실 부분이 있으실 경우 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 이메일로 문의해주시기 바랍니다.

## 문의
* email: [jinhasong@sogang.ac.kr](jinhasong@sogang.ac.kr)
