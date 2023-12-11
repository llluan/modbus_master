import datetime


def get_currant_time():
    data = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    data = "[ "+data+" R]"
    return data

def get_name():
    data = datetime.datetime.now().strftime('%Y_%m_%d_%H-%M-%S-%f')
    return data