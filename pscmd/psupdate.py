import argparse
import sys
import os
import time
import json
import psapi
import time
import zipfile
from PiSenseDefs import *


def NodeFirmwareUpdate(serNum, filename, zipfilename):
    try:
        zip = zipfile.ZipFile(filename)
        x = zip.getinfo(zipfilename)
        filesize = x.file_size
        f = zip.open(zipfilename)
        img = f.read()
        f.close()
    except:
        print "Error reading file"
        return 1

    header = img[:256]
    filesize -= 256
    fields = header.split('\0')
    if len(fields) < 4:
        print "Invalid firmware file"
        return 2
    signature = fields[0]
    if not signature == "[->>PiSense<<-]":
        print "Signature not found in firmware file"
        return 3

    models = fields[1]
    hwVersions = fields[2]
    fwVersion = fields[3]

    print '    Firmware         : %s' % filename
    print '    Firmware size    : %d bytes' % filesize
    print '    Models           : %s' % models
    print '    Hardware Versions: %s' % hwVersions
    print '    Firmware Version : %s' % fwVersion

    heximg = img[256:].encode("hex")
    fw = {"models":models, "hwVersions":hwVersions, "fwVersion":fwVersion, "fwSize":filesize, "image":heximg }
    cmd = {'cmd':'nodefwupdate', 'sernum':serNum, 'fw':fw}
    pkt = psapi.ExecCommand(cmd)
    try:
        return pkt[0]
    except TypeError:
        return 4


def GetAttr(serNum, attr, inst):
    cmd = {'cmd':'getattrib', 'sernum':serNum, 'attrib':'{:02x}'.format(attr), 'inst':'{:02x}'.format(inst)}
    pkt = psapi.ExecCommand(cmd)
    result = EvalPacket(pkt)
    #if result == 'Error':
    #    print "Error communicating with node"
    #    sys.exit(2)
    return result


def GetNodeInfo(serNum):
    nodeInfo = {'serNum':serNum, 'manufacturer':'', 'model':'', 'hwVersion':'', 'fwVersion':''}
    nodeInfo['manufacturer'] = GetAttr(serNum, ATTRIB_MANUFACTURER, 0)
    if nodeInfo['manufacturer'] == 'Error':
        nodeInfo['manufacturer'] = 'Could not find node'
    else:
        nodeInfo['model'] = GetAttr(serNum, ATTRIB_MODEL, 0)
        nodeInfo['hwVersion'] = GetAttr(serNum, ATTRIB_HW_VERSION, 0)
        nodeInfo['fwVersion'] = GetAttr(serNum, ATTRIB_FW_VERSION, 0)
    return nodeInfo


def PrintNodeInfo(label, serNum):
    print label
    print "    Waiting for node response..."
    nodeInfo = GetNodeInfo(serNum)
    print "    Manufacturer:  ", nodeInfo['manufacturer']
    print "    Model:         ", nodeInfo['model']
    print "    HW Version:    ", nodeInfo['hwVersion']
    print "    FW Version:    ", nodeInfo['fwVersion']
    return nodeInfo['fwVersion']


def fwUpdate (nodeInfo, filename):
    print "PiSense Firmware Update for node:", nodeInfo['serNum']

    PrintNodeInfo("  Node attributes prior to update:", nodeInfo['serNum'])

    print ("  Updating node firmware (may take several minutes)")
    status = NodeFirmwareUpdate(nodeInfo['serNum'], filename, nodeInfo['filename'])

    if not status == 0:
        print "  Update failed with status of ", status
        nodeInfo['updateStatus'] = 'Failed'
        nodeInfo['newFwVersion'] = 'n/a'
        return 1

    print "  File sent to node"
    print "  Waiting for node reboot"
    time.sleep(15)

    nodeInfo['newFwVersion'] = PrintNodeInfo("  Node attributes after update:", nodeInfo['serNum'])
    nodeInfo['updateStatus'] = 'Success'
    return 0


def getFwFileInfo(filename):
    result = []
    try:
        zip = zipfile.ZipFile(filename)
        for zipfilename in zip.namelist():
            entry = {}
            f = zip.open(zipfilename)
            header = f.read(256)
            f.close()
            fields = header.split('\0')
            if len(fields) >= 4:
                signature = fields[0]
                if signature == "[->>PiSense<<-]":
                    entry['models'] = fields[1]
                    entry['hwVersions'] = fields[2]
                    entry['fwVersion'] = fields[3]
                    entry['filename'] = zipfilename
                    x = zip.getinfo(zipfilename)
                    entry['filesize'] = x.file_size
                    result.append(entry)
    except IOError:
        print "Could not open archive", filename

    return result


# Main-----------------------------------------

