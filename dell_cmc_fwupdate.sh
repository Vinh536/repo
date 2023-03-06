#!/bin/bash
> mac_dell.txt
if [ "$#" -eq 0 ]; then
echo "Useage:./dell_clrsel.sh ip_list.file"
exit
fi
foo () {
	local i=$1
	echo "                                                                   " >> mac_dell.txt
	echo "===================================================================" >> mac_dell.txt
	racadm -r $i -u root -p calvin getsvctag | grep -v 'racadm\|password' >> mac_dell.txt #each node ST
	racadm -r $i -u root -p calvin getmacaddress | grep -v 'racadm\|password' >> mac_dell.txt #all mac
	racadm -r $i -u root -p calvin fwupdate -g -u -a 10.0.8.2  -d fx2_cmc_2.30_A00.bin
}

for i in $(cat ${1})
do
	echo ${i}
	foo ${i}&
done
