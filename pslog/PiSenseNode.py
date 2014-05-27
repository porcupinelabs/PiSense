#import PiSenseDb
#import PiSenseCSV
#import time

def FirstMatch(iterable, default=None):
    for item in iterable:
        return item
    return default


class PsSensor:
    def __init__(self, SensorNum):
        self.SensorNum = SensorNum
        self.LastValue = "Unknown"
        self.LastDateTime = "Unknown"

    def ProcessReport(self, PsDb, Id, SensorNum, Value, DateTime):
        #if SensorNum == 2:
        #    print '['+Value+']'
        #add a conversion here to insert only the "instantaneous" value from the sensor inst,min,max,avg
        if (',' in Value):
            self.LastValue=Value[0:Value.index(',')]
        else:
            self.LastValue = Value
        self.LastDateTime = DateTime
        PsDb.SensorDataNew(Id, SensorNum, Value, DateTime)

    def PrintSensor(self):
        print self.SensorNum, self.LastValue, self.LastDateTime

    def GetDictSensorData(self):
        result = {'sn':self.SensorNum, 'lv':self.LastValue, 'dt':self.LastDateTime}
        return result


class PsNode:
    def __init__(self, Id):
        self.Id = Id
        self.SensorList = []
        self.LastDateTime = "Unknown"
        self.LastLqi = 0
        self.LastRssi = 0
        self.LastBattery = 0

    def ProcessReport(self, PsDb, Id, SensorNum, Value, DateTime, lqi, rssi):
        self.LastDateTime = DateTime
        self.LastLqi = lqi
        self.LastRssi = rssi
        if SensorNum == 0:                  #Assumes sensor 0 is battery
            self.LastBattery = Value
        Sensor = FirstMatch(x for x in self.SensorList if x.SensorNum == SensorNum)
        if Sensor == None:
            Sensor = PsSensor(SensorNum)    #New PsSensor object
            self.SensorList.append(Sensor)  #Add it to the list
            PsDb.SensorNew(Id, SensorNum)   #Add Sensor to persistant database if needed
            #Need to get units from PsDb
        Sensor.ProcessReport(PsDb, Id, SensorNum, Value, DateTime)
    
    def PrintNode(self):
        print self.Id
        for Sensor in self.SensorList:
            Sensor.PrintSensor()

    def GetDictSensorData(self):
        result = {'id':self.Id, 'dt':self.LastDateTime, 'lqi':self.LastLqi, 'rssi':self.LastRssi, 'sl':[Sensor.GetDictSensorData() for Sensor in self.SensorList]}
        return result


class PsNodeList:
    def __init__(self):
        self.NodeList = []
        self.ReportCounter = 0

    def ProcessReport(self, PsDb, Id, SensorNum, Value, DateTime, lqi, rssi):
        Node = FirstMatch(x for x in self.NodeList if x.Id == Id)
        if Node == None:
            Node = PsNode(Id)           #New PsNode object
            self.NodeList.append(Node)  #Add it to the list
            PsDb.NodeNew(Id)            #Add Node to persistant database if needed
        Node.ProcessReport(PsDb, Id, SensorNum, Value, DateTime, lqi, rssi)
        self.ReportCounter += 1

    def PrintNodeList(self):
        for Node in self.NodeList:
            Node.PrintNode()

    def GetDictSensorData(self):
        result = [Node.GetDictSensorData() for Node in self.NodeList]
        return result

    def GetDictStats(self):
        result = {'nodecount':len(self.NodeList), 'reportcounter':self.ReportCounter}
        return result

    def GetNodeListWithData(self, PsDb):
        db = PsDb.GetNodeDb()
        for dbnode in db:
            #print dbnode
            Node = FirstMatch(x for x in self.NodeList if x.Id == dbnode['Id'])
            DictSensorData=Node.GetDictSensorData()
            if not Node == None:
                dbnode['LastDateTime'] = Node.LastDateTime
                dbnode['LastLqi']      = Node.LastLqi
                dbnode['LastRssi']     = Node.LastRssi
                dbnode['LastBattery']  = Node.LastBattery
                for dbsensor in dbnode['SensorList']:
                    #could be a virtual sensor OR a raw sensor
                    Sensor = FirstMatch(x for x in Node.SensorList if x.SensorNum == dbsensor['SensorNum'])
                    if not Sensor == None:
                        #it is a raw sensor; last reading will have been stored by this module
                        dbsensor['LastValue'] = Sensor.LastValue
                        dbsensor['LastDateTime'] = Sensor.LastDateTime
                        PsDb.PostProcess(DictSensorData,dbsensor) #postprocess here for calibration case
                    else:
                        #it is a virtual sensor: reading to be calculated
                        PsDb.PostProcess(DictSensorData,dbsensor)
        return db




