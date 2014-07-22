import time
import threading
import csv
import collections #for namedtuple
import Queue
import sys
sys.path.insert(0,'../pscmd')
from PiSenseDefs import *
import PiSenseDefs
import os
import traceback
import ast
import copy

ActiveNodeList=[] #list of node IDs
ActiveSensorList=[] #list of tuples (nodeID, SensorNum)

MinMaxAvgTuple=collections.namedtuple('MinMaxAvgTuple',['inst','min','max','avg','span'])
SensorSummaryTuple=collections.namedtuple('SensorSummaryTuple',['stamp','sensornum','MinMaxAvg'])
NodeRawQueueList=[] #List of Queues, one Queue per Node, with elements SensorSummaryTuples
RawInterval=10
SummaryIntervals=[60,600,3600,3600*24] 
IntervalNodeList=[] #one list per interval - list of NodeQueueLists
IntervalNodeList.append(NodeRawQueueList)
for i in SummaryIntervals :
    NodeSummaryQueueList=[]
    IntervalNodeList.append(NodeSummaryQueueList)
RawNodeDb=[] #build on the fly
NodeDb=[]# may contain virtual sensors
GlobalVSensors=[]
NodeVSensors=[]
ThreadList=[]
EventProc=[]

#threading locks
LockNodeDesc=threading.Lock()
LastDateTime=0

DataDir='data'

