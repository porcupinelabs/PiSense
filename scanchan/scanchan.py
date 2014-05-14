import serial
import os
import time
import sys

# Class for monitoring the PiSense Hub which is connected to Raspberry Pi via the serial port
class PiSenseHubMonitor:
    def __init__(self):
        self.ser = None
        self.even = True
        self.rxByte = 0
        self.rxPacket = []
        self.rxMsgPacket = []
        self.rxMsgPacketReady = False
        self.SampleCount = 0;

    # Opens the serial port on Raspberry Pi and Windows
    def HubMonitorOpen(self):
        if os.name == 'nt':
            PortName = 'COM3'
        else:
            PortName = '/dev/ttyAMA0'
        self.ser = serial.Serial(PortName, 38400, timeout=0.1)
        self.ser.flushInput()
        self.ser.flushOutput()
        Command = '\ns 1\n' # Turn on scanning mode
        self.ser.write(bytearray(Command, "UTF-8"))  # Enter listen mode
        print "Serial port " + PortName + " openned"

    # Closes the serial port
    def HubMonitorClose(self):
        Command = '\ns 0\n' # Turn off scanning mode
        self.ser.write(bytearray(Command, "UTF-8"))  # Enter listen mode
        time.sleep(1)
        self.ser.close()
        print "Serial port closed"

    # Called continuously from the main loop
    def HubMonitorTask(self):
        # Blocking read of serial port.  Returns after the timeout period (100ms) with whatever data
        # has been received from the serial port.  Data is in ASCII hex: 12 23 56 AA FF.  As it's
        # received we will convert it to a list if bytes until we get a carriage return at the end
        # of the packet.
        buf = self.ser.read(1000)
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
                if len(self.rxPacket) >= 12:
                    # Packets from the PiSense hub are terminted with a carriage return, we have
                    # a packet now, so go process it.
                    self.ProcessRxPacket()
                self.rxPacket = []
                self.even = True
                self.rxByte = 0

    def ProcessRxPacket(self):
        #print self.rxPacket
        if len(self.rxPacket) != 16:
            print "Error"
            return
        for i in range(16):
            ChanList[i] += self.rxPacket[i]
        self.SampleCount += 1
        if (self.SampleCount % 20) == 0:
            sys.stdout.write('.')

ChanList = [0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0]

print "This utility scans all of the available radio channels (1000 iteratations) to determine the"
print "least used channel.  PiSense supports sixteen different channels inthe 2.4GHz band.  The"
print "channels are numbered 11 through 26.  This utility will display the relative amount of"
print "2.4GHz traffic on each channel.  There are many devices that share the 2.4GHz band such"
print "as Wifi, Bluetooth, cordless phones, etc.  Running your PiSense network on a little used"
print "channel will minimize interference and increase network performance."
print " "
print "Openning hub connection"

Hub = PiSenseHubMonitor()
Hub.HubMonitorOpen()

print "Scanning all radio channels"

try:
    while Hub.SampleCount < 1000:
        Hub.HubMonitorTask()
except KeyboardInterrupt:
    print "KeyboardInterrupt"
except:
    print "Main loop exception", sys.exc_info()

print "."
print "Scan complete"

print "Channel   Traffic"
for i in range(16):
    print ("{0:>4} {1:>10}".format(i+11, ChanList[i]))

BestChan = 11 + ChanList.index(min(ChanList))

print "The best channel is:", BestChan

Hub.HubMonitorClose()

