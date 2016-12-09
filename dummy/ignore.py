# -*- coding: utf-8 -*-
from Utils import auto_save_and_load
import os


@auto_save_and_load()
def ignore_dir(filename):
    os.chdir('../images')
    return [f for f in os.listdir('.') if os.path.isdir(f)]
