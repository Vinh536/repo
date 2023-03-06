#!/bin/bash

# Exit early if the user does not provide a list of IPs to target.
if [[ $# -lt 1 ]]; then
	echo "USAGE: $0 <OS IP LIST>";
	exit 1;
fi

for ip in $( cat $1 );
do
	#PING_SUCCESS=$( ping ${ip} -t 1 -c 1 && echo "GOOD" || echo "BAD" )
	#echo $PING_SUCCESS;
	#if [[ ${PING_SUCCESS} == "GOOD" ]]; then
		echo "Targeting ${ip} ...";
		curl --silent -X 'POST' \
	  	'http://'${ip}'/services/stressapptest?state=stop' \
	  	-H 'accept: application/json' | jq
	#else
	#	echo "FAILED TO RUN STRESS TEST FOR: $i";
	#fi
done
