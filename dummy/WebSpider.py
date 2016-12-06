# -*- coding: utf-8 -*-
import requests
import re
import gevent
import json
import os
import Utils


class Spider3dm:
    def __init__(self, url):
        self.main_url = url
        self.main_page = None

    def page_end(self):
        """<a  href='3612893_44.html'>末页</a> -> 44"""
        pattern = re.compile(r"<a  href='[0-9]+_[0-9]+.html'>末页</a>")
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        end = pattern.findall(self.main_page.content)
        return end[0][end[0].find('_') + 1:end[0].find('.html')]

    def image_urls(self, page):
        """<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2.jpg
        " style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2_lit.jpg
        " border="0" alt="" /></a></p>
        <p>咖啡师初学者</p>"""
        pattern = re.compile(
            r'<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/[0-9]+/.*?" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/[0-9]+/.*?" border="0" alt="" /></a></p>.*?<p>.*?</p>',
            flags=re.DOTALL)
        urls = pattern.findall(page)
        imgs = []
        strs = []
        for url in urls:
            imgs.append(
                str(url[url.find('href="http:') + len('href="'):url.find('" style="text-indent: 24px;"><img src=')]))
            strs.append(str(url[url.rfind('<p>') + len('<p>'):-4]))
        return imgs, strs

    @Utils.auto_save_and_load()
    def get_all_url_str(self, filename):
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        imgs, strs = self.image_urls(self.main_page.content)
        for i in range(2, int(self.page_end()) + 1):
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

    def download(self):
        murl = self.main_url
        self.dirname = murl[murl.rfind('/') + 1:-5]
        print self.dirname
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)
        os.chdir(self.dirname)
        filename = self.dirname + '.py'
        data = self.get_all_url_str(filename=filename)
        self.strs = data['strs']
        self.imgs = data['imgs']
        threads = []
        for url in self.imgs:
            threads.append(gevent.spawn(Spider3dm.download_image(url)))
        gevent.joinall(threads)
        os.chdir('..')

    @staticmethod
    def download_image(url):
        filename = url[url.rfind(r'/') + 1:]
        if os.path.exists(filename):
            return
        r = requests.get(url)
        Spider3dm.write_file(filename, r.content)

    @staticmethod
    def write_file(filename, content):
        with open(filename, 'wb') as fd:
            fd.write(content)


@Utils.auto_save_and_load()
def get_join_pic_urls(main_url, filename):
    totalpage = 164
    params = {'tid': '151', 'totalpage': str(totalpage), 'page': '1'}
    join_pic_urls = []
    for i in range(totalpage):
        params['page'] = str(i + 1)
        r = requests.get(main_url, params=params)
        pattern = re.compile(r'<a href="http://www.3dmgame.com/zt/[0-9]+/[0-9]+.html" target="_blank">.*?</a>',
                             flags=re.DOTALL)
        urls = pattern.findall(r.content)
        for url in urls:
            if '周' in url and '囧图' in url:
                pic_url = str(url[len('<a href="'):url.find('" target="_blank">')])
                join_pic_urls.append(pic_url)
    return join_pic_urls


def main():
    root_url = 'http://www.3dmgame.com/zt/'
    os.chdir('../images')
    print os.getcwd()
    urls = get_join_pic_urls(root_url, filename='join_pic_urls.py')
    for url in urls:
        r = Spider3dm(url)
        r.download()


if __name__ == '__main__':
    main()
