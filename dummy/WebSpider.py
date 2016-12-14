# -*- coding: utf-8 -*-
import re
import os

import requests

import gevent
from gevent import monkey
from gevent.pool import Pool

import dm3spider.utils as Utils
from ignore import ignore_dir
from dm3spider.check import check_images

monkey.patch_all()
os.chdir('../images')

threads = []
download_pool = Pool(80)

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
headers = {'user-agent': user_agent}
"""<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2.jpg
" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2_lit.jpg
" border="0" alt="" /></a></p>
<p>咖啡师初学者</p>
<img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161305_2_lit.jpg" border="0" alt="" /></a></p>
<p>比较词穷的一个广告标语</p>
<IMG alt="" src="http://www.3dmgame.com/Article/UploadFiles/201205/20120525103609569.jpg" border=undefined></A><BR>一老大爷在上海地铁10号线上淡定自若地杀鸡!!</P>"""
pic_url_pattern = re.compile(
            r'<[imgIMG]+[\s border="0undefined" alt="" ]+src="((?:http://[a-z]+\.3dmgame\.com)?/[Articleuploads]+/[allimgUploadFiles]+/\d+/[_\dlit]+\.[jpgif]+?)"[\s border="0" ABRundefinedalt="" /></a></p><p>]+(.*?)</[pP]?>',
            flags=re.M)

join_pic_page_url_pattern = re.compile(r'<a href="http://www\.3dmgame\.com/zt/[0-9]+/[0-9]+\.html" target="_blank">.*?</a>')
"""<a  href='3612893_44.html'>末页</a> -> 44"""
page_end_pattern = re.compile(r"<a  href='[0-9]+_[0-9]+.html'>末页</a>")

ignored_dirs = ignore_dir(filename='ignored_dirs.py')


class Spider3dm:
    def __init__(self, url):
        self.main_url = url
        self.main_page = None

    def page_end(self):
        if self.main_page is None:
            self.main_page = requests.get(self.main_url)
        end = page_end_pattern.findall(self.main_page.content)
        return end[0][end[0].find('_') + 1:end[0].find('.html')]

    def image_urls(self, page):
        urls = pic_url_pattern.findall(page)
        imgs = []
        strs = []
        for url in urls:
            img = url[0]
            if url[0][0] =='/':
                img = 'http://www.3dmgame.com' + url[0]
            imgs.append(img.replace('_lit.', '.'))
            strs.append(url[1])
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
        if self.dirname in ignored_dirs:
            return
        if not os.path.exists(self.dirname):
            os.makedirs(self.dirname)
        filename = self.dirname + '/' + self.dirname + '.py'
        data = self.get_all_url_str(filename=filename)
        self.strs = data['strs']
        self.imgs = data['imgs']   
        for url in self.imgs:
            filename = self.dirname + '/' + url[url.rfind(r'/') + 1:]
            if not os.path.exists(filename):
                #threads.append(gevent.spawn(Spider3dm.download_image, url, filename))
                download_pool.wait_available()
                download_pool.spawn(Spider3dm.download_image, url, filename)
                #gevent.sleep(1)

    @staticmethod
    def download_image(url, filename):
        image = requests.get(url).content
        Spider3dm.write_file(filename, image)

    @staticmethod
    def write_file(filename, content):
        with open(filename, 'wb') as fd:
            fd.write(content)
        print 'finish download: %s' % filename


@Utils.auto_save_and_load()
def get_join_pic_urls(main_url, filename):
    totalpage = 164
    params = {'tid': '151', 'totalpage': str(totalpage), 'page': '1'}
    join_pic_urls = []
    for i in range(totalpage):
        params['page'] = str(i + 1)
        r = requests.get(main_url, params=params)    
        urls = join_pic_page_url_pattern.findall(r.content)
        for url in urls:
            if '周' in url and '囧图' in url:
                pic_url = str(url[len('<a href="'):url.find('" target="_blank">')])
                join_pic_urls.append(pic_url)
    return join_pic_urls


def joiner(tick_count):
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
            idle_cnt = 0
            gevent.sleep(tick_count)


def download_missing_imgs():
    global threads
    missing_imgs = check_images(filename='missing_imgs.py')
    for fdir, url in missing_imgs:
        if not os.path.exists(fdir):
            os.mkdir(fdir)
        os.chdir(fdir)
        if url:
            filename = url[url.rfind(r'/') + 1:]
            Spider3dm.download_image(url, filename)
        os.chdir('..')


def main():
    fix = False
    if fix:
        download_missing_imgs()
    else:
        root_url = 'http://www.3dmgame.com/zt/'
        print os.getcwd()
        urls = get_join_pic_urls(root_url, filename='join_pic_urls.py')
        r = []
        for url in urls:
            r.append(Spider3dm(url))
            r[-1].download()
        download_pool.join()


if __name__ == '__main__':
    t = False
    if t:
        sss = """<p>&nbsp;</p>
<p>邪恶内涵图总是激情不断，最新爆笑囧图。给你不一样的周一风情!</p>
<p align="center"><a target="_blank" href="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113829449.jpg"><img border="undefined" src="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113829449.jpg" alt="" /></a><br />
连细菌都不吃的东西，网友们也别吃了</p>
<p align="center"><a target="_blank" href="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113840370.jpg"><img border="undefined" src="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113840370.jpg" alt="" /></a><br />
你第一个接吻的人不是她！是我！</p>
<p align="center"><a target="_blank" href="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113847964.jpg"><img border="undefined" src="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113847964.jpg" alt="" /></a><br />
求大神PS 把背景换成一个身临其境的感觉</p>
<p align="center"><a target="_blank" href="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113853620.jpg"><img border="undefined" src="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113853620.jpg" alt="" /></a><br />
真是好味道</p>
<p align="center"><a target="_blank" href="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113902858.jpg"><img border="undefined" src="http://www.3dmgame.com/Article/UploadFiles/201302/20130225113902858.jpg" alt="" /></a><br />
去掉头就可以</p>
<div align="center" class="page_fenye">
<div class="pagelistbox">
<span>共 54 页/54条记录</span><span class="indexPage">首页 """
        test = Spider3dm('')
        ret = test.image_urls(sss)
        print ret
    else:
        main()
