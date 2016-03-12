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
