# IMSICatcherCatcher
Scan for giveaways of fake Mobile Base Stations to detect them.


Howto:
------Installation:-------
Open terminal in location of git files

capture and decoder:
(via software center) 
install wireshark
install tshark

scanner: 
sudo apt-get install libdbi-perl
sudo apt-get install libcpan-sqlite-perl
chmod +x imsicc_scanfreq.pl
--> fixing error of grgsm:
#	step 1: run 'sudo nano /usr/local/bin/grgsm_scanner'
#	step 2: Change first line from: "#!/usr/bin/python2" to "#!/usr/bin/python2 -u"
#	Explanation: now Python will write unbuffered output to STDOUT, not missing any output/towers 


------Running:----------
Run capture and decoder: python main.py
Run scanner: perl imsicc_scanfreq_v0.02.pl

# Fixing lua sudo errors tshark and wireshark:

# Option 1:
# Setting network privileges for dumpcap
# 1. Ensure your linux kernel and filesystem supports File Capabilities and also you have
# installed necessary tools.
# 2. "setcap 'CAP_NET_RAW+eip CAP_NET_ADMIN+eip' /usr/bin/dumpcap"
# 3. Start Wireshark as non-root and ensure you see the list of interfaces and can do
# capture.
#
# It should be noted also that in order to perform step two in this process you need to do it as root user otherwise you will be told "bash: setcap: command not found". You can't even access the man page for setcap unless you are the root user. Once you have perfomed the operation you can then go back to being a user with admin rights and start wireshark happy and free.
#
# Option 2 (which i used):
# 2014-11-12, 04:08 PM
# gedit /usr/share/wireshark/init.lua
# then
# -- Set disable_lua to true to disable Lua support.
# disable_lua = true //set it to true

It is possible to select rtl-sdr dongle:
-with device index through commanline parameter: `--args="rtl=1"` (where 1 is the device index). Caution: device index is not unique identifier and it changes on each connection of the dongle.
-with devices serial number, the commandline option in this case has following form: `--args="rtl=00000001"` (where 00000001 is the serial number).

NOTE: You can set the serial number with use of:
```sh
rtl_eeprom -s <serial_number>
