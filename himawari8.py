#!/usr/local/bin/python3
'''
The script generate image for earth and set it to desktop picture
'''
from os import environ, system
import json
from io import BytesIO
from datetime import time, datetime
from threading import Thread

import requests
from PIL import Image

# the directory where you want the script and saved image to be
IMG_DIR = environ['HOME'] + '/.himawari8'
# if you want another image to show in a range of time of a day,
# set the path to it below
DAY_IMG_PATH = '/Users/yuan/.himawari8/cowboy.jpg'
# set image generator. there are three of them,
# each generate different desktop image
imageGenerator = 'generateImage1'
# startTime and endTime indicate the range in which
# you want to set another image for desktop
# If you don't want it, just set both to (0,0)
# both time are presented as (hour, minute) in 24 format
startTime = (0, 0)
endTime = (0, 0)


class ThreadWithReturn(Thread):
    '''This class is a override of Tread class primarily for
    getting return value from function called in thread.
    This way I can set timeout for gen_img function
    and also get the returned path of generated image.'''

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


class ImageGenerator():
    '''This class contains several method that the program can use to generate image of desktop'''

    def generateImage1(self, width=2560, height=1600):
        '''This method generate a normal earth with given desktop size,
        if any of the dimension is less than 1100 pixel, the earth won't be full.
        This generator get image from himawari8 site.'''
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
        print('Image downloaded')

        # create a image and comine four pieces
        img = Image.new('RGB', (width, height), 'black')
        ori_x = int((width - 1100) / 2)
        ori_y = int((height - 1100) / 2)
        img.paste(img_lis[0], (ori_x, ori_y))
        img.paste(img_lis[1], (ori_x + 550, ori_y))
        img.paste(img_lis[2], (ori_x, ori_y + 550))
        img.paste(img_lis[3], (ori_x + 550, ori_y + 550))
        print('Image modified')

        imagePath = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
            ':', '-') + '.png'
        img.save(imagePath)
        print('Image saved')
        return imagePath

    def generateImage2(self, width=2560, height=1600):
        '''This generator generate a "off color" desktop with given dimension.
        The source of the image is another website.
        If any dimension is less than 1100 the earth won't be full'''
        url = 'http://rammb.cira.colostate.edu/ramsdis/online/images/latest_hi_res/himawari-8/full_disk_ahi_natural_color.jpg'
        config_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
        curr_date = json.loads(requests.get(config_url).text)['date']
        # example: {"date":"2017-07-22 04:50:00","file":"PI_H08_20170722_0450_TRC_FLDK_R10_PGPFD.png"}

        # avoid DecompressionBombWarning
        Image.MAX_IMAGE_PIXELS = 1000000000

        r = requests.get(url).content
        print('Image downloaded')
        earth_img = Image.open(BytesIO(r))
        earth_img_small = earth_img.resize(
            (1100, 1100), resample=Image.ANTIALIAS)
        background_img = Image.new('RGB', (width, height), 'black')

        origin_x = int((width - 1100) / 2)
        origin_y = int((height - 1100) / 2)
        background_img.paste(earth_img_small, (origin_x, origin_y))
        print('Image modified')

        imagePath = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
            ':', '-') + '.jpg'

        background_img.save(imagePath)
        print('Image saved')

        return imagePath

    def generateImage2OriginalSize(self):
        '''This generator generate image of size 11000x11000. The shape is square
        thus no dimension is needed.'''
        url = 'http://rammb.cira.colostate.edu/ramsdis/online/images/latest_hi_res/himawari-8/full_disk_ahi_natural_color.jpg'
        config_url = 'http://himawari8-dl.nict.go.jp/himawari8/img/D531106/latest.json'
        curr_date = json.loads(requests.get(config_url).text)['date']
        # example: {"date":"2017-07-22 04:50:00","file":"PI_H08_20170722_0450_TRC_FLDK_R10_PGPFD.png"}

        r = requests.get(url).content
        print('Image downloaded')

        imagePath = IMG_DIR + '/' + curr_date.replace(' ', '-').replace(
            ':', '-') + '.jpg'

        with open(imagePath, 'wb') as f:
            f.write(r)

        print('Image saved')

        return imagePath


def generateImageWithTimeOut(generator, timeout, imageSize=(2560, 1600)):
    '''create a thread that calls image generator,
    if it takes too long, kill it and try again.
    timeout has to be float in seconds, imageSize is a tuple with first atom being width
    and second being height'''
    for retryCount in range(1, 6):
        generatorThread = ThreadWithReturn(
            target=generator, args=(generator, *imageSize))
        generatorThread.start()
        imagePath = generatorThread.join(timeout)
        if not generatorThread.is_alive():
            return imagePath
        print('Time out, trying again. RetryCount: {}'.format(retryCount))
    return False


def set_desktop(imagePath):
    # system(
    #     "osascript -e 'tell application \"Finder\" to set desktop picture to \"{}\" as POSIX file'".
    #     format(imagePath))
    system(
        "osascript -e 'tell application \"System Events\" to set picture of every desktop to (\"{}\" as POSIX file as alias)'".
        format(imagePath))


def inRange(t1, t2):
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
    if inRange(startTime, endTime):
        set_desktop(DAY_IMG_PATH)
    else:
        imagePath = generateImageWithTimeOut(
            getattr(ImageGenerator, imageGenerator), 20.0, (2560, 1600))
        if imagePath is not False:
            set_desktop(imagePath)
        else:
            print('Image generation failed.')
