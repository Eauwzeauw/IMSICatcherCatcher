other_saving_location = None  # set a (valid!) location here. The script will use this as base path
frequency = '926800000'  # as can be found through grgsm_livemon
capture_length = '180'  # in seconds
delete_capture_after_processing = True

decode_bcch = False  # one of these 2 (or both) must be True, otherwise nothing happens:)
decode_sdcch = True

use_wireshark = True  # False = use tshark
