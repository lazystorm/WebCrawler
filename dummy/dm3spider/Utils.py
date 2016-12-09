# -*- coding: utf-8 -*-
import json
import os


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

