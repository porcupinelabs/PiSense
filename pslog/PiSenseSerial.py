import serial
import time
import PiSenseNode
import PiSenseDb
import os
import sys
import binascii

SimPkt = " 00 30 30 30 30 30 31 30 30 32 00 FF BE 03 0106 00 04 38 34 2E 31 03 0106 01 05 32 35 2E 31 32 03 0106 02 01 33 03 0106 03 06 31 34 39 2E 30 30 03 0106 04 03 31 2E 31 00\r\n"

OTA_MAX_BLOCK_SIZE = 90
d_status = {
    0x00: 'OTA_SUCCESS_STATUS',
    0x01: 'OTA_CLIENT_READY_STATUS',
    0x02: 'OTA_NETWORK_ERROR_STATUS',
    0x03: 'OTA_CRC_ERROR_STATUS',
    0x04: 'OTA_NO_RESPONSE_STATUS',
    0x05: 'OTA_SESSION_TIMEOUT_STATUS',
    0x06: 'OTA_UPGRADE_STARTED_STATUS',
    0x07: 'OTA_UPGRADE_COMPLETED_STATUS',
    0x10: 'OTA_NO_SPACE_STATUS',
    0x11: 'OTA_HW_FAIL_STATUS',
    0x80: 'APP_UART_STATUS_CONFIRMATION',
    0x81: 'APP_UART_STATUS_PASSED',
    0x82: 'APP_UART_STATUS_UPGRADE_IN_PROGRESS',
    0x83: 'APP_UART_STATUS_NO_UPGRADE_IN_PROGRESS',
    0x84: 'APP_UART_STATUS_UNKNOWN_COMMAND',
    0x85: 'APP_UART_STATUS_MALFORMED_REQUEST',
    0x86: 'APP_UART_STATUS_MALFORMED_COMMAND',
    0x87: 'APP_UART_STATUS_SESSION_TIMEOUT',
}


