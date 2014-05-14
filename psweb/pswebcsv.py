import time
import threading
import SimpleHTTPServer, SocketServer
import urlparse
import json
import psapi
import csv


RunWebServer = False

def GetSensorDataSummary(Id, SensorNum, TimePeriod):
    PeriodTable = {'all':1300000000, 'year':31536000, 'month':2678400, 'week':604800, 'day':86400, 'hour':3600}
    TblTypeTable = {'all':'3600', 'year':'86400', 'month':'86400', 'week':'86400', 'day':'3600', 'hour':'3600'}
    StartTime = int(round(time.time())) - PeriodTable.get(TimePeriod, 3600)
    TblType = TblTypeTable.get(TimePeriod, '3600')
    
    SensorListName = Id + '_sensors.csv'
    TblName = Id + "_" + TblType + '.csv'

    SensorArrayFile=open('../pslog/'+SensorListName,'r')
    DataArrayFile=open('../pslog/'+TblName, 'r')
    
    SensorReader=csv.reader(SensorArrayFile)
    DataReader=csv.reader(DataArrayFile)

    for sensorrow in SensorReader:
        SensorArray=sensorrow #gets last line
    position=sensorrow.index(SensorNum)
    SensorArrayFile.close()
                         
    summarydata=[]
    rows=[]
    for datarow in DataReader:
        if datarow[0]>StartTime:
            summarydata.append(datarow)
            #summary csv's contain min,max,avg for every sensor on one row
            #in the same order as sensor numbers in the sensor file
            #index 0 is the stamp
            rows.append([datarow[0],datarow[position*3-2],datarow[position*3-1]])
                
    Result = zip(*rows)             # Result is three arrays [[stamp1, stamp2, ...][min1, min2, ...][max1, max2, ...]]
    #TODO:include the average
    DataArrayFile.close()

    return Result


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
                self.processMyRequest(queryParsed, pathlist[2:], jsonp)
                return
        # Default to serve up a local file 
        SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self);

    def processMyRequest(self, query, pathlist, jsonp):
        if len(pathlist) < 1:
            self.wfile.write("{}");     # Error: path has nothing after /data
        elif pathlist[0] == "history":
            # Handle /data/history/<Id>/<SensorNum>/<Period>
            if len(pathlist) < 4:
                self.wfile.write("{}");
            else:
                Id = pathlist[1]
                SensorNum = pathlist[2]
                Period = pathlist[3]
                jsonData = GetSensorDataSummary(Id, SensorNum, Period)
                self.sendJsonAscii(jsonData, jsonp)
                #self.wfile.write(json.dumps(jsonData));
        else:
            jsonData = psapi.ExecCommand({'cmd':'getobject', 'path':pathlist})
            self.sendJsonAscii(jsonData, jsonp)
            #self.wfile.write(json.dumps(jsonData));
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
    PORT = 8000
    httpd = SocketServer.ThreadingTCPServer(("", PORT), Handler)
    httpd.timeout = 1
    print "Serving at port", PORT
    while RunWebServer:
        httpd.handle_request()


def WebServerOpen():
    global RunWebServer
    RunWebServer = True
    global WebServerThread
    WebServerThread = threading.Thread(target=WebServerMain)
    WebServerThread.start()

def WebServerClose():
    print "Closing web server"
    global RunWebServer
    RunWebServer = False
    WebServerThread.join()
    print "Done"


WebServerOpen()
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print "KeyboardInterrupt"
WebServerClose()

