# 0602
* 형식 단일화를 위해 각 모듈의 결과 값을 저장하는 부분일 일부 수정하였으니 반드시 pull하신 후 작업을 진행하시기 바랍니다.
* 모듈 업데이트 후 pull request를 통해 소스코드 업데이트 바라며, 
다른 연구실의 검출기 소스코드와 충돌되지 않도록 미리 root repository([https://github.com/JinhaSong/EdgeAnalysisModule](https://github.com/JinhaSong/EdgeAnalysisModule))에서 pull하신 후 pull request하시기 바랍니다.
* 연구실에 Jetson Nano가 없을 경우 AS1001호에서 대여 가능합니다.<br>(미리 dependency 설치가 필요하고 개수가 얼마 없으므로 미리 문의주시고 찾아오시기 바랍니다.)
* 각 연구실의 모델만을 테스트 하고 싶으실 경우 아래와 같이 사용하고자 하는 검출기를 제외한 나머지를 모두 주석 처리하고 사용하시면 됩니다.<br>
→ [링크](https://github.com/JinhaSong/EdgeAnalysisModule/blob/master/Server/AnalysisServer.py)
``` python
        fight_detection_model = FightDetection(self.debug)
        print("INFO: {} - {} model is loaded".format(datetime.now(), fight_detection_model.model_name))

        # wander_detection_model = WanderDetection(self.debug)
        # print("INFO: {} - {} model is loaded".format(datetime.now(), wander_detection_model.model_name))

        # obstacle_model = Obstacle(self.debug)
        # print("INFO: {} - {} model is loaded".format(datetime.now(), obstacle_model.model_name))

        # tailing_kidnapping_model = Tailing_Kidnapping(self.debug)
        # print("INFO: {} - {} model is loaded".format(datetime.now(), tailing_kidnapping_model.model_name))

        self.models.append(fight_detection_model)
        # self.models.append(wander_detection_model)
        # self.models.append(obstacle_model)
        # self.models.append(tailing_kidnapping_model)
        print("INFO: {} - Server is Initialized".format(datetime.now()))
```
* fight detection model만 테스트하고자 하는 경우
