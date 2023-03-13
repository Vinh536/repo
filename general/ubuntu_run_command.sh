#!/bin/bash
IPLIST=$1
USER="ubuntu"
PASSWORD="ubuntu123"

#echo "Please enter a command to perform on the target system(s): ";
#read command;

for i in $( cat ${IPLIST} );
do
	sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${i} "sudo apt-get install smartmontools && echo "${PASSWORD}"";
done