class PiSenseCSV:
    def __init__(self):
        self.csvfiles=[] #let this be a list of raw data files
        self.opened=False
        self.columns=[] #next column to write in csvfile
        self.numvalues=[]
        pass

    def Open(self, Hub):
        global DataDir
        try:
            os.mkdir(DataDir)
        except:
            pass #assuming directory is there; add error handling here
        #open nodelist file - 1 line per powerup/reset - lists discovered nodes
        self.NodelistFile=open(DataDir + '/nodelist.csv','w')
        self.NodelistFile.write('\n'+time.asctime())
        self.opened=True
        self.Hub=Hub #used as a handle to the Hub for serial port and sensor command access
        #get global virtual sensor file (sensor postprocessing replacement)
        try:
            f=open('global_vsensors.cfg')
            try:
                s=f.read()
                global GlobalVSensors
                GlobalVSensors=ast.literal_eval(s) #expecting a dictionary indexed by serial number
            except:
                f.close() #list will remain empty, but close the file handle
        except:
            pass #list will remain empty
       #node specific vsensors (handles calibration, for example)
        try:
            f=open('node_vsensors.cfg')
            try:
                s=f.read()
                global NodeVSensors
                NodeVSensors=ast.literal_eval(s) #expecting a dictionary indexed by serial number
            except:
                f.close() #list will remain empty, but close the file handle
        except:
            pass #list will remain empty

        try:
            f=open('event.cfg')
            try:
                s=f.read()
                global EventProc
                EventProc=ast.literal_eval(s) #expecting a dictionary indexed by serial number
            except:
                f.close() #list will remain empty, but close the file handle
        except:
            pass #list will remain empty

    def Close(self):
        self.NodelistFile.close()
        for f in self.csvfiles:
            f.close()
        self.opened=False

    def NodeNew(self, Id):
        print "new node", Id
        # Add node to nodelist file
        self.NodelistFile.write(','+Id)
        # also keep a regular list
        global AcviteNodeList
        ActiveNodeList.append(Id)
        # open the raw data file for this node
        global DataDir
        f = open(DataDir + '/'+ Id+'_raw.csv','a+') #a+  reading allowed
        self.csvfiles.append(f)
        self.columns.append(0)
        self.numvalues.append([])
        # create a raw queue for the Node
        q=Queue.Queue()
        global NodeRawQueueList
        NodeRawQueueList.append(q)
        global IntervalNodeList
        for i in SummaryIntervals:
            q=Queue.Queue()
            IntervalNodeList[SummaryIntervals.index(i)].append(q);
        #keep a sensor list for the nodes
        f=open(DataDir + '/'+ Id+'_sensors.csv','a')
        f.write('\n'+time.asctime())
        f.close()
        #get a description for this node and save the attributes
        newnodethread=NewNodeQueryThread(Id,self.Hub)
        RegisterThread(newnodethread)
        newnodethread.start()

    def SensorNew(self, Id, SensorNum):
        print "new sensor", Id, SensorNum
        #append this sensor to the current line of this node's sensor file
        global DataDir
        f=open(DataDir + '/'+ Id+'_sensors.csv','a')
        f.write(','+str(SensorNum))
        f.close()
        #maintain a sensorlist in memory too
        global ActiveSensorList
        ActiveSensorList.append((Id,SensorNum))
        #also query all the sensor attributes for reporting...
        newsensorthread=NewSensorQueryThread(Id,SensorNum,self.Hub)
        RegisterThread(newsensorthread)
        newsensorthread.start()

    def SensorDataNew(self, Id, SensorNum, Value, DateTime):
        # Add sensor dataset as a line in the csv file
        # id=8byte string, sensornum=one byte, value=string, datetime=epoch secs
        position = ActiveNodeList.index(Id) #position is NODE position/index
        f=self.csvfiles[position]
        global ActiveSensorList
        # added some logic here to keep the csv file aligned in case of missed packets
        expected_column=0
        for sensortuple in ActiveSensorList:
            if sensortuple[0] == Id: #belongs to this node
                if sensortuple[1]==SensorNum:
                    break
                expected_column += 1

        if expected_column > self.columns[position]:
            misalignment = expected_column - self.columns[position]
            for i in range(misalignment):
                for k in range(self.numvalues[position][self.columns[position]+i]):
                    f.write(',')
        elif expected_column == self.columns[position]: #the normal case if all received
            if expected_column == 0:
                f.write('\n')
                f.write(str(DateTime))
        else:
            f.write('\n')
            f.write(str(DateTime))
            misalignment = expected_column
            for i in range(misalignment):
                for k in range(self.numvalues[position][i]):
                    f.write(',')
        f.write(',' + Value)

        self.columns[position]=expected_column+1

        #queue the reading for the summary thread
        templist=Value.split(',')
        #form into list of min,max,avg
        self.numvalues[position].append(len(templist))#this line must assume no missed packets first time through
        if len(templist) == 1:
            templist.append(templist[0])
            templist.append(templist[0])
            templist.append(templist[0]) #just let single value become the min,max,avg
        global RawInterval
        templist.append(RawInterval) #span of a raw reading
        #NodeRawQueueList is IntervalNodeList[0]
        global NodeRawQueueList
        try:
            NodeRawQueueList[position].put(SensorSummaryTuple(DateTime,SensorNum,
                                                          MinMaxAvgTuple(templist[0],templist[1],
                                                                         templist[2],templist[3],templist[4])))
        except:
            print templist

        for event_processor in EventProc:
            #is sensor in trigger list?
            for nodedict in RawNodeDb:
                if nodedict['Id'] == Id:
                    break
            try:
                for sensordict in nodedict['SensorList']:
                    if sensordict['SensorNum'] == SensorNum:
                        if sensordict['Property'] in event_processor['Inputs']:
                            global LastDateTime
                            if (DateTime != LastDateTime):
                                module=__import__(event_processor['Module'])
                                module.event_trigger([],Value, DateTime)
                            LastDateTime=DateTime
            except:
                pass #sensor list may not have been created yet

    def GetNodeDb(self):
        global RawNodeDb
        global NodeDb
        #when all the Node query and Sensor Query threads are done, then RawNodedb is ready
        global ThreadList
        for th in ThreadList:
            if th.is_alive(): #RawNodeDb is locked for modification
                return NodeDb
        #no attribute collection is in progress...
        for rawnodedict in RawNodeDb:
            #is it already in NodeDb?
            copied=False
            for nodedict in NodeDb:
                if nodedict['Id'] == rawnodedict['Id']:
                    copied=True
            if not copied:
                modified_node_dict=copy.deepcopy(rawnodedict)
                senscount=modified_node_dict['SensorCount']
                #virtual sensor replacement
                for vsensor in GlobalVSensors:
                    all_inputs_present_in_raw_node_db = True
                    #find vsensor inputs in raw dictionary
                    for sensorname in vsensor['Inputs']:
                        found=False
                        for sensordict in modified_node_dict['SensorList']:
                            if sensordict['Property'] == sensorname:
                                found=True
                                if (vsensor['Replace'][vsensor['Inputs'].index(sensorname)] == 1):
                                    #delete it...
                                    modified_node_dict['SensorList'].remove(sensordict)
                                    senscount=senscount-1
                        if not found:
                            all_inputs_present_in_raw_node_db = False
                    #add virtual sensors to modified node dictionary's sensor list
                    if (all_inputs_present_in_raw_node_db):
                        vsensordict = {}
                        vsensordict['Id']=modified_node_dict['Id']
                        #by convention, start these at 100.  do not use SensorCount because this
                        #node attribute indicates the number of active sensors, and we don't want to
                        #conflict with one that is disabled
                        vsensordict['SensorNum']=GlobalVSensors.index(vsensor)+100
                        vsensordict['Property']=vsensor['Output']
                        vsensordict['DataType']=10
                        vsensordict['Maximum']=0 #not populated
                        vsensordict['Minimum']=0 #not populated
                        vsensordict['Enable']=1
                        vsensordict['Units']=vsensor['Units']
                        senscount=senscount+1
                        modified_node_dict['SensorCount']=senscount
                        modified_node_dict['SensorList'].append(vsensordict)
                NodeDb.append(modified_node_dict)
        return NodeDb


    def GetHistoryData(self, Id, sensorNum, period, mxa, start, end):
        # period: one of "day", "hour", "10min", "min", if "hour", then return one data value per hour
        # mxa: one, two or three character string
        #        if m is present, then return min values
        #        if x is present, then return max values
        #        if a is present, then return average
        #        examples: "mx" means return min and max values, "a" means just return average values, "mxa" means return all three values
        # start/end: time stamp values in seconds (should already be rounded to a period boundary)
        # return data format: [[timestamp array],[min1,min2,...,minN],[max1,max2,...,maxN],[avg1,avg2,...,avgN]]   omit min, max, or avg inner array as requested by mxa parameter

        mins=[]
        maxes=[]
        avges=[]
        stamps=[]
        results=[]

        #this print is useful debug...
        #print time.time(),':',Id,sensorNum,period,mxa,start,end

        try:
            periods=["min","10min","hour","day"]
            interval_secs = SummaryIntervals[periods.index(period)]
            
            #note: summary files are written to on clock (time of day) boundaries
            #this function will initially assume the requested timestamps fall on those boundaries
            #but will fix it if not
            start_mod = int(start) - (int(start) % interval_secs)
            end_mod = int(end) - (int(end) % interval_secs)
            count=(start_mod - end_mod) + 1 #the number of results to return

            #find sensor position in summary file: note - it is based on last powerup of that node
            global DataDir
            SensorListName = DataDir + '/'+ Id + '_sensors.csv'
            SensorArrayFile=open('../pslog/'+SensorListName,'r')
            SensorReader=csv.reader(SensorArrayFile)
            SensorArray=[]
            for sensorrow in SensorReader:
                SensorArray=sensorrow #gets last line
            try:
                position=SensorArray.index(str(sensorNum))
            except:
                position=None
            SensorArrayFile.close()

            if position == None:
                #virtual sensor?
                node_found=False
                sensor_found=False
                for nodedict in RawNodeDb:
                    if nodedict['Id'] == Id:
                        node_found=True
                        break
                if node_found:
                    #convert sensor index into virtual sensor index
                    vsensor=GlobalVSensors[int(sensorNum)-100] #by convention
                    input_sensor_nums=[]
                    for sensordict in nodedict['SensorList']:
                        if sensordict['Property'] in vsensor['Inputs']:
                            input_sensor_nums.append(sensordict['SensorNum'])
                    if not len(input_sensor_nums) == len(vsensor['Inputs']):
                        return [] #error - didn't locate all necessary inputs to virtual calculation
                    input_results = []
                    for i in input_sensor_nums:
                        temp=self.GetHistoryData(Id, i, period, mxa, start, end) #recursive
                        input_results.append(temp)
                    #keep the timestamps, and the conversion will work on the mins, maxes and avg
                    module=__import__(vsensor['Module'])
                    mxa_count=len(input_results[0])-1#number of lists to build in final result, subtract timestamp list
                    in_count=len(input_results)#number of input params to module
                    vresult=[]
                    vresult.append(input_results[0][0]) #the timestamps
                    for mxa_index in range(mxa_count):#index is really mxa_index+1 to skip timestamp list
                        mxa_list=[]
                        for b in range(len(input_results[0][0])): #derive length from length of timestamp list
                            inparams=[]
                            for a in range(in_count):
                                inparams.append(input_results[a][mxa_index + 1][b])
                            mxa_list.append(module.postprocess(vsensor['Params'],inparams)) #not sure whether m,x, or a but doesn't matter
                        vresult.append(mxa_list)
                    return(vresult)
                else:
                    return []

            #initial implementation will return complete averages for datasets that encompass
            #the entire interval.  Decide later what to do about partial intervals during which the sensor was not
            #reporting the entire time.
            filename = DataDir + '/'+ str(Id)+'_'+str(interval_secs)+'.csv'
            f=open('../pslog/'+filename, 'r')
            r=csv.reader(f)
            for row in r:
                stamp=int(row[0])
                    
                if stamp>=start_mod and stamp<=end_mod and len(row)>position*3:
                        stamps.append(stamp)
                        if 'm' in mxa:
                            mins.append(row[position*3-2])
                        if 'x' in mxa:
                            maxes.append(row[position*3-1])
                        if 'a' in mxa:
                            avges.append(row[position*3])
                     
            f.close()
        except IOError:
            #TODO: clean up any open file handles here
            #print 'exception'
            pass
        
        results.append(stamps)
        if 'm' in mxa:
            results.append(mins)
        if 'x' in mxa:
            results.append(maxes)
        if 'a' in mxa:
            results.append(avges)
        #print results
        return results

    def PropertyToSensorNumber(self,id,property):
        global RawNodeDb
        for node in RawNodeDb:
            if node['Id'] == id:
                for sensor in node['SensorList']:
                    if sensor['Property'] == property:
                        return sensor['SensorNum']

    def DictNumToIdx(self,sensornum,sensorlist):
        for sensor in sensorlist:
            if sensor['sn'] == sensornum:
                return sensorlist.index(sensor)

    def GetSensorCount(self,id):
        global RawNodeDb
        for node in RawNodeDb:
            if node['Id'] == id:
                return node['SensorCount']

    #called from PiSenseNode in response to Dashboard page refresh
    #replace raw sensors with postprocessed results
    def PostProcess(self, result, dbsensor):
        #input to function:
        #  format of result is dictionary with entry sl (sensor list)
        #  {...'sl':[list]}
        #  where list is list of dictionaries
        #  used to get values for raw inputs into post processing
        #output:
        #  populate dbsensor (of format of a list entry for sensor lists in NodeDb)
        #  with new elements 'LastValue'(calculated) and 'LastDateTime'
        if result['id'] in NodeVSensors:
            #this node has specific virtual sensors
            vsensors=NodeVSensors[result['id']]
            for vsensor in vsensors:
                if vsensor['Output']==dbsensor['Property']:
                    module=__import__(vsensor['Module'])
                    ins=[]
                    for input in vsensor['Inputs']:
                        sn = self.PropertyToSensorNumber(result['id'],input)
                        list_idx = self.DictNumToIdx(sn,result['sl'])
                        sensval= result['sl'][list_idx]['lv']
                        ins.append(sensval)
                    outval=module.postprocess(vsensor['Params'],ins)
                    outprop=vsensor['Output']
                    sn = self.PropertyToSensorNumber(result['id'],outprop)
                    list_idx = self.DictNumToIdx(sn,result['sl'])
                    dbsensor['LastValue']=outval
                    dbsensor['LastDateTime']=result['sl'][list_idx]['dt']

        #now the global virtual sensors
        senscount=self.GetSensorCount(id)
        #virtual sensor replacement
        for vsensor in GlobalVSensors:
            if vsensor['Output']==dbsensor['Property']:
                dt = result['dt']
                module=__import__(vsensor['Module'])
                ins=[]
                for sensorname in vsensor['Inputs']:
                    sn = self.PropertyToSensorNumber(result['id'],sensorname)
                    list_idx = self.DictNumToIdx(sn,result['sl'])
                    if list_idx == None:
                        pass #error handling goes here
                    sensval= result['sl'][list_idx]['lv']
                    ins.append(sensval)
                    dt=result['sl'][list_idx]['dt']

                outval=module.postprocess(vsensor['Params'],ins)
                dbsensor['LastValue'] = outval
                dbsensor['LastDateTime']= dt
                break
        return

    def GetSensorDataSummary(self, Id, SensorNum, TimePeriod):
        pass
        
    def DeleteSummary(self):
        pass

