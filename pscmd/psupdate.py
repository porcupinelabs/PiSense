import sys
import os
import time
import json
import psapi
import time
from PiSenseDefs import *


def NodeFirmwareUpdate(serNum, filename):
    cmd = {'cmd':'nodefwupdate', 'sernum':serNum, 'filename':filename}
    pkt = psapi.ExecCommand(cmd)
    return pkt[0]


def GetAttr(serNum, attr, inst):
    cmd = {'cmd':'getattrib', 'sernum':serNum, 'attrib':'{:02x}'.format(attr), 'inst':'{:02x}'.format(inst)}
    pkt = psapi.ExecCommand(cmd)
    result = EvalPacket(pkt)
    if result == 'Error':
        print "Error communicating with node"
        sys.exit(2)
    return result


def PrintSensorInfo(label, serNum):
    print label
    print "    Waiting for node response..."

    mfg = GetAttr(serNum, ATTRIB_MANUFACTURER, 0)
    model = GetAttr(serNum, ATTRIB_MODEL, 0)
    hwver = GetAttr(serNum, ATTRIB_HW_VERSION, 0)
    fwver = GetAttr(serNum, ATTRIB_FW_VERSION, 0)

    print "    Serial Number: ", serNum
    print "    Manufacturer:  ", mfg
    print "    Model:         ", model
    print "    HW Version:    ", hwver
    print "    FW Version:    ", fwver
    return



def fwUpdate (serNum, filename):
    print "PiSense Firmware Update"
    PrintSensorInfo("  Node prior to update:", serNum)

    print ("  Updating node firmware (may take several minutes)")
    status = NodeFirmwareUpdate(serNum, filename)

    if not status == 0:
        print "  Update failed with status of ", status
        return 1

    print "  File sent to node"
    print "  Waiting for node reboot"
    time.sleep(10)
    PrintSensorInfo("  Node after update:", serNum)
    return 0


# Main-----------------------------------------

if len(sys.argv) < 3:
    print "Usage: psupdate <serialNum> <filename>"
    print "        Note: filename must be an absolute path (not relative)"
    sys.exit(2)

serNum = sys.argv[1]
if (len(serNum) < 4) or (len(serNum) > 8):
    print "Error: serialNum must be 4 - 8 digits"
    sys.exit(3)

filename = sys.argv[2]
try:
    filesize = os.path.getsize(filename)
except OSError, msg:
    print "Error:", msg
    sys.exit(4)

if (filesize > 0x20000):
    print "Error: file is too big"
    sys.exit(5)

status = fwUpdate(serNum, filename)
sys.exit(status)
