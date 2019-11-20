import time
import random
import hashlib


def unique():
    current_time = str(time.time())
    random_seed = str(random.random())
    m = hashlib.md5(bytes(random_seed, encoding='utf-8'))
    m.update(bytes(current_time, encoding='utf-8'))
    return m.hexdigest()
