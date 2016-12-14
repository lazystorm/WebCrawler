# -*- coding: utf-8 -*-
import os
import requests
from gevent.pool import Pool
from gevent import monkey

import env
from utils import auto_save_and_load


class JoinPageParser:
    def __init__(self, url):
        self.main_url = url
        self.main_page = None

    def page_end(self):
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        end = env.page_end_pattern.findall(self.main_page.content)
        return end[0][end[0].find('_') + 1:end[0].find('.html')]

    @staticmethod
    def image_urls(page):
        urls = env.pic_url_pattern.findall(page)
        imgs = []
        strs = []
        for url in urls:
            img = url[0]
            if url[0][0] =='/':
                img = 'http://www.3dmgame.com' + url[0]
            imgs.append(img.replace('_lit.', '.'))
            strs.append(url[1])
        return imgs, strs

    @auto_save_and_load()
    def do_get_all_url_str(self, filename):
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        imgs, strs = self.image_urls(self.main_page.content)
        pend = int(self.page_end())
        for i in range(2, pend + 1):
            url = self.main_url[:-5] + '_' + str(i) + self.main_url[-5:]
            page = requests.get(url)
            im, st = self.image_urls(page.content)
            strs += st
            imgs += im
        data = {
            'strs': strs,
            'imgs': imgs,
        }
        return data

    def get_all_url_str(self):
        m_url = self.main_url
        dir_name = m_url[m_url.rfind('/') + 1:-5]
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        filename = dir_name + '/' + dir_name + '.py'
        data = self.do_get_all_url_str(filename=filename)
        print 'finish parsing image urls of %s\n%d urls found in %s' % (m_url, len(data['imgs']), dir_name)


class UrlParser:
    def __init__(self, ru):
        self.root_url = ru
        self.join_pic_urls = []
        self.parser_pool = Pool(env.parser_pool_size)

    @auto_save_and_load()
    def get_join_pic_urls(self, filename):
        total_page = int(env.total_page.search(requests.get(self.root_url).content).group(1))
        params = {'tid': '151', 'totalpage': str(total_page), 'page': '1'}
        join_pic_urls = []
        for i in range(total_page):
            params['page'] = str(i + 1)
            r = requests.get(self.root_url, params=params)
            urls = env.join_pic_page_url_pattern.findall(r.content)
            for url in urls:
                if '周' in url and '囧图' in url:
                    pic_url = str(url[len('<a href="'):url.find('" target="_blank">')])
                    join_pic_urls.append(pic_url)
        return join_pic_urls

    def get_all_image_urls(self):
        self.join_pic_urls = self.get_join_pic_urls(filename=env.join_pic_urls_filename)
        print 'finish parsing join_pic_urls of %s\n%d urls found' % (self.root_url, len(self.join_pic_urls))
        parser_list = []
        for url in self.join_pic_urls:
            parser = JoinPageParser(url)
            parser_list.append(parser)
            self.parser_pool.wait_available()
            self.parser_pool.spawn(parser.get_all_url_str)

    def finish(self):
        self.parser_pool.join()


def main():
    monkey.patch_all()
    os.chdir(env.image_dir)
    url_parser = UrlParser(env.root_url)
    try:
        url_parser.get_all_image_urls()
    finally:
        url_parser.finish()


if __name__ == '__main__':
    main()
