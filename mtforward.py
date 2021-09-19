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
import pyrogram
from pyrogram import Client, filters
from pyrogram.raw import functions
from pyrogram.raw import types
from PIL import Image
import pytesseract
import os
import schedule
import time
import threading
import io
import math

def handle(sock, addrs, copies, ocr, message):
    if ocr and hasattr(message, 'photo') and hasattr(message.photo, 'file_id'):
        path = app.download_media(message.photo.file_id)
        im = Image.open(path)
        message.photo.ocr = pytesseract.image_to_string(im)
        os.remove(path)
    jsn = str(message)
    for a in addrs:
        sock.sendto(bytes(jsn, "utf-8"), (a['host'], a['port']))
    if hasattr(message, 'chat') and message.chat.id in copies:
        for d in copies[message.chat.id]:
            message.copy(d)

def runOnline():
    while True:
        schedule.run_pending()
        time.sleep(1)

def jobOnline():
    app.send(functions.account.UpdateStatus(offline=False))
    
def getDiff(channel, sock, addrs, copies, ocr):
    time.sleep(2)
    u = app.send(functions.contacts.ResolveUsername(username = channel))
    chann = types.InputChannel(channel_id = u.chats[0].id, access_hash = u.chats[0].access_hash)
    full = app.send(functions.channels.GetFullChannel(channel=chann))
    pts = full.full_chat.pts    
    while True:
        diff = app.send(functions.updates.GetChannelDifference(channel = chann, filter = types.ChannelMessagesFilterEmpty(), limit = 10, pts=pts))
        pts = diff.pts
        if hasattr(diff, 'new_messages'):
            for m in diff.new_messages:
                chat = pyrogram.types.Chat(id=m.peer_id.channel_id,username=channel,type='channel')
                msg = pyrogram.types.Message(message_id=m.id, text=m.message, date=m.date, chat=chat)

                if ocr and hasattr(m, 'media') and hasattr(m.media, 'photo'):
                    print(m)
                    p = m.media.photo
                    for s in p.sizes:
                        if s.type == 'm':
                            size = s.size
                    limit = pow(2, math.ceil(math.log(size, 2))) * 4
                    loc = types.InputPhotoFileLocation(id=p.id, access_hash=p.access_hash, file_reference=p.file_reference, thumb_size='i')
                    file = app.send(functions.upload.GetFile(location=loc, offset=0, limit=limit))
                    im = Image.open(io.BytesIO(file.bytes))
                    text = pytesseract.image_to_string(im)
                    msg.photo = {"ocr": text}

                handle(sock, addrs, copies, ocr, msg)
        now = datetime.now()
        if (now.minute == 59 and now.second > 45) or (now.minute == 0 and now.second < 5):
            time.sleep(0.1)
        else:
            time.sleep(5)

options, rest = getopt.getopt(sys.argv[1:], '', ['id=','hash=','session=','addr=','copy=', 'poll=', 'ocr','online','version'])
version = False
api_id = ''
api_hash = ''
session = ''
addr = ''
copy = ''
poll = ''
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
    elif opt == '--poll':
        poll = arg
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

    if online:
        schedule.every().minute.at(":45").do(jobOnline)
        t = threading.Thread(target=runOnline, daemon=True)
        t.start()
        print('auto online thread started')

    if poll != '':
        for c in poll.split(","):
            t = threading.Thread(target=getDiff, args=(c, sock, addrs, copies, ocr), daemon=True)
            t.start()

    app.run()

    