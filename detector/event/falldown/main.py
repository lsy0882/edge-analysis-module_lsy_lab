from __future__ import print_function

import os
import numpy as np
import json
import time
from detector.event.template.main import Event
# Notice
# - Dummy class는 참고 및 테스트용이기 때문에 해당 class는 수정 또는 삭제하지 말고 참고만 해주시기 바랍니다.
# - 이미 정의된 함수 및 클래스 멤버 변수의 이름은 *****절대로**** 변경하지마세요.


class FalldownEvent(Event):
    model = None
    path = os.path.dirname(os.path.abspath(__file__))

    def __init__(self, debug=False):
        super().__init__(debug)
        self.model_name = "falldown"
        self.people_max = 100
        
        self.analysis_time = 0
        self.debug = debug
        self.history = []
        self.result = False

        for i in range(self.people_max):
            self.history.append(0)
        # TODO: __init__
        # - 분석에 필요한 모델이 별도의 초기화나 load가 필요한 경우 이곳에서 초기화를 진행합니다.
        # - self.model_name을 분석 모델의 이름으로 수정해야 하며 이 변수는 전체 결과에서 구분자 역할을 합니다.
        # - 위의 4개 변수(model_name, analysis_time, debug, result) 중 하나라도 삭제하면 동작이 안되니 유의해주시기 바랍니다.


        


        self.people_locate = []
        for i in range(self.people_max):
            self.people_locate.append([0,0])
        
        self.temp_frame =1
        self.stop_count = 0
        self.tracking_method = False
        self.before_falldown_count = [0 for i in range (self.people_max)]

    def inference(self, od_result):
        start = 0
        end = 0

        if self.debug :
            start = time.time()

        # TODO: analysis(시작 지점)
        # - 분석에 필요한 내용을 작성해주실 부분입니다.
        # - 마지막 라인(return self.result)는 테스트 코드에서 확인하기 위한 코드이며 실제로는 thread에서 사용하지 않습니다.
        #   따라서 반드시 결과 값은 self.result에 저장하시기 바라며, 마지막 라인은 변경하지 마시기 바랍니다.
        # - 이전 프레임의 결과를 사용해야하는 모듈들의 경우 self.history에 저장한 후 사용하시기 바랍니다.
        # - self.result에는 True 또는 False 값으로 이벤트 검출 결과를 저장해주시기 바랍니다.

        # rule 1  
        count = 0
        detection_result = od_result['results'][0]['detection_result']
        self.result = False #init 
            
        for info_ in detection_result:
            #print(info_['position'])
            #dets =[]
            if info_['label'][0]['description'] == "person" and float(info_['label'][0]['score']) > 50:
                #dets.append(int(info_['position']['x']))
                #dets.append(int(info_['position']['y']))
                #dets.append(int(info_['position']['x']+info_['position']['w']))
                #dets.append(int(info_['position']['y']+info_['position']['h']))
                #convert to [x1,y1,w,h] to [x1,y1,x2,y2]
                #dets.append(float(info_['label'][0]['score']))

                #print("x: , ", int(info_['position']['x']) , " y: ",int(info_['position']['y']) )  
                        
                
                if self.tracking_method == True:
                
                    for i in range(self.people_max):
                        dis_x = self.people_locate[i][0] - int(info_['position']['x'])
                        dis_y = self.people_locate[i][1] - int(info_['position']['y'])
                        
                        if (dis_x*dis_x) + (dis_y*dis_y) < 100\
                            and int(info_['position']['w']) >= int(info_['position']['h']):
                            self.history[i] += 1
                            break # if checked the info_['position'], break and check other person
                            
                        elif self.history[i] > 0 : 
                            self.history[i] -= 1
                    
                    
                    self.people_locate[count] = [int(info_['position']['x']), int(info_['position']['y'])]
                    
                else:
                    if int(info_['position']['w']) >= int(info_['position']['h']): #falldown
                        self.before_falldown_count[count] += 1
                    elif  self.before_falldown_count[count] > 0:
                        self.before_falldown_count[count] -= 1
                        
                    #print("before_falldown_count : ", self.before_falldown_count[count])
                    
                count += 1 # person count 
                
        #print("history : ", self.history)
        
        if self.tracking_method == True:
            for i in range(self.people_max):
                if self.history[i] > 3:
                    #print("Fall down!, ", self.people_locate[i])
                    self.result = True
        else:
            for i in range(self.people_max):
                if self.before_falldown_count[i] > 2 :
                    #print("Fall down!, ", self.before_falldown_count[i])
                    self.result = True
                    break
        #print("self.result :", self.result )    

        # TODO: analysis(끝 지점)
        if self.debug :
            end = time.time()
            self.analysis_time = end - start
        
        return self.result