runDbTask = False

def CSVTaskStart():
    global runDbTask
    runDbTask = True
    global DbTaskThread
    DbTaskThread = PsCSVThread()
    DbTaskThread.start()

def CSVTaskStop():
    global runDbTask
    runDbTask = False
    global DbTaskThread
    print "Waiting for DbTaskThread to stop..."
    DbTaskThread.join()
    print "Stopped"

#the summary thread only needs to deal with active sensors so used shared globals for the lists
class PsCSVThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        #TODO: build queues from existing nonvolatile data
        
    def run(self):
        now = int(round(time.time()))
        global SummaryIntervals
        interval = SummaryIntervals[0] 
        self.NextSummary = now - (now % interval) + interval #wake up on time of day boundaries
        global runDbTask
        while runDbTask:
            time.sleep(1)
            now = int(round(time.time()))
            if now >= self.NextSummary:
                self.NextSummary = now - (now % interval) + interval
                print time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.localtime(now))
                global ActiveNodeList
                for node in ActiveNodeList:
                    self.SummarizeNode(now,node)

    def SummarizeNode(self, SumTime, Id):
        #SumTime is an integer timestamp (epoch seconds)
        EndTime = SumTime - (SumTime % SummaryIntervals[0])  # EndTime = last intervalboundary
        t = time.localtime(SumTime)     # t = struct with y,m,d,h,m,s fields

        for i in SummaryIntervals:
            if EndTime % i == 0: #will be true in this loop for SummaryIntervals[0], at least
                intervalindex=SummaryIntervals.index(i)
                nodequeuelist=IntervalNodeList[intervalindex] #input queue
                position = ActiveNodeList.index(Id)
                summaryqueue=nodequeuelist[position]
                queueentries=[]
                while not summaryqueue.empty(): #queue has data for multiple sensors
                    queueentries.append(summaryqueue.get(False))
                newfileline=str(EndTime)
                global ActiveSensorList
                fully_built = True
                for sensor in ActiveSensorList:
                    if sensor[0]==Id: #belongs to this node 
                        sensornum=sensor[1]
                        minlist=[]
                        maxlist=[]
                        avgsum=0
                        spansum=0
                        for summary in queueentries:
                            if summary.sensornum == sensornum:
                                entry=summary.MinMaxAvg
                                minlist.append(float(entry.min))
                                maxlist.append(float(entry.max))
                                avgsum = avgsum + float(entry.avg) * float(entry.span)
                                spansum = spansum + entry.span
                        if minlist and maxlist and spansum:
                            newmin=min(minlist)
                            newmax=max(maxlist)
                            newavg=avgsum/spansum
                            newtuple1=MinMaxAvgTuple(float(entry.inst), newmin,newmax,newavg,spansum)
                            newtuple2=SensorSummaryTuple(EndTime,sensornum,newtuple1)
                            #1)queue up summary for higher interal summary
                            outputqueueindex=intervalindex+1
                            if outputqueueindex < len(SummaryIntervals): #last summary interval does not use an output queue
                                nodequeuelist=IntervalNodeList[outputqueueindex]
                                outqueue=nodequeuelist[position]
                                outqueue.put(newtuple2)        
                            #2) build line for this interval's summary file
                            newfileline=newfileline+','+str(newmin)+','+str(newmax)+','+str(newavg)
                            #queues may be initially empty, so only write a line if there is data to avoid the empties
                            #put summarized line in interval file
                        else:
                            #attempt to avoid empty lines
                            fully_built = False
                if fully_built:
                    f=open(DataDir + '/'+ Id+'_'+str(i)+'.csv','a')
                    f.write(newfileline+'\n')
                    f.close()

