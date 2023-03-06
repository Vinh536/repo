#!/bin/bash
IPLIST=$1
USER="root"
PASSWORD="ocptester"

echo "Please enter a command to perform on the target system(s): ";
read command;

for i in $( cat ${IPLIST} );
do
	sshpass -p ${PASSWORD} ssh -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null -t ${USER}@${i} "${command}";
done
