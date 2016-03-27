import os
from os.path import expanduser

import sys

import config
import pyshark
import sqlite3


class PostProcessing:
    def __init__(self):

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

        # connect to the -already existing- database
        if not os.path.isfile(config.db_location):
            print 'Error: DB file does not exist, check given db_location in config. Exiting now'
            sys.exit()
        self.connection = sqlite3.connect(config.db_location)
        self.cursor = self.connection.cursor()

        # test db
        # for row in self.cursor.execute('SELECT frequency FROM roguetowers WHERE arfcn=1014'):
        #     print row

        # rejection dictionary
        self.rejections = {}
        self.reject_per_freq_counter = 0

        # post-process all pcapng files
        for location in filelist:
            frequency = self.get_freq_by_filename(location)
            print '\n Now processing frequency: ' + str(frequency) + ' using file: ' + os.path.basename(location)
            cell_id = self.process_capture(location)
            print 'cell id: ' + str(cell_id)

            # save rejections table
            self.rejections[(cell_id, frequency)] = self.rejections.get((cell_id, frequency), 0) +\
                                                    self.reject_per_freq_counter
            self.reject_per_freq_counter = 0

        print 'Rejections numbers: '
        print self.rejections

        # close db connection when finished
        self.connection.close()

    def process_capture(self, location):
        """
        Process the given pcapng file; for every packet in this capture, check what it is and call accompanying method.
        """
        capture = pyshark.FileCapture(location)
        i = 0
        cell_id = -1
        for packet in capture:
            # temp for develop, first x packets
            # if i > 60:
            #     break
            i += 1

            #frame_number = packet['gsmtap'].frame_nr
            # print 'packet frame number: ' + str(frame_number) + ' , i= ' + str(i)
            # if packet['gsmtap'].frame_nr == '389283':
            #     print packet
            #     print ' type: ' + str(packet['gsm_a.dtap'].msg_rr_type)

            # all ccch traffic
            if hasattr(packet, 'gsm_a.ccch'):
                #print str(i) + ' = ' + packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type

                # Sys info 3
                if packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type == '27':
                    cell_id = self.process_sys_info_3(packet)

            # lapdm cipher traffic
            if hasattr(packet, 'gsm_a.dtap'):
                self.process_lapdm_ciphering_mode(packet)

        print 'number of packets processed: ' + str(i)
        return int(cell_id)

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
        return cell_id

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
        dtap = packet['gsm_a.dtap']
        # check if this packet has DTAP Radio Resources Management Message Type: Ciphering Mode Command
        if hasattr(dtap, 'msg_rr_type'):
            # if message type is that of ciphering mode command
            if dtap.msg_rr_type == '53':
                # get the cipher: zero is A5/1?
                cipher = dtap.gsm_a_rr_algorithm_identifier

        # federico rejection stuff
        if hasattr(dtap, 'msg_mm_type'):
            if hasattr(dtap, 'msg_rr_type'):
                # TODO: find correct values, as these won't ever be True
                if dtap.msg_mm_type == 0x08 or dtap.msg_mm_type == 0x04 or dtap.msg_rr_type == 0x35:
                    print 'reject'
                    self.reject_per_freq_counter += 1

    def get_freq_by_filename(self, filename):
        """
        Frequency has to be determined for database access. split by _, take last section, remove file extension
        """
        return filename.split('_')[-1][:-7]


PostProcessing()