parser = argparse.ArgumentParser(description='PiSense node firmware update utility')
parser.add_argument("-u", "--update", help="Do firmware update (default is to just display)", action="store_true")
parser.add_argument("-f", "--force", help="Force update even for node(s) that are down rev", action="store_true")
parser.add_argument("-s", "--sernum", help="Serial number of one node to update (default is all that are down rev)")
parser.add_argument("-a", "--archive", help="Specifiy a firmware archive to use (default is to use latest pisense-fw-yyyy-mm-dd.zip file)")
args = parser.parse_args()

# Find the latest firmware archive file whose filename looks like "pisense-fw-yyyy-mm-dd.zip" and 
# then extract and display the details of the firmware images contained in that archive.

if args.archive:
    print "Using archive:", args.archive
    latestFilename = args.archive
else:
    files = [f for f in os.listdir(".") if f[:10]=="pisense-fw" and f[-4:]==".zip"]
    latestFilename = ""
    for filename in files:
        if filename > latestFilename:
            latestFilename = filename
    print 'Contents of latest firmware archive:', latestFilename

fwList = getFwFileInfo(latestFilename)
if len(fwList) == 0:
    print "No firmware images available"
else:
    print 'Filename        Models                         HW Ver     FW Ver    Size'
    print '--------------- ------------------------------ ---------- -------- ------'
    for fw in fwList:
        print '{0:15s} {1:30s} {2:10s} {3:8s} {4:6d}'.format(fw['filename'], fw['models'], fw['hwVersions'], fw['fwVersion'], fw['filesize'])

# Determine a list of nodes, query attributes of each node, and determine which nodes need a firmware update

print
if args.sernum:
    print "Node", args.sernum
    nodelist = [args.sernum]
else:
    hubSerNum = GetAttr('00000000', ATTRIB_SERIAL_NUMBER, 0)
    nodelist = [hubSerNum]
    files = [f for f in os.listdir("../pslog/data") if f[-4:]==".csv"]
    for filename in files:
        if filename[9:16] == 'sensors':
            nodelist.append(filename[:8])
    print "All nodes:", len(nodelist), "node(s) present in log data (../pslog/data/)"

nodeInfoList = []
print '                                 Current   Latest'
print 'Serial # Model           HW Ver  FW Ver    FW Ver   Update?'
print '-------- --------------  ------  --------  -------- -------'
for serNum in nodelist:
    sys.stdout.write(serNum)
    sys.stdout.flush()
    nodeInfo = GetNodeInfo(serNum)
    nodeInfo['latestFwVersion'] = 'Unknown'
    for fw in fwList:
        if nodeInfo['model'] in fw['models']:
            if nodeInfo['hwVersion'] in fw['hwVersions']:
                nodeInfo['latestFwVersion'] = fw['fwVersion']
                nodeInfo['filename'] = fw['filename']
                break
    nodeInfo['updateNeeded'] = 'N'
    if not nodeInfo['fwVersion'] == '':      # This catches the case where GetNodeInfo failed
        if args.force:
            nodeInfo['updateNeeded'] = 'Y'
        else:
            if nodeInfo['fwVersion'] < nodeInfo['latestFwVersion']:
                nodeInfo['updateNeeded'] = 'Y'
    nodeInfoList.append(nodeInfo)
    print ' {0:15s} {1:6s}  {2:8s}  {3:8s}    {4:1s}'.format(nodeInfo['model'], nodeInfo['hwVersion'], nodeInfo['fwVersion'], nodeInfo['latestFwVersion'], nodeInfo['updateNeeded'])

# Now do all of the firmware updates that are requested / needed

print
if not args.update:
    print "Display only (no update)"
    sys.exit(0)
else:
    if args.force:
        print "Starting forced updates"
    else:
        print "Starting updates"

nodesToUpdateList = list(x for x in nodeInfoList if x['updateNeeded'] == 'Y')
if len(nodesToUpdateList) == 0:
    print "No nodes to update"
    sys.exit(0)

for nodeInfo in nodesToUpdateList:
    fwUpdate(nodeInfo, latestFilename)

# Display a summary of the updates that were attempted / done

print
print "Summary of updates"
print '                                 Old       New'
print 'Serial # Model           HW Ver  FW Ver    FW Ver   Update Status'
print '-------- --------------  ------  --------  -------- -------------'
for nodeInfo in nodesToUpdateList:
    print '{0:8s} {1:15s} {2:6s}  {3:8s}  {4:8s} {5:14s}'.format(nodeInfo['serNum'], nodeInfo['model'], nodeInfo['hwVersion'], nodeInfo['fwVersion'], nodeInfo['newFwVersion'], nodeInfo['updateStatus'])

print "Done"
sys.exit(0)