#!/bin/bash

password="ocptester"
s_number="dmidecode -s system-serial-number"
asa_serial="";
command="cd /opt/afulnx64";
# Create a function to make it easier to invoke what sshpass is doing under the hood.
function _sshpass() {
    echo -e "Running ${command} on: ${i}\n=========================";
    temp="";
    current_serial=$( sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "${s_number}" );
    echo "Current Serial: ${current_serial}";
    # Check if the Product Serial field currently contains an S. If so, move into a temp value.
    if [[ ${current_serial} =~ ^S* ]]; then
        temp=${current_serial};
        echo "Chassis Serial: ${temp}";
        sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "$command; ./amidelnx_26_64 /S ${temp}"
        asa_serial=${serial};
        echo "Product Serial: ${asa_serial}";
        sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "$command; ./amidelnx_26_64 /SS ${asa_serial}"
    fi
    new_serial=$( sshpass -p ${password} ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "${s_number}" );
    echo "New Serial: ${new_serial}";
}

# Check if the first input is a file.
if [[ -f $1 ]]; then
    echo "ERROR! Only perform this script on ONE machine at a time! Otherwise it will duplicate the serial...";
    echo "USAGE: ./do_dmi.sh <SINGLE_IP_ADDRESS> <ASA_SERIAL>";
    exit 1;
else
   i=$1;
   serial=$2;
   _sshpass;
fi
