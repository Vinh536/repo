#!/bin/bash
# This program will check the job status of Dell EMC systems.
if [[ $# -lt 1 ]]; then
	echo "USAGE: $0 <LIST_OF_BMC_IPS>";
	exit 1;
fi

for ip in $( cat $1 ); do
	echo "=========================";
	echo $ip;
	jobs=$( curl --silent -k -u root:calvin -X GET https://$ip/redfish/v1/JobService/Jobs | jq -r '.Members[]."@odata.id"' ); 
	for job in $jobs;
	do
		curl -k -u root:calvin --silent -X GET https://$ip$job | jq -r '.Name,.JobState,.Messages[]."Message"'; 
	done
	echo "=========================";

done
