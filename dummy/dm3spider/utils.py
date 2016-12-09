# -*- coding: utf-8 -*-
import json
import os
import gevent

def dump(obj, filename):
    with open(filename, 'wb') as fd:
        fd.write('# -*- coding: utf-8 -*-\n')
        json.dump(obj, fd, ensure_ascii=False, indent=4)


def load(filename):
    with open(filename, 'rb') as fd:
        fd.readline()
        obj = json.load(fd, encoding='utf-8')
    return obj


def read_file(filename):
    with open(filename, 'rb') as fd:
        data = fd.read()
    return data


def auto_save_and_load(auto_update=True):
    def decorator(updater):
        def wrapper(*args, **kw):
            filename = kw['filename']
            if auto_update and os.path.exists(filename):
                obj = load(filename)
            else:
                obj = updater(*args, **kw)
                dump(obj, filename)
            return obj

        return wrapper

    return decorator


def check_img_complete(img_name):
    img = read_file(img_name)
    if img_name.endswith('.jpg') or img_name.endswith('.JPG'):
        if img.endswith('\xff\xd9'):
            return True
        else:
            return False
    elif img_name.endswith('.gif'):
        if img.endswith('\x3b'):
            return True
        else:
            return False
