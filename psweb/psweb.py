import sqlite3
import time
import threading
import SimpleHTTPServer, SocketServer
import urlparse
import json
import psapi


RunWebServer = False

class MyHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    def do_GET(self):
        parsedParams = urlparse.urlparse(self.path)
        queryParsed = urlparse.parse_qs(parsedParams.query)
        params = parsedParams.path.split("&")

        jsonp = ""
        if len(params) > 1:
            callback = params[1].split("=")
            if callback[0] == "callback":
                jsonp = callback[1]

        pathlist = params[0].split("/")

        if len(pathlist) > 0:
            if pathlist[1] == "data":
                self.processJsonRequest(queryParsed, pathlist[2:], jsonp)
                return
        # Default to serve up a local file 
        self.path = "http/" + self.path
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self);

    def processJsonRequest(self, query, pathlist, jsonp):
        if len(pathlist) < 1:
            self.wfile.write("{}");     # Error: path has nothing after /data
        else:
            jsonData = psapi.ExecCommand({'cmd':'getobject', 'path':pathlist})
            self.sendJsonAscii(jsonData, jsonp)
        self.wfile.close();

    def sendJsonAscii(self, jsonData, jsonp):
        self.send_response(200)
        self.send_header('Content-Type', 'text/javascript; charset=utf-8')
        self.end_headers()
        if not len(jsonp) == 0:
            self.wfile.write(jsonp + '({"query":')
        self.wfile.write(json.dumps(jsonData))
        if not len(jsonp) == 0:
            self.wfile.write("})")


Handler = MyHandler

def WebServerMain():
    PORT = 80
    global httpd
    httpd = SocketServer.ThreadingTCPServer(("", PORT), Handler)
    httpd.timeout = 1
    print "Serving at port", PORT
    while RunWebServer:
        httpd.serve_forever()


def WebServerOpen():
    global RunWebServer
    RunWebServer = True
    global WebServerThread
    WebServerThread = threading.Thread(target=WebServerMain)
    WebServerThread.start()

def WebServerClose():
    print "Closing web server"
    global RunWebServer
    global httpd
    RunWebServer = False
    httpd.shutdown()
    WebServerThread.join()
    print "Done"


WebServerOpen()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "KeyboardInterrupt"
WebServerClose()

