# Template/main.py merge_sequence 함수 관련

* /detector/event/template/main.py에 merge_sequence 함수가 업데이트 되었습니다.

* 해당함수는 def merge_sequence(self, frame_info) 입니다.

* 해당함수는 assault, falldown 등 각각의 프레임별 이벤트에 대해 나오는 True, False에 대해 True에 대한 구간정보를 묶어줍니다.

* 임의의 테스트 영상에 대해 merge_sequence 함수가 return 해주는 예시입니다.<br>해당 예시는 assault 이벤트에 대한 리턴값 입니다.

```
ex)  {'assault': [{'start': 30, 'end': 31}, {'start': 34, 'end': 34}, {'start': 411, 'end': 540}, {'start': 561, 'end': 561}, {'start': 573, 'end': 573}, {'start': 1329, 'end': 1531}, {'start': 1788, 'end': 2154}, {'start': 2199, 'end': 3031}, {'start': 3288, 'end': 3465}, {'start': 4170, 'end': 4170}, {'start': 4173, 'end': 4173}, {'start': 4176, 'end': 4263}, {'start': 5188, 'end': 5188}, {'start': 5191, 'end': 5191}, {'start': 5205, 'end': 5205}, {'start': 5326, 'end': 5328}, {'start': 5332, 'end': 5332}], 'falldown': [{'start': 103, 'end': 301}, {'start': 4231, 'end': 4491}], 'obstacle': [{'start': 1, 'end': 967}, {'start': 1332, 'end': 3924}, {'start': 4467, 'end': 5685}, {'start': 5691, 'end': 5710}], 'kidnapping': [{'start': 31, 'end': 471}, {'start': 480, 'end': 612}, {'start': 1330, 'end': 1453}, {'start': 1783, 'end': 2827}, {'start': 2875, 'end': 2932}, {'start': 2943, 'end': 2949}, {'start': 3289, 'end': 3621}, {'start': 4171, 'end': 4467}, {'start': 5128, 'end': 5140}, {'start': 5145, 'end': 5551}], 'tailing': [{'start': 31, 'end': 274}, {'start': 283, 'end': 289}, {'start': 411, 'end': 469}, {'start': 480, 'end': 491}, {'start': 495, 'end': 516}, {'start': 561, 'end': 567}, {'start': 1330, 'end': 1455}, {'start': 1783, 'end': 1863}, {'start': 1866, 'end': 1921}, {'start': 1926, 'end': 1942}, {'start': 1945, 'end': 2530}, {'start': 2542, 'end': 2551}, {'start': 2581, 'end': 2769}, {'start': 2773, 'end': 2791}, {'start': 2794, 'end': 2809}, {'start': 2880, 'end': 2929}, {'start': 2941, 'end': 2959}, {'start': 3289, 'end': 3625}, {'start': 4173, 'end': 4183}, {'start': 5115, 'end': 5131}, {'start': 5136, 'end': 5149}, {'start': 5188, 'end': 5293}, {'start': 5296, 'end': 5307}, {'start': 5311, 'end': 5343}, {'start': 5347, 'end': 5358}, {'start': 5445, 'end': 5455}, {'start': 5496, 'end': 5509}], 'wanderer': [{'start': 499, 'end': 517}, {'start': 523, 'end': 592}, {'start': 598, 'end': 607}, {'start': 2193, 'end': 2415}, {'start': 2421, 'end': 2442}, {'start': 2445, 'end': 2467}, {'start': 2509, 'end': 2524}, {'start': 5482, 'end': 5547}]}
```
