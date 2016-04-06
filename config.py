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
one_file_mode = None # '/home/eauwzeauw/IMSI/captures/22-03-2016_21:20:48/somepackets_923600000.pcapng'  # None otherwise
db_location = '/home/eauwzeauw/PycharmProjects/IMSICatcherCatcher' + '/imsicc.db'

######### GIVEAWAY VARIABLES ##########
#A5/3 = 2, A5/1 = 0
disallowedEncryption = [1,2,3] #WARNING 0,1,2,3 do not necessarily correspond to A5/0-1-2-3 respectively, determined by wireshark.


# often used frequencies:
## Delft (TU):

## Delft (Marnix): 926800000, 930000000, 932000000, 932400000, 932800000, 937200000
#



