# -*- coding: utf-8 -*-
from Utils import auto_save_and_load
from Utils import read_file
import os
import json


def check_img_complete(img_name):
    img = read_file(img_name)
    if img_name.endswith('.jpg') or img_name.endswith('.JPG'):
        if img.endswith('\xff\xd9'):
            return True
        else:
            return False
    elif img_name.endswith('.gif'):
        if img.endswith('\x3b'):
            return True
        else:
            return False


@auto_save_and_load()
def check_images(filename):
    if os.path.exists('../images'):
        os.chdir('../images')
    file_roots = [dir for dir in os.listdir('.') if os.path.isdir(dir)]
    missing_imgs = []
    for fr in file_roots:
        os.chdir(fr)
        log_file = fr + '.py'
        if os.path.exists(log_file):
            with open(log_file, 'rb') as lf:
                lf.readline()
                logs = json.load(lf, encoding='utf-8')
            img_should_download = dict([[str(url[url.rfind('/') + 1:]), url] for url in logs['imgs']])
            img_downloaded = set([f for f in os.listdir('.') if not f.endswith('.py') and os.path.isfile(f)])
            for img in img_downloaded:
                if not check_img_complete(img):
                    print img
                    missing_imgs.append([fr, img_should_download.get(img, None)])
            for img in img_should_download:
                if img not in img_downloaded:
                    print img
                    missing_imgs.append([fr, img_should_download.get(img, None)])
        os.chdir('..')
    return missing_imgs

if __name__ == '__main__':
    fname = 'missing_imgs.py'
    path = '../images/' + fname
    if os.path.exists(path):
        os.remove(path)
    check_images(filename=fname)