# Class for monitoring the PiSense Hub which is connected to Raspberry Pi via the serial port
class PiSenseHubMonitor:
    def __init__(self):
        self.ser = None
        self.even = True
        self.rxByte = 0
        self.rxPacket = []
        self.rxMsgPacket = []
        self.rxMsgPacketReady = False
        self.rxOtaPacket = []
        self.rxOtaPacketReady = False
        self.simfile=None
        self.simlist=None
        self.simsize=0
        self.simidx=0

    # Opens the serial port on Raspberry Pi and Windows
    def HubMonitorOpen(self,simfilename):
        if (simfilename != ''):
            self.simfile = open(simfilename,'r')
            self.simlist=self.simfile.readlines()
            self.simsize=len(self.simlist)
            print 'sim file lines: ' + str(self.simsize)
        else:    
            if os.name == 'nt':
                PortName = 'COM3'
            else:
                PortName = '/dev/ttyAMA0'
            self.ser = serial.Serial(PortName, 38400, timeout=0.1)
            self.ser.flushInput()
            self.ser.flushOutput()
            Command = '\nl\nl\n'
            self.ser.write(bytearray(Command, "UTF-8"))  # Enter listen mode
            #Line = self.ser.readline()
            print "Serial port " + PortName + " openned"

    # Closes the serial port
    def HubMonitorClose(self):
        #Command = '\x1b'
        #ser.write(bytearray(Command, "UTF-8"))  # Exit from listen mode
        if (not self.simfile == None):
            print self.simfile.name + ' closing'
            self.simfile.close()
        else:
            self.ser.close()
            print "Serial port closed"

    # Called continuously from the main loop
    def HubMonitorTask(self, Nodes, PsDb):
        # Blocking read of serial port.  Returns after the timeout period (100ms) with whatever data
        # has been received from the serial port.  Data is in ASCII hex: 12 23 56 AA FF.  As it's
        # received we will convert it to a list if bytes until we get a carriage return at the end
        # of the packet.
        if (not self.simfile==None):
            buf = self.simlist[self.simidx]
            self.simidx=self.simidx+1
            if(self.simidx>=self.simsize):
                self.simidx=0 #wrap
            time.sleep(1)
        else:     
            buf = self.ser.read(1000)
        #buf = SimPkt

        #if len(buf):
            #print buf

        for c in buf:
            if c >= b'0' and c <= b'9':
                if self.even:
                    self.rxByte = (ord(c) - 0x30) << 4
                    self.even = False
                else:
                    self.rxByte |= (ord(c) - 0x30)
                    self.even = True
                    self.rxPacket.append(self.rxByte)
            elif c >= b'A' and c <= b'F':
                if self.even:
                    self.rxByte = (ord(c) - ord('A') + 0x0A) << 4
                    self.even = False
                else:
                    self.rxByte |= (ord(c) - ord('A') + 0x0A)
                    self.even = True
                    self.rxPacket.append(self.rxByte)
            elif c == b'\n':
                # Packets from the PiSense hub are terminted with a carriage return, we have
                # a packet now, so go process it.
                if len(self.rxPacket) > 0:
                    self.ProcessRxPacket(Nodes, PsDb)
                self.rxPacket = []
                self.even = True
                self.rxByte = 0

    def ProcessRxPacket(self, Nodes, PsDb):
        now = int(round(time.time()))
        endpoint = self.rxPacket[0]
        if endpoint == 1:
            self.rxMsgPacket = self.rxPacket
            self.rxMsgPacketReady = True
            return
        elif endpoint == 3:
            self.rxOtaPacket = self.rxPacket
            self.rxOtaPacketReady = True
            return
        if len(self.rxPacket) < 12: # Minimum valid packet length
            return
        serNum = ""
        for c in self.rxPacket[1:11]:
            if c >= 0x30 and c <= 0x39:
                serNum += chr(c)
            elif c >= 0x41 and c <= 0x46:
                serNum += chr(c)
        if len(serNum) < 8:     # Serial number must have at least 8 hex digits
            return

        lqi = self.rxPacket[11]
        rssi = self.rxPacket[12]
        #print endpoint, serNum, lqi, rssi, now

        msgBuf = self.rxPacket[13:]
        msgOffset = 0
        while msgOffset < len(msgBuf):
            if msgBuf[msgOffset] != 3: #MSGTYPE_REPORT
                break
            msg = msgBuf[msgOffset:msgOffset+5]
            if len(msg) != 5:
                return          # Malformed message (don't trust anything else in the packet)
            msgType = msg[0]
            attribute = (msg[1] << 8) + msg[2]
            instance = msg[3]
            payloadSize = msg[4]

            msgPayload = msgBuf[msgOffset+5:msgOffset+5+payloadSize]
            value = ""
            for c in msgPayload:
                value += chr(c)

            #print msgType, attribute, instance, payloadSize, value
            Nodes.ProcessReport(PsDb, serNum, instance, value, now, lqi, rssi)
            msgOffset += 5 + payloadSize

    def GetAttributeSingleTry(self, serNum, attrib, inst):
        command = "g " + serNum + " " + attrib + " " + inst + "\n"
        #print bytearray(command, "UTF-8")
        self.ser.write(bytearray(command, "UTF-8"))
        self.rxMsgPacketReady = False
        timeOutCount = 200 # in 100ms units, hub times out after 15 sec, so this should never really happen
        while self.rxMsgPacketReady == False:
            time.sleep(0.1)
            timeOutCount -= 1
            if timeOutCount <= 0:
                print "Timeout in GetAttribute"
                return [0]
        return self.rxMsgPacket

    def GetAttributeStringArg(self, serNum, attrib, inst):  # Called from PsApi.py (already have args as strings)
        print serNum, attrib, inst
        retryCount = 5
        while retryCount > 0:
            pkt = self.GetAttributeSingleTry(serNum, attrib, inst)
            if len(pkt) > 1:
                return pkt
            print "GetAttribute retrying"
            retryCount -= 1
        print "GetAttribute retries exhausted"
        return [0]

    def GetAttribute(self, serNum, attrib, inst):   # Takes args as numbers
        return self.GetAttributeStringArg(serNum, '{:02x}'.format(attrib), '{:02x}'.format(inst))

    def otaRecv(self, expect = None):
        self.rxOtaPacketReady = False
        timeOutCount = 8000 # in 10ms units
        while self.rxOtaPacketReady == False:
            time.sleep(0.01)
            timeOutCount -= 1
            if timeOutCount <= 0:
                print "Timeout in NodeFwUpdate"
                return False
        if len(self.rxOtaPacket) < 2:
            print "Response too short"
            return False
        status = self.rxOtaPacket[1]
        if status in d_status:
            if d_status[status] != expect:
                print 'Error: OTA unexpected status (%s)' % d_status[status]
                return False
        else:
            print 'Error: OTA unexpected status (UNKNOWN_0x%02x)' % status
            return False
        return True

    def NodeFwUpdate(self, serNum, fw):
        print 'NodeFwUpdate'

        try:
            models = fw["models"]
            hwVersions = fw["hwVersions"]
            fwVersion = fw["fwVersion"]
            filesize = fw["fwSize"]
            heximg = fw["image"]
        except KeyError:
            print "Bad parameter"
            return [1]

        print '  Serial number    : %s' % serNum
        print '  Firmware size    : %d bytes' % filesize
        print '  Models           : %s' % models
        print '  Hardware Versions: %s' % hwVersions
        print '  Firmware Version : %s' % fwVersion

        command = "us " + serNum + " " + format(filesize, 'x') + "\n"
        self.ser.write(command)
        status = self.otaRecv('OTA_CLIENT_READY_STATUS')
        if not status:
            return [2]
        print 'Firmware update started'

        remaining = filesize
        while remaining > 0:
            if remaining > OTA_MAX_BLOCK_SIZE:
                size = OTA_MAX_BLOCK_SIZE
            else:
                size = remaining
            remaining -= size
            block = heximg[:2*size]
            heximg = heximg[2*size:]

            command = "ub " + block + '\n'
            self.ser.write(command)
            if remaining > 0:
                sys.stdout.write('.')
                status = self.otaRecv('OTA_CLIENT_READY_STATUS')
            else:
                sys.stdout.write('*')
                status = self.otaRecv('OTA_UPGRADE_COMPLETED_STATUS')
            sys.stdout.flush()
            if not status:
                return [3]

        print '\nFirmware update complete'
        return [0]


