#!/usr/bin/python3
import argparse
from argparse import RawTextHelpFormatter
import subprocess
import time
import os
import requests
import json
import xmltodict
from datetime import datetime

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

def download_latest_catalog():
	# Check if the file does NOT currently exist.
	url = "https://downloads.dell.com/catalog/Catalog.gz"
	get_catalog = subprocess.run(["wget",f"{url}"])
	# Unzip the Catalog. Will be renamed to 'Catalog'.
	subprocess.run(["gunzip",f"{os.getcwd()}/Catalog.gz"])

""" Find the path to the Dell.com download for the EXE file. Use the driver ID to find the correct firmware location we want. """
def make_download_obj(catalog, driver_id, platform):
	template = {
		'id'          : driver_id,
		'platform'    : platform,
		'url'         : None,
		'version'     : None,
		'release date': None
	}
	for element in catalog['Manifest']['SoftwareComponent']:
		#print(json.dumps(element, indent=4))
		if '@packageID' in element.keys():
			if element['@packageID'] == driver_id:
				path= element['@path']
				if '.EXE' in path:
					url                     = f"https://downloads.dell.com/{path}"
					template['url']         = url
					template['version']     = element['@vendorVersion']
					template['release date']= element['@releaseDate']
					return template

if __name__ == '__main__':

	cwd = os.getcwd()

	# Argument Parser
	parser=argparse.ArgumentParser(description="Python Ipmitool Utility", formatter_class=RawTextHelpFormatter)
	parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=True)
	parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)',type=argparse.FileType('r'), required=False)
	parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=True)
	parser.add_argument('-p', '--pass', help='IPMI/BMC IP Password for system(s)', required=True)
	parser.add_argument('-o', '--option', help=usage(), required=False)
	parser.add_argument('-s', '--sleep', help='For list of BMC IP addresses, run sleep command for X seconds')

	args=vars(parser.parse_args())

	ipmi_ip   = args['ip']
	ipmi_user = args['user']
	ipmi_pass = args['pass']

	model_name = None
	# Check the target system.
	output    = subprocess.run(["ipmitool","-I","lanplus","-H",f"{ipmi_ip}","-U",f"{ipmi_user}","-P",f"{ipmi_pass}","fru","print","0"], capture_output=True)
	for line in output.stdout.decode("utf-8").split("\n"):
		if 'Product Name' in line:
			model_name = line.split(":")[1].strip().split(" ")[1]
			break
	#download_latest_catalog()

	info = None
	#with open(f"{cwd}/Catalog", encoding="utf8", errors="ignore") as payload:
	#	info = xmltodict.parse(payload.read())
	#if info is not None:
	#	with open("JSON_Catalog.json", "w") as jsonfile:
	#		jsonfile.write(json.dumps(info))
	with open("JSON_Catalog.json","r") as jsonfile:
		info = json.loads(jsonfile.read())
	firmwares      = []
	firmware_paths = []
	dell_firmwares = []
	JSON = info
	#print(json.dumps(JSON, indent=4))
	for element in JSON["Manifest"]["SoftwareBundle"]:
		#print(JSON['Manifest'].keys())
		if 'TargetSystems' in element.keys():
			# Check if the correct brand was detected in the Catalog.
			if 'Brand' in element['TargetSystems'].keys():
				# For some elements this is a list instead of a dictionary.
				if type(element['TargetSystems']['Brand']) is dict:
					if 'Model' in element['TargetSystems']['Brand'].keys():
						if type(element['TargetSystems']['Brand']['Model']) is dict:
							if 'Display' in element['TargetSystems']['Brand']['Model'].keys():
								text = element['TargetSystems']['Brand']['Model']['Display']['#text']
								if text == model_name:
									firmwares.append(element)
	for element in firmwares:
		if 'Contents' in element.keys():
			if 'Package' in element['Contents'].keys():
				for package in element['Contents']['Package']:
					if '@path' in package.keys():
						if 'EXE' not in package['@path']:
							break
						else:
							pathname = package['@path'].split(".")[0].split("_")
							driver_id= None
							for val in pathname:
								if val == 'WN64':
									break
								driver_id= val
							output   = make_download_obj(catalog=info,driver_id=driver_id, platform=model_name)
							dell_firmwares.append(output)
	# Sort it to make it easier to find the latest firmwares. :D
	dell_firmwares = sorted(dell_firmwares, key=lambda x : datetime.strptime(x['release date'], "%B %d, %Y"))
	for firm in dell_firmwares:
		print(json.dumps(firm, indent=4))
