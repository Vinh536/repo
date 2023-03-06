#!/usr/bin/python3

import argparse
from argparse import RawTextHelpFormatter
import subprocess
import time
from collections import Counter
import os
import json
import time

def usage():
	message = """This script will reboot the systems 6 times every 5 minutes. Check SEL Logs for possible errors. If no errors pass systems to QC."""
	return message

# Argument Parser
parser=argparse.ArgumentParser(description="Python Ipmitool Utility", formatter_class=RawTextHelpFormatter)
parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=False)
parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=False)
parser.add_argument('-p', '--pass', help='IPMI/BMC IP Password for system(s)', required=False)
# Default to pausing for <X> minutes.
parser.add_argument('-s', '--sleep', help='For list of BMC IP addresses, run sleep command for X seconds', default=1)

args=vars(parser.parse_args())

ipmi_ip   = args['ip']
ipmi_list = args['list']
ipmi_user = args['user']
ipmi_pass = args['pass']
pause     = args['sleep']

# If no username or password were passed in, read them in from an environment file. The assumption is this file is in the same working directory.
if not ipmi_user or not ipmi_pass:
	with open("./.secrets","r") as secretfile:
		secrets = secretfile.readlines()
		for line in secrets:
			if 'USERNAME' in line:
				ipmi_user = line.split("=")[1].strip()
			if 'PASSWORD' in line:
				ipmi_pass = line.split("=")[1].strip()

def run(ipmi_ip, ipmi_user, ipmi_pass, svctag, count):
	# Return a dictionary. Initialize it with some empty data.
	template= {
		'state'     : None,
		'message'   : None,
		'ip'        : None,
		'svctag'    : svctag,
		'Rebooted'  : count + 1
	}
	command = f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis power reset'
	result  = subprocess.run(command, capture_output=True, shell=True)
	stdout  = result.stdout.decode("utf-8")
	stderr  = result.stderr.decode("utf-8")
	# Check if an error happened. For example, the incorrect password was provided. Or, the machine could not be reached.
	if len(stderr) > 0:
		template['state']   = 'Failed!'
		template['message'] = stderr.strip()
	else:
		template['state']   = 'Success!'
		template['ip']      = ipmi_ip
		template['message'] = stdout.strip()
	return template

def get_svctag(ipmi_ip, ipmi_user, ipmi_pass):
	result  = subprocess.run(f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} fru print 0', capture_output=True, shell=True)
	stdout  = result.stdout.decode("utf-8")
	stderr  = result.stderr.decode("utf-8")
	# This clearly failed if anything is in standard error.
	if len(stderr) > 0:
		return None
	for line in stdout.split("\n"):
		if 'Product Serial' in line:
			svctag = line.split(":")[1].strip()
			return svctag

# Initialize counter
#count = 1
# Iterate the loop 6 times
#while count < 7:
	# Increment the counter
#	count = count + 1
if __name__ == '__main__':
	# Can change "max_counter" name and the rest will change and work.
	max_counter = 7
	sleep_timer = 5
	output    = None
	# Initalize a counter.
	counter= 0
	# Store one or many IPs into a list. May be a list of one element or many elements.
	ips          = []
	success_list = []
	failure_list = []
	# Contain the IP and the service tag in a dictionary so we only need to look up the service tag once.
	if ipmi_list:
		with open(args['list'].name) as iplist:
			for ip in iplist:
				template = {
					'ip'     : None,
					'svctag' : None
				}
				template['ip'] = ip.strip()
				svctag         = get_svctag(ipmi_ip=template['ip'], ipmi_user=ipmi_user, ipmi_pass=ipmi_pass)
				if svctag is not None:
					template['svctag'] = svctag
				ips.append(template)
	else:
		template['ip'] = ipmi_ip.strip()
		svctag         = get_svctag(ipmi_ip=template['ip'], ipmi_user=ipmi_user, ipmi_pass=ipmi_pass)
		if svctag is not None:
			template['svctag'] = svctag
			ips.append(template)

	while counter < max_counter:
		# Iterate over the list of IPs. Continue running the 'run' function until the counter hits the max_counter.
		for ip in ips:
			# Edge case #1: A system failed for some reason. Lets remove it from the list.
			output = run(ipmi_ip=ip['ip'], ipmi_user=ipmi_user, ipmi_pass=ipmi_pass,svctag=ip['svctag'], count=counter)
			if output is None:
				if output['state'] == 'Failed!':
					ips.remove(ip)
					failure_list.append(ip)
			else:
				print(json.dumps(output, indent=4))
		counter += 1
		# Check if a sleep value was passed in. If so, pause execution for that many seconds.
		if pause:
			time.sleep(int(pause) * 60)
			#time.sleep(sleep_timer * 60)
	print("===================================")
	print(f"Total: {len(ips) + len(failure_list)} | Success: {len(ips)} | Failure: {len(failure_list)}") 
	print("===================================")
