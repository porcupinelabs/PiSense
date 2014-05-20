apt-get install python-serial 
sed -i '/ttyAMA0/s/^/#/' /etc/inittab
sed -i 's/ .*=ttyAMA0.[0-9]* / /' /boot/cmdline.txt

echo "# Start PiSense" >> /etc/rc.local
echo "cd ~pi/PiSense/pslog"
echo "printf \"starting PiSense datalogger...\\n\"" >> /etc/rc.local
echo "python pslog.py > pslog.log 2>&1 &" >> /etc/rc.local
echo "printf \"starting PiSense web server...\\n\"" >> /etc/rc.local
echo "cd ~pi/PiSense/psweb" >> /etc/rc.local
echo "python psweb.py > psweb.log 2>&1 &" >> /etc/rc.local
echo "exit 0" >> /etc/rc.local
