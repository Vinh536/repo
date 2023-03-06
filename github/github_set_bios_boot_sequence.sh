#!/bin/bash
filename="bmcip-r650-storage"
filename="temp"
for i in $( cat ${filename} ); 
do 
	echo $i; 
	set_order=$( racadm -r $i -u root -p calvin set Bios.BiosBootSettings.BootSeq \
	NIC.Slot.2-1-1,NIC.Integrated.1-1-1 );
	echo $set_order;
	if [[ $set_order == *"RAC1017"* ]]; then
		keyname=$( echo $set_order | grep -i 'Key=' | cut -f 2 -d "=" | cut -f 1 -d "#")
		echo $i $keyname;
		jid=$( racadm -r $i -u root -p calvin jobqueue create $keyname | grep -i 'JID' \
		| cut -f 2 -d "=" | awk '{print $1}' )
		echo -e "Success!\nRun: racadm -r $i -u root -p calvin jobqueue view -i $jid"

	else
		echo "Failed to set boot order for: " $i;
	fi
done
