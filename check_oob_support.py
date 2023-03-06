#!/usr/bin/python3
import argparse
from io import UnsupportedOperation
import requests
import json
import sys
import requests
from requests.auth import HTTPBasicAuth
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

parser=argparse.ArgumentParser(description="Benchmark.py - Helper script to run various benchmark utilities")
parser.add_argument('-u','--user', help='Username of the BMC', required=True)
parser.add_argument('-p','--password', help='Password of the BMC', required=True)
parser.add_argument('-l', '--list', help='Text file of the BMC IP addresses', required=True)

def check_oob(username: str, password: str, file: str):
    systems             = []
    activated_systems   = []
    unactivated_systems = []
    did_not_query       = []
    with open(file, 'r') as iplist:
        for ip in iplist.readlines():
            systems.append(ip)
            license = query_license(username=username, password=password, ip=str(ip.strip()))
            if license == 'OOB License Activated':
                activated_systems.append(ip)
            elif license == 'OOB License NOT Activated!':
                unactivated_systems.append(ip)
            else:
                did_not_query.append(ip)
            #else:
            #    did_not_query.append(ip)
    print("+--------------------------------------------------------+")
    print("|\t\t\tSummary\t\t\t\t |")
    print("+--------------------------------------------------------+")
    print(f'Total: {len(systems)} | Activated: {len(activated_systems)} | NOT Activated: {len(unactivated_systems)} | Unknown: {len(did_not_query)}')
    


# Since the 'QueryLicense' URI is under a path that requires a license, we need to check the parent-most URI locked by license.
def has_a_license(username: str, password: str, ip: str) -> bool:
    uri     = 'redfish/v1/Managers'
    message = ""
    try:
        response  = requests.get(f'https://{ip}/{uri}', auth=HTTPBasicAuth(username, password), verify=False).json()
        json_response = json.dumps(response)
        if 'error' in response:
            message = response['error']['@Message.ExtendedInfo'][0]['Message']
            if 'unauthorized' in message:
                print(f"{ip} : {message}")
                raise UnsupportedOperation
            else:
            # To make the expected format a bit easier for operators/QC, this message is returned instead:
                print(f"{ip} : OOB License NOT Activated!")
            return False
        else:
            return True
    except Exception as e:
        if 'unauthorized' in message:
            print(f"Failed to query {ip}: Incorrect username/password specified.")
        # If no JSON is returned, system does not support Redfish at all.
        else:
            print(f"Failed to query {ip}: System does not support the Redfish standard")
        raise UnsupportedOperation

def query_license(username: str, password: str, ip: str) -> dict:
    oob_template = {
        'ip'  : ip,
        'oob' : None,

    }
    try:
        is_activated = has_a_license(username=username, password=password, ip=ip)
        if is_activated:
            # In order to query the license info, you need a license to target the QueryLicense URI. Lol.
            uri      = 'redfish/v1/Managers/1/LicenseManager/QueryLicense'
            try:
                response  = requests.get(f'https://{ip}/{uri}', auth=HTTPBasicAuth(username, password), verify=False).json()
                json_resp = json.dumps(response)
                licenses  = response['Licenses']
                for license in licenses:
                    info = json.loads(license)['ProductKey']['Node']['LicenseName']

                    print(f"{ip} : OOB License Activated")
                    if 'OOB' in info:
                        return 'OOB License Activated'
            except Exception as err:
                # Older model systems do not always have the QueryLicense URI defined.
                # However being able to query the Managers route is essentially enough to validate the license is active.
                try:
                    print(f"{ip} : OOB License Activated")
                    return 'OOB License Activated'
                except Exception as old_err:
                    print(old_err)
        else:
            return 'OOB License NOT Activated!'
    except UnsupportedOperation as redfish_not_supported:
        return 'Redfish unsupported for this platform/model.'
        
if __name__ == '__main__':
    args=vars(parser.parse_args())
    username = args['user']
    password = args['password']
    file     = args['list']
    print("Checking OOB License. Please be patient as this may take some time.\n")
    check_oob(username=username, password=password, file=file)