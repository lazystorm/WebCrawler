# -*- coding: utf-8 -*-
import gevent
import env
import json
import random
import utils
import requests
from gevent.pool import Group
from gevent.queue import Queue
from gevent.greenlet import Greenlet
from gevent import monkey
from utils import QueueConsumer, QueueConsumerPool

proxy_tobe_verified_metas = Queue()
proxy_verified_metas = Queue()


class ProxyHunter(Greenlet):
    def __init__(self):
        super(ProxyHunter, self).__init__()

    def _run(self):
        self.get_all_proxies()

    def get_all_proxies(self):
        pass


class KuaiDaiLi(ProxyHunter):
    def __init__(self):
        super(KuaiDaiLi, self).__init__()
        self.home_url = 'http://www.kuaidaili.com/'
        self.proxy_list_url = self.home_url + 'proxylist/'
        types = ['inha/', 'intr/', 'outha/', 'outtr/']
        self.typed_list_urls = [self.home_url + 'free/' + t for t in types]
        self.max_list = 11

    def get_all_proxies(self):
        for purl in self.typed_list_urls + [self.proxy_list_url]:
            for i in range(1, self.max_list):
                url = purl + str(i) + '/'
                content = get(url).content
                KuaiDaiLi.parse(content)

    @staticmethod
    def parse(content):
        proxies_meta_raw = env.kuai_proxy_meta_pattern.findall(content)
        for p in proxies_meta_raw:
            for pre in p[2].split(', '):
                proxy = {pre.lower(): pre.lower() + '://' + p[0] + ':' + p[1]}
                meta = {
                    'key': proxy,
                    'var': 'unknown',
                }
                proxy_tobe_verified_metas.put_nowait(meta)


class XiCiDaiLi(ProxyHunter):
    def __init__(self, use_api=True):
        super(XiCiDaiLi, self).__init__()
        self.home_url = 'http://www.xicidaili.com/'
        self.proxy_list_url = self.home_url
        types = ['nn/', 'nt/', 'wn/', 'wt/']
        self.typed_list_urls = [self.home_url + t for t in types]
        self.api_url = 'http://api.xicidaili.com/free2016.txt'
        self.max_list = 11
        self.use_api = use_api

    def get_all_proxies(self):
        if self.use_api:
            r = get(self.api_url)
            if r.status_code == 200:
                XiCiDaiLi.parse_api(r.content)
        else:
            r = get(self.proxy_list_url)
            XiCiDaiLi.parse(r.content)
            for purl in self.typed_list_urls:
                for i in range(1, self.max_list):
                    url = purl + str(i)
                    content = get(url).content
                    XiCiDaiLi.parse(content)

    @staticmethod
    def parse_api(content):
        for addr in content.split('\r\n'):
            proxy = {'http': 'http://' + addr}
            meta = {
                'key': proxy,
                'var': 'unknown',
            }
            proxy_tobe_verified_metas.put_nowait(meta)

    @staticmethod
    def parse(content):
        proxies_meta_raw = env.xici_proxy_meta_pattern.findall(content)
        for p in proxies_meta_raw:
            pre = p[2]
            proxy = {pre.lower(): pre.lower() + '://' + p[0] + ':' + p[1]}
            meta = {
                'key': proxy,
                'var': 'unknown',
            }
            proxy_tobe_verified_metas.put_nowait(meta)


class Verifier(QueueConsumer):
    def __init__(self, proxy_meta_queue):
        super(Verifier, self).__init__(proxy_meta_queue)
        self.urls = [
            'https://www.google.com',
            'https://www.baidu.com',
            'https://www.so.com',
            'http://cn.bing.com/',
            'https://www.sogou.com',
            'http://www.youdao.com',
        ]

    def consume(self, meta):
        proxy = meta['key']
        suc_cnt = 0
        for url in self.urls:
            try:
                r = get(url, proxies=proxy, timeout=5)
            except requests.RequestException:
                pass
            else:
                suc_cnt += 1
        if suc_cnt == 0 and meta['var'] == 'bad':
            meta['var'] = 'dead'
        elif suc_cnt > 4:
            meta['var'] = 'perfect'
        elif suc_cnt > 2:
            meta['var'] = 'good'
        else:
            meta['var'] = 'bad'
        proxy_verified_metas.put_nowait(meta)


class DBWriter(QueueConsumer):
    def __init__(self, proxy_verified_queue):
        super(DBWriter, self).__init__(proxy_verified_queue)

    def consume(self, meta):
        if meta['var'] == 'dead':
            env.proxy_db.Delete(json.dumps(meta['key']))
        else:
            env.proxy_db.Put(json.dumps(meta['key']), meta['var'])
        print meta


class ProxyManager(Greenlet):
    def __init__(self):
        super(ProxyManager, self).__init__()
        self.proxies = []
        self.hunters = [XiCiDaiLi(), KuaiDaiLi(), XiCiDaiLi(False)]
        self.db_writer = DBWriter(proxy_verified_metas)
        self.verifiers = QueueConsumerPool(64, Verifier, proxy_tobe_verified_metas)
        self.deams = Group()

    def _run(self):
        self.deams.spawn(self.update_web_proxies)
        self.deams.spawn(self.update_db_proxies)

    def start(self):
        self.proxies = [json.loads(p[0]) for p in env.proxy_db.RangeIter() if p[1] == 'perfect']
        self.db_writer.start()
        super(ProxyManager, self).start()

    def join(self, timeout=None):
        self.deams.kill()
        self.verifiers.join(timeout=timeout)
        self.db_writer.join(timeout=timeout)
        super(ProxyManager, self).join(timeout=timeout)

    def update_web_proxies(self):
        while True:
            gevent.sleep(1800)
            hunter_group = Group()
            for h in self.hunters:
                hunter_group.start(h)
            hunter_group.join()
            gevent.sleep(1800)

    def update_db_proxies(self):
        while True:
            for key, var in env.proxy_db.RangeIter():
                meta = {
                    'key': json.loads(key),
                    'var': var,
                }
                proxy_tobe_verified_metas.put_nowait(meta)
            gevent.sleep(3600)

    def get_proxy(self):
        if len(self.proxies) > 0:
            proxy = random.choice(self.proxies)
            return proxy
        else:
            return None


def get(url, use_proxy=False, params=None, **kwargs):
    kwargs['headers'] = env.headers
    if 'proxies' not in kwargs and use_proxy:
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


def main():
    monkey.patch_all()
    env.proxy_manager.start()
    gevent.sleep(100)
    env.proxy_manager.join()

if __name__ == '__main__':
    main()
