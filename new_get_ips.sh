#!/bin/bash
echo "SERIAL | OS IP | BMC IP";
echo "+======================+";
for i in $( cat $1 );
do
	hyperlink=$( curl --silent -X GET http://10.0.7.170/$i | jq -r '.Hyperlink' );
	DATA=$( curl --silent -X GET $hyperlink | jq );
	SERIAL=$( echo $DATA | jq -r '.serial' );
	OS_IP=$( echo $DATA | jq -r '."OS IP"' );
	BMC_IP=$( echo $DATA | jq -r '.bmc.ip' );
	echo -e "$SERIAL  | $OS_IP | $BMC_IP";
done
