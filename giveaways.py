import os
import sqlite3
import sys
import config
from colorama import init, Fore, Back, Style
init(autoreset=True)


class Giveaways:
	def __init__(self):
		"""
		Look for multiple giveaways in a single database file which is
		the result of running the following scripts:
		1. main.py
		2. imsicc_scanfreq vx.xx.pl
		3. GetGPS vx.x.sh
		4. TODO -> script to merge all .db files in a single database
		5. post_process.py
		"""
		self.test = 'test'
		if not os.path.isfile(config.db_location):
			print(Fore.RED + 'Error: DB file does not exist, check given db_location in config. Exiting now')
			sys.exit()
		self.towersList = getUniqueTowers()


	#returns a list of towers that use one of the encryption methods specified in the config file
	def encryption(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = set()
		query = 'SELECT DISTINCT cellid, frequency FROM towers WHERE cellid != 0'
		#check config file for selected encryptions to filter on
		#modify query if any encryption methods are specified
		if config.disallowedEncryption:
			query += ' AND '
			encryptionTypes = set()
			for encryption in config.disallowedEncryption:
				encryptionTypes.add('usedencryption == ' + str(encryption))
			query += " OR ".join(encryptionTypes)

		for row in cursor.execute(query):
			towers.add((row[0],row[1]))
		connection.close()
		return towers

	def neighbouringList(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		flaggedTowers = set()
		timestamps = []
		#First get all distinct timestamps, checking for the neighbouring list giveaway is done per scan
		for row in cursor.execute('SELECT DISTINCT recordadded FROM towers WHERE cellid != 0 AND arfcn != 0'):
			timestamps.append(row[0])
		#print timestamps
		
		approvedTowers = set() #Maintain a set of towers that have found neighbours accross all timestamps
		#Checking for the giveaway is done for towers found with the same timestamp
		for t in timestamps:
			cellinfo = set() #for storing cell information
			for row in cursor.execute('SELECT DISTINCT arfcn, neighbourcells, cellid, frequency FROM towers WHERE recordadded == ?', (t,)):
				cellinfo.add((row[0], row[1], row[2], row[3]))
			#print cellinfo
			
			#For each neighbour list, check if at least one tower in the list is found with the same timestamp
			for neighbourlist in cellinfo:
				foundNeighbour = False
				for arfcn in cellinfo:
					if str(arfcn[0]) in neighbourlist[1]:
						foundNeighbour = True
						approved = (neighbourlist[2], neighbourlist[3])
						if approved not in approvedTowers:
							approvedTowers.add(approved)
							#print approved
				#print foundNeighbour
				if not foundNeighbour:
					flaggedTowers.add((neighbourlist[2], neighbourlist[3]))
	
		towers = flaggedTowers - approvedTowers #remove towers that have been approved at least once from all flagged towers, can happen when you get additional information of a cell during different scans
		connection.close()
		return towers

	def gain(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = []
		connection.close()
		return towers

	def rejections(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = []
		connection.close()
		return towers


#Retrieve a list of all unique towers. Can check each tower for a specific giveaway in a later stage.
def getUniqueTowers():
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()
	towers = []
	for row in cursor.execute('SELECT DISTINCT cellid, frequency FROM towers WHERE cellid != 0'):
		towers.append((row[0],row[1]))
	connection.close()
	return towers

        
giveaway = Giveaways()
giveaway.encryption()
print giveaway.neighbouringList()