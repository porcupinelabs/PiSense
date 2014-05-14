import PiSenseNode
import PiSenseDb
import PiSenseCSV
import PiSenseSerial
import PiSenseApi
import sys
import time
import argparse
import traceback

def PsRun(storetype,simfilename):

    #open ether the serial port to the hub (simfilename==''), or a simulation file
    Hub = PiSenseSerial.PiSenseHubMonitor()
    try:
        Hub.HubMonitorOpen(simfilename)
    except IOError:
        print simfilename+" not found"
        sys.exit()

    Nodes = PiSenseNode.PsNodeList()

    #open either the raw csv file (storetype = 'csv', or the database (storetype=='db')
    if (storetype == 'csv'):
        PsDb = PiSenseCSV.PiSenseCSV()
        PsDb.Open(Hub)
        PiSenseCSV.CSVTaskStart()
    else:
        PsDb = PiSenseDb.PiSenseDatabase()
        PsDb.Open(Hub)
        PiSenseDb.DbTaskStart ()
        
    PiSenseApi.ApiStart(Nodes, PsDb, Hub)
    
    try:
        while True:
            Hub.HubMonitorTask(Nodes, PsDb)
    except KeyboardInterrupt:
        print "KeyboardInterrupt"
    except:
        print "Main loop exception", sys.exc_info()
        traceback.print_exc()

    #cleanup
    Hub.HubMonitorClose()        
    PiSenseApi.ApiStop()
    PsDb.Close()
    if (storetype == 'csv'):
        PiSenseCSV.CSVTaskStop()
        PiSenseCSV.KillThreads()
    else:
        PiSenseDb.DbTaskStop()


def PsTest():
    Nodes = PiSenseNode.PsNodeList()
    PsDb = PiSenseDb.PiSenseDatabase()
    PsDb.Open()

    #print PsDb.GetNodeDb()
    #PsDb.DumpTable("SDRAW_000001002_1")
    #print PsDb.GetSensorDataDb("000001002", 1, 'year')

    #PsDb.DeleteSummary()
    #tStart = int(time.mktime((2013, 9, 17, 19, 0, 0, 0, 0, 1)))
    #tEnd   = int(time.mktime((2013, 9, 22, 01, 0, 0, 0, 0, 1)))
    #tStart = int(time.mktime((2013, 9, 21, 20, 0, 0, 0, 0, 1)))
    #tEnd   = int(time.mktime((2013, 9, 22, 04, 0, 0, 0, 0, 1)))
    #for t in range(tStart, tEnd, 60):
    #    PsDb.Summarize(t)

    #PsDb.DbTask()    

    print PsDb.GetSensorDataSummary("000001002", 1, "day")

    PsDb.Close()

parser = argparse.ArgumentParser()
parser.add_argument('-d', dest='storetype', action='store',
                    choices=['csv','db'], default='csv',
                    help="data storage type: CSV(default) or Database")
parser.add_argument('-s', dest='simfilename', action='store',
                    default='',
                    help="-s <filename containing simulation data for hub serial port>")
args = parser.parse_args()
PsRun(args.storetype,args.simfilename)
    
#PsTest()
