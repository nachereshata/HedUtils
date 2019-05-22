from datetime import datetime


def utcnow():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S.%f")