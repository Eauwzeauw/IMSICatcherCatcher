#!/bin/bash
# GPS Position Grabber v1.4
# by Piotr Tekieli
# for Hacking Lab research project

#Defined variables
breakline="--------------------------------------------------------------------"
_ip="192.168.43.1" #Set mobile's IP address
_port="50000" #Set destination port
_database="imsicc.db" #Set destination database

#Check if notebook and mobile phone are in the same network
#Check if software is configured to host data on defined port
clear
echo "Checking connection with GPS device..."
if [[ $(nmap -p $_port $_ip | grep -E $_port | grep -E open) ]]; then
  echo "Good! The port seems to be open"
else
  echo "Neh #sadface. Check if GPS device and laptop are working in the same network"
  exit
fi
echo "Moving to Phase 2 / 3"
sleep 5s

#Check if data is produced and outputted via defined port
clear
echo "Checking data exchange with GPS sharing software"
if [[ $(nc $_ip $_port | head -n 5) ]]; then
  echo "Good! The exchange is working correctly"
else
  echo "Neh #sadface. Re-check application's settings"
  exit
fi
echo "Moving to Phase 3 / 3"
sleep 5s

#Check if gps device is producing GPGGA strings (3D fix information)
#If yes, then it is conncected with sattelites and ready for further operations
#If no, then the software will wait for proper connection (halt further processes)
clear
echo "Trying to aquire GPS coordinates..."
while read -r line;
do
  echo "NMEA String Found : $line"
  echo $breakline
  #Output entries to be modified (rows lacking GPS data)
  echo "String to be modified : [ID], [NMEA]"
  sqlite3 $_database "SELECT id,nmea FROM roguetowers WHERE nmea IS null;"
  echo $breakline
  #Fill them with information 1/3 - Add timestamps to those entries
  sqlite3 $_database "UPDATE roguetowers SET recordadded = '$(date +"%b, %d %Y %H:%M:%S.%N")' WHERE nmea IS null;"
  #Fill them with information 2/3 - Parse captured NMEA information and save it as longitudes and latitudes inside DB
  latitude=$(echo $line | awk -F ',' '/\$GPGGA/ {print (substr($3,0,3) + (substr($3,3) / 60.0)) $4}')
  longitude=$(echo $line | awk -F ',' '/\$GPGGA/ {print (substr($5,0,4) + (substr($5,4) / 60.0)) $6}')
  sqlite3 $_database "UPDATE roguetowers SET latitude='${latitude}' WHERE nmea IS null;"
  sqlite3 $_database "UPDATE roguetowers SET longitude='${longitude}' WHERE nmea IS null;"
  #Fill them with information 3/3 - Enter NMEA data (Filling process becomes complete after this operation)
  sqlite3 $_database "UPDATE roguetowers SET nmea = '$line' WHERE nmea IS null;"
  #Output modified entries
  echo "Strings modified (check if the insertion was correct) : [ID], [TIMESTAMP], [LAT], [LONG], [NMEA]"
  sqlite3 $_database "SELECT id,recordadded, latitude, longitude, nmea FROM roguetowers WHERE nmea='$line';"
  exit 123
done < <(nc $_ip $_port | grep --line-buffered '$GPGGA')
