import os
from os.path import expanduser
import config
import pyshark


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

        for location in filelist:
            frequency = self.get_freq_by_filename(location)
            print 'Now processing frequency: ' + str(frequency)
            self.process_capture(location)

    def process_capture(self, location):
        """
        Process the given pcapng file; for every packet in this capture, check what it is and call accompanying method.
        """
        capture = pyshark.FileCapture(location)
        i = 0
        for packet in capture:
            # temp for develop, first x packets
            if i > 20:
                break
            i += 1

            frame_number = packet['gsmtap'].frame_nr
            # print 'packet frame number: ' + str(frame_number) + ' , i= ' + str(i)
            # if packet['gsmtap'].frame_nr == '389283':
            #     print ' type: ' + str(packet['gsm_a.dtap'].msg_rr_type)

            # all ccch traffic
            if hasattr(packet, 'gsm_a.ccch'):
                print str(i) + ' = ' + packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type

                # Sys info 3
                if packet['gsm_a.ccch'].gsm_a_dtap_msg_rr_type == '27':
                    self.process_sys_info_3(packet)

            # lapdm cipher traffic
            if hasattr(packet, 'gsm_a.dtap'):
                self.process_lapdm_ciphering_mode(packet)

    def process_sys_info_3(self, packet):
        ccch = packet['gsm_a.ccch']
        print 'ccch: ' + dir(ccch)
        lac = ccch.gsm_a_lac
        cell_id = ccch.gsm_a_bssmap_cell_ci

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

    def get_freq_by_filename(self, filename):
        """
        Frequency has to be determined for database access. split by _, take last section, remove file extension
        """
        return filename.split('_', 1)[-1][:-7]


PostProcessing()
