# -*- coding: utf-8 -*-
import re
import os
import json
import requests
import collections

def getCnt(file):
    with open(file, 'r') as fd:
        fd.readline()
        data = json.load(fd, encoding='utf-8')
    return len(data)

def clearp():
    os.chdir('../images')
    for dir in os.listdir('.'):
        if os.path.isdir(dir):
            fs = os.listdir(dir)
            fcnt = len(fs)
            if fcnt < 5:
                print dir, fcnt
                #os.removedirs(fs)
                __import__('shutil').rmtree(dir)

cookies = {'name': 'nhpcc1', 'password': 'Nhpcc502','rn': '1D08974651A91F2D638ED49E155FCBCD4FF04CEC', '_ga': 'GA1.3.1429341455.1430800581', '_gscu_1103646635': '34363116y416rh77',}
url = 'http://wlt.ustc.edu.cn/cgi-bin/ip'
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.99 Safari/537.36'
headers = {'user-agent': user_agent,'host': 'wlt.ustc.edu.cn'}
port = 6
params = {
	'cmd': 'set',
	'url': 'URL',
	'type': str(port),
	'exp': '0',
	'go': '+%BF%AA%CD%A8%CD%F8%C2%E7+',
}
jar = requests.cookies.RequestsCookieJar()
jar.set('name', 'nhpcc1', domain='wlt.ustc.edu.cn', path='/cgi-bin')
jar.set('password', 'Nhpcc502', domain='wlt.ustc.edu.cn', path='/cgi-bin')
print jar
r = requests.get(url, headers=headers, cookies=cookies,params=params)
print requests.get(r.url).url
