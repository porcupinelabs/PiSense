import serial
import time
import PiSenseNode
import PiSenseDb
import os

SimPkt = " 00 30 30 30 30 30 31 30 30 32 00 FF BE 03 0106 00 04 38 34 2E 31 03 0106 01 05 32 35 2E 31 32 03 0106 02 01 33 03 0106 03 06 31 34 39 2E 30 30 03 0106 04 03 31 2E 31 00\r\n"


# Class for monitoring the PiSense Hub which is connected to Raspberry Pi via the serial port
class PiSenseHubMonitor:
    def __init__(self):
        self.ser = None
        self.even = True
        self.rxByte = 0
        self.rxPacket = []
        self.rxMsgPacket = []
        self.rxMsgPacketReady = False
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
                PortName = 'COM2'
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

    def GetAttribute(self, serNum, attrib, inst):
        print serNum, attrib, inst
        command = "g " + serNum + " " + attrib + " " + inst + "\n"

        #print bytearray(command, "UTF-8")

        self.ser.write(bytearray(command, "UTF-8"))

        self.rxMsgPacketReady = False
        timeOutCount = 800 # in 100ms units
        while self.rxMsgPacketReady == False:
            time.sleep(0.1)
            timeOutCount -= 1
            if timeOutCount <= 0:
                print "Timeout in GetAttribute"
                return [0]
        return self.rxMsgPacket





