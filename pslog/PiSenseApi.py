import threading
import socket
import json
from struct import *
import PiSenseNode
import PiSenseDb

HOST = 'localhost'
PORT = 59747

runServer = False
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

def ApiStart(Nodes, PsDb, Hub):
    global NodeList
    NodeList = Nodes
    global Database
    Database = PsDb
    global HubMon
    HubMon = Hub
    global runServer
    runServer = True
    global ApiThread
    ApiThread = PsApiThread()
    ApiThread.start()


def ApiStop():
    global runServer
    runServer = False
    global ApiThread
    global s
    s.close()
    print "Waiting for PsApiThread to stop..."
    ApiThread.join()
    print "Stopped"


class PsApiThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        #self.ApiRunning = False

    def run(self):
        global s

        s.bind((HOST, PORT))

        global runServer
        while runServer:
            try:        
                jsonStr = ''
                s.settimeout(1)
                s.listen(3)
                conn, addr = s.accept()
                #print "Accept"
                s.settimeout(10)
                jsonLenStr = conn.recv(4)
                jsonLenTup = unpack('L', jsonLenStr)
                jsonLen = jsonLenTup[0]
                #print jsonLen
                #Check for jsonLen being absurdly big............
                while len(jsonStr) < jsonLen:
                    chunk = conn.recv(4096)
                    if not chunk: break
                    jsonStr = jsonStr + chunk

                try:
                    req = json.loads(jsonStr)
                except ValueError:
                    req = {'cmd':'error'}
                resp = {}
                try:
                    print 'Connected by', addr, req['cmd']
                    if req['cmd'] == 'getobject':
                        pathlist = req['path']
                        if len(pathlist) == 0:
                            resp = {'res':'ok', 'ret':{}}
                        elif pathlist[0] == "nodelist":
                            ret = Database.GetNodeDb()
                            resp = {'res':'ok', 'ret':ret}
                        elif pathlist[0] == "sensordata":
                            ret = NodeList.GetDictSensorData()
                            resp = {'res':'ok', 'ret':ret}
                        elif pathlist[0] == "nodelistwithdata":
                            ret = NodeList.GetNodeListWithData(Database)
                            resp = {'res':'ok', 'ret':ret}
                        elif pathlist[0] == "history":
                            # Handle data/history/<nodeId>/<sensorNum>/<period>/<mxa>/<start>/<end>     (start/end are in seconds, m=min/x=max/a=avg)
                            if len(pathlist) == 7:
                                nodeId = pathlist[1]
                                sensorNum = pathlist[2]
                                period = pathlist[3]
                                mxa = pathlist[4]
                                start = pathlist[5]
                                end = pathlist[6]
                                ret = Database.GetHistoryData(nodeId, sensorNum, period, mxa, start, end)
                            else:
                                ret = {}
                            resp = {'res':'ok', 'ret':ret}
                    elif req['cmd'] == 'getattrib':
                        sernum = req['sernum']
                        attrib = req['attrib']
                        inst = req['inst']
                        ret = HubMon.GetAttribute(sernum, attrib, inst)
                        resp = {'res':'ok', 'ret':ret}
                    elif req['cmd'] == 'nodefwupdate':
                        sernum = req['sernum']
                        filename = req['filename']
                        ret = HubMon.NodeFwUpdate(sernum, filename)
                        resp = {'res':'ok', 'ret':ret}
                    elif req['cmd'] == 'getstats':
                        ret = NodeList.GetDictStats()
                        resp = {'res':'ok', 'ret':ret}
                    #elif req['cmd'] == 'stop':
                    #    resp = {'res':'ok', 'ret':{}}
                    #    runServer = False
                except KeyError:
                    pass

                jsonResp = json.dumps(resp)
                jsonLenStr = pack('L', len(jsonResp))
                conn.send(jsonLenStr)
                conn.send(jsonResp)
                conn.close()
            except socket.error:
                pass

