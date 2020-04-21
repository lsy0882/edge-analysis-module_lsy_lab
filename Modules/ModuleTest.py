from dummy.main import Dummy
import argparse
import os
import json
import sys


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Please check your model")
    parser.add_argument("--json_path", type=str, default=os.path.join(os.getcwd(), "data", "json", "sample1.json"), help="sample json file path")

    try:
        opt = parser.parse_known_args()[0]

        # TODO:
        #   - 테스트 하고자 하는 모델로 수정
        #     (e.g.
        #       from dummy.main import Dummy -> from fireDetection.main import FireDetection()
        #       Dummy()                      -> FireDetection()
        #     )
        model = Dummy()
        json_path = opt.json_path

        with open(json_path) as od_result_file:
            od_result = json.load(od_result_file)

        print(model.inference_by_path(od_result))

    except:
        print("")
        parser.print_help()
        sys.exit(0)