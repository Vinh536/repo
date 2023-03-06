#!/bin/bash

DHCP_SERVER="10.0.8.2"
DHCP_API_PORT="8000"

# Exit early if no text file is passed.
if [[ $# -lt 1 ]]; then
	echo "USAGE: $0 <TEXT_FILE_OF_SERVICE_TAGS>";
	exit 1;
fi

# Keep a running tally of the number of successes and failures.
SUCCESS_CTR=0
FAILURE_CTR=0
TOTAL_CTR=0

FAILURE_LIST=();

SUCCESS_FILE="./bmcip";

# Creates backup of current bmcip text file.
mv bmcip bmcip.backup

for info in $( cat $1);
do
	# Prevent an edge case by capitalizing the input string. Then swap with original input.
	uppercase=$( echo $info | tr '[:lower:]' '[:upper:]' );
	info=$uppercase;
	# Check if the API returned valid info. If it did, output to the screen the following:
	# Service Tag / Asset Tag of target machine; IP address found.
	# Write the IP address to a target file specified by the user.
	api_info=$( curl --silent -X GET http://${DHCP_SERVER}:${DHCP_API_PORT}/leases/$info );
	check_status=$( echo $api_info | jq 'has("404")' );
	# If we got a 404 then we did NOT find any info for the target system!
	# So in this event, continue. Otherwise through a message indicating that nothing was found.
	if [[ $check_status == "true" ]]; then
		FAILURE_CTR=$(( FAILURE_CTR + 1 ));
		echo -e "FAILURE: $info did not find IP address!";
		FAILURE_LIST+=$info;
	else
		IP_ADDRESS=$( echo $api_info | jq .ip | sed 's/"//g');
		SUCCESS_CTR=$(( SUCCESS_CTR + 1 ));
		echo -e "SUCCESS: $info has IP Address: $IP_ADDRESS";
		# Renames old bmcip text file.
#		mv bmip bmcip.backup
		# Write the successful IPs to a target file.
		echo $IP_ADDRESS  >> $SUCCESS_FILE;
			# Creates and sorts through bmcip text file.
			sort bmcip | uniq > temp
			mv temp bmcip
	fi

	TOTAL_CTR=$(( TOTAL_CTR + 1 ));
done

echo -e "TOTAL: $TOTAL_CTR | SUCCESS: $SUCCESS_CTR | FAILURE: $FAILURE_CTR";
echo "Failed systems:";
for info in $FAILURE_LIST;
do
	echo " " $info;
done

