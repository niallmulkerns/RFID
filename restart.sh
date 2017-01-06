#!/bin/bash
CHECK_SCRIPT="tracker"
condition=$(ps -ef |grep -v grep| grep -c tracker)
#echo condition = $condition
message="Hello.\n\nTracker is being restarted.\nThis email is automated, please do not respond to this."
emailList="niall.mulkerns@stfc.ac.uk"

if [ "$condition" -gt "0" ]
then
	logger -s "$CHECK_SCRIPT is running. Do nothing"

elif [ "$condition" -eq "0" ]
then
	logger -s "$CHECK_SCRIPT is not running. Restarting script..."
	/usr/auto_run
	echo -e '$message' | mail -s 'Alert' -a 'From: Lab 6 Tracker <lab6tracker@stfc.ac.uk>' $emailList
	#python /home/pi/Documents/RFID/tracker.py
else 
	 logger -s "Invalid number given"

fi
