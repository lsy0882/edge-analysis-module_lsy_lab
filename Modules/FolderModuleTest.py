from FalldownDetection.main import FalldownDetection
#from WanderDetection.main import WanderDetection
# from FightDetection.main import FightDetection
import argparse
import os
import json
import sys
import cv2


def main(database_path, video_filename):
    
    #opt = parser.parse_known_args()[0]
    
    model = FalldownDetection(0)
    
    frame_folder_path = os.path.join(database_path, "frames_5fps", video_filename)
    json_folder_path = os.path.join(database_path, "detection_results", video_filename)
    
    #frame_file_list = os.listdir(frame_folder_path)
    #frame_file_list.sort()
    
    json_file_list = os.listdir(json_folder_path)
    json_file_list.sort()

    
    for json_file_name in json_file_list:

        with open(os.path.join(json_folder_path,json_file_name), "r") as json_file:
            #result =[]
            
            frame_file_name = os.path.join(frame_folder_path, os.path.splitext(os.path.basename(json_file_name))[0]+".jpg")
            
            if os.path.exists(frame_file_name) == False:
                print("There is no ", frame_file_name)
                continue
                
            od_result = json.load(json_file)
            frame = cv2.imread(frame_file_name)
            
            results = od_result["results"]
            bboxs = (results[0])["detection_result"]
            for bbox in bboxs:
                if bbox["label"][0]["description"] == "person" and  bbox["label"][0]["score"] > 50:
                    box = bbox["position"]
                    frame = cv2.rectangle(frame,(box["x"], box["y"]), (box["x"]+box["w"], box["y"]+box["h"]), (0,0,255),2)
            
            
            output = model.analysis_from_json(od_result)
            print(output)
            
           
            
            if output == 1:
                frame = cv2.putText(frame, "Event!", (30,50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255, 0, 0), 2)
            else:
                frame = cv2.putText(frame, "Nothing..", (30,50), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 100), 2)
            
            
            cv2.imshow('Module Test', frame)
            k = cv2.waitKey(100)
            
            '''
            for f in file_list:
                t=os.path.join(opt.json_seq_path,f)
                frame_num = f[:-5] # json file name number
                print(frame_num)
                with open(t) as od_result_file:
                    od_result = json.load(od_result_file)
                    result.append(model.analysis_from_json(od_result))
                    # print(model.analysis_from_json(od_result).frame)
            json.dump(result, json_file)
            '''


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check your model")
    #parser.add_argument("--json_seq_path", type=str, default=os.path.join(os.getcwd(),"data","tracking"), help="sample json file path")
    parser.add_argument("--database_path", type=str, default="/database/dabucheo/")
    parser.add_argument("--video_filename", type=str, default="1_360p")
    args = parser.parse_args()
    main(**args.__dict__)
