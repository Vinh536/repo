#!/usr/bin/python3
import requests
import json
import argparse
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import subprocess

parser=argparse.ArgumentParser(description="Python Redfish Client Usage")
parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=False)
parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)', required=False)
parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=False)
parser.add_argument('-p', '--password', help='IPMI/BMC IP Password for system(s)', required=False)
parser.add_argument('-s', '--silent', help='Only show the pass/fail state for each system', required=False, action='store_true')

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def get_bios_settings(ip, username, password, expected_settings, silent_flag=None):
	try:
		uri       = 'redfish/v1/Systems/System.Embedded.1/Bios'
		resp      = requests.get(f'https://{ip}/{uri}', auth=HTTPBasicAuth(username, password), verify = False).json()
		incorrect_settings = []
		service_tag = ""
		for key in resp['Attributes']:
			if key == 'SystemServiceTag':
				service_tag = resp['Attributes']['SystemServiceTag']
			# Compare the current attribute to expected value if it is in the expected_settings dictionary.
			if key in expected_settings.keys():
				if resp['Attributes'][key] != expected_settings[key]:
					current_attribute = {
						"key"   : key,
						"value" : resp['Attributes'][key]
					}
					incorrect_settings.append(current_attribute)
		# If any settings are incorrect, denote which ones diverge from the expected settings.
		message = f'IP: {ip}, Svctag: {service_tag}\n'
		result  = 'N/A'
		if len(incorrect_settings) > 0:
			for setting in incorrect_settings:
				if not silent_flag:
					result_message = f'\nKey: {setting["key"]}\n'
					result_message += f'Expected: {expected_settings[setting["key"]]}\nGot: {setting["value"]}\n'
					message += result_message
				result = 'BIOS - FAIL'
		else:
			message += 'All BIOS settings correct!\n'
			result = 'BIOS - PASS'
		message += f'\nResult: {result}\n'
		print(message)
		if 'Network' in expected_settings.keys():
			is_set = get_pxe_settings(ip, username, password, expected_settings)
			if not is_set:
				print("Result: Network - FAIL")
				raise KeyError
			else:
				print("Result: Network - PASS")
		return message
	except KeyError as err:
		print(f"Skipping {ip}...\n")

""" Some settings such as for add-on NICs can be hard to find through Redfish. As such, we'll use racadm for some things. """
def get_pxe_settings(idrac_ip, idrac_username, idrac_password, expected_settings):
	network_device = expected_settings["Network"]
	current_setting= None
	try:
		output = subprocess.check_output(f"racadm -r {idrac_ip} -u {idrac_username} -p {idrac_password} get {network_device['Device']}", shell=True)
		current_setting = output.decode("utf-8").replace("\r","").split("\n")
		for line in current_setting:
			if 'legacybootproto=' in line:
				current_setting = line.split("=")[1].strip()
				break
		if current_setting == network_device["Setting"]:
			print(f"{network_device['Device']} settings correct!")
			return True
		else:
			raise Exception
	except Exception:
		print(f"Expected: {network_device['Device']} : {network_device['Setting']}")
		print(f"Got: {network_device['Device']} : {current_setting}")
		return False

if __name__ == '__main__':
	args=vars(parser.parse_args())
	ip          = args['ip']
	ipfile      = args['list']
	silent_flag = args['silent']
	if args['user'] is None:
		username = 'root'
	else:
		username = args['user']
	if args['password'] is None:
		password = 'calvin'
	else:
		password = args['password']

	expected_settings = {
        "BIOS" : {
            "Attributes" : {
                "BootMode"  : "Bios",
                "SysProfile": "PerfOptimized"
            }
        },
        "Network" : {
                "Device" : "NIC.NICConfig.5.legacybootproto",
                "Setting": "PXE"
            }
        }

	#expected_settings = {
        #    "BootMode"  : "Bios",
        #    "SysProfile": "PerfOptimized" 
	#}

	results       = []
	success_rate  = 0
	failure_rate  = 0
	total_systems = 0
	if ip:
		result = get_bios_settings(ip, username, password, expected_settings["BIOS"]["Attributes"], silent_flag)
	elif ipfile:
		ips = []
		with open(ipfile, 'r') as f:
			data = f.readlines()
			for item in data:
				if item != "":
					# Remove whitespace to avoid crashing the program.
					ips.append(item.strip())
		for ip in ips:
			get_bios_settings(ip, username, password, expected_settings["BIOS"]["Attributes"], silent_flag)
