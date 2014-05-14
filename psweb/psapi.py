import socket
import json
from struct import *

HOST = 'localhost'
PORT = 50001

def ExecCommand(req):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((HOST, PORT))
        jsonStr = json.dumps(req)
        jsonLenStr = pack('L', len(jsonStr))
        s.send(jsonLenStr)
        s.send(jsonStr)

        jsonLenStr = s.recv(4)
        jsonLenTup = unpack('L', jsonLenStr)
        jsonLen = jsonLenTup[0]

        jsonStr = ''
        while len(jsonStr) < jsonLen:
            chunk = s.recv(4096)
            if not chunk: break
            jsonStr = jsonStr + chunk
        s.close()
    except socket.error:
        jsonStr = '{}'

    try:
        resp = json.loads(jsonStr)
    except ValueError:
        resp = {'cmd':'error'}

    ret = None
    try:
        if resp['res'] == 'ok':
            ret = resp['ret']
        else:
            print 'Result =', resp['res']
    except KeyError:
        print resp
        print 'Error in response'
    return ret

