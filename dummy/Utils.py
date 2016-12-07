# -*- coding: utf-8 -*-
import json
import os


def auto_save_and_load(auto_update=True):
    def decorator(updater):
        def wrapper(*args, **kw):
            filename = kw['filename']
            if auto_update and os.path.exists(filename):
                with open(filename, 'rb') as fd:
                    fd.readline()
                    obj = json.load(fd, encoding='utf-8')
            else:
                obj = updater(*args, **kw)
                with open(filename, 'wb') as fd:
                    fd.write('# -*- coding: utf-8 -*-\n')
                    json.dump(obj, fd, ensure_ascii=False, indent=4)
            return obj

        return wrapper

    return decorator