#!/bin/bash
echo -e "SVCTAG \t\t OS IP \t\t BMC IP";
for svctag in $( cat $1 ); 
do
	# Get the OC number for this system. (Loose server)
	ORDER=$( curl --silent -X GET http://10.0.7.170/$svctag | jq -r .order_number );
	# Get the IP Addresses for each system.
	INFO=$( curl --silent -X GET http://10.0.7.170/order/$ORDER/$svctag | jq );
	# The "||" means "if this fails, do the thing on the right". It's basically the "else" in an "if else" statement. But specific to Bash.
	OS_IP=$( echo $INFO | jq -r '.[0]."OS IP"'|| echo "BMC IP not found!" );
	BMC_IP=$( echo $INFO | jq -r '.[].BMC.ip' || echo "BMC IP not found!");
	echo -e "$svctag \t $OS_IP \t $BMC_IP \t";
done
