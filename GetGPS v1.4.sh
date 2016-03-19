#!/bin/bash
###############################################
# GPS Position Grabber v1.1 ###################
# by Piotr Tekieli ############################
###############################################
#
breakline="--------------------------------------------------------------------"
_ip="192.168.43.1" #Set mobile's IP address
_port="50000" #Set destination port
_database="imsicc.db" #Set destination database
echo "Checking connection with GPS device..."
if [[ $(nmap -p $_port $_ip | grep -E $_port | grep -E open) ]]; then
  echo "Good! The port seems to be open"
else
  echo "Neh #sadface. Check if GPS device and laptop are working in the same network"
  exit
fi
sleep 5s
clear
echo "Checking data exchange with GPS sharing software"
if [[ $(nc $_ip $_port | head -n 5) ]]; then
  echo "Good! The exchange is working correctly"
else
  echo "Neh #sadface. Re-check application's settings"
  exit
fi
sleep 5s
clear
echo "Trying to aquire GPS coordinates..."
while read -r line;
do
  echo "NMEA String Found : $line"
  echo $breakline
  echo "String to be modified : [ID], [GPS]"
  sqlite3 $_database "SELECT id,gps FROM roguetowers WHERE gps IS null;"
  echo $breakline
  sqlite3 $_database "UPDATE roguetowers SET gps = '$line' WHERE gps IS null;"
  echo "Strings modified (check if the insertion was correct) : [ID], [GPS]"
  sqlite3 $_database "SELECT id,gps FROM roguetowers WHERE gps='$line';"
  exit 123
done < <(nc $_ip $_port | grep --line-buffered '$GPGGA')
