#!/usr/bin/python3

import argparse
from argparse import RawTextHelpFormatter
import subprocess
import time

# Argument Parser
parser=argparse.ArgumentParser(description="Set PowerEdge port for PXE boot.")
parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=False)
parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=True)
parser.add_argument('-p', '--pass', help='IPMI/BMC IP Password for system(s)', required=True)

args=vars(parser.parse_args())

ipmi_ip   = args['ip']
ipmi_list = args['list']
ipmi_user = args['user']
ipmi_pass = args['pass']

"""
	Some platforms will change the NIC enumeration such that the mezzanine card / "riser card" will be at enumeration 1 (rather than 3).
	As such, we should check the platform to determine which enumeration will be targeted.
	TODO: CHECK IF THIS BREAKS FOR NON-PUBMATIC BUILDS (E.G. QUALYS)!
"""
def get_platform(ip: str, user: str, password: str):
    print(f"Checking platform for {ip}...")
    platform    = subprocess.check_output(f"racadm -r {ip} -u {user} -p {password} getsysinfo", shell=True).decode('utf-8')
    enumeration = None 
    if "PowerEdge R6515" in platform or "PowerEdge R440" in platform:
        # Then the enumeration will be:
        enumeration = "NIC.NICConfig.1.LegacyBootProto"
    else:
        enumeration = "NIC.NICConfig.3.LegacyBootProto"
        #enumeration  = "NIC.NICConfig.1.LegacyBootProto"
    return enumeration
"""
    FQDD = Fully Qualified Device Descriptor.
    This nomenclature is used by Dell to give a human readable enumeration for components in the system (e.g. network cards, storage controllers, etc).
"""
def schedule_job(fqdd: str, ip: str, user: str, password: str):
    print(f"Setting {fqdd} for PXE boot...")
    job_status = subprocess.check_output(f"racadm -r {ip} -u {user} -p {password} set {fqdd} PXE", shell=True).decode('utf-8')
    if 'Successfully' in job_status:
        # Parse out the keyname from the success message since the jobqueue targets this value. It differs from the previous FQDD.
        keyname = None
        for line in job_status.split('\n'):
            if 'Key' in line:
                keyname = str(line.split("=")[1]).split("#")[0]
        if keyname:
            print(f"Setting job for {keyname}...")
            # Now set the job in the jobqueue so that racadm can actually change the value.
            queued = subprocess.check_output(f"racadm -r {ip} -u {user} -p {password} jobqueue create {keyname}", shell=True).decode('utf-8')
            # On success, a job ID will be returned. We can use the "jobqueue view" subcommand to check the status of the running job.
            # NOTE: The JID is randomly generated using the current system clock time as a seed. All systems will have a different job ID.
            # TODO: Add in an output file to save the JID into a dictionary with the iDRAC IP and the JID.
            message = None
            if 'JID' in queued:
                message = f"{ip}: Successfully set {fqdd} for PXE boot!"
            else:
                message = f"{ip}: ERROR! Failed to set {fqdd} for PXE boot. Check if this platform supports this option..."

            print(f"Please make sure to reboot {ip} to allow the changes to take effect!")
            return message


def run(ipmi_ip, ipmi_user, ipmi_pass):
    fqdd = get_platform(ip=ipmi_ip, user=ipmi_user, password=ipmi_pass)
    job  = schedule_job(fqdd=fqdd, ip=ipmi_ip, user=ipmi_user, password=ipmi_pass)

if ipmi_list:
	with open(args['list'].name) as iplist:
		for ip in iplist.readlines():
			ipmi_ip = ip.strip()
			output = run(ipmi_ip, ipmi_user, ipmi_pass)
			print(output)
else:
	output = run(ipmi_ip, ipmi_user, ipmi_pass)
	print(output)
