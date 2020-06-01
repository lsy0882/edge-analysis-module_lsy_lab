# EdgeAnalysisModule
## 변경 사항
* (0601)[] - 각 모듈별 테스트를 위한 방법 추가

## Introduce
본 프로젝트는 Jetson Nano에서 object detection 결과를 입력으로 받아 각 분석 엔진의 결과를 종합하여 관제 서버에 전송하는 서비스를 제공합니다.

각 분석 엔진의 결과를 종합한 전체 분석 결과 전송 모듈은 프로토콜을 정의하는 중으로 추후에 추가될 예정입니다. 

Python 코드로 구성되어 있으며, 소켓 통신을 기반으로 개발하였습니다.

본 프로젝트에서의 모델 테스트는 아래에 설명된 __분석 모델 테스트__([링크](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%B6%84%EC%84%9D-%EB%AA%A8%EB%8D%B8-%ED%85%8C%EC%8A%A4%ED%8A%B8))에 걸쳐 테스트를 하길 권장합니다.

Jetson Nano에 설치될 예정이기 때문에 Ubuntu 18.04 환경에서 테스트하시길 권장하며, 만약 다른 환경에서 테스트를 진행하시려면 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 메일로 문의해주시기 바랍니다.

분석 모델의 입력은 json으로 되어있으며 object detection의 입력으로 사용되는 원본 이미지는 json내에 경로로 입력되어 있으니 원본 이미지가 필요한 경우 해당 경로로 읽고 사용하시기 바랍니다.

또한 입력 json의 형식은 각 연구실에서 필요한 입력에 따라 데이터가 추가될 수 있으니 참고하시기 바랍니다.

## Prerequisites
* Ubuntu 18.04
* python 3.6

## Installation
Python 3.6의 기본 라이브러리를 이용하여 작성한 프로그램이기 때문에 별도의 pip를 이용하여 설치해야 할 라이브러리는 없습니다.

분석 모델에서 필요한 pip requirement가 있을 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/1))에 명시된 예시와 같이 코멘트를 추가해주시기 바랍니다. 
 
### Program
```shell script
sudo apt install -y python3 python3-dev python3-pip git
```
### Download Source Code
```shell script
git clone https://github.com/sogang-mm/EdgeAnalysisModule.git
```

## 분석 모델 정의
모든 설치가 끝났다면 Modules에 분석 모델을 정의하기위해 Modules 디렉토리로 이동합니다.

Modules 디렉토리 내에는 예시로 dummy와 dummy2 디렉토리가 있으며, dummy 디렉토리를 복사하신 후 분석 모델을 작성하시면 됩니다.

작성하셔야 하는 부분은 dummy 디렉토리 내의 main.py을 참고하여 작성하시기 바랍니다.

### 모델 수정(${PROJECT_DIR}/Modules/${MODEL_NAME}/main.py)
해당 파트에서는 수정하셔야 할 부분을 언급합니다.
```python
class Dummy:
```
* class 이름을 분석 모듈의 이름으로 수정하여 주시기 바랍니다.(예: Dummy -> FireDetection) 
```python
    def __init__(self):
        # TODO
        #   - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        #   - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        #     (전체 결과 예시 : [{'name': 'Dummy', 'result': []}, {'name': 'Dummy2', 'result': []}]})
        self.model_name = "Dummy"
```
* 해당 함수는 필요한 경우 분석 전에 필요한 모듈이나 모델을 불러오기 및 대기 상태 유지를 위한 코드를 작성하는 부분입니다.
* self.model_name은 모든 분석 모델의 결과를 종합할 때 분석 모델의 구분자로 쓰여지기 떄문에 되도록 class이름과 동일하게 해주시길 바랍니다. 

