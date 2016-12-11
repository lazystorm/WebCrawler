# -*- coding: utf-8 -*-
import json
import os
import gevent
import env
import requests
from gevent.queue import Queue
from gevent.pool import Pool, Group
from gevent.greenlet import Greenlet


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


class QueueConsumer(Greenlet):
    def __init__(self, queue):
        super(QueueConsumer, self).__init__()
        self.queue = queue
        self.stop = False

    def _run(self):
        while not self.stop or not self.queue.empty():
            if not self.queue.empty():
                meta = self.queue.get()
                self.consume(meta)
            else:
                gevent.sleep(0.1)

    def consume(self, meta):
        print 'consuming:', meta

    def join(self, timeout=None):
        self.stop = True
        super(QueueConsumer, self).join(timeout=timeout)


class QueueConsumerPool(Pool):
    def __init__(self, size=None, greenlet_class=None, queue=None):
        super(QueueConsumerPool, self).__init__(size=size, greenlet_class=greenlet_class)
        if size and queue and greenlet_class:
            for i in xrange(size):
                self.start(greenlet_class(queue))

    def join(self, timeout=None, raise_error=False):
        for i in list(self.__iter__()):
            i.join(timeout=timeout)
        super(QueueConsumerPool, self).join(timeout=timeout, raise_error=raise_error)


def get(url, params=None, **kwargs):
    kwargs['headers'] = env.headers
    if 'proxies' not in kwargs:
        while True:
            kwargs['proxies'] = env.proxy_manager.get_proxy()
            try:
                ret = requests.get(url, params=params, **kwargs)
            except:
                print 'get %s failed!' % url,
                env.proxy_db.Put(json.dumps(kwargs['proxies']), 'bad')
            else:
                print 'get %s successed! ' % url
                return ret
    else:
        return requests.get(url, params=params, **kwargs)


if __name__ == '__main__':
    q = Queue()
    p = QueueConsumerPool(4, QueueConsumer, q)

    q.put_nowait('sdf')
    q.put_nowait('s2df')

    q.put_nowait('sd3f')
    q.put_nowait('s1df')
    p.join()