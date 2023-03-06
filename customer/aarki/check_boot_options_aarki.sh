#!/bin/bash

# Take the service tag, scan for the IP address.
function get_ip_addr() {
	ip=$( curl --silent \
	-X GET http://10.0.8.2:8000/leases/${mac} \
	| jq '.ip' \
	| sed 's/"//g' \
	)
	#echo $ip;
}

function check_boot_options {
	redfishtool -r ${ip} -u root -p calvin raw GET redfish/v1/Systems/System.Embedded.1/BootOptions/ | jq
}

for mac in $( cat $1 );
do
	#echo $mac;
	get_ip_addr;
	check_boot_options;
done
