# -*- coding: utf-8 -*-
import os

import gevent
from gevent.pool import Pool
from gevent.queue import Queue
from gevent import monkey

import env
import proxy
from utils import load, dump

image_file_metas = Queue()
download_pool = Pool(env.download_pool_size)


class JoinImageDownloader:
    def __init__(self, dir_name, downloaded_images, ):
        self.dir_name = dir_name
        self.image_urls = set()
        self.downloaded_images = set(downloaded_images)
        self.init()

    def init(self):
        img_file_name = self.dir_name + '/' + self.dir_name + '.py'
        if os.path.exists(img_file_name):
            self.image_urls = set(load(img_file_name)['imgs'])
        else:
            print 'Image url file not found! %s' % img_file_name

    def download(self):
        for url in self.image_urls:
            image_name = url[url.rfind(r'/') + 1:]
            if image_name not in self.downloaded_images:
                download_pool.wait_available()
                download_pool.spawn(self.download_image, url, image_name)

    def download_image(self, url, image_name):
        # content = requests.get(url).content
        content = proxy.get(url, use_proxy=True).content
        file_meta = {'dir_name': self.dir_name, 'content': content, 'image_name': image_name}
        image_file_metas.put_nowait(file_meta)
        print 'Finish download: %s' % image_name


class DownloadManager:
    def __init__(self):
        self.downloaded_images = dict()
        if os.path.exists(env.download_log_filename):
            self.downloaded_images = load(env.download_log_filename)
        self.writer = DownloadManager.Writer(self.downloaded_images)
        self.file_writer = gevent.spawn(self.writer.write)

    def download(self):
        dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
        for dir_ in dirs:
            downloaded_images = self.downloaded_images.get(dir_, [])
            join_image_downloader = JoinImageDownloader(dir_, downloaded_images)
            join_image_downloader.download()
        download_pool.join()

    def finish(self):
        self.writer.finish()
        gevent.joinall([self.file_writer])
        dump(self.downloaded_images, env.download_log_filename)

    # TODO: using QueueConsumer
    class Writer:
        def __init__(self, downloaded_images):
            self.stop = False
            self.downloaded_images = downloaded_images

        def finish(self):
            self.stop = True

        def write(self):
            while not self.stop or not image_file_metas.empty():
                if not image_file_metas.empty():
                    file_meta = image_file_metas.get()
                    dir_name = file_meta['dir_name']
                    content = file_meta['content']
                    image_name = file_meta['image_name']
                    file_name = os.path.join(dir_name, image_name)
                    with open(file_name, 'wb') as fd:
                        fd.write(content)
                    downloaded_imgs = self.downloaded_images.get(dir_name, None)
                    if downloaded_imgs is None:
                        self.downloaded_images[dir_name] = [image_name]
                    else:
                        self.downloaded_images[dir_name].append(image_name)
                    if image_file_metas.empty():
                        dump(self.downloaded_images, env.download_log_filename)
                else:
                    gevent.sleep(0.1)
            print 'Quitting writer!'


def main():
    monkey.patch_all()
    os.chdir(env.image_dir)
    downloader = DownloadManager()
    try:
        downloader.download()
    except KeyboardInterrupt:
        pass
    finally:
        downloader.finish()

if __name__ == '__main__':
    main()
