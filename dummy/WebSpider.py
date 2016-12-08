# -*- coding: utf-8 -*-
import requests
import re
import gevent
import os
import Utils
from ignore import ignore_dir
from check import check_images
from gevent import monkey


monkey.patch_all()
os.chdir('../images')

threads = []
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
headers = {'user-agent': user_agent}
"""<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2.jpg
" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161205/153_161205155056_2_lit.jpg
" border="0" alt="" /></a></p>
<p>咖啡师初学者</p>
<img src="http://www.3dmgame.com/uploads/allimg/160603/153_160603161305_2_lit.jpg" border="0" alt="" /></a></p>
<p>比较词穷的一个广告标语</p>"""
pic_url_pattern = re.compile(
            r'<img[\s border="0" alt="" ]+src="(http://[a-z]+\.3dmgame\.com/uploads/allimg/.*?)"[\s border="0" alt="" /></a></p><p>]+(.*?)</p>',
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
            imgs.append(url[0].replace('_lit.', '.'))
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
                threads.append(gevent.spawn(Spider3dm.download_image, url, filename))
                gevent.sleep(1)

    @staticmethod
    def download_image(url, filename):
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
    missing_imgs = check_images(filename='missing_imgs.py')
    for fdir, url in missing_imgs:
        filename = os.path.join(fdir, url[url.rfind(r'/') + 1:])
        if not os.path.exists(fdir):
            os.mkdir(fdir)
        if not os.path.exists(filename):
            threads.append(gevent.spawn(Spider3dm.download_image, url, filename))


def main():
    root_url = 'http://www.3dmgame.com/zt/'
    print os.getcwd()
    urls = get_join_pic_urls(root_url, filename='join_pic_urls.py')
    r = []
    j = [gevent.spawn(joiner, 10)]
    download_missing_imgs()
    for url in urls:
        r.append(Spider3dm(url))
        r[-1].download()
    gevent.joinall(j)


if __name__ == '__main__':
    t = False
    if t:
        sss = """<a  href='3612345_2.html'>下页</a> 
<a  href='3612345_44.html'>末页</a> 
</div>
</div><div class="lgxZ con"><div class="miaoshu">周五依然有小编带来的雷人内涵搞笑图集，男生最喜欢和这样的妹子出去喝酒，不要问为什么。</div>
<div>
<p>周<a class='simzt' href='http://www.3dmgame.com/games/fivegod/' target='_blank'>五</a>依然有小编带来的雷人内涵搞笑图集，男生最喜欢和这样的妹子出去喝酒，不要问为什么。</p>

<p><a target="_blank" href="/uploads/allimg/161202/153_161202161325_1.jpg"><img onerror="this.src=this.src.replace(/img([\d]+)\.3dmgame\.com/,'www\.3dmgame\.com');this.onerror=null" src="http://img02.3dmgame.com/uploads/allimg/161202/153_161202161325_1_lit.jpg" border="0" alt="" /></a></p>
<p>男生最喜欢和这样的妹子出去喝酒</p>

<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_2.gif" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_2_lit.gif" border="0" alt="" /></a></p>
<p>天气预报拍出来11区动作片</p>

<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_3.jpg" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_3_lit.jpg" border="0" alt="" /></a></p>
<p>首师大宿管大妈：别以为我不知道你们在想什么</p>

<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_4.jpg" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_4_lit.jpg" border="0" alt="" /></a></p>
<p>游戏审核那点事</p>

<p><a target="_blank" href="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_5.gif" style="text-indent: 24px;"><img src="http://admin.3dmgame.com/uploads/allimg/161202/153_161202161325_5_lit.gif" border="0" alt="" /></a></p>
<p>太坏了</p>

<span style="display:none"></span><p><b style="color:#f00">更多精彩尽在 <a target="_blank" href="http://www.3dmgame.com/games/fivegod/" style="color:#f00">五</a>专题：</b><a target="_blank" href="http://www.3dmgame.com/games/fivegod/" class="">http://www.3dmgame.com/games/fivegod/</a>
</p><div align="center" class="page_fenye">
<div class="pagelistbox">
<span>共 44 页/44条记录</span><span class="indexPage">首页 
</span><strong>1</strong>
<a target="_self"  href='3612345_2.html'>2</a>
<a target="_self"  href='3612345_3.html'>3</a>
<a target="_self"  href='3612345_4.html'>4</a>
<a target="_self"  href='3612345_5.html'>5</a>
<a target="_self"  href='3612345_6.html'>6</a>
<a target="_self"  href='3612345_7.html'>7</a>
<a target="_self"  href='3612345_8.html'>8</a>
<a target="_self"  href='3612345_9.html'>9</a>
<a target="_self"  href='3612345_10.html'>10</a>
<a target="_self"  href='3612345_11.html'>11</a>
<a  href='3612345_2.html'>下页</a> 
<a  href='3612345_44.html'>末页</a> 
</div>
</div>"""
        test = Spider3dm('')
        ret = test.image_urls(sss)
        print ret
    else:
        main()
