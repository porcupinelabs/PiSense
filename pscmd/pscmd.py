import time
import json
import psapi
from PiSenseDefs import *

def GetAttr(serNum, attr, inst):
    cmd = {'cmd':'getattrib', 'sernum':serNum, 'attrib':'{:02x}'.format(attr), 'inst':'{:02x}'.format(inst)}
    #print cmd
    pkt = psapi.ExecCommand(cmd)

    return EvalPacket(pkt)

def GetAttrCount(serNum):
    return GetAttr(serNum, ATTRIB_ATTRIBUTE_COUNT, 0)

def GetAttrCode(serNum, attrNum):
    return GetAttr(serNum, ATTRIB_ENUM, attrNum)

def GetAttrName(serNum, attrNum):
    return GetAttr(serNum, ATTRIB_NAME, attrNum)

def GetSensorCount(serNum):
    return GetAttr(serNum, ATTRIB_SENSOR_COUNT, 0)

def GetSensorAttribCount(serNum):
    return GetAttr(serNum, ATTRIB_SENSOR_ATTRIB_COUNT, 0)


serNum = '10001007'
#print GetAttr(serNum, ATTRIB_MANUFACTURER, 0), GetAttr(serNum, ATTRIB_MODEL, 0)

attrCount_str = GetAttrCount(serNum)
sensorCount_str = GetSensorCount(serNum)
sensorAttribCount_str = GetSensorAttribCount(serNum)
attrCount= int(attrCount_str)
sensorCount= int(sensorCount_str)
sensorAttribCount= int(sensorAttribCount_str)
print attrCount

for attrNum in range(attrCount-sensorAttribCount):
    attrCode = GetAttrCode(serNum, attrNum)
    if not attrCode == ATTRIB_NULL:
        print attrNum, GetAttrName(serNum, attrNum), ':', GetAttr(serNum, attrCode, 0)
for attrNum in range(sensorAttribCount):
    attrCode = GetAttrCode(serNum, attrNum+attrCount-sensorAttribCount)
    if not attrCode == ATTRIB_NULL:
        name=GetAttrName(serNum, attrNum+attrCount-sensorAttribCount)
        for instance in range(sensorCount):
            print attrNum, name,'(',instance,'):', GetAttr(serNum, attrCode, instance)


