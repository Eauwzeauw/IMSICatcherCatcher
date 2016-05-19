import os
from os.path import expanduser
import sys
import pyshark
import sqlite3
import config
from colorama import init, Fore, Back, Style
init(autoreset=True)




class PostProcessing:
    def __init__(self):
        """
        Post process the resulting pcapng files; look for giveaways (and input this in the DB with BST info)
        Look for every pcapng file in IMSI folder and then process per frequency. at the end put this info in DB
        """
        # prepare files to process. If only one file; enter this in the config. otherwise search imsi folder recursively
        filelist = []
        if config.one_file_mode:
            filelist.append(config.one_file_mode)
        else:
            # set used location
            if config.other_saving_location:
                user_home_location = config.other_saving_location
            else:
                user_home_location = expanduser("~")
            location = user_home_location + "/IMSI/captures"

            # search for correct files
            for dirpath, dirnames, filenames in os.walk(location):
                for filename in (f for f in filenames if f.endswith(".pcapng")):
                    filelist.append(os.path.join(dirpath, filename))

        # connect to the -already existing- database, see https://docs.python.org/2/library/sqlite3.html for functions
        if not os.path.isfile(config.db_location):
            print(Fore.RED + 'Error: DB file does not exist, check given db_location in config. Exiting now')
            sys.exit()
        self.connection = sqlite3.connect(config.db_location)
        self.cursor = self.connection.cursor()

        # test db
        # for row in self.cursor.execute('SELECT frequency FROM towers WHERE arfcn=1014'):
        #     print row

        # rejection dictionary
        self.rejections = {}
        self.reject_per_freq_counter = 0
        self.location_updating_request_per_freq_counter = 0
        self.accept_per_freq_counter = 0

        self.other_data = {}

        # post-process all pcapng files
        for location in filelist:
            frequency = self.get_freq_by_filename(location)
            print '\n Now processing frequency: ' + str(frequency) + ' using file: ' + os.path.basename(location)
            cell_id, cipher, reselect_offset, temporary_offset, reselect_hysteris = self.process_capture(location)
            print 'cell id: ' + str(cell_id)

            if cell_id == -1:
                print(Fore.RED + 'WARNING: no cell id detected for frequency ' + str(frequency))
                print(Style.RESET_ALL)
            if cipher == -1:
                print(Fore.RED + 'WARNING: no cipher detected for frequency ' + str(frequency))
                print(Style.RESET_ALL)

            if cipher == 55: #translate no cipher int to str
                cipher = "A5/0"

            # save rejections table
            rejec, request, accept = self.rejections.get((cell_id, frequency), [0, 0, 0])
            new_num_rejec = rejec + self.reject_per_freq_counter
            new_num_request = request + self.location_updating_request_per_freq_counter
            new_num_accept = accept + self.accept_per_freq_counter
            self.rejections[(cell_id, frequency)] = [new_num_rejec, new_num_request, new_num_accept]

            self.other_data[(cell_id, frequency)] = [reselect_offset, temporary_offset, cipher, reselect_hysteris]

            # reset counters
            self.reject_per_freq_counter = 0
            self.location_updating_request_per_freq_counter = 0
            self.accept_per_freq_counter = 0
            print 'cipher: ' + str(cipher)
            print 'reselect offset: ' + str(reselect_offset)
            print 'temporary offset: ' + str(temporary_offset)
            print 'reselect hysteris: ' + str(reselect_hysteris)

        print '\n Rejections/requests/accepts numbers: '
        print self.rejections

        print 'Processing this data into the database...'

        # start adding to database
        for cell_id, frequency in self.rejections:
            rejects, requests, accepts = self.rejections[(cell_id, frequency)]
            reselect_offset, temporary_offset, cipher, reselect_hysteris = self.other_data[(cell_id, frequency)]

            # First, check if the combination of cellid and freq (which makes it unique) already exists in the DB
            content = (cell_id, frequency)
            self.cursor.execute('SELECT * FROM towers WHERE cellid=? AND frequency=?', content)
            result = self.cursor.fetchone()

            # Then insert depending on result
            content = (rejects, requests, accepts, cell_id, frequency, cipher, reselect_offset, temporary_offset, reselect_hysteris)
            #if result is None:  # combination of cellid and freq doesn't exist yet, make a new row

            #Whether a row already exists for combination of cellid and freq, always insert new row so not overwrite useful information.
            self.cursor.execute('INSERT INTO towers (nrrejects, nrupdates, nrciphercommands, cellid, frequency, usedencryption, pcapngtower, reselection_offset, temporary_offset, reselect_hysteresis) values (?,?,?,?,?,?,1,?,?,?)', content)

            # And finally actually apply changes made
            self.connection.commit()

        # close db connection when finished
        self.connection.close()

        print '\n all done:)'

    def process_capture(self, location):
        """
        Process the given pcapng file; for every packet in this capture, check what it is and call accompanying method.
        """
        capture = pyshark.FileCapture(location)
        print capture
        i = 0

        # initialise values for if it isn't found in the packets
        cell_id = 0
        new_cipher = -1
        reselect_offset = 0
        temporary_offset = 0
        reselect_hysteris = 0
        for packet in capture:
            i += 1

            # all ccch traffic
            if hasattr(packet, 'gsm_a.ccch'):
                #print str(i) + ' = ' + packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type

                # Sys info 3
                #print packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type
                if packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type == hex(27):
                    #print 'hello sys3'
                    cell_id, reselect_offset, temporary_offset, reselect_hysteris = self.process_sys_info_3(packet)

            # lapdm cipher traffic
            if hasattr(packet, 'gsm_a.dtap'):
                cipher = self.process_lapdm_ciphering_mode(packet)

                # check if there are multiple ciphers in 1 freq (first one is used)
                if new_cipher == -1 and cipher != -1:
                    #print new_cipher
                    new_cipher = cipher
                if new_cipher != -1 and cipher != new_cipher and cipher != -1:
                    if int(str(cipher)) not in config.allowedEncryption:
                        print(Fore.RED + 'Detected unsafe Encryption:' + str(cipher))
                        new_cipher = cipher
        print 'number of packets processed: ' + str(i)
        return int(str(cell_id), 16), int(str(new_cipher), 16), int(str(reselect_offset), 16), int(str(temporary_offset), 16), int(str(reselect_hysteris), 16)

    def process_sys_info_3(self, packet):
        """
        Process sys info packets, giving:
        'e212_mcc', 'e212_mnc', 'field_names', 'get_field', 'get_field_by_showname', 'get_field_value',
        'gsm_a_bssmap_cell_ci', 'gsm_a_dtap_msg_rr_type', 'gsm_a_l3_protocol_discriminator', 'gsm_a_lac',
        'gsm_a_rr_acc', 'gsm_a_rr_acs', 'gsm_a_rr_att', 'gsm_a_rr_bs_ag_blks_res', 'gsm_a_rr_bs_pa_mfrms',
        'gsm_a_rr_cbq', 'gsm_a_rr_cbq3', 'gsm_a_rr_ccch_conf', 'gsm_a_rr_cell_barr_access',
        'gsm_a_rr_cell_reselect_hyst', 'gsm_a_rr_cell_reselect_offset', 'gsm_a_rr_dtx_bcch', 'gsm_a_rr_gprs_ra_colour',
        'gsm_a_rr_l2_pseudo_len', 'gsm_a_rr_max_retrans', 'gsm_a_rr_ms_txpwr_max_cch', 'gsm_a_rr_mscr', 'gsm_a_rr_neci',
        'gsm_a_rr_penalty_time', 'gsm_a_rr_pwrc', 'gsm_a_rr_radio_link_timeout', 'gsm_a_rr_re',
        'gsm_a_rr_rxlev_access_min', 'gsm_a_rr_si13_position', 'gsm_a_rr_t3212', 'gsm_a_rr_temporary_offset',
        'gsm_a_rr_tx_integer', 'gsm_a_skip_ind', 'layer_name', 'pretty_print', 'raw_mode']
        """
        ccch = packet['gsm_a.ccch']
        lac = ccch.gsm_a_lac
        cell_id = ccch.gsm_a_bssmap_cell_ci
        mcc = ccch.e212_mcc
        mnc = ccch.e212_mnc
        reselect_offset = ccch.gsm_a_rr_cell_reselect_offset
        temporary_offset = ccch.gsm_a_rr_temporary_offset # if needed
        reselect_hysteris = ccch.gsm_a_rr_cell_reselect_hyst
        return cell_id, reselect_offset, temporary_offset, reselect_hysteris

    def process_lapdm_ciphering_mode(self, packet):
        """
        Process the lapdm packets, which give the ciphering command, possible field names:

        'e212_mcc', 'e212_mnc', 'field_names',
        'follow_on_request', 'get_field', 'get_field_by_showname', 'get_field_value', 'gsm_a_a5_1_algorithm_sup',
        'gsm_a_es_ind', 'gsm_a_ie_mobileid_type', 'gsm_a_l3_protocol_discriminator', 'gsm_a_lac', 'gsm_a_len',
        'gsm_a_msc_rev', 'gsm_a_oddevenind', 'gsm_a_rf_power_capability', 'gsm_a_skip_ind', 'gsm_a_spare_bits',
        'gsm_a_spareb8', 'gsm_a_tmsi', 'gsm_a_unused', 'layer_name', 'msg_mm_type', 'pretty_print',
        'protocol_discriminator', 'raw_mode', 'seq_no', 'updating_type']
        """
        cipher = -1
        dtap = packet['gsm_a.dtap']
        # check if this packet has DTAP Radio Resources Management Message Type: Ciphering Mode Command
        if hasattr(dtap, 'msg_rr_type'):
            # if message type is that of ciphering mode command
            if dtap.msg_rr_type == '0x35': #53

                self.accept_per_freq_counter += 1
                #print 'ACCEPT-COUNTER = ' + str(self.accept_per_freq_counter)
                # get the cipher: zero is A5/1?
                try:
                    cipher = dtap.gsm_a_rr_algorithm_identifier
                except AttributeError:
                    print(Fore.RED + '\nNO ENCRYPTION PRESENT!\n')
                    print(Style.RESET_ALL)
                    cipher = 37 #means no encryption, decimal: 55

        # federico rejection stuff
        if hasattr(dtap, 'msg_mm_type'):
            # DTAP Mobility Management Message Type: Location Updating Reject (0x04) == dtap.msg_mm_type == '4'
            if dtap.msg_mm_type == '0x04':  # or dtap.msg_rr_type == 0x35:
                self.reject_per_freq_counter += 1
                #print 'REJECT-COUNTER = ' + str(self.reject_per_freq_counter)

            # DTAP Mobility Management Message Type: Location Updating Request (0x08)
            if dtap.msg_mm_type == '0x08':
                self.location_updating_request_per_freq_counter += 1
        return cipher

    def get_freq_by_filename(self, filename):
        """
        Frequency has to be determined for database access. split by _, take last section, remove file extension
        """
        return filename.split('_')[-1][:-7]


PostProcessing()

