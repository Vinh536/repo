#!/bin/bash

# This script will display the hard drive information. Use this to verify all hard drives before sending inventory to QC or Tony.
# Counters
total_ctr=0;
success_ctr=0;
failure_ctr=0;

echo "Enter the amount of drives the order is support to have."; 
read user_input;

for i in $( cat $1 | awk '{print $1}' );
do
	echo -n $i": ";
	# || if condition on left fails, do right side.
	output=$( sshpass -p ocptester ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -t root@$i "cd /opt/MegaRAID/perccli/ && ./perccli /c0 show j" 2> /dev/null || echo "COMMAND_FAILED");
	if [[ ${output} == *"COMMAND_FAILED"* ]]; then
		failure_ctr=$(( failure_ctr + 1 ));
		echo "LOOKUP FAILED FOR: ${i}"
	else
		# Store the output into a temporary variable. Lookup the value against the user input at the end of the else block.
		temp=$( echo ${output}   \
		| jq                     \
		| grep 'Physical Drives' \
		| sed 's/ \|,//g' 	 \
		| cut -f 2 -d ":";
		# Remove any unnecessary whitespace. NOTE: This sed command will remove ALL whitespace (even internal)!
	        #| awk '{print $3}'       \
		)
		#echo ${temp};
		# Now that the variable is captured, NOW compare against the expected input according to the user.
		echo -n "Drive Count: ";
		# Compares user input with output from temp using wild card to search all.
		if [[ ${user_input} == *${temp}* ]]; then
			success_ctr=$(( success_ctr + 1 ));
			echo ${temp};
		else
			failure_ctr=$(( failure_ctr + 1 ));
			echo "Expected: ${user_input}. Got: ${temp}";
		fi
	fi
	total_ctr=$(( total_ctr + 1 ));
done

echo "+=====================================+";
echo -e "| Total: ${total_ctr} | Success: ${success_ctr} | Failed: ${failure_ctr} |";
echo "+=====================================+";

