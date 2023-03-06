#!/bin/bash
# Customer: Xamount
# Purpose: Set the BIOS version to the version locked in by the customer.
# * If the customer specific BIOS is loaded, then attempt to configure the BIOS settings (requires an OOB license).
# * If the BIOS settings fail to be loaded, then log an error indicating the BIOS was not set correctly.

CUSTOMER_NAME="xamount";
CUSTOMER_BMC_USER="ADMIN";
CUSTOMER_BMC_PASSWORD="Qualcomm5G";
# Various boolean (true/false) flags to determine if we should even ATTEMPT to flash BIOS binary or BIOS settings XML file.
IS_BIOS_SET_FLAG=0;
IS_OOB_LICENSE_ACTIVATED=0;
# Exit early if this is being performed on a system clearly NOT for the customer.
UNSUPPORTED_PLATFORM_DETECTED=0;

REPO_IP="10.0.8.41";
REPOSITORY="http://${REPO_IP}/xamount/";

# Check if we are in Debian 10 or Debian 11. Base the route to smc_sum based on this.
	if [[ $( grep -i "VERSION_ID" /etc/os-release ) == *"11"* ]]; then
		SUM=/usr/local/bin/smc_sum
		IPMICFG=/opt/dmi/IPMICFG
	else
		SUM=/root/smc_sum
		IPMICFG=/root/IPMICFG
	fi

# Is it the X11DPi-NT, X12DPi-N6, or a different platform the customer is currently using?
# Use the platform to determine the customer BIOS version. Defaults to the X11DPi-NT model.
function get_platform() {
	motherboard_model=$(cat /sys/class/dmi/id/board_name);
	if [[ ${motherboard_model} == *"X11DPi-NT"* ]]; then
		CUSTOMER_BIOS="3.6";
		CUSTOMER_BIOS_BINARY=${REPO_IP}/"xamount"/${motherboard_model}/"bios3.6";
		CUSTOMER_BIOS_BINARY_CHECKSUM="c0ab77b64dd630441257a0a0696b5440";
		CUSTOMER_BIOS_SETTINGS_XML=${REPO_IP}/"xamount"/${motherboard_model}/"Xamount_X11DPi-NT_BIOS_Settings.xml";
		CUSTOMER_BIOS_SETTINGS_CHECKSUM="358b7231085026557b0c9bac6aa6ff1c";
		CUSTOMER_BMC_VERSION="01.61";
		CUSTOMER_BMC_BINARY=${REPO_IP}/"xamount"/${motherboard_model}/"ipmi161.bin";
	elif [[ ${motherboard_model} == *"X12DPi-N6"* ]]; then
		CUSTOMER_BIOS="1.1b.V1";
		CUSTOMER_BIOS_BINARY=${REPO_IP}/"xamount"/${motherboard_model}/"X12DPi-NT6_BIOS_1.1b.V1.bin";
		CUSTOMER_BIOS_BINARY_CHECKSUM="4d4f591ef2322ae6f392679a67ef94ed";
		CUSTOMER_BIOS_SETTINGS_XML=${REPO_IP}/"xamount"/${motherboard_model}/"Xamount_X12DPi-N6_BIOS_Settings.xml";
		CUSTOMER_BIOS_SETTINGS_CHECKSUM="bbcee6e56fce1724d5d678d5d697fb66";
		CUSTOMER_BMC_BINARY=${REPO_IP}/"xamount"/${motherboard_model}/"BMC_X12AST2600-ROT-5201MS_20211022_01.00.21_STDsp.bin";
		CUSTOMER_BMC_VERSION="01.00.21";
		CUSTOMER_BMC_VERSION_CHECKSUM="be308a41dd9459e94fca6eca5223e6a9";
	else
		UNSUPPORTED_PLATFORM_DETECTED=1;
	fi
}

function check_bios_version() {
    CURRENT_BIOS=$(cat /sys/class/dmi/id/bios_version)
    if [[ ${CURRENT_BIOS} == ${CUSTOMER_BIOS} ]]; then
		echo "Customer BIOS version is already set. Skipping BIOS flash.";
		IS_BIOS_SET_FLAG=1;
    else
		echo "Incorrect BIOS version detected. Will attempt to load the correct BIOS with /root/smc_sum. DO NOT REBOOT THE SYSTEM!";
    fi
}

function flash_bios() {
	# Check the checksum of the customer BIOS. If the checksum does not match, exit early.
	CHECKSUM_BINARY=$(md5sum ${CUSTOMER_BIOS_BINARY} | awk '{print $1}' );
	if [[ ${CHECKSUM_BINARY} == *${CUSTOMER_BIOS_BINARY_CHECKSUM}* ]]; then
		echo "Beginning BIOS flash...";
        if [[ 'X11DPi-NT' == *${motherboard_model}* ]]; then
			${SUM} -c UpdateBios --file ${CUSTOMER_BIOS_BINARY} | tee /tmp/checking_bios_flash_result.txt;
        else
        	# First we need to assign an IP address for the Redfish_HI device 'usb0'.
            dhclient usb0;
			${SUM} -c UpdateBios -I Redfish_HI -U ADMIN -P ${CUSTOMER_BMC_PASSWORD} --file ${CUSTOMER_BIOS_BINARY} --reboot \
	| tee /tmp/checking_bios_flash_result.txt;
			echo "SYSTEM WILL REBOOT AUTOMATICALLY! DO NOT REMOVE POWER FROM THE UNIT!";
			sleep 30;
		fi
		if [[ $(cat /tmp/checking_bios_flash_result.txt) == *"Manual"* ]]; then
			echo "FILE DESCRIPTOR TABLE (FDT) IS DIFFERENT! SYSTEM WILL REBOOT IN 30 SECONDS! RE-RUN SCRIPT ON REBOOT!";
			sleep 30;
			reboot;
		else
			echo "BIOS FLASH COMPLETED! Please reboot for changes to go into effect!";
			echo "DO NOT USE IPMITOOL CHASSIS POWER RESET! THE OS MUST CALL 'reboot' IN ORDER TO PUT THE ME INTO FLASH MODE!";
		fi
	else
		echo -e "Incorrect Md5 Checksum detected!\nCalculated ${CHECKSUM_BINARY}\nShould be: ${CUSTOMER_BIOS_BINARY_CHECKSUM}";
		exit 1;
	fi
}

