import os
import threading
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

        # start wireshark:
        wiresharkBashCommand = "sudo wireshark -k -f udp -Y gsmtap -i lo"
        print(Fore.YELLOW + 'Executing command: ' + str(wiresharkBashCommand))
        Popen(wiresharkBashCommand, shell=True)
        time.sleep(5)  # sleep to allow you to hit enter for the warning messages :)

        # make separate folder for this capture (with current time)
        foldername = time.strftime("%d-%m-%Y_%H:%M:%S")
        os.makedirs(foldername)
        os.chdir(foldername)

        # start actually doing stuff
        self.start_loop()

    def start_loop(self):
        """
        Run the capturing and decoding until one presses a key and the enter key. The loop will finish it's workings.
        """
        stop = []
        thread.start_new_thread(self.stop_loop, (stop,))
        i = 0
        while not stop:
            # capture GSM Data
            filename = self.capture_raw_data(i)

            # decode GSM Data to GSM packets (while starting new capture)
            decode_thread = threading.Thread(target=self.decode_raw_data, args=(filename,))
            decode_thread.start()
            i += 1

        print(Fore.GREEN + 'Stopped. Exiting now')

    def capture_raw_data(self, filenumber):
        """
        Capture raw antenna data using grgsm_capture.
        """
        filename = 'capture' + str(filenumber) + '.cfile'
        captureBashCommand = "grgsm_capture.py -c " + filename + " -f " + config.frequency + ' -T ' + config.capture_length
        print(Fore.YELLOW + 'Executing command: ' + str(captureBashCommand))
        print(Fore.GREEN + 'Script will do nothing for ' + config.capture_length + ' seconds.')

        # Start capture
        os.system(captureBashCommand)

        # Check if capture was succesful (as sometimes receiver quits for no reason)
        if not os.path.isfile(filename):
            print(Fore.RED + str(filename) + ': Capture went wrong, exiting now')
            sys.exit(0)

        print(Fore.GREEN + str(filename) + ': Finished capturing')
        return filename

    def decode_raw_data(self, filename):
        """
        Decode the captured data into GSM packets readable by wireshark. Also deleted raw data when requested to.
        """
        print(Fore.GREEN + str(filename) + ': Starting decoding of SDCCH8 and BCCH.')
        SDCCH_bash = 'grgsm_decode -c ' + filename + ' -f ' + config.frequency + ' -m SDCCH8 -t 1'
        BCCH_bash = 'grgsm_decode -c ' + filename + ' -f ' + config.frequency + ' -m BCCH -t 0'

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

        # Delete is wanted
        if config.delete_capture_after_processing:
            print(Fore.GREEN + str(filename) + ': Deleting capture file as requested (change this in config file).')
            os.remove(filename)

        print(Fore.GREEN + str(filename) + ': Finished decoding')

    def stop_loop(self, stop):
        """
        Stops the loop in start_loop. The loop finishes and is then ended.
        """
        raw_input()
        stop.append(None)
        print(Fore.RED + 'The processing will stop after finishing current capturing and decoding...')


Capturing()
