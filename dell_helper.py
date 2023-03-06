#!/usr/bin/python3
#import multiprocessing
import concurrent.futures
import json
import datetime
import sys
import argparse
from argparse import RawTextHelpFormatter
import subprocess
import time
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def usage():
	message = """ OPTIONS:
    jobs      - Check the job queue
    logs      - Check the system event log
    readings  - Get thermal and voltage readings of the unit(s).
"""
	return message

# Argument Parser
parser=argparse.ArgumentParser(description="Dell Helper Script", formatter_class=RawTextHelpFormatter)
parser.add_argument('-i', '--ip', help='IPMI/BMC IP Address', required=False)
parser.add_argument('-l', '--list', help='List of IPMI/BMC IP Addresses (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-u', '--user', help='IPMI/BMC IP Username for system(s)', required=True)
parser.add_argument('-p', '--pass', help='IPMI/BMC IP Password for system(s)', required=True)
parser.add_argument('-o', '--option', help=usage(), required=True)

# BMC IP: 10.0.7.16
args=vars(parser.parse_args())

# Check the manufacturer of the system to verify that the platform is Dell.
# This script will ONLY work for Dell EMC systems for the time being.
def is_dell(ipmi_ip, ipmi_user, ipmi_pass):
    fru  = subprocess.run(["/usr/bin/ipmitool","-I","lanplus","-H",ipmi_ip,"-U",ipmi_user,"-P",ipmi_pass,"fru","print","0"], capture_output=True)
    errors = fru.stderr.decode("utf-8")
    if len(errors) > 0:
        print(json.dumps({'ip' : ipmi_ip, 'message' : errors.strip()}))
        return False
    
    output = fru.stdout.decode("utf-8")
    for line in output.splitlines():
        if 'Product Manufacturer' in line:
            data = line.split(":")[1].strip()
            if data.upper() == "DELL":
                return True
    return False

def redfish(ipmi_ip, ipmi_user, ipmi_pass, uri):
    url      = f"https://{ipmi_ip}{uri}"
    auth     = HTTPBasicAuth(ipmi_user, ipmi_pass)
    response = requests.get(url, verify=False, auth=auth)
    if response.status_code == 200:
        return response.json()
    return None

def get_jobs(ipmi_ip, ipmi_user, ipmi_pass):
    jobs     = []
    uri      = "/redfish/v1/JobService/Jobs"
    jobqueue = redfish(ipmi_ip, ipmi_user, ipmi_pass, uri)
    if jobqueue:
        if 'Members' in jobqueue.keys():
            for member in jobqueue['Members']:
                job_id = member["@odata.id"]
                r      = redfish(ipmi_ip, ipmi_user, ipmi_pass, job_id)
                if r:
                    data     = r
                    template = {
                        'id'   : data['Id'],
                        'name' : data['Name'],
                        'state': data['JobState'] 
                    }
                    jobs.append(template)
        temp = redfish(ipmi_ip, ipmi_user, ipmi_pass, uri="/redfish/v1/")
        # Get the Service Tag for convenience.
        svctag = temp['Oem']['Dell']['ServiceTag']
        information = {
            'ip'    : ipmi_ip,
            'serial': svctag,
            'jobs'  : jobs

        }
        return json.dumps(information)

def get_sel(ipmi_ip, ipmi_user, ipmi_pass):
    uri     = "/redfish/v1/Managers/iDRAC.Embedded.1/LogServices/Sel/Entries"
    logs    = []
    entries = redfish(ipmi_ip=ipmi_ip, ipmi_user=ipmi_user, ipmi_pass=ipmi_pass, uri=uri)
    if entries:
        if 'Members' in entries.keys():
            for member in entries['Members']:
                job_id = member["@odata.id"]
                r      = redfish(ipmi_ip, ipmi_user, ipmi_pass, job_id)
                if r:
                    data     = r
                    template = {
                        'id'       : data['Id'],
                        'timestamp': data['Created'],
                        'severity' : data['Severity'],
                        'message'  : data['Message'] 
                    }
                    logs.append(template)
        temp = redfish(ipmi_ip, ipmi_user, ipmi_pass, uri="/redfish/v1/")
        # Get the Service Tag for convenience.
        svctag = temp['Oem']['Dell']['ServiceTag']
        information = {
        'ip'    : ipmi_ip,
        'serial': svctag,
        'logs'  : logs

        }
        return json.dumps(information)

