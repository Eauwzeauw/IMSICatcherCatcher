other_saving_location = None #'/media/eauwzeauw/ac51b22f-80ed-42b9-96bd-1f0dd6c6634a'  # set a (valid!) location here. The script will use this as base path
frequencies = ['932000000'
               ]  # as can be found through grgsm_livemon  # as can be found through grgsm_livemon
frequencies_scanner = [937.2]  # as can be found through grgsm_scanner
test_frequencies = True
capture_length = '150'  # in seconds
number_of_rounds = 2  # number of captures to be done (this number * capture length = total seconds of capture per freq)
delete_capture_after_processing = True

decode_bcch = True  # one of these 2 (or both) must be True, otherwise nothing happens:)
decode_sdcch = True
execute_decode = True  # if set to False then no decoding is done (at all, ignoring settings above)

use_wireshark = False  # False = use tshark

available_antennas = ['00000006']

######### POST PROCECCSING VARIABLES ###########
one_file_mode = '/home/eauwzeauw/IMSI/captures/22-03-2016_21:20:48/capture0_923600000.pcapng'  # None otherwise


# often used frequencies:
## Delft (TU):

## Delft (Marnix): 926800000, 930000000, 932000000, 932400000, 932800000, 937200000
#



