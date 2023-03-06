#!/usr/bin/bash 

DHCP_SERVER="10.0.8.2"
DHCP_API_PORT="8000"

# Exit early if no text file is passed.
if [[ $# -lt 1 ]]; then
	echo "USAGE: $0 <TEXT_FILE_OF_SERVICE_TAGS>";
	exit 1;
fi

SUCCESS_FILE="./bmcip"

# Creates backup list
mv bmcip_list bmcip_list.backup


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
		echo -e "FAILURE: $info did not find IP address!";
	else
		IP_ADDRESS=$( echo $api_info | jq .ip | sed 's/"//g');
		echo -e "$IP_ADDRESS";
		# Renames old bmcip text file.
#		mv bmip bmcip.backup
		# Write the successful IPs to a target file.
		echo $IP_ADDRESS  >> $SUCCESS_FILE;
			# Creates and sorts through bmcip text file.
			sort bmcip | uniq > temp
			mv temp bmcip_list 
        
	fi

done

echo "##########################################"
echo "# Please wait for output messages:       #"
echo "##########################################"

# Grabs osips: Note: Systems must have booted to live once.
for i in $(cat bmcip_list); do racadm -r $i -u root -p calvin getsysinfo | grep -i "current ip address      = 1" | sed 's/"//g' | awk '{print $5}' ;done > osip_testing

echo "BMCIP list was created with"  && wc -l bmcip_list

echo "OSIP list was created with" && wc -l osip_testing