def get_readings(ipmi_ip, ipmi_user, ipmi_pass):
    thermal_uri      = "/redfish/v1/Chassis/System.Embedded.1/Thermal"
    voltage_uri       = "/redfish/v1/Chassis/System.Embedded.1/Power"
    temp = redfish(ipmi_ip, ipmi_user, ipmi_pass, uri="/redfish/v1/")
    # Get the Service Tag for convenience.
    svctag = temp['Oem']['Dell']['ServiceTag']
    information = {
        'ip'           : ipmi_ip,
        'serial'       : svctag,
        'temperatures' : [],
        'voltages'     : []
    }
    thermal_readings = redfish(ipmi_ip=ipmi_ip, ipmi_user=ipmi_user, ipmi_pass=ipmi_pass, uri=thermal_uri)
    voltage_readings = redfish(ipmi_ip=ipmi_ip, ipmi_user=ipmi_user, ipmi_pass=ipmi_pass, uri=voltage_uri)
    if thermal_readings:
        for reading in thermal_readings['Temperatures']:
            component = {
                'name'        : reading['Name'],
                'temperature' : reading['ReadingCelsius'],
                'health'      : reading['Status']['Health']
            }
            information['temperatures'].append(component)
    if voltage_readings:
        for reading in voltage_readings['Voltages']:
            if reading['ReadingVolts'] == None:
                continue
            component = {
                'name'    : reading['Name'],
                'voltage' : reading['ReadingVolts'],
                'health'  : reading['Status']['Health']
            }
            information['voltages'].append(component)
    return json.dumps(information)

if __name__ == '__main__':
    args=vars(parser.parse_args())
    ipmi_ip     = args['ip']
    ipmi_list   = args['list']
    ipmi_user   = args['user']
    ipmi_pass   = args['pass']
    ipmi_option = args['option']
    
    # Instantiate / create the array of tasks / jobs to run.
    processes   = []
    iplist      = []
    return_val  = {}
    if ipmi_list is not None and ipmi_ip is None:
        with open(args['list'].name, "r") as filename:
            data = filename.readlines()
            for d in data:
                iplist.append(d.strip())
    elif ipmi_ip is not None and ipmi_list is None:
        iplist.append(str(ipmi_ip))
    else:
        print("Error! Please ONLY use `--ip` OR `--list`! Do NOT use both at the same time! Exiting...")
        sys.exit(1)

    function_name = None
    for ip in iplist:
        if is_dell(ipmi_ip=ip, ipmi_user=ipmi_user, ipmi_pass=ipmi_pass):
            # Check which option the user passed in.
            # Use the specified option to determine the name of the function to invoke.
            if ipmi_option.lower() == 'jobs':
                function_name = get_jobs
            elif ipmi_option.lower() == 'logs':
                function_name = get_sel
            elif ipmi_option.lower() == 'readings':
                function_name = get_readings
            else:
                print("Invalid option specified! Valid options:")
                print(usage())
                sys.exit(1)
    
    if function_name is not None:
        """
        # Create a series of worker processes. Attempt to set the amount to the amount of available CPU cores (e.g. 4 on my laptop).
        with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
            # Note: The 'apply' method is blocking and will wait for each request to finish. 'apply_async' is slightly better for big batches of systems to work with.
            process = pool.apply_async(
                function_name, 
                (ip, ipmi_user, ipmi_pass)
            )
            print(process.get(timeout=30))
        """
        with concurrent.futures.ThreadPoolExecutor() as executor:
            responses = []
            for ip in iplist:
                responses.append(executor.submit(function_name, ipmi_ip=ip, ipmi_user=ipmi_user, ipmi_pass=ipmi_pass))
            for response in concurrent.futures.as_completed(responses):
                print(response.result())