import time
from datetime import datetime
import thread
import socket
import json
from struct import *

import  wx
import  wx.lib.newevent

# This creates a new Event class and a EVT binder function
(UpdateDataEvent, EVT_UPDATE_DATA) = wx.lib.newevent.NewEvent()

HOST = 'localhost'
PORT = 59747

#---------------------------------------------------------------------------

class PsMonThread:
    def __init__(self, win):
        self.win = win
        self.host = HOST

    def Start(self):
        self.keepGoing = self.running = True
        thread.start_new_thread(self.Run, ())

    def Stop(self):
        self.keepGoing = False

    def IsRunning(self):
        return self.running

    def SetHost(self, host):
        self.host = host

    def Run(self):
        while self.keepGoing:
            d = self.ExecCmd({'cmd':'getstats'})
            if not d == None:
                evt = UpdateDataEvent(value = d)
                wx.PostEvent(self.win, evt)
            else:
                evt = UpdateDataEvent(value = {})
                wx.PostEvent(self.win, evt)
            time.sleep(5)
        self.running = False

    def ExecCmd(self, req):
        try:
            # Open a socket connection to the PiSense host
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((self.host, PORT))

            # Convert the request to json and send it
            jsonStr = json.dumps(req)
            jsonLenStr = pack('L', len(jsonStr))
            s.send(jsonLenStr)
            s.send(jsonStr)

            # Read 4 bytes, they contain a long uint indicating the size of the response
            jsonLenStr = s.recv(4)
            jsonLenTup = unpack('L', jsonLenStr)
            jsonLen = jsonLenTup[0]

            # Read from the socket until all bytes have been received, then close the socket
            jsonStr = ''
            while len(jsonStr) < jsonLen:
                chunk = s.recv(4096)
                if not chunk: break
                jsonStr = jsonStr + chunk
            s.close()
        except socket.error:
            return None

        # Convert the response from json to a dictionary
        try:
            resp = json.loads(jsonStr)
        except ValueError:
            resp = {'res':'error'}

        # If the response result is 'ok', then return the 'ret' object
        ret = None
        try:
            if resp['res'] == 'ok':
                ret = resp['ret']
        except KeyError:
            pass
        return ret


#----------------------------------------------------------------------

class MainFrame(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, "PiSense Monitor", size=(480,300))
        self.panel = MainPanel(self)
        self.Bind(EVT_UPDATE_DATA, self.OnUpdate)
        self.thread = PsMonThread(self)
        self.thread.Start()
        self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)

    def OnUpdate(self, evt):
        self.panel.RefreshData(evt.value)

    def OnCloseWindow(self, evt):
        self.panel.logger.AppendText('Closing connection...')
        #busy = wx.BusyInfo("One moment please, closing connection...")
        wx.Yield()
        self.thread.Stop()
        while self.thread.IsRunning():
            time.sleep(0.1)
        self.panel.logger.AppendText('Done')
        wx.Yield()
        self.Destroy()

#----------------------------------------------------------------------

class MainPanel(wx.Panel):
    def quickText(self, sizer, row, labelTxt, dataTxt):
        label = wx.StaticText(self, label=labelTxt)
        sizer.Add(label, pos=(row,0))
        data = wx.StaticText(self, label=dataTxt)
        sizer.Add(data, pos=(row,1))
        return data

    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        grid = wx.GridBagSizer(hgap=5, vgap=5)
        hSizer = wx.BoxSizer(wx.HORIZONTAL)

        # Checkboxes
        self.check1 = wx.CheckBox(self, label="Enable sensor data logging?")
        grid.Add(self.check1, pos=(0,0), span=(1,2), flag=wx.BOTTOM, border=5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.check1)
        self.check2 = wx.CheckBox(self, label="Enable web server?")
        grid.Add(self.check2, pos=(1,0), span=(1,2), flag=wx.BOTTOM, border=5)
        self.Bind(wx.EVT_CHECKBOX, self.EvtCheckBox, self.check2)

        # Edit controls
        hostLable = wx.StaticText(self, label="PiSense host:")
        grid.Add(hostLable, pos=(2,0))
        self.hostText = wx.TextCtrl(self, value="localhost", size=(100,-1))
        grid.Add(self.hostText, pos=(2,1))

        self.goButton = wx.Button(self, 1003, "Go", size=(22,22))
        grid.Add(self.goButton, pos=(2,2))
        self.Bind(wx.EVT_BUTTON, self.OnGoButton, self.goButton)

        # Info display
        self.data0 = self.quickText(grid, 3, "PiSense host status:", "Connecting...")
        self.data1 = self.quickText(grid, 4, "Active node count:", "0")
        self.data2 = self.quickText(grid, 5, "Last data received:", "Unknown")
        self.data3 = self.quickText(grid, 6, "Sensor reports received:", "0")
        self.data4 = self.quickText(grid, 7, "HTTP requests", "0")

        #grid.Add((10, 40), pos=(2,0))
        hSizer.Add(grid, 0, wx.ALL, 5)

        # A multiline TextCtrl
        self.logger = wx.TextCtrl(self, size=(200,150), style=wx.TE_MULTILINE | wx.TE_READONLY)
        hSizer.Add(self.logger)

        self.SetSizerAndFit(hSizer)

    def EvtCheckBox(self, event):
        self.logger.AppendText('EvtCheckBox: %d\n' % event.Checked())

    def OnGoButton(self, event):
        self.GetParent().thread.SetHost(self.hostText.GetValue())

    def RefreshData(self, value):
        try:
            nodeCount = value['nodecount']
            reportCount = value['reportcounter']
            lastDataTime = datetime.fromtimestamp(value['lastdatatime'])
            self.data0.SetLabel('Connected')
            self.data1.SetLabel(str(nodeCount))
            self.data2.SetLabel(str(lastDataTime))
            self.data3.SetLabel(str(reportCount))
            self.logger.AppendText('RefreshData\n')
        except KeyError:
            self.data0.SetLabel('Not found')
            self.logger.AppendText('Error connecting to PiSense host\n')

#----------------------------------------------------------------------



app = wx.App(False)
frame = MainFrame(None)
frame.Show()
app.MainLoop()
