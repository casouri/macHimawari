#! /bin/python

import platform
import os
import environ

plist_template = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
    <dict>
        <key>Label</key>
        <string>com.yuan.himawari8</string>

        <key>Program</key>
        <string>{}</string>

        <key>RunAtLoad</key>
        <true/>

        <key>StartInterval</key>
        <integer>300</integer>
    </dict>
</plist>
'''


def is_win():
    return platform.system() == 'Windows'


def is_mac():
    return platform.system() == 'Darwin'


if is_win():
    app_dir = 'C:\My Documents\himawari8'
    day_img_path = app_dir + '\cowboy.bmp'
    script_path = app_dir + '\himawari8.py'

elif is_mac():
    app_dir = environ['HOME'] + '/.himawari8'
    day_img_path = app_dir + '/cowboy.bmp'
    script_path = app_dir + '/himawari8.py'

    os.system('cp himawari8.py {}'.format(script_path))

    plist = plist_template.format(script_path)
    os.system('rm $HOME/Library/LaunchAgents/com.yuan.himawari8.plist')
    with open(
            environ['HOME'] + '/Library/LaunchAgents/com.yuan.himawari8.plist',
            'w') as f:
        f.write(plist)
    os.system(
        'launchctl unload $HOME/Library/LaunchAgents/com.yuan.himawari8.plist')
    os.system(
        'launchctl load $HOME/Library/LaunchAgents/com.yuan.himawari8.plist')
    os.system('pip3 install Pillow, requests')
