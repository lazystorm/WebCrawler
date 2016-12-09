# -*- coding: utf-8 -*-
import re

image_dir = '/home/storm/Desktop/GitHub/WebCrawler/images'

root_url = 'http://www.3dmgame.com/zt/'
join_pic_urls_filename = 'join_pic_urls.py'
download_log_filename = 'download_log.py'
pic_url_pattern = re.compile(
            r'<[imgIMG]+[\s border="0" alt="" ]+src="(http://[a-z]+\.3dmgame\.com/[Articleuploads]+/[allimgUploadFiles]+/\d+/[_\dlit]+\.[jpgif]+?)"[\s border="0" ABRundefinedalt="" /></a></p><p>]+(.*?)</[pP]?>',
            flags=re.M)

join_pic_page_url_pattern = re.compile(r'<a href="http://www\.3dmgame\.com/zt/[0-9]+/[0-9]+\.html" target="_blank">.*?</a>')
page_end_pattern = re.compile(r"<a  href='[0-9]+_[0-9]+.html'>末页</a>")
total_page = re.compile(r'totalpage=(\d+)')

parser_pool_size = 16
download_pool_size = 16