class NewSensorQueryThread(threading.Thread):
    def __init__(self,Id,SensorNum,Hub):
        threading.Thread.__init__(self)
        self.Id=Id
        self.SensorNum=SensorNum
        self.Hub=Hub

    def run(self):
        try:
            global RawNodeDb
            global LockNodeDesc
            LockNodeDesc.acquire(True)

            for node_dict in RawNodeDb:
                if node_dict['Id'] == self.Id:
                    try:
                        global DataDir
                        f=open(DataDir + '/'+ str(self.Id) + '_'+ str(self.SensorNum) + '.dat')
                        try:
                            s=f.read()
                            d=ast.literal_eval(s)
                            node_dict['SensorList'].append(d)
                        except:
                            f.close()
                    except:
                        print '-------could not find:' + str(self.Id) + '_'+ str(self.SensorNum) + '.dat, gathering data...'
                        #gather the data over the air
                        attrCount=node_dict['AttribCount']
                        sensorAttribCount=node_dict['SensorAttributes']
                        sensorAttrInfo=node_dict['sensorAttrInfo']
                        sens_dict={'Id':self.Id,'SensorNum':self.SensorNum}
                        try:
                            for attrNum in range(sensorAttribCount):
                                attrCode = sensorAttrInfo[attrNum]['attrCode']
                                if not attrCode == ATTRIB_NULL:
                                    name = sensorAttrInfo[attrNum]['name']
                                    pkt = self.Hub.GetAttribute(str(self.Id), attrCode, self.SensorNum)
                                    val=EvalPacket(pkt)
                                    sens_dict[name]=val
                                    print 'sensor attr - ',name,':',val
                            node_dict['SensorList'].append(sens_dict)
                            f=open(DataDir + '/'+ str(self.Id)+'_'+str(self.SensorNum)+'.dat','w')
                            f.write(str(sens_dict))
                            f.close()
                        except:
                            #some problem occurred trying to gather attributes from the sensor
                            print 'problem gathering sensor attributes'
                            sens_dict = {'Id':self.Id,'SensorNum':self.SensorNum,'Property': 'Unknown', 'DataType': 10, 'Maximum': '85.0', 'Minimum': '-40.0', 'Enable': 1, 'Units': '?'}
                            node_dict['SensorList'].append(sens_dict)
        except:
            traceback.print_exc()
            time.sleep(1.0)
            os.kill(os.getpid(), 15)
        finally:
            LockNodeDesc.release()


