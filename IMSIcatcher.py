import os
import sqlite3
import sys
import config
import giveaways as ga
import csv
from colorama import init, Fore, Back, Style
init(autoreset=True)


class IMSIcatcher:
	def __init__(self):
		"""
		This script creates a new table where only (cellid, frequency) pairs are listed that have at least one giveaway.
		The table provides a clear overview of which giveaways are present
		Each giveaway function from giveaways.py is processed here separately to create the new table
		Furthermore, the locations of possible imsicatchers are written to a .csv file used for triangulation.
		"""

		connection = sqlite3.connect(config.db_location)
		cursor = connection.cursor()

		cursor.execute('DROP TABLE IF EXISTS imsicatchers')
		cursor.execute("""CREATE TABLE imsicatchers (
			id			INTEGER PRIMARY KEY AUTOINCREMENT,
			cellid 		UNSINGED INTEGER(5),
			frequency	UNSIGNED INTEGER(10),
			encryption	VARCHAR (255), /* encryption used (wireshark value) */
			neighbourlist UNSIGNED INTGEGER (5), /* stores TRUE if giveaway is present */
			signal_gain	VARCHAR (255), /* tuple (reselection offset, temporary offset) */
			rejections	VARCHAR (255)) /* triple (#rejections, #updates, #ciphercommands) */ """)

		processEncryption()
		processNeighbourList()
		processGain()
		processRejections()
		towerCount = 0
		cursor.execute('SELECT * FROM IMSIcatchers')
		response = cursor.fetchall()
		csvdata = [['cellid', 'frequency', 'signalstrength', 'longitutde', 'latitude']] #data to be written to csv file
		for tower in response:
			towerCount += 1
			print 'Cell ID: ' + redIfTrue(tower[1])
			print 'Frequency: ' + redIfTrue(tower[2])
			print 'Encryption Giveaway: ' + redIfTrue(tower[3])
			print 'Neighbour list Giveaway: ' + redIfTrue(tower[4])
			print 'Signal Gain Giveaway: ' + redIfTrue(tower[5])
			print 'Rejections Giveaway: ' + redIfTrue(tower[6])
			locCount = 1;
			for location in cursor.execute('SELECT DISTINCT latitude, longitude, signalstrength FROM towers WHERE cellid = ? AND frequency = ? AND (latitude IS NOT NULL AND longitude IS NOT NULL )', (tower[1], tower[2])):
				print 'Location ' + str(locCount) + ': ' + str(location[0]) + ', ' + str(location[1])
				locCount += 1
				csvdata.append([tower[1], tower[2], location[2], location[0], location[1]])
			if locCount == 1:
				print 'Location not available'

			print ' '

		print Fore.RED + str(towerCount) + ' possible IMSIcatchers found!'
		print 'Data saved to database'

		connection.commit()
		connection.close()

		#write csv data to file
		with open('locations.csv', 'w') as fp:
			a = csv.writer(fp, delimiter=',')
			a.writerows(csvdata)



def processEncryption():
	encryptionTowers = giveaways.encryption()
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()

	for tower in encryptionTowers:
		for result in encryptionTowers:
			cellid = tower[0]
			frequency = tower[1]
			cursor.execute("SELECT cellid FROM imsicatchers WHERE cellid = ? AND frequency = ?", (cellid, frequency))
			data = cursor.fetchone()

			cursor.execute('SELECT usedencryption FROM towers WHERE cellid = ? AND frequency = ? AND usedencryption IS NOT NULL', (cellid, frequency))
			cipher = cursor.fetchone()[0]
			if data is None:
				cursor.execute("INSERT INTO imsicatchers (cellid, frequency, encryption) VALUES (?,?,?)", (cellid, frequency, cipher))
			else:
				cursor.execute("UPDATE imsicatchers SET encryption = ? WHERE cellid = ? AND frequency = ?", (cellid, frequency))
	connection.commit()
	connection.close()

def processNeighbourList():
	neighbourListTowers = giveaways.neighbourList()
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()
	for tower in neighbourListTowers:
		cellid = tower[0]
		frequency = tower[1]
		cursor.execute("SELECT cellid FROM imsicatchers WHERE cellid = ? AND frequency = ?", (cellid, frequency))
		data = cursor.fetchone()
		cursor.execute('SELECT DISTINCT latitude, longitude FROM towers WHERE cellid = ? AND frequency = ? AND (latitude IS NOT NULL AND longitude IS NOT NULL )', (cellid, frequency))
		locCount = len(cursor.fetchall())
		if data is None:
			cursor.execute("INSERT INTO imsicatchers (cellid, frequency, neighbourlist) VALUES (?,?,?)", (cellid, frequency, locCount))
		else:
			cursor.execute("UPDATE imsicatchers SET neighbourlist = 'TRUE' WHERE cellid = ? AND frequency = ?", (cellid, frequency))
	connection.commit()
	connection.close()

def processGain():
	gainTowers = giveaways.gain()
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()
	for tower in gainTowers:
		cellid = tower[0]
		frequency = tower[1]
		cursor.execute("SELECT cellid FROM imsicatchers WHERE cellid = ? AND frequency = ?", (cellid, frequency))
		data = cursor.fetchone()
		cursor.execute("SELECT reselection_offset, temporary_offset, reselect_hysteris FROM towers WHERE cellid = ? AND frequency = ? AND (reselection_offset != 0 OR temporary_offset != 0)", (cellid, frequency))
		gain_data = cursor.fetchone()
		signal_gain = str(gain_data[0]) + ' ' + str(gain_data[1]) + ' ' + str(gain_data[2])

		if data is None:
			cursor.execute("INSERT INTO imsicatchers (cellid, frequency, signal_gain) VALUES (?,?,?)", (cellid, frequency, signal_gain))
		else:
			cursor.execute("UPDATE imsicatchers SET signal_gain = ? WHERE cellid = ? AND frequency = ?", (signal_gain, cellid, frequency))
	connection.commit()
	connection.close()

def processRejections():
	rejectionTowers = giveaways.rejections()
	connection = sqlite3.connect(config.db_location)
	cursor = connection.cursor()
	for tower in rejectionTowers:
		cellid = tower[0]
		frequency = tower[1]
		cursor.execute("SELECT cellid FROM imsicatchers WHERE cellid = ? AND frequency = ?", (cellid, frequency))
		data = cursor.fetchone()
		cursor.execute("SELECT nrrejects, nrupdates, nrciphercommands FROM towers WHERE cellid = ? AND frequency = ? AND (nrrejects != 0 OR nrupdates != 0 OR nrciphercommands != 0)", (cellid, frequency))
		rejection_data = cursor.fetchone()
		rejection = str(rejection_data[0]) + ' ' + str(rejection_data[1]) + ' ' + str(rejection_data[2])

		if data is None:
			cursor.execute("INSERT INTO imsicatchers (cellid, frequency, rejections) VALUES (?,?,?)", (cellid, frequency, rejection))
		else:
			cursor.execute("UPDATE imsicatchers SET rejections = ? WHERE cellid = ? AND frequency = ?", (rejection, cellid, frequency))
	connection.commit()
	connection.close()

def redIfTrue(value):
	if (value != None ):
		return Fore.RED + str(value)
	else:
		return str(value)



giveaways = ga.Giveaways()
IMSIcatcher()