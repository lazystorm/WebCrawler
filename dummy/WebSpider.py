# -*- coding: utf-8 -*-
import requests
import re
import gevent
import os
import Utils
from gevent import socket
from gevent import monkey; monkey.patch_all()

threads = []

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
        <p>咖啡师初学者</p>
        <img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161305_2_lit.jpg" border="0" alt="" /></a></p>
        <p>比较词穷的一个广告标语</p>"""

        pattern = re.compile(
            r'src="http://[a-z]+.3dmgame.com/uploads/allimg/[0-9]+/.*?" border="0" alt="" /></a></p>.*?<p>.*?</p>',
            flags=re.DOTALL)
        urls = pattern.findall(page)
        imgs = []
        strs = []
        for url in urls:
            imgs.append(str(url[url.find('src="http:') + len('src="'):url.find('" border="0" alt=""')]).replace('_lit.', '.'))
            strs.append(str(url[url.rfind('<p>') + len('<p>'):-4]))
        return imgs, strs

    @Utils.auto_save_and_load()
    def get_all_url_str(self, filename):
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

    def download(self):
        murl = self.main_url
        self.dirname = murl[murl.rfind('/') + 1:-5]
        print self.dirname
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)
        filename = self.dirname + '/' + self.dirname + '.py'
        data = self.get_all_url_str(filename=filename)
        self.strs = data['strs']
        self.imgs = data['imgs']    
        for url in self.imgs:
            threads.append(gevent.spawn(self.download_image, url))

    def download_image(self, url):
        filename = self.dirname + '/' + url[url.rfind(r'/') + 1:]
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

def joinner(tick_count):
    global threads
    idle_cnt = 0
    while True:
        if len(threads) != 0:
            gevent.joinall(threads, timeout=tick_count)
            tthrs = []
            for thr in threads:
                if not thr.successful():
                    tthrs.append(thr)
            threads = tthrs
            print 'no of downloading threads %d' % len(threads)
            if len(threads)==0:
                idle_cnt += 1
                if idle_cnt == 100:
                    return
        else:
            gevent.sleep(tick_count)


def main():
    root_url = 'http://www.3dmgame.com/zt/'
    os.chdir('../images')
    print os.getcwd()
    urls = get_join_pic_urls(root_url, filename='join_pic_urls.py')
    r = []
    j = [gevent.spawn(joinner, 10)]
    for url in urls:
        r.append(Spider3dm(url))
        r[-1].download()
    gevent.joinall(j)


if __name__ == '__main__':
    t = False
    if t:
        sss = """好！</p>
    <p><a target="_blank" href="/uploads/allimg/160603/153_160603161305_1.gif"><img onerror="this.src=this.src.replace(/img([\d]+)\.3dmgame\.com/,'www\.3dmgame\.com')" src="http://img02.3dmgame.com/uploads/allimg/160603/153_160603161305_1_lit.gif" border="0" alt="" /></a></p>
    <p>美女裸睡画面真美好</p>
    <p><a target="_blank" href="http://www.3dmgame.com/uploads/allimg/160603/153_160603161305_2.jpg" style="text-indent: 24px;"><img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161305_2_lit.jpg" border="0" alt="" /></a></p>
    <p>比较词穷的一个广告标语</p>
    <p><a target="_blank" href="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_3.jpg" style="text-indent: 24px;"><img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_3_lit.jpg" border="0" alt="" /></a></p>
    <p>听说妹纸夏天双肩包与短裙更配哦！</p>
    <p><a target="_blank" href="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_4.jpg" style="text-indent: 24px;"><img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_4_lit.jpg" border="0" alt="" /></a></p>
    <p>妹纸的比基尼不错哦，绿色环保</p>
    <p><a target="_blank" href="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_5.jpg" style="text-indent: 24px;"><img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161306_5_lit.jpg" border="0" alt="" /></a></p>
    <p>用花求婚都弱爆了</p>"""
        test = Spider3dm('')
        ret = test.image_urls(sss)
        print ret
    else:
        main()
