# -*- coding: utf-8 -*-
import os

from dm3spider.utils import auto_save_and_load


@auto_save_and_load()
def ignore_dir(filename):
    os.chdir('../images')
    return [f for f in os.listdir('.') if os.path.isdir(f)]
