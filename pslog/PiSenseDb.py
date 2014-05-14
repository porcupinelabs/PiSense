import sqlite3
import time
import threading

PISENSE_DB_NAME = 'PiSense.db'

def GetTableName(Id, SensorNum, Type):
    return "SD" + "_" + Id + "_" + str(SensorNum) + "_" + Type


class PiSenseDatabase:
    def __init__(self):
        pass

    def Open(self):
        self.Conn = sqlite3.connect(PISENSE_DB_NAME)
        #self.Conn.row_factory = sqlite3.Row
        c = self.Conn.cursor()
        c.execute("PRAGMA journal_mode=WAL")
        
        c.execute("""create table if not exists Nodes (
            Id varchar(10),
            Model varchar(80),
            Manufacturer varchar(80),
            Nickname varchar(80),
            HwVersion varchar(16),
            FwVersion varchar(16),
            UNIQUE(Id) ON CONFLICT REPLACE
        )""")
        self.Conn.commit()

        c.execute("""create table if not exists Sensors (
            Id varchar(10),
            SensorNum smallint,
            Property varchar(40),
            Units varchar(16),
            Minimum float,
            Maximum float,
            IntervalEnable integer,
            IntervalTime integer,
            ThreshMinEnable integer,
            ThreshMin float,
            ThreshMaxEnable integer,
            ThreshMax float,
            ChangePercentEnable integer,
            ChangePercent float,
            UNIQUE(Id,SensorNum) ON CONFLICT REPLACE
        )""")
        self.Conn.commit()


    def Close(self):
        self.Conn.close()

    def NodeNew(self, Id):
        # Add node if not present in database
        c = self.Conn.cursor()
        c.execute("SELECT * FROM Nodes WHERE Id=?", (Id,))
        row = c.fetchone()
        if row is None:
            print "New Node", Id
            Model = "PiSense Enviro"
            Manufacturer = "Porcupine Electronics"
            if Id == 12345678:
                Nickname = "Inside Temp"
            else:
                Nickname = "Outside Temp"
            HwVersion = "v3"
            FwVersion = "0.1.1"
            c.execute("INSERT INTO Nodes VALUES (?,?,?,?,?,?)",(Id, Model, Manufacturer, Nickname, HwVersion, FwVersion))
            self.Conn.commit()
        #else:
        #    print "Found Node", (row)


    def SensorNew(self, Id, SensorNum):
        PropertyList = ["Battery", "Temperature", "Humidity", "Pressure", "Light"]
        UnitsList = ["% charged", "degrees C", "% RH", "mbar", "% full"]
        # Add sensor if not present in database
        c = self.Conn.cursor()
        c.execute("SELECT * FROM Sensors WHERE Id=? AND SensorNum=?", (Id, SensorNum))
        row = c.fetchone()
        if row is None:
            print "New Sensor", Id, SensorNum
            Property = PropertyList[SensorNum]
            Units = UnitsList[SensorNum]
            Minimum  = -40.0
            Maximum = 85.0
            IntervalEnable = 0
            IntervalTime = 0
            ThreshMinEnable = 0
            ThreshMin = 0.0
            ThreshMaxEnable = 0
            ThreshMax = 0.0
            ChangePercentEnable = 0
            ChangePercent = 0.0
            c.execute("INSERT INTO Sensors VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(Id, SensorNum, Property, Units, Minimum, Maximum, IntervalEnable, IntervalTime, ThreshMinEnable, ThreshMin, ThreshMaxEnable, ThreshMax, ChangePercentEnable, ChangePercent))
            self.Conn.commit()

            Cmd = "create table if not exists " + GetTableName(Id, SensorNum, "RAW") + " (Stamp int, Value varchar(10))"
            c.execute(Cmd)
            self.Conn.commit()
            Cmd = "create table if not exists " + GetTableName(Id, SensorNum, "MIN") + " (Stamp int, Min real, Max real)"
            c.execute(Cmd)
            self.Conn.commit()
            Cmd = "create table if not exists " + GetTableName(Id, SensorNum, "10M") + " (Stamp int, Min real, Max real)"
            c.execute(Cmd)
            self.Conn.commit()
            Cmd = "create table if not exists " + GetTableName(Id, SensorNum, "HOU") + " (Stamp int, Min real, Max real)"
            c.execute(Cmd)
            self.Conn.commit()
            Cmd = "create table if not exists " + GetTableName(Id, SensorNum, "DAY") + " (Stamp int, Min real, Max real)"
            c.execute(Cmd)
            self.Conn.commit()
        #else:
        #    print "Found Sensor", (row)


    def SensorDataNew(self, Id, SensorNum, Value, DateTime):
        # Add sensor data record to database
        c = self.Conn.cursor()
        Cmd = "INSERT INTO " + GetTableName(Id, SensorNum, "RAW") + " VALUES (?,?)"
        c.execute(Cmd, (DateTime, Value))
        self.Conn.commit()

    def DumpTable(self, TableName):
        c = self.Conn.cursor()
        for row in c.execute("SELECT * FROM " + TableName):
            print row

    def GetNodeDb(self):
        #t1 = time.time()
        Conn = sqlite3.connect('PiSense.db')
        Conn.row_factory = sqlite3.Row
        c = Conn.cursor()
        NodeDb = [dict(zip(row.keys(), row)) for row in c.execute("SELECT * FROM Nodes")]
        for Node in NodeDb:
            cmd = "SELECT * FROM Sensors WHERE Id='" + Node['Id'] + "'"
            SensorList = [dict(zip(row.keys(), row)) for row in c.execute(cmd)]
            Node['SensorList'] = SensorList
        Conn.close()
        #t2 = time.time()
        #print t2 - t1
        return NodeDb

    def GetSensorDataDb(self, Id, SensorNum, TimePeriod):
        #t1 = time.time()
        SqlPeriodTable = {'all':1300000000, 'year':31536000, 'month':2678400, 'week':604800, 'day':86400, 'hour':3600, 'minute':60}
        StartTime = int(round(time.time())) - SqlPeriodTable.get(TimePeriod, 3600)
        Conn = sqlite3.connect('PiSense.db')
        c = Conn.cursor()
        cmd = "SELECT * FROM " + GetTableName(Id, SensorNum, "RAW") + " WHERE Stamp>" + str(StartTime)
        rows = c.execute(cmd)           # rows is an array of tuples (with one value each)
        Result = zip(*rows)             # Result is two arrays [[stamp1, stamp2, ...][value1, value2, ...]]
        Conn.close()
        #t2 = time.time()
        #print t2 - t1
        return Result
        
    def GetSensorDataSummary(self, Id, SensorNum, TimePeriod):
        SqlPeriodTable = {'all':1300000000, 'year':31536000, 'month':2678400, 'week':604800, 'day':86400, 'hour':3600}
        SqlTblTypeTable = {'all':'MIN', 'year':'DAY', 'month':'HOU', 'week':'HOU', 'day':'10M', 'hour':'MIN'}
        StartTime = int(round(time.time())) - SqlPeriodTable.get(TimePeriod, 3600)
        TblType = SqlTblTypeTable.get(TimePeriod, 'MIN')
        Conn = sqlite3.connect('PiSense.db')
        c = Conn.cursor()
        cmd = "SELECT * FROM " + GetTableName(Id, SensorNum, TblType) + " WHERE Stamp>" + str(StartTime)
        rows = c.execute(cmd)           # rows is an array of tuples (with one value each)
        Result = zip(*rows)             # Result is three arrays [[stamp1, stamp2, ...][min1, min2, ...][max1, max2, ...]]
        Conn.close()
        return Result

    def DeleteSummary(self):
        #c = self.Conn.cursor()
        #rows = c.execute("SELECT Id,SensorNum FROM Sensors")
        rows = [["000001002",0],["000001002",1],["000001002",2],["000001002",3],["000001002",4]]
        for row in rows:
            for DestTable in ["MIN","10M","HOU","DAY"]:
                c2 = self.Conn.cursor()
                Cmd = "DELETE FROM " + GetTableName(row[0], row[1], DestTable)
                print Cmd
                c2.execute(Cmd)
                self.Conn.commit()


# Performance notes:
# <This was done when all sensor data was in a single table>
# With about two weeks of 10s sampled Enviro data the database is 11.7MB
# There are about 100k records * five sensors (22 bytes per record)
# A SELECT that gets all of one sensor's data takes about 10s
# It then takes about 3s to send that data over HTTP (to client on same LAN)
# And then it takes Google line chart about 14s to draw the chart

# Each record, when converted to JSON takes ~21 bytes ("1375672166, " + "'25.18', ")

# Summary Tables
# Hour: 1 per minute = 60
# Day: 1 per 10 minutes = 144
# Week: 1 per hour = 160
# Month: 1 per hour = 640
# Year: 1 per day = 365

runDbTask = False

def DbTaskStart():
    global runDbTask
    runDbTask = True
    global DbTaskThread
    DbTaskThread = PsDbThread()
    DbTaskThread.start()

def DbTaskStop():
    global runDbTask
    runDbTask = False
    global DbTaskThread
    print "Waiting for DbTaskThread to stop..."
    DbTaskThread.join()
    print "Stopped"

class PsDbThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        now = int(round(time.time()))
        self.NextSummary = now - (now % 60) + 60
        global runDbTask
        while runDbTask:
            time.sleep(1)
            now = int(round(time.time()))
            if now >= self.NextSummary:
                self.NextSummary = now - (now % 60) + 60
                print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(now))
                self.Summarize(now)

    def Summarize(self, SumTime):
        self.Conn = sqlite3.connect(PISENSE_DB_NAME)
        c = self.Conn.cursor()
        rows = c.execute("SELECT Id,SensorNum FROM Sensors")
        SensorList = []
        for row in rows:    # Make a copy of rows, so the list won't get disturbed
            SensorList.append([row[0], row[1]])
        for sensor in SensorList:
            self.SummarizeSensor(SumTime, sensor[0], sensor[1])
        self.Conn.close()

    def SummarizeSensor(self, SumTime, Id, SensorNum):
        EndTime = SumTime - (SumTime % 60)  # Set time to the last one minute boundary
        t = time.localtime(SumTime)     # t = struct with y,m,d,h,m,s fields

        StartTime = EndTime - 60        # Once per minute
        c = self.Conn.cursor()
        cmd = "SELECT Value FROM " + GetTableName(Id, SensorNum, "RAW") + " WHERE Stamp BETWEEN " + str(StartTime) + " AND " + str(EndTime)
        rows = c.execute(cmd)           # rows is an array of tuples (with one value each)
        lval = []
        for row in rows:
            lval.append(float(row[0]))
        if len(lval) > 0:
            Cmd = "INSERT INTO " + GetTableName(Id, SensorNum, "MIN") + " VALUES (?,?,?)"
            #The following line once got: OperationalError: database is locked
            c.execute(Cmd, (StartTime, min(lval), max(lval)))
            self.Conn.commit()
        if t.tm_min % 10 == 0:          # Once per 10 minutes
            StartTime = EndTime - 10*60
            self.SummarySub(Id, SensorNum, StartTime, EndTime, "MIN", "10M")
        if t.tm_min == 0:               # Once per hour
            StartTime = EndTime - 60*60
            self.SummarySub(Id, SensorNum, StartTime, EndTime, "10M", "HOU")
        if (t.tm_hour == 0) and (t.tm_min == 0):  # Once per day
            StartTime = EndTime - 24*60*60
            self.SummarySub(Id, SensorNum, StartTime, EndTime, "HOU", "DAY")


    def SummarySub(self, Id, SensorNum, StartTime, EndTime, SrcTable, DestTable):
        c = self.Conn.cursor()
        cmd = "SELECT Min,Max FROM " + GetTableName(Id, SensorNum, SrcTable) + " WHERE Stamp BETWEEN " + str(StartTime) + " AND " + str(EndTime)
        rows = c.execute(cmd)           # rows is an array of tuples (with one value each)
        lmin = []
        lmax = []
        for row in rows:
            lmin.append(float(row[0]))
            lmax.append(float(row[1]))
        if len(lmin) > 0:
            st = time.strftime("%d %b %Y %H:%M", time.localtime(StartTime))
            print "Summary: " + DestTable, st, Id, SensorNum
            Cmd = "INSERT INTO " + GetTableName(Id, SensorNum, DestTable) + " VALUES (?,?,?)"
            c.execute(Cmd, (StartTime, min(lmin), max(lmax)))
            self.Conn.commit()

        




