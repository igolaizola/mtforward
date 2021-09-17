#!/usr/bin/env python3
"""
Telegram message listener that launches commands
Usage::
    ./mtforward.py --id api_id --hash api_hash --session session_path --addr localhost:5353,localhost:5454 --copy -1001122334455:-1009988776655,-1001122334400:-1009988776600
"""

import getopt
import socket
import sys
from datetime import datetime
from pyrogram import Client, filters
from PIL import Image
import pytesseract
import os
import schedule
import time
import threading
from pyrogram.raw import functions

def handle(sock, addrs, copies, ocr, message):
    if ocr and hasattr(message, 'photo') and hasattr(message.photo, 'file_id'):
        path = app.download_media(message.photo.file_id)
        im = Image.open(path)
        message.photo.ocr = pytesseract.image_to_string(im)
        os.remove(path)
    jsn = str(message)
    for a in addrs:
        sock.sendto(bytes(jsn, "utf-8"), (a['host'], a['port']))
    if message.chat.id in copies:
        for d in copies[message.chat.id]:
            message.copy(d)

def runOnline(stop):
    while True:
        if stop():
            break
        schedule.run_pending()
        time.sleep(1)

def jobOnline():
    app.send(functions.account.UpdateStatus(offline=False))

options, rest = getopt.getopt(sys.argv[1:], '', ['id=','hash=','session=','addr=','copy=','ocr','online','version'])
version = False
api_id = ''
api_hash = ''
session = ''
addr = ''
copy = ''
ocr = False
online = False
for opt, arg in options:
    if opt == '--id':
        api_id = arg
    elif opt == '--hash':
        api_hash = arg
    elif opt == '--session':
        session = arg
    elif opt == '--addr':
        addr = arg
    elif opt == '--copy':
        copy = arg
    elif opt == '--ocr':
        ocr = True
    elif opt == '--online':
        online = True
    elif opt == '--version':
        version = True

if version:
    print('1.21.1')
elif api_id == '' or api_hash == '' or session == '' or (addr == '' and copy == ''):
    print('Usage mtforward.py --id api_id --hash api_hash --session session_path --addr localhost:5353,localhost:5454 --copy -1001122334455:-1009988776655,-1001122334400:-1009988776600')
else:
    app = Client(session, api_id, api_hash)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    
    addrs = []
    if addr != '':
        for a in addr.split(","):    
            s = a.split(":")
            host = s[0]
            port = int(s[1])
            addrs.append({'host': host, 'port': port})

    copies = {}
    if copy != '':
        for c in copy.split(","):
            s = c.split(":")
            src = int(s[0])
            dst = int(s[1])
            if src in copies:
                copies[src].append(dst)
            else:
                copies[src] = [dst]

    print(datetime.now().time(), 'mtforward started')

    @app.on_message()
    def onMessage(client, message):
        handle(sock, addrs, copies, ocr, message)

    stop = False
    if online:
        schedule.every().hour.at("00:55").do(jobOnline)
        t = threading.Thread(target=runOnline, args =(lambda : stop, ))
        t.start()
        print('auto online thread started')


    app.run()
    stop = True