class NewNodeQueryThread(threading.Thread):
    def __init__(self,Id,Hub):
        threading.Thread.__init__(self)
        self.Id=Id
        self.Hub=Hub

    def run(self):
        try:
            global RawNodeDb
            global LockNodeDesc
            LockNodeDesc.acquire(True)

            try:
                global DataDir
                f=open(DataDir + '/'+ str(self.Id) + '.dat')
                try:
                    s=f.read()
                    d=ast.literal_eval(s)
                    RawNodeDb.append(d)
                except:
                    f.close()
            except:
                try:
                    entry={'Id':self.Id,'SensorList':[],'Nickname':str(self.Id)}
                    #gather the data over the air
                    pkt=self.Hub.GetAttribute(str(self.Id),ATTRIB_ATTRIBUTE_COUNT,0)
                    attrCount = int(EvalPacket(pkt))
                    pkt=self.Hub.GetAttribute(str(self.Id),ATTRIB_SENSOR_ATTRIB_COUNT,0)
                    sensorAttribCount = int(EvalPacket(pkt))
                    for attrNum in range(attrCount-sensorAttribCount):
                        pkt=self.Hub.GetAttribute(str(self.Id),ATTRIB_ENUM,attrNum)
                        attrCode = int(EvalPacket(pkt))
                        if not attrCode == ATTRIB_NULL:
                            pkt = self.Hub.GetAttribute(str(self.Id),ATTRIB_NAME,attrNum)
                            name=EvalPacket(pkt)
                            pkt = self.Hub.GetAttribute(str(self.Id),attrCode,0)
                            val=EvalPacket(pkt)
                            entry[name]=val
                            print 'node attr - ',name,':',val
                    sensorAttrInfo = []
                    for attrNum in range(sensorAttribCount):
                        pkt = self.Hub.GetAttribute(str(self.Id),ATTRIB_ENUM,attrNum+attrCount-sensorAttribCount)
                        attrCode = EvalPacket(pkt)
                        if not attrCode == ATTRIB_NULL:
                            pkt = self.Hub.GetAttribute(str(self.Id),ATTRIB_NAME,attrNum+attrCount-sensorAttribCount)
                            name=EvalPacket(pkt)
                            sensorAttrInfo.append({'attrCode':attrCode, 'name':name})
                    entry['sensorAttrInfo'] = sensorAttrInfo
                    RawNodeDb.append(entry)

                    f=open(DataDir + '/'+ str(self.Id)+'.dat','w')
                    f.write(str(entry))#TODO: there may be a nicer way to print this
                    f.close()
                except:
                    #some problem gathering attributes
                    print 'problem gathering node attributes'
                    # Instead of adding placeholder data to RawNodeDb, just continue.  The node query will get retried after a reboot.
                    #entry={'Id':self.Id,'SensorList':[],'Nickname':str(self.Id),'HardwareVersion': '?', 'SerialNumber': '?', 'SensorCount': 1, 'TxPower': 13, 'AttribCount': 1, 'SensorAttributes': 6, 'RxSignalStrength': 100, 'Model': '?', 'FirmwareVersion': '?', 'Manufacturer': 'Porcupine', 'sensorAttrInfo':[]}
                    #RawNodeDb.append(entry)
        except:
            traceback.print_exc()
            time.sleep(1.0)
            os.kill(os.getpid(), 15)
        finally:
            LockNodeDesc.release()



def RegisterThread(th):
    global ThreadList
    ThreadList.append(th)

def KillThreads():
    global ThreadList
    print 'stopping other threads...'
    for th in ThreadList:
        th.join(1) #with a timeout
        # #workaround. pslog modified so this is last.
        #hammer the entire process if the thread won't stop
        if th.is_alive():
            print '....threads not stopping - killing process'
            time.sleep(1)
            os.kill(os.getpid(), 15)
    print '....stopped'