```python
    def analysis_from_json(self, od_result):
        '''...'''
        result = []
        import time
        time.sleep(2)

        self.result = result

        return self.result
```
* 해당 함수는 입력한 json 데이터를 기반으로 분석을 진행하는 함수로 import time과 time.sleep(2)을 지우시고 분석 모듈의 내용을 작성하시면 되며 최종적인 결과 값은 self.result에 저장하시기 바랍니다.
* object detection에 사용된 원본 이미지의 경우 json 파일 내에 명시되어 있으니 해당 경로를 이용하여 opencv나 pilimage를 이용해 불러와 사용하시면 됩니다.
* 분석에 필요한 입력 데이터가 없을 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/2))에 코멘트로 추가하여 주시면 해당 데이터를 정의하고 추가하도록 하겠습니다.
* 분석 결과의 경우 각 연구실별로 분석 내용이 다르고 분석 결과의 형식이 정해지지 않았기 때문에 분석 결과 형식의 경우 __관련 이슈__([링크](https://github.com/JinhaSong/EdgeAnalysisModule/issues/3))에 작성하여 주시기 바랍니다.
* 분석에 필요한 입력 데이터와 분석 결과 형식이 관련 이슈에 작성된 내용가 많이 상이하여 해당 형식을 이용하지 못할 경우 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 메일로 기

## 분석 모델 테스트
### 분석 모델 단독 테스트 (${PROJECT_DIR}/ModelTest.py)
모델을 작성 후 정의하신 분석 모델을 단독으로 테스트하기 위한 소스코드 파일입니다.
#### 테스트 코드 내 호출 모델 변경
```python
from dummy.main import Dummy # --> from Fire.main import FireDetection
```
* 정의허신 class로 변경하여 import 합니다.(예: from dummy.main import Dummy -> from Fire.main import FireDetection)
```python
model = Dummy()              # --> model = FireDetection()
```
* 정의한 class로 변경하여 호출합니다.(예: model = Dummy() -> model = FireDetection())
#### 테스트 코드 실행 방법
```shell script
cd ${PROJECT_DIR}
python3 Modules/ModuleTest.py
```
### 서버-클라이언트 기반 모델 테스트
실제로 모든 분석 모델을 통합한 전체 분석 결과를 전달하는 소켓 기반 서버-클라이언트 분석 프로그램입니다.


CCTV 영상을 decoding 및 object detection하는 프로그램과는 소켓으로 통신하며, 정의하신 모델을 테스트하기 위한 클라이언트 예시 코드(${PROJECT_DIR}/Client/example.py)를 작성해놓았으니 서버-클라이언트 테스트는 아래와 같이 진행하시면 됩니다.

클라이언트 코드는 프로젝트 내에 정의된 ${PROJECT_DIR}/data/ 하위의 json 디렉토리 내의 모든 json 파일을 모두 분석하는 형태로 되어있으며, 기존 추가된 데이터 외의 다른 데이터를 테스트 하시려면 ${PROJECT_DIR}/data/json 내의 파일을 참고하여 데이터를 추가하시면 추가 데이터에 대해서 테스트 가능합니다.

반드시 서버 코드(${PROJECT_DIR}/Server/AnalysisServer.py)를 먼저 실행하시고 클라이언트 코드(${PROJECT_DIR}/Client/example.py)를 실행하시기 바랍니다.
#### 서버 코드 내 호출 모델 변경(${PROJECT_DIR}/Server/AnalysisServer.py)
```python
from Modules.dummy.main import Dummy # --> from Modules.Fire.main import FireDetection
```
* 기존 호출 모델인 Dummy 대신 정의하신 분석 모델을 import 해야 하는 부분입니다.
```python
    def __init__(self, host="127.0.0.1", port=10001):
        self.host = host
        self.port = port

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        self.models = []

        dummy_model = Dummy()               # --> fire_detection_model = FireDetection()
        dummy2_model = Dummy2()

        self.models.append(dummy_model)     # --> self.models.append(fire_detection_model)
        self.models.append(dummy2_model)
```
* 정의하신 class로 변경하여 호출하고 model list(self.models)에 추가(append)해줍니다. (예: dummy_model = Dummy() --> fire_detection_model = FireDetection(), self.models.append(dummy_model) --> self.models.append(fire_detection_model))
#### 클라이언트 코드 사용방법(${PROJECT_DIR}/Client/example.py)
```shell script
cd ${PROJECT_DIR}
python3 Client/example.py --json_dir=${JSON_DIR}
```
* 기본적으로 프로젝트 디렉토리 내의 ${PROJECT_DIR}/data/json 하위의 json 확장자를 가진 파일만을 Server에 보내며 다른 데이터로 테스트를 하시길 원한다면 [${PROJECT_DIR}/data/json/sample1.json](https://github.com/JinhaSong/EdgeAnalysisModule/blob/master/data/json/sample1.json)을 참고하여 작성하신 후 테스트하시길 바랍니다.

## 분석 엔진 반영 방법
각 연구실에서는 해당 소스 코드를 fork하여 개발을 진행해주시기 바라며, 각 연구실의 분석 모듈이 완성될 경우 을${PROEJCT_DIR}/Modules 내에 정의하신 분석 모듈만을 pull request 해주시길 바랍니다.

해당 사항에 대하여 문의하실 부분이 있으실 경우 [문의](https://github.com/JinhaSong/EdgeAnalysisModule#%EB%AC%B8%EC%9D%98)에 있는 이메일로 문의해주시기 바랍니다.

## 문의
* email: [jinhasong@sogang.ac.kr](jinhasong@sogang.ac.kr)
