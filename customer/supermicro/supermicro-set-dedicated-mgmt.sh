#!/bin/bash
# Determine the operating system to determine the path for IPMICFG.
UTILITY="";

if [[ *$( grep "VERSION_CODENAME" /etc/os-release )* == *"bullseye"* ]]; then
    UTILITY=/opt/dmi/IPMICFG;
else
    UTILITY=/root/IPMICFG;
fi

echo "${UTILITY}...";

# Determine the manufacturer.
manufacturer=$( cat /sys/class/dmi/id/sys_vendor )
# These are the outputs from checking the management LAN's configuration.
if [[ ${manufacturer} == *"Supermicro"* ]]; then
	DEDICATED_LAN="00";
	SHARED_LAN="01";
	FAILOVER_LAN="02";

	# 0x30 0x70 0x0C is the raw command to target the BMC LAN.
	# The single '0' means "do not modify value". Will print out the current setting.
	# A '1' followed by a space and then either 0,1, or 2, will change the current setting.
	# 0x30 0x70 0x0C 1 0 // This will set dedicated mode.
	# 0x30 0x70 0x0C 1 1 // This will set shared LAN mode.
	# 0x30 0x70 0x0C 1 2 // This will set Failover mode.

	current_mode=$(${UTILITY} -raw 0x30 0x70 0x0C 0);
	
	if [[ ${current_mode} == *${FAILOVER_LAN}* ]]; then
		echo "Failover LAN state detected";
		echo "Changing to Dedicated LAN...";
		${UTILITY} -raw 0x30 0x70 0x0C 1 0;
		echo "Verifying changes...";
	
	# Systems WITHOUT a BMC may come in shared LAN state. For these, do not modify.
	elif [[ ${current_mode} == *${SHARED_LAN}* && -e /dev/ipmi0 ]]; then
		echo "Shared LAN state detected.";
		echo "Changing to Dedicated LAN...";
		${UTILITY} -raw 0x30 0x70 0x0C 1 0;
		echo "Verifying changes...";
	else
		echo "Dedicated LAN state already set.";
	fi
	
	# Do one last check to make sure the setting was changed successfully.
	new_mode=$(${UTILITY} -raw 0x30 0x70 0x0C 0);
	
	if [[ ${new_mode} == *${DEDICATED_LAN}* ]]; then
		echo "PASS";
		echo "BMC is in proper state: Dedicated LAN";
	else
		echo "FAIL";
		echo "BMC is not in correct state.";
		echo "Expected: Dedicated LAN";
		if [[ ${new_mode} == *${SHARED_LAN}* ]]; then
			echo "Got: Shared LAN";
		elif [[ ${new_mode} == *${FAILOVER_LAN}* ]]; then
			echo "Got: Failover LAN";
		else
			echo "Got: Unknown state";
		fi
	fi
else
	echo "Not a Supermicro system...";
fi
