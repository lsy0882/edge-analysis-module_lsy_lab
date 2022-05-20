import numpy as np

def linear_assignment(cost_matrix):
  try:
    import lap
    _, x, y = lap.lapjv(cost_matrix, extend_cost=True)
    return np.array([[y[i],i] for i in x if i >= 0]) #
  except ImportError:
    from scipy.optimize import linear_sum_assignment
    x, y = linear_sum_assignment(cost_matrix)
    return np.array(list(zip(x, y)))



def iou(bb_test, bb_gt):
  xx1 = np.maximum(bb_test[0], bb_gt[0])
  yy1 = np.maximum(bb_test[1], bb_gt[1])
  xx2 = np.minimum(bb_test[2], bb_gt[2])
  yy2 = np.minimum(bb_test[3], bb_gt[3])
  w = np.maximum(0., xx2 - xx1)
  h = np.maximum(0., yy2 - yy1)
  wh = w * h
  o = wh / ((bb_test[2] - bb_test[0]) * (bb_test[3] - bb_test[1])
    + (bb_gt[2] - bb_gt[0]) * (bb_gt[3] - bb_gt[1]) - wh)
  return(o)


def convert_bbox_to_z(bbox):
  w = bbox[2] - bbox[0]
  h = bbox[3] - bbox[1]
  x = bbox[0] + w/2.
  y = bbox[1] + h/2.
  s = w * h    
  r = w / float(h)
  return np.array([x, y, s, r]).reshape((4, 1))


def convert_x_to_bbox(x,score=None):
  w = np.sqrt(x[2] * x[3])
  h = x[2] / w
  if(score==None):
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.]).reshape((1,4))
  else:
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.,score]).reshape((1,5))


def associate_detections_to_trackers(detections,trackers,iou_threshold = 0.2):
  if(len(trackers)==0):
    return np.empty((0,2),dtype=int), np.arange(len(detections)), np.empty((0,5),dtype=int)
  iou_matrix = np.zeros((len(detections),len(trackers)),dtype=np.float32)

  for d,det in enumerate(detections):
    for t,trk in enumerate(trackers):
      iou_matrix[d,t] = iou(det,trk)

  if min(iou_matrix.shape) > 0:
    a = (iou_matrix > iou_threshold).astype(np.int32)
    if a.sum(1).max() == 1 and a.sum(0).max() == 1:
        matched_indices = np.stack(np.where(a), axis=1)
    else:
      matched_indices = linear_assignment(-iou_matrix)
  else:
    matched_indices = np.empty(shape=(0,2))

  unmatched_detections = []
  for d, det in enumerate(detections):
    if(d not in matched_indices[:,0]):
      unmatched_detections.append(d)
  unmatched_trackers = []
  for t, trk in enumerate(trackers):
    if(t not in matched_indices[:,1]):
      unmatched_trackers.append(t)

  
  matches = []
  for m in matched_indices:
    if(iou_matrix[m[0], m[1]]<iou_threshold):
      unmatched_detections.append(m[0])
      unmatched_trackers.append(m[1])
    else:
      matches.append(m.reshape(1,2))
  if(len(matches)==0):
    matches = np.empty((0,2),dtype=int)
  else:
    matches = np.concatenate(matches,axis=0)

  return matches, np.array(unmatched_detections), np.array(unmatched_trackers)

def cos_sim(v1_1, v1_2, v2_1, v2_2):
    
    vector_1 = v1_2 - v1_1
    vector_2 = v2_2 - v2_1
    
    if vector_1[0] == 0.0:
        vector_1[0] = 0.01

    if vector_1[1] == 0.0:
        vector_1[1] = 0.01

    if vector_2[0] == 0.0:
        vector_2[0] = 0.01

    if vector_2[1] == 0.0:
        vector_2[1] = 0.01

    return np.dot(vector_1, vector_2) / (np.linalg.norm(vector_1) * np.linalg.norm(vector_2))



def check_zeroValue(coordinates, n):
    
    if np.array([0.0, 0.0]) in coordinates[n]:
        return check_zeroValue(coordinates, n - 1)
    else:
        return coordinates[:n+1]

def getCxCy(coord):
    #xyxy -> get cx, cy
    cx = (coord[0] + coord[2])/2
    cy = (coord[1] + coord[3])/2
    return [cx, cy]


def det_to_trk_data_conversion(detection_result):
  detection_result = detection_result['results'][0]['detection_result']
  boxes_tmp_list = []
  boxes_list = []
  scores_tmp_list = []
  scores_list = []
  classes_tmp_list = []
  classes_list = []
  for info_ in detection_result:
      boxes_tmp_list.append(info_['position']['x'])
      boxes_tmp_list.append(info_['position']['y'])
      boxes_tmp_list.append(info_['position']['x'] + info_['position']['w'])
      boxes_tmp_list.append(info_['position']['y'] + info_['position']['h'])
      scores_tmp_list.append(info_['label'][0]['score'])
      classes_tmp_list.append(info_['label'][0]['class_idx'])
      boxes_list.append(boxes_tmp_list)
      scores_list.append(scores_tmp_list)
      classes_list.append(classes_tmp_list)
      boxes_tmp_list = []
      scores_tmp_list = []
      classes_tmp_list = []
  
  boxes_list_array = np.array(boxes_list)
  scores_list_array = np.array(scores_list)
  classes_list_array = np.array(classes_list)

  return boxes_list_array, scores_list_array, classes_list_array

def is_not_boundary(xyah):
  x = xyah[0]
  y = xyah[1]
  if 20 < x < 605 and 30 < y < 318:
      return True
  else:
      return False

def xyxy2xywh(coords):
    x1, y1, x2, y2 = coords[0] , coords[1], coords[2], coords[3]
    w = 2*x2 - x1
    h = 2*y2 - y1
    return [x1, y1, w, h]

def cos_similiarity(v1, v2): 
    dot_product = np.dot(v1, v2) 
    l2_norm = (np.sqrt(sum(np.square(v1)))*np.sqrt(sum(np.square(v2)))) 
    similarity = dot_product/l2_norm 
    return similarity