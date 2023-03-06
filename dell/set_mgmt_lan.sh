#!/bin/bash

password="ocptester"
command="/root/IPMICFG -raw 0x30 0x70 0x0C 1 0"

# Create a function to make it easier to invoke what sshpass is doing under the hood.
function _sshpass() {
    echo -e "Running ${command} on: ${i}\n=========================";
    echo $2;
    sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "$command";
}

# Check if the first input is a file.
if [[ -f $1 ]]; then
    for i in $( cat $1 );
    do
        _sshpass $2;
    done
else
    echo "USAGE: ./set_mgmt_lan.sh <LIST_OF_OS_IPS>";
fi
