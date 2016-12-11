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

proxy_metas = Queue()
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
                print url
                content = utils.get(url).content
                KuaiDaiLi.parse(content)

    @staticmethod
    def parse(content):
        proxies_meta_raw = env.kuai_proxy_meta_pattern.findall(content)
        for p in proxies_meta_raw:
            for pre in p[2].split(', '):
                proxy = {pre.lower(): pre.lower() + '://' + p[0] + ':' + p[1]}
                proxy_metas.put_nowait(proxy)
                print proxy


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
            r = requests.get(self.api_url)
            print r.url
            if r.status_code == 200:
                XiCiDaiLi.parse_api(r.content)
        else:
            r = utils.get(self.proxy_list_url)
            XiCiDaiLi.parse(r.content)
            for purl in self.typed_list_urls:
                for i in range(1, self.max_list):
                    url = purl + str(i)
                    print url
                    content = utils.get(url).content
                    XiCiDaiLi.parse(content)

    @staticmethod
    def parse_api(content):
        for addr in content.split('\r\n'):
            proxy = {'http': 'http://' + addr}
            proxy_metas.put_nowait(proxy)
            print proxy

    @staticmethod
    def parse(content):
        proxies_meta_raw = env.xici_proxy_meta_pattern.findall(content)
        for p in proxies_meta_raw:
            pre = p[2]
            proxy = {pre.lower(): pre.lower() + '://' + p[0] + ':' + p[1]}
            proxy_metas.put_nowait(proxy)
            print proxy


class Verifier(QueueConsumer):
    def __init__(self, proxy_meta_queue):
        super(Verifier, self).__init__(proxy_meta_queue)
        self.url = 'http://www.baidu.com'

    def consume(self, proxy):
        meta = {'key': proxy}
        try:
            r = utils.get(self.url, proxies=proxy, timeout=10)
        except:
            print 'bad proxy!!!!!!!!!', proxy
            meta['var'] = 'bad'
        else:
            print 'good proxy!!!!!!!!!', proxy
            meta['var'] = 'good'
        finally:
            proxy_verified_metas.put_nowait(meta)


class DBWriter(QueueConsumer):
    def __init__(self, proxy_verified_queue):
        super(DBWriter, self).__init__(proxy_verified_queue)

    def consume(self, meta):
        env.proxy_db.Put(json.dumps(meta['key']), meta['var'])


class ProxyManager(Greenlet):
    def __init__(self):
        super(ProxyManager, self).__init__()
        self.proxies = []
        self.hunters = [XiCiDaiLi(), KuaiDaiLi(), XiCiDaiLi(False)]
        self.db_writer = DBWriter(proxy_verified_metas)
        self.verifiers = QueueConsumerPool(64, Verifier, proxy_metas)

    def _run(self):
        self.update()

    def update(self):
        hunter_group = Group()
        for h in self.hunters:
            hunter_group.start(h)
        hunter_group.join()

    def start(self):
        self.proxies = [json.loads(p[0]) for p in env.proxy_db.RangeIter() if p[1] == 'good']
        self.db_writer.start()
        super(ProxyManager, self).start()

    def join(self, timeout=None):
        self.verifiers.join(timeout=timeout)
        self.db_writer.join(timeout=timeout)
        super(ProxyManager, self).join(timeout=timeout)

    def get_proxy(self):
        if len(self.proxies) > 0:
            proxy = random.choice(self.proxies)
            return proxy
        else:
            return None


def main():
    monkey.patch_all()
    env.proxy_manager.start()
    env.proxy_manager.join()

if __name__ == '__main__':
    main()
