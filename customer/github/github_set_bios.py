#!/usr/bin/python3
import json
import requests
import sys
import subprocess
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Most of this code is thanks to the following documentation:
# Source: https://dl.dell.com/manuals/all-products/esuprt_software/esuprt_it_ops_datcentr_mgmt/dell-management-solution-resources_white-papers11_en-us.pdf

""" Add to the job queue and reboot the system """
def set_job(idrac_ip, idrac_username="root", idrac_password="calvin", reboot_flag=False):
    url     = f"https://{idrac_ip}/redfish/v1/Managers/iDRAC.Embedded.1/Jobs"
    payload = { "TargetSettingsURI":"/redfish/v1/Systems/System.Embedded.1/Bios/Settings" }
    headers = {'content-type' : 'application/json'}
    response = requests.post(url, data=json.dumps(payload), headers=headers,
verify=False,auth=(idrac_username, idrac_password))
    if response.status_code == 200:
        print(f"{idrac_ip}: Added BIOS settings to job queue.")

""" LegacyBootProto appears to not really be supported in Redfish? So let's split the dictionary into three components:
    {
        "BIOS"    : {"Attributes" : {KEYS:VALUE}},
        "Network" : {NETWORK_FQDD : {KEY:VALUE}}
    }
"""
def set_bios(idrac_ip, idrac_username, idrac_password, bios_settings):
    headers = {'content-type' : 'application/json'}
    url = f"https://{idrac_ip}/redfish/v1/Systems/System.Embedded.1/Bios/Settings"
    # Check if network device needs to be modified.
    if "Network" in bios_settings.keys():
        # Modify the object's setting to allow it to be appended to the job queue.
        try:
            output = subprocess.run(f"racadm -r {idrac_ip} -u {idrac_username} -p {idrac_password} set {bios_settings['Network']['Device']} {bios_settings['Network']['Setting']}" \
                     , shell=True, capture_output=True).stdout.decode("utf-8")
            if 'Success' in output:
                info = output.replace("\r","").split("\n")
                key = None
                for line in info:
                    if 'Key=' in line:
                        key = "".join(line.split("=")[1]).split("#")[0]
                        print(key)
                if key:
                    subprocess.run(f"racadm -r {idrac_ip} -u {idrac_username} -p {idrac_password} jobqueue create {key}", shell=True)
                    print(f"Configuration network job for {idrac_ip}")
                else:
                    print(f"Failed to create network configuration job for {idrac_ip}")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred for {idrac_ip} during settings configuration... {str(e)}")
    response = requests.patch(url, data=json.dumps(bios_settings["BIOS"]), headers=headers, verify=False, auth=(idrac_username, idrac_password))
    if response.status_code == 200:
        set_job(idrac_ip)
    else:
        print(response.status_code)
        print(json.dumps(response.text))

if __name__ == '__main__':
    bios_settings = {
        "BIOS" : {
            "Attributes" : {
                "BootMode"  : "Bios",
                "SysProfile": "PerfOptimized",
                "SerialComm": "OnConRedirCom1",
		"SetBootOrderEn": "NIC.Slot.2-1-1,NIC.Integrated.1-1-1"
            }
        },
        "Network" : {
            "Device" : "NIC.NICConfig.5.legacybootproto",
            "Setting": "PXE"
        }
    }

    idrac_username = "root"
    idrac_password = "calvin"

    with open(sys.argv[1], "r") as iplist:
        idrac_ips = iplist.readlines()
        for idrac_ip in idrac_ips:
            set_bios(idrac_ip.strip(), idrac_username, idrac_password, bios_settings)
