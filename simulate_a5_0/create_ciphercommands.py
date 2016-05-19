#hexadecimal representation of a ciphering command package
#only the 45th byte will be modified containing the cipher mode.
cipher_template1 = """0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
0010   00 43 41 fd 40 00 40 11 fa aa 7f 00 00 01 7f 00
0020   00 01 e9 a8 12 79 00 2f fe 42 02 04 01 01 00 00
0030   dc 00 00 0f 54 6d 08 00 01 00 03 64 0d 06 35 """

cipher_template2 = """
0040   59 71 d1 8e d9 39 45 b9 c5 b1 55 ca 26 b6 ce 4e
0050   6e
"""

cipherString = ""

#ciphering mode is set using 4 bits
for i in range(0,16):
	ciphermode = '{0:02x}'.format(i)
	cipherString = cipherString + cipher_template1 + ciphermode + cipher_template2
	
#write generated strings to file
with open("ciphertext", "w") as text_file:
	text_file.write(cipherString)