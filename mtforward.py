#!/usr/bin/env python3
"""
Telegram message listener that launches commands
Usage::
    ./mtforward.py api_id api_hash session "chat_id,command,regex" "chat_id,command,regex" ...
"""

import getopt
import socket
import sys
from datetime import datetime
from pyrogram import Client, filters

def handle(sock, host, port, message):
    jsn = str(message)
    sock.sendto(bytes(jsn, "utf-8"), (host, port))

options, rest = getopt.getopt(sys.argv[1:], '', ['id=','hash=','session=','addr=', 'version'])
version = False
addr = ''
for opt, arg in options:
    if opt == '--id':
        api_id = arg
    elif opt == '--hash':
        api_hash = arg
    elif opt == '--session':
        session = arg
    elif opt == '--addr':
        addr = arg
    elif opt == '--version':
        version = True

if version:
    print('1.21.1')
elif api_id == '' or api_hash == '' or session == '' or addr == '':
    print('Usage mtforward.py --id api_id --hash api_hash --session session_path --addr localhost:5353')
else:
    app = Client(session, api_id, api_hash)
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # UDP
    s = addr.split(":")
    host = s[0]
    port = int(s[1])

    print(datetime.now().time(), 'mtforward started')


    @app.on_message(filters.text)
    def onMessage(client, message):
        handle(sock, host, port, message)

    app.run()
