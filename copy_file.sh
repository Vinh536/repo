#!/bin/bash
IPLIST=$1
USER="root"
PASSWORD="ocptester"

echo "Please enter a file to copy to the target system: ";
read filename;

for i in $( cat ${IPLIST} );
do
	sshpass -p ${PASSWORD} scp -o StrictHostKeyChecking=False -o UserKnownHostsFile=/dev/null ${filename} ${USER}@$i: ; 
done
