# -*- coding: utf-8 -*-
import re
import leveldb

from proxy import ProxyManager

#dirs
image_dir = '/home/storm/Desktop/GitHub/WebCrawler/images/'
db_dir = '/home/storm/Desktop/GitHub/WebCrawler/databases/'
tmp_dir = '/home/storm/Desktop/GitHub/WebCrawler/temp/'

#header
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
headers = {'user-agent': user_agent}

#db
proxy_db = leveldb.LevelDB(db_dir + 'proxy.ldb')
proxy_manager = ProxyManager()


#3dm
root_url = 'http://www.3dmgame.com/zt/'
join_pic_urls_filename = 'join_pic_urls.py'
download_log_filename = 'download_log.py'
pic_url_pattern = re.compile(
            r'<[imgIMG]+[\s border="0" alt="" ]+src="(http://[a-z]+\.3dmgame\.com/[Articleuploads]+/[allimgUploadFiles]+/\d+/[_\dlit]+\.[jpgif]+?)"[\s border="0" ABRundefinedalt="" /></a></p><p>]+(.*?)</[pP]?>',
            flags=re.M)

join_pic_page_url_pattern = re.compile(r'<a href="http://www\.3dmgame\.com/zt/[0-9]+/[0-9]+\.html" target="_blank">.*?</a>')
page_end_pattern = re.compile(r"<a  href='[0-9]+_[0-9]+.html'>末页</a>")
total_page = re.compile(r'totalpage=(\d+)')

#kuaidaili
kuai_proxy_meta_pattern = re.compile(r'<tr>\s+<td data-title="IP">([\d.]+)</td>\s+<td data-title="PORT">(\d+)</td>\s+<td data-title="匿名度">\W+</td>\s+<td data-title="类型">([\w,\s]+)</td>(?:\s+<td data-title="get/post支持">[\w,\s]+</td>)?\s+<td data-title="位置">[\W\s]+</td>\s+<td data-title="响应速度">([\d.]+)秒</td>\s+<td data-title="最后验证时间">.*?</td>\s+</tr>')

#xicidaili
xici_proxy_meta_pattern = re.compile(r'<td>([\d.]+)</td>\s+<td>(\d+)</td>\s+<td>[\s\W]+</td>\s+<td class="country">\W+</td>\s+<td>([HTTPS]+)</td>')

parser_pool_size = 16
download_pool_size = 32