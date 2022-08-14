from datetime import timedelta


def convert_framenumber2timestamp(frame_number, fps):
    str_time = str(timedelta(seconds=frame_number / fps))
    if "." not in str_time:
        str_time += ".000"
    else :
        str_time = str_time[:-3]
    return str_time