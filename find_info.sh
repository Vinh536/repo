#!/bin/bash
file_name=$1;

function usage() {
	echo -e "Usage: $0 <Asset_Tag_File>";
	echo "Please pass in a text file to use this script!";
	echo "Exiting...";
	exit 1;
}
# Invoke the above function. If it fails, the script will end before doing ANYTHING else.
if [[ $# -eq 0 ]]; then
	usage;
fi
# Scp's server_info.csv from 10.0.8.41 & makes bmcip list & server_info.csv

#scp root@10.0.8.41:/root/server_info.csv . 
#-p ocptester

# Capture the current working directory.
PWD=$(pwd);

# Make a backup of the old server info file. Just in case...
if [[ -e ${PWD}/server_info.csv ]]; then
	echo "Detected previous server_info file. Making backup to: server_info.csv.old";
	mv ${PWD}/server_info.csv ${PWD}/server_info.csv.old;
fi

echo "Downloading server_info.csv ...";
# 2> /dev/null redirects 'stderr' messages from the screen to the great landfill in the operating system. /dev/null, where all error messages go to die a gruesome zeroized death.
sshpass -p ocptester scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null root@10.0.8.41:/root/server_info.csv . 2> /dev/null;
if [[ -f ${PWD}/server_info.csv ]]; then
	echo "Downloaded file to: ${PWD}/server_info.csv";
fi

for sstags in $(cat $file_name); do  grep -i "$sstags," server_info.csv | tail -n 1; done > temp.csv

cat temp.csv | cut -f 4 -d "," > bmcip
echo "bmcip list created"
wc -l bmcip

cat temp.csv | cut -f 2 -d "," > osip
echo "osip list created"
wc -l osip

mv temp.csv server_info.csv
echo "server_info.csv created"
wc -l server_info.csv

echo "#########################################################"

wc -l $1
