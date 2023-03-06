#!/usr/bin/python3
import json
import argparse
import requests

parser=argparse.ArgumentParser(description="Build RAID")
parser.add_argument('-i', '--ip', help='Single IP address of one machine', required=False)
parser.add_argument('-l', '--list', help='List of ip addresses',type=argparse.FileType('r'), required=False)

""" Use one of the system(s) to get the available drives behind the RAID controller."""
def get_drives(ip):
    drives  = None
    response= requests.get(f"http://{ip}/inventory")
    if response:
        data  = response.json()
        try:
            drives = data['Storage']['Offboard']['info']['Physical Drives']['Drives']
        except KeyError:
            return None
    return drives

def get_controller(ip):
    id  = None
    response= requests.get(f"http://{ip}/inventory")
    if response:
        data  = response.json()
        try:
            id = data['Storage']['Offboard']['id']
        except KeyError:
            return None
    return id

if __name__ == '__main__':
    args      = vars(parser.parse_args())
    single_ip = args['ip']
    iplist    = args['list']
    if iplist:
        with open(iplist.name, "r") as fname:
            iplist = fname.readlines()
            single_ip = iplist[0].strip()
    drives    = get_drives(single_ip)
    ctrl_id   = get_controller(single_ip)
    drive_ctr = 0
    print("Current Available Drives:")
    for drive in drives:
        drv_state = drive['State']
        drv_size  = drive['Capacity']
        print(f"#{drive_ctr}|{drv_state}|{drv_size}")
        drive_ctr += 1
    raid_level = input("Please enter RAID level to create: ")
    raid_drives= input("Please select drive number(s) to target (comma-separated list or press enter for ALL drives): ")
    template   = {}
    if raid_drives is None or raid_drives == "" or raid_drives == "\n":
        template['drives'] = [drive['Location'] for drive in drives]
        template['level']  = int(raid_level)
    else:
        # Take a comma-separated string and split it into a list.
        raid_drives        = raid_drives.split(",")
        template['drives'] = []
        ctr                = 0
        for drv in raid_drives:
            for drive in drives:
                # Does the ctr variable match the number currently in the list? Assumes the list is in sorted order split originally by comma.
                if ctr == drv:
                    template['drives'].append(drive['Location'])
            # Update the counter outside of the internal for-loop.
            ctr += 1
        template['level']  = int(raid_level)
    if iplist:
        for ip in iplist:
            ip = ip.strip()
            response = requests.post(f"http://{ip}/components/storage/{ctrl_id}", json=template)
            print(json.dumps(response.json(), indent=4))
    else:
        ip = single_ip.strip()
        response = requests.post(f"http://{ip}/components/storage/{ctrl_id}", json=template)
        print(json.dumps(response.json(), indent=4))
