# EdgeAnalysisModule
## 변경 사항
* [0601](https://github.com/JinhaSong/EdgeAnalysisModule/blob/master/UPDATE.md#0602) - 각 모듈별 테스트를 위한 방법 추가

## Introduce
본 프로젝트는 Jetson Nano 및 Jetson Xavier NX에서 object detection 결과를 입력으로 받아 각 분석 엔진의 결과를 종합하여 관제 서버에 전송하는 서비스를 제공합니다.

Python 코드로 구성되어 있으며, 소켓 통신을 기반으로 개발하였습니다.

본 프로젝트에서의 모델 테스트는 아래에 설명된 __분석 모델 테스트__([링크](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%B6%84%EC%84%9D-%EB%AA%A8%EB%8D%B8-%ED%85%8C%EC%8A%A4%ED%8A%B8))에 걸쳐 테스트를 하길 권장합니다.

Jetson Nano 및 Jetson Xavier NX에 설치될 예정이기 때문에 Ubuntu 18.04 환경에서 테스트하시길 권장하며, 만약 다른 환경에서 테스트를 진행하시려면 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 메일로 문의해주시기 바랍니다.

분석 모델의 입력은 json으로 되어있으며 object detection의 입력으로 사용되는 원본 이미지는 json내에 경로로 입력되어 있으니 원본 이미지가 필요한 경우 해당 경로로 읽고 사용하시기 바랍니다.

또한 입력 json의 형식은 각 연구실에서 필요한 입력에 따라 데이터가 추가될 수 있으니 참고하시기 바랍니다.

## Installation
설치 방법은 Jetson Nano & Jetson Xavier NX에서 진행하는 방법과 docker-compose 상에서 실행하는 방법으로 구성됩니다.

분석 모델에서 필요한 pip requirement가 있을 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/1))에 명시된 예시와 같이 코멘트를 추가해주시기 바랍니다. 
 
* [Jetson Nano & Jetson Xavier NX](https://github.com/JinhaSong/EdgeAnalysisModule/docs/build_on_jetson.md)
* [docker-compose](https://github.com/JinhaSong/EdgeAnalysisModule/docs/build_on_docker-compose.md)

## 분석 모델 정의
모든 설치가 끝났다면 이벤트 검출기 모델을 정의하기위해 detector/event/ 디렉토리로 이동합니다.

detector/event/ 디렉토리 내에는 기존에 정의하셨던 모델들을 rename하여 업로드 해놓았으니 각 연구실에서 담당하는 모델들을 수정하시고 테스트를 진행하시면 됩니다.

작성하셔야 하는 부분은 각 이벤트(assault, falldown, kidnapping, obstacle, reid, wanderer) 디렉토리 내의 main.py을 참고하여 작성하시기 바랍니다.

변경된 이벤트 디렉토리 이름 및 클래스 이름은 다음과 같습니다.
* FightDetection -> assault, AssaultEvent
* FalldownDetection -> falldown, FallDown
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
### 분석 모델 단독 테스트 (${PROJECT_DIR}/ModelTest.py)
모델을 작성 후 정의하신 분석 모델을 단독으로 테스트하기 위한 소스코드 파일입니다.
#### 테스트 코드 내 호출 모델 변경
```python
from detector.event.template.main import Event # --> from detector.event.assault.main import AssaultEvent
```
* 정의허신 class로 변경하여 import 합니다.(예: from detector.event.template.main import Event -> from detector.event.assault.main import AssaultEvent)
```python
model = Event()              # --> model = AssaultEvent()
```
* 정의한 class로 변경하여 호출합니다.(예: model = Event() -> model = AssaultEvent())
#### 테스트 코드 실행 방법
```shell script
cd ${PROJECT_DIR}
python3 Modules/ModuleTest.py --json_path ${json_path}
```
### EdgeAnalysisModule 전체 실행 방법
```shell script
python3 main.py --mode=console --cam_address=rtsp://163.239.25.80:8554/1_360p --analysis_fps=4
python3 main.py --mode=console --cam_address=/workspace/videos/1_360p.mp4 --analysis_fps=4
```
Argument
* mode: UI 모드 또는 console 모드 (UI 모드는 jetson 상에서만 가능하며 docker container는 GUI 환경을 가지지 못하기 때문에 docker 상에서는 console 모드로만 사용하시기 바랍니다.)
* cam_address: 분석하고자하는 비디오 스트리밍의 주소 또는 비디오 파일의 경로 입니다.
* analysis_fps: 초당 분석할 프레임의 수입니다.

## 분석 엔진 반영 방법
각 연구실에서는 해당 소스 코드를 fork하여 개발을 진행해주시기 바라며, 각 연구실의 분석 모듈이 완성될 경우 을${PROEJCT_DIR}/Modules 내에 정의하신 분석 모듈만을 pull request 해주시길 바랍니다.

pull request를 통해 소스 코드를 업데이트 하시기 전 테스트를 위한 주석 코드들은 모두 삭제하시고 pull request를 보내주시기 바랍니다.

해당 사항에 대하여 문의하실 부분이 있으실 경우 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 이메일로 문의해주시기 바랍니다.

## 문의
* email: [jinhasong@sogang.ac.kr](jinhasong@sogang.ac.kr)
