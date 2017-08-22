#!/usr/local/bin/python3
'''
There are three image generation functions, _blue generate blue earth,
_rect and _square generate an off color yellowish earth.
_rect generate picture in 16:9 while _suare generate image in 11000x11000 pixels.
'''
from os import environ, system
import json
from io import BytesIO
from datetime import time, datetime
from threading import Thread

import requests
from PIL import Image

IMG_DIR = environ['HOME'] + '/.himawari8'
DAY_IMG_PATH = '/Users/yuan/.himawari8/cowboy.jpg'


class ThreadWithReturn(Thread):
    '''This class is a override of Tread class primarily for
    getting return value from function called in thread.
    This way I can set timeout for gen_img function
    and be able to terminate it when it took too long.'''

    def __init__(self,
                 group=None,
                 target=None,
                 name=None,
                 args=(),
                 kwargs=None,
                 *,
                 daemon=None):
        Thread.__init__(self, group, target, name, args, kwargs, daemon=daemon)
        self._return = None

    def run(self):
        if self._target is not None:
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, timeout=None):
        Thread.join(self, timeout=timeout)
        return self._return


def gen_img_blue(width=2560, height=1600):
    config_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
    base_img_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/2d/550/'
    # example: http://himawari8-dl.nict.go.jp/himawari8/img/D531106/2d/550/2016/01/08/035000_0_0.png

    curr_date = json.loads(requests.get(config_url).text)['date']
    # example: {"date":"2017-07-22 04:50:00","file":"PI_H08_20170722_0450_TRC_FLDK_R10_PGPFD.png"}
    format_date = curr_date.replace('-', '/').replace(' ', '/').replace(
        ':', '')
    # from 2017-07-22 04:50:00 to 2017/07/22/045000

    # four pieces of the earth image
    urls = [
        base_img_url + format_date + '_0_0.png',
        base_img_url + format_date + '_1_0.png',
        base_img_url + format_date + '_0_1.png',
        base_img_url + format_date + '_1_1.png'
    ]
    img_lis = []
    for url in urls:
        r = requests.get(url).content
        i = Image.open(BytesIO(r))
        img_lis.append(i)

    # create a image and comine four pieces
    img = Image.new('RGB', (width, height), 'black')
    ori_x = int((width - 1100) / 2)
    ori_y = int((height - 1100) / 2)
    img.paste(img_lis[0], (ori_x, ori_y))
    img.paste(img_lis[1], (ori_x + 550, ori_y))
    img.paste(img_lis[2], (ori_x, ori_y + 550))
    img.paste(img_lis[3], (ori_x + 550, ori_y + 550))

    img_path = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
        ':', '-') + '.png'
    img.save(img_path)
    return img_path


def gen_img_new_rect(width=2560, height=1600):
    url = 'http://rammb.cira.colostate.edu/ramsdis/online/images/latest_hi_res/himawari-8/full_disk_ahi_natural_color.jpg'
    config_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
    # example: http://himawari8-dl.nict.go.jp/himawari8/img/D531106/2d/550/2016/01/08/035000_0_0.png

    curr_date = json.loads(requests.get(config_url).text)['date']
    # example: {"date":"2017-07-22 04:50:00","file":"PI_H08_20170722_0450_TRC_FLDK_R10_PGPFD.png"}

    # avoid DecompressionBombWarning
    Image.MAX_IMAGE_PIXELS = 1000000000

    r = requests.get(url).content
    print('Image downloaded')
    earth_img = Image.open(BytesIO(r))
    earth_img_small = earth_img.resize((1100, 1100), resample=Image.ANTIALIAS)
    earth_img_small.save('img.jpg')
    background_img = Image.new('RGB', (width, height), 'black')

    origin_x = int((width - 1100) / 2)
    origin_y = int((height - 1100) / 2)
    background_img.paste(earth_img_small, (origin_x, origin_y))
    print('Image modified')

    img_path = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
        ':', '-') + '.jpg'

    background_img.save(img_path)
    print('Image saved')

    return img_path


def gen_img_new_square(width, height):
    url = 'http://rammb.cira.colostate.edu/ramsdis/online/images/latest_hi_res/himawari-8/full_disk_ahi_natural_color.jpg'
    config_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
    # example: http://himawari8-dl.nict.go.jp/himawari8/img/D531106/2d/550/2016/01/08/035000_0_0.png

    curr_date = json.loads(requests.get(config_url).text)['date']
    # example: {"date":"2017-07-22 04:50:00","file":"PI_H08_20170722_0450_TRC_FLDK_R10_PGPFD.png"}

    r = requests.get(url).content
    print('Image downloaded')

    img_path = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
        ':', '-') + '.jpg'

    with open(img_path, 'wb') as f:
        f.write(r)

    print('Image saved')

    return img_path


def genImageWithTimeOut(gen_img, timeout, img_size=(2560, 1600)):
    '''create a thread that called image generation function,
    if it takes too long, kill it and try again.
    timeout has to be float, img_size is a tuple with first atom being width
    and second being height'''
    for retryCount in range(1, 6):
        gen_img_thread = ThreadWithReturn(target=gen_img, args=img_size)
        gen_img_thread.start()
        img_path = gen_img_thread.join(timeout)
        if not gen_img_thread.is_alive():
            return img_path
        print('Time out, trying again. RetryCount: {}'.format(retryCount))
    return False


def set_desktop(img_path):
    # system(
    #     "osascript -e 'tell application \"Finder\" to set desktop picture to \"{}\" as POSIX file'".
    #     format(img_path))
    system(
        "osascript -e 'tell application \"System Events\" to set picture of every desktop to (\"{}\" as POSIX file as alias)'".
        format(img_path))


def in_range(t1, t2):
    '''
    t1, t2 are time range in where script doen not run
    in that range the desktop will be set to another image
    t1, t2 are tuple
    24 hour mode
    10:24 --> (10, 24)
    '''
    now = datetime.now()
    now_time = now.time()
    if now_time >= time(t1[0], t1[1]) and now_time <= time(t2[0], t2[1]):
        return True
    else:
        return False


if __name__ == '__main__':
    # if in_range((7, 0), (7, 1)):
    #     set_desktop(DAY_IMG_PATH)
    # else:
    img_path = genImageWithTimeOut(gen_img_blue, 120.0, (2560, 1600))
    if img_path is not False:
        set_desktop(img_path)
    else:
        print('Image generation failed.')
