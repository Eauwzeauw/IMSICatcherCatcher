import os
import threading
from Queue import Queue
from os.path import expanduser
import time
from subprocess import Popen
import thread
import sys

import config
from colorama import init, Fore, Back, Style
init(autoreset=True)


class Capturing:
    def __init__(self):
        """
        Start capturing GSM packets and decode them
        Print statements used:
            Green = Normal operation, information
            Yellow = Executing statements
            Red = Something went wrong
        """
        self.continue_loop = True

        print(Fore.GREEN + '------------- Imsi Catcher^2 -------------')
        print(Fore.GREEN + 'To stop the loop: Hit Enter')

        # set used location
        if config.other_saving_location:
            user_home_location = config.other_saving_location
        else:
            user_home_location = expanduser("~")
        location = user_home_location + "/IMSI/captures"
        print(Fore.GREEN + 'Saving location: ' + location)

        # make save folder if it does not exist yet. Change bash location to new folder.
        if not os.path.exists(location):
            os.makedirs(location)
        os.chdir(location)

        # make a queue for decodes to be done
        self.stop_decode = False
        self.q = Queue()

        # start wireshark or tshark:
        if config.use_wireshark:
            wiresharkBashCommand = "sudo wireshark -k -f udp -Y gsmtap -i lo"
            print(Fore.YELLOW + 'Executing command: ' + str(wiresharkBashCommand))
            Popen(wiresharkBashCommand, shell=True)
            time.sleep(5)  # sleep to allow you to hit enter for the warning messages :)

        # make separate folder for this capture (with current time)
        foldername = time.strftime("%d-%m-%Y_%H:%M:%S")
        os.makedirs(foldername)
        os.chdir(foldername)

        #  device queue
        self.deviceq = Queue()
        for device in config.available_antennas:
            self.deviceq.put(device)

        # allow entry of frequencies in both formats
        self.frequencies = []
        for freq in config.frequencies:
            self.frequencies.append(freq)
        for short_freq in config.frequencies_scanner:
            long_freq = str(int(short_freq * 1000000))
            self.frequencies.append(long_freq)
        print 'The following frequencies will be processed:'
        for freq in self.frequencies:
            print freq

        # start actually doing stuff
        self.start_loop()

    def start_loop(self):
        """
        Run the capturing and decoding until one presses a key and the enter key. The loop will finish it's workings.
        """
        stop = []
        thread.start_new_thread(self.stop_loop, (stop,))
        if config.execute_decode:
            thread.start_new_thread(self.decode_loop, ())
        i = 0
        while not stop:
            # capture certain amount of times
            if i < config.number_of_rounds:
                # every freq in one iteration
                for freq in self.frequencies:
                    while True:
                        # only continue if antenna available
                        if self.deviceq.qsize() > 0:
                            # TODO: add check which sees if enough harddiskspace
                            antenna = str(self.deviceq.get())
                            print(Fore.GREEN + 'starting capturing on freq ' + str(freq))
                            #self.capture_raw_data(i, freq, antenna)
                            thread.start_new_thread(self.capture_raw_data, (i, freq, antenna))
                            time.sleep(2)
                            break
                        else:
                            time.sleep(10)
                i += 1
            else:
                break

        self.stop_decode = True
        print(Fore.GREEN + 'Finished ALL capturing')
        if not self.q.empty() and config.execute_decode:
            self.decode_loop

    def decode_loop(self):
        """
        Decode GSM Data to GSM packets with use of a queue (which contains the filenames to decode)
        """
        while True:
            # check if we should stop (so finished capturing, and the decode queue is empty
            if self.stop_decode and self.q.empty():
                print(Back.YELLOW + 'stop_decode = true')
                break
            # if the queue is filled, we should decode that!
            if not self.q.empty():
                filename, freq = self.q.get()
                self.decode_raw_data(filename, freq)
            # if the queue is empty, let's chill for a while
            else:
                time.sleep(5)

        print(Fore.GREEN + 'Finished ALL decoding; let\'s go to to the next location!')
        sys.exit(0)

    def capture_raw_data(self, filenumber, freq, antenna):
        """
        Capture raw antenna data using grgsm_capture.
        """
        filename = 'capture' + str(filenumber) + '_' + str(freq) + '.cfile'
        captureBashCommand = "grgsm_capture.py -c " + filename + " -f " + freq + ' -T ' \
                             + config.capture_length \
                             + ' --args="rtl=' + antenna + '"'
        #captureBashCommand = 'grgsm_capture.py -c %s -f %d -T %s  --args="rtl=%s"' % (
        #     filename, freq, config.capture_length, antenna
        # )
        print(Fore.YELLOW + 'Executing command: ' + str(captureBashCommand))
        print(Fore.GREEN + 'Script will do nothing for ' + config.capture_length + ' seconds.')

        # Start capture
        os.system(captureBashCommand)

        everything_to_hell = False
        # Check if capture was succesful (as sometimes receiver quits for no reason)
        if not os.path.isfile(filename):
            print(Back.RED + str(filename) + ': I think the capture went wrong, please check!! I will not decode this')
            everything_to_hell = True

        print(Fore.GREEN + str(filename) + ': Finished capturing')
        if not everything_to_hell:
            print(Back.YELLOW + 'adding to queue: ' + str(filename))
            self.q.put((filename, freq))
        self.deviceq.put(antenna)

    def decode_raw_data(self, filename, freq):
        """
        Decode the captured data into GSM packets readable by wireshark. Also deleted raw data when requested to.
        """
        print(Fore.GREEN + str(filename) + ': Starting decoding of SDCCH8 and BCCH.')
        SDCCH_bash = 'grgsm_decode -c ' + filename + ' -f ' + freq + ' -m SDCCH8 -t 1'
        BCCH_bash = 'grgsm_decode -c ' + filename + ' -f ' + freq + ' -m BCCH -t 0'

        # Start Tshark if wanted to capture this packet output of this capture file
        if not config.use_wireshark:
            tsharkBashCommand = "sudo tshark -w " + filename[:-6] + ".pcapng -i lo -q"
            print(Fore.YELLOW + 'Executing command: ' + str(tsharkBashCommand))
            tshark = Popen(tsharkBashCommand, shell=True)
            #print(Back.RED + 'tshark should have started')
            time.sleep(5)  # sleep to allow you to enter sudo password

        # Sleep to allow release of lock on file
        time.sleep(2)

        # Actually start decoding, depending on which channel to decode
        if config.decode_sdcch:
            print(Fore.YELLOW + str(filename) + ': Decoding SDCCH, using commmand: ' + SDCCH_bash)
            SDCCH = Popen(SDCCH_bash, shell=True)
            SDCCH.wait()
        if config.decode_bcch:
            print(Fore.YELLOW + str(filename) + ': Decoding BCCH, using commmand: ' + BCCH_bash)
            BCCH = Popen(BCCH_bash, shell=True)
            BCCH.wait()

        # Delete if wanted
        if config.delete_capture_after_processing:
            print(Fore.GREEN + str(filename) + ': Deleting capture file as requested (change this in config file).')
            os.remove(filename)

        if not config.use_wireshark:
            tshark.terminate()
            #print(Back.RED + 'tshark should have stopped')

        print(Fore.GREEN + str(filename) + ': Finished decoding')

    def stop_loop(self, stop):
        """
        Stops the loop in start_loop. The loop finishes and is then ended.
        """
        raw_input()
        stop.append(None)
        print(Fore.RED + 'The processing will stop after finishing current capturing and decoding...')

Capturing()
while 1:
    pass
