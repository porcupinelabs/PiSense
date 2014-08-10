#PiSense

PiSense is an easy to setup, wireless sensor network that uses your Raspberry Pi to collect sensor data and make it available on the web.  Just attach the PiSense Hub to your Pi's GPIO port and run our open source data collection app to start logging data from one or multiple sensors.  View your sensor data in real time or historical graphs from any web browser, anywhere.  More information on PiSense is
available at Porcupine Labs - http://www.porcupinelabs.com

This software is a customizable family of python apps that implement the PiSense data logger and web server.

##Installation

To install this software on a Raspberry Pi do the following:

`mkdir /home/pi/PiSense`  
`cd /home/pi/PiSense`  
`sudo apt-get install python-pip`  
`pip install -t . https://github.com/porcupinelabs/PiSense/archive/master.zip`  
`sudo bash install.sh`  
`sudo reboot`  

Upon rebooting, your Raspberry Pi will run pslog and psweb automatically.

##PiSense Applications

The following applications make up the PiSense software:

* pslog - The PiSense data logger.  Receives and logs sensor data from the Raspberry Pi's serial port.  Also implements a sockets API
          that is used by psweb and other software components to get real-time and historical data.
* psweb - The PiSense web server.  Implements a light weight web server on the Raspberry Pi's port 80.  Web content is contained in the
          http directory.  The PiSense web application is implemented using the Angular.js framework.
* pscmd - Contains two command line utilities:
           * pscmd.py - A simple demo utility that demonstrates how to communicate with PiSense sensors
           * psupdate.py - Checks sensor and hub firmware versions and optionally updates firmware
* psmon - A simple GUI (wxPython based) app that displays the status of your PiSense network
* scanchan - A utility that scans various radio channels in the 2.4GHz band and displays the amount of traffic seen on each channel.
