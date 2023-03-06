#!/usr/bin/python3

import argparse
from argparse import RawTextHelpFormatter
import subprocess
import time

def usage():
	message = """ OPTIONS:
	bios      - Boot to bios
	pxe       - Boot to PXE
	off       - Turn system off
	on        - Turn system on
	reset     - Power cycle the system
	bmc_reset - Reset the BMC
	blink     - Turn the system light on
	noblink   - Turn the system light off
        clear     - Clear the System Event Log
"""
	return message

# Argument Parser
parser=argparse.ArgumentParser(description="Python Ipmitool Utility", formatter_class=RawTextHelpFormatter)
parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=False)
parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=True)
parser.add_argument('-p', '--pass', help='IPMI/BMC IP Password for system(s)', required=True)
parser.add_argument('-o', '--option', help=usage(), required=True)
parser.add_argument('-s', '--sleep', help='For list of BMC IP addresses, run sleep command for X seconds')

args=vars(parser.parse_args())

ipmi_ip   = args['ip']
ipmi_list = args['list']
ipmi_user = args['user']
ipmi_pass = args['pass']
ipmi_option = args['option']
pause = args['sleep']
def run(ipmi_ip, ipmi_user, ipmi_pass, ipmi_option):
	options = {
        'bios'      : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis bootdev bios',
        'pxe'       : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis bootdev pxe',
        'off'       : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis power off',
        'on'        : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis power on',
        'reset'     : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis power reset',
        'bmc_reset' : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} bmc reset cold',
        'blink'     : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis identify force',
        'noblink'   : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} chassis identify 0',
        'clear'     : f'ipmitool -I lanplus -H {ipmi_ip} -U {ipmi_user} -P {ipmi_pass} sel clear',
	}
	if ipmi_option in options:
		option = subprocess.check_output(options[ipmi_option], shell=True)
		return option.decode('utf-8')
	else:
		return None

if ipmi_list:
	with open(args['list'].name) as iplist:
		for ip in iplist:
			ipmi_ip = ip.strip()
			if pause:
				time.sleep(int(pause))
				output = run(ipmi_ip, ipmi_user, ipmi_pass, ipmi_option)
				print(output)
			else:
				output = run(ipmi_ip, ipmi_user, ipmi_pass, ipmi_option)
				print(output)

else:
	output = run(ipmi_ip, ipmi_user, ipmi_pass, ipmi_option)
	print(output)
