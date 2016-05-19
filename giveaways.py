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
		there is a function for each giveaway that returns a list of (cellid, frequency) pairs
		"""

		#Check if database exists
		if not os.path.isfile(config.db_location):
			print(Fore.RED + 'Error: DB file does not exist, check given db_location in config. Exiting now')
			sys.exit()
		self.towersList = getUniqueTowers()

		self.timestamps = getTimestamps()


	############## GIVEAWAYS ###############
	#returns a list of towers that use one of the encryption methods specified in the config file
	def encryption(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = set()
		query = 'SELECT DISTINCT cellid, frequency FROM towers WHERE cellid != 0'
		#check config file for selected encryptions to filter on
		#modify query if any encryption methods are specified
		if config.allowedEncryption:
			query += ' AND '
			encryptionTypes = set()
			for encryption in config.allowedEncryption:
				encryptionTypes.add('usedencryption != ' + str(encryption))
			query += " AND ".join(encryptionTypes)

		for row in cursor.execute(query):
			towers.add((row[0],row[1]))
			
		connection.close()
		return towers

	def neighbourList(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		flaggedTowers = set()
		
		approvedTowers = set() #Maintain a set of towers that have found neighbours accross all timestamps
		#Checking for the giveaway is done for towers found with the same timestamp
		for t in self.timestamps:
			cellinfo = set() #for storing cell information
			for row in cursor.execute('SELECT DISTINCT arfcn, neighbourcells, cellid, frequency FROM towers WHERE recordadded == ?', (t,)):
				cellinfo.add((row[0], row[1], row[2], row[3]))
			
			#For each neighbour list, check if at least one tower in the list is found with the same timestamp
			for neighbourlist in cellinfo:
				if neighbourlist[2] != 0: #cell id should be present, otherwise information not reliable
					foundNeighbour = False
					for arfcn in cellinfo:
						if str(arfcn[0]) in neighbourlist[1]:
							foundNeighbour = True
							approved = (neighbourlist[2], neighbourlist[3])
							if approved not in approvedTowers:
								approvedTowers.add(approved)
					if not foundNeighbour:
						flaggedTowers.add((neighbourlist[2], neighbourlist[3]))

		towers = flaggedTowers - approvedTowers #remove towers that have been approved at least once from all flagged towers, can happen when you get additional information of a cell during different scans
		connection.close()
		return towers

	#TODO gain giveaway
	def gain(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = set()

		query = 'SELECT DISTINCT cellid, frequency FROM towers WHERE reselection_offset != 0 OR temporary_offset != 0 OR (reselect_hysteresis < 2 AND reselect_hysteresis > 4)'

		for row in cursor.execute(query):
			towers.add((row[0],row[1]))

		connection.close()
		return towers

	#TODO rejection giveaway
	def rejections(self):
		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()
		towers = set()

		query = 'SELECT DISTINCT cellid, frequency, nrrejects, nrupdates, nrciphercommands FROM towers WHERE nrrejects != 0 OR nrupdates != 0 OR nrciphercommands != 0'
		for row in cursor.execute(query):
			nrrejects = row[2]
			nrupdates = row[3]
			nrciphercommands = row[4]
			#The number of rejections should not be significant compared to the sum of rejections and ciphering commands
			if (nrrejects + nrciphercommands) > config.updates_minimum:
				if nrrejects > ((nrrejects + nrciphercommands) * config.rejection_ratio):
					towers.add((row[0],row[1]))

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

#Retrieve a list of all unique timestamps for detecting the neighbour list giveaway
def getTimestamps():
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()
	timestamps = []
	#First get all distinct timestamps, checking for the neighbouring list giveaway is done per scan
	for row in cursor.execute('SELECT DISTINCT recordadded FROM towers WHERE cellid != 0 AND arfcn != 0 AND recordadded IS NOT NULL'):
		timestamps.append(row[0])
	connection.close()
	return timestamps

        
giveaway = Giveaways()