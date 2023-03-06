#!/bin/bash

# This uses the BMCIP list and does not wait for the system to pxe boot.
# This will set the systems to reboot every 5 minutes for 6 times.
# Use before sending to QC, to verify if any amber lights comes on. 

IPLIST=$1 
USER="root"
PASSWORD="calvin"
count=0

function Reboot-6-Times() {
	for i in $( cat ${IPLIST} );
	do
		#racadm -u  ${USER} -p ${PASSWORD} -r $i serveraction hardreset & > /dev/null 2
		racadm -u  ${USER} -p ${PASSWORD} -r $i jobqueue view | grep -i "PR19" & 2> /dev/null
		sleep 5
	done
	
}


for count in $(seq 6); 
	do	
		echo ''
		echo \========================================
		echo  = Inprogress $count/6 times 
		echo \======================================== 
		echo ''
		Reboot-6-Times
		count=$((count+1))
		if [ $count == 7 ]; then
			echo ''
			echo ========================================
			echo "All progress has been completed 100%"
			echo ========================================
			echo ''
		fi
	done
