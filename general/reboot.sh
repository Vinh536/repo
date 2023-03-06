#!/bin/bash
IPLIST=$1
USER="root"
PASSWORD="ocptester"
PXE="ipmitool chassis bootdev pxe"
REBOOT="ipmitool chassis power reset"


function Reboot-6-Times() {
	for i in $( cat ${IPLIST} );
	do
		sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${i} "${PXE}" &
		sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${i} "${REBOOT}" &
	done
	sleep 5m &
}


count=6
for c in $(seq $count); 
	do
		Reboot-6-Times
		echo $count
	done
	
	



	