function check_bmc_version() {
	CURRENT_BMC=$( ${IPMICFG} -ver | awk '{print $3}');
	if [[ ${CUSTOMER_BMC_VERSION} == *${CURRENT_BMC}* ]]; then
		echo -e "Current BMC version is already at customer version: ${CUSTOMER_BMC_VERSION}";
		IS_BMC_SET_FLAG=1;
	fi
}

function flash_bmc() {
	if [[ ${motherboard_model} == *"X11"* ]]; then
		if [[ ${IS_BMC_SET_FLAG} -ne 1 ]]; then
			echo "FLASHING BMC. DO NOT INTERRUPT THIS PROCESS!"
			${SUM} -c UpdateBmc --file ${CUSTOMER_BMC_BINARY} --overwrite_cfg --overwrite_sdr;
			echo "Checking if BMC is responding again. This may take 30 seconds...";
			# Check if the BMC is responding again.
			check_bmc_response=$(ipmitool lan print)
			if [[ ${check_bmc_response} == *"Error"* ]]; then
				echo "BMC still not responding. Waiting an additional 30 seconds...";
				sleep 30;
			fi
			# Reset the BMC password to customer specifications.
			echo "Setting customer password...";
			ipmitool user set password 2 ${CUSTOMER_BMC_PASSWORD};
		fi
	elif [[ ${motherboard_model} == *"X12"* ]]; then
		if [[ ${IS_BMC_SET_FLAG} -ne 1 ]]; then
			# We need to set up an IP address on the Redfish_HI interface to allow smc_sum to work correctly.
			dhclient usb0;
			echo "FLASHING BMC. DO NOT INTERRUPT THIS PROCESS!"
			${SUM} -c UpdateBmc -I Redfish_HI -u ${CUSTOMER_BMC_USER} -p ${CUSTOMER_BMC_PASSWORD} --file ${CUSTOMER_BMC_BINARY} --overwrite_cfg --overwrite_sdr;
			echo "Checking if BMC is responding again. This may take 30 seconds...";
			# Check if the BMC is responding again.
			check_bmc_response=$(ipmitool lan print)
			if [[ ${check_bmc_response} == *"Error"* ]]; then
				echo "BMC still not responding. Waiting an additional 30 seconds...";
				sleep 30;
			fi
			# Reset the BMC password to customer specifications.
			echo "Setting customer password...";
			ipmitool user set password 2 ${CUSTOMER_BMC_PASSWORD};
		fi
	else
		echo "UNSUPPORTED PLATFORM! SKIPPING!";
	fi
}

function set_bios_settings() {
	# First we will need to check to see if the OOB license is activated. This is a REQUIREMENT to use /root/smc_sum to load the correct BIOS settings.
	echo "Checking for OOB License...Please wait...";
	CHECK_OOB=$( $SUM -c CheckOOBSupport );
	if [[ ${CHECK_OOB} == *"SFT-OOB-LIC"* ]]; then
		echo "OOB License is activated. Will attempt to load the customer specific BIOS settings. Please wait...";
		# Next, verify that the XML checksum is consistent with our previous batches. If not, exit early and alert the operator.
		CHECKSUM_XML=$(md5sum ${CUSTOMER_BIOS_SETTINGS_XML} | awk '{print $1}');
		if [[ ${CHECKSUM_XML} == ${CUSTOMER_BIOS_SETTINGS_CHECKSUM} ]]; then
			echo -e "Loading BIOS settings from ${CUSTOMER_BIOS_SETTINGS_XML} ...";
			${SUM} -c ChangeBiosCfg --file ${CUSTOMER_BIOS_SETTINGS_XML};
		else
			echo -e "Incorrect Md5 checksum detected!\nCalculated ${CHECKSUM_XML}\nShould be: ${CUSTOMER_BIOS_SETTINGS_CHECKSUM}";
			exit 1;
		fi
	else
		echo "OOB License is NOT activated! The OOB license MUST be activated in order to load the customer BIOS settings...";
		exit 1;
	fi
}

# ============ #
# !!! MAIN !!! #
# ============ #
get_platform;

if [[ ${UNSUPPORTED_PLATFORM_DETECTED} -eq 1 ]]; then
	echo "ERROR! Unsupported platform detected! This script is ONLY intended to be ran for the following customer: ${CUSTOMER_NAME}";
	exit 1;
else
	# We need to set the BMC Password before we can perform an in-band update.
	ipmitool user set password 2 ${CUSTOMER_BMC_PASSWORD};
	# The files are inside the computer.
	# Then skip re-downloading the files!
	if [[ ! -d "/root/10.0.8.41" ]]; then
		wget --recursive --no-parent ${REPOSITORY};
	fi
fi

echo "Supported platform detected. Checking BMC version...";
check_bmc_version;
if [[ ${IS_BMC_SET_FLAG} -ne 1 ]]; then
	flash_bmc;
fi

echo "Supported platform detected. Checking BIOS version...";
check_bios_version;
if [[ ${IS_BIOS_SET_FLAG} -ne 1 ]]; then
	flash_bios;
elif [[ ${IS_BIOS_SET_FLAG} -eq 1 ]]; then
	set_bios_settings;
fi
