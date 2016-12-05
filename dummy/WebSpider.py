# -*- coding: utf-8 -*-
import requests
import re
import gevent

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
        return end[0][end[0].find('_')+1:end[0].find('.html')]

    def image_urls(self, page):
        """<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2.jpg
        " style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2_lit.jpg
        " border="0" alt="" /></a></p>
        <p>咖啡师初学者</p>"""
        pattern = re.compile(r'<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/[0-9]+/.*?" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/[0-9]+/.*?" border="0" alt="" /></a></p>.*?<p>.*?</p>', flags=re.DOTALL)
        urls = pattern.findall(page)
        imgs = []
        strs = []
        for url in urls:
            imgs.append(str(url[url.find('href="http:') + len('href="'):url.find('" style="text-indent: 24px;"><img src=')]))
            strs.append(str(url[url.rfind('<p>') + len('<p>'):-4]))
        return imgs, strs

    def get_all_url_str(self):
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        self.imgs, self.strs = self.image_urls(self.main_page.content)
        for i in range(2, int(self.page_end())+1):
            url = self.main_url[:-5] + '_' + str(i) + self.main_url[-5:]
            page = requests.get(url)
            im, st = self.image_urls(page.content)
            self.strs += st
            self.imgs += im
        return self.strs, self.imgs

    def download(self):
        self.get_all_url_str()
        threads = []
        for url in self.imgs:
            threads.append(gevent.spawn(Spider3dm.download_image(url)))
        gevent.joinall(threads)

    @staticmethod
    def download_image(url):
        filename = url[url.rfind(r'/') + 1:]
        r = requests.get(url)
        Spider3dm.write_file(filename, r)

    @staticmethod
    def write_file(filename, content):
        with open(filename, 'wb') as fd:
            for chunk in content.iter_content(chunk_size=4096*1024):
                fd.write(chunk)

def main():
    r = Spider3dm('http://www.3dmgame.com/zt/201612/3612893.html')
    r.download()

if __name__ == '__main__':
    main()
