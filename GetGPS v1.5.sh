#!/bin/bash
# GPS Position Grabber v1.5 - Start Stricpt for Java App
# by Piotr Tekieli
# for Hacking Lab research project

#Defined variables
breakline="--------------------------------------------------------------------"
_ip="192.168.43.1" #Set mobile's IP address
_port="50000" #Set destination port
_database="imsicc.db" #Set destination database

clear
java -jar GPSA.jar $_ip $_port $_database
