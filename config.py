other_saving_location = None  # set a (valid!) location here. The script will use this as base path
frequencies = ['932800000',
               '937200000',
               ]  # as can be found through grgsm_livemon
capture_length = '50'  # in seconds
delete_capture_after_processing = True

decode_bcch = True  # one of these 2 (or both) must be True, otherwise nothing happens:)
decode_sdcch = True

use_wireshark = False  # False = use tshark

available_antennas = ['00000001',
                      '00000002',
                      '00000006']
