#!/usr/bin/python3
import requests
import json
import argparse
import re
import sys
import os
import csv
# Argument Parser
parser=argparse.ArgumentParser(description="Build Inventory (CSV file)")
parser.add_argument('-s', '--serial', help='Single serial number of one system', required=False)
parser.add_argument('-l', '--list', help='List of serials or svctags (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-r', '--racks', help='List of RACK SERIAL NUMBERS (must be a text file)', type=argparse.FileType('r'), required=False)
parser.add_argument('-o', '--oc', help='Get ALL units of the OC number provided (can also provide rack serial instead)', required=False)

def get_order(order_num: str):
    response = requests.get("http://10.0.7.170/order/" + order_num)
    status_code = response.status_code
    # If the order was not found, then it may be a rack order. Try checking the rack database.
    if status_code == 404:
        response = requests.get("http://10.0.7.170/rack/" + order_num)
        new_status_code = response.status_code
        if new_status_code == 404:
            print("Provided OC number does not exist for appliance or rack orders! Please try again! Exiting...")
    return response.json()

def get_unit(order_num: str, serial: str):
    route    = f"http://10.0.7.170/order/{order_num}/{serial}"
    response = requests.get(route)
    if response.status_code == 404:
        route        = f"http://10.0.7.170/rack/{order_num}/{serial}"
        new_response = requests.get(route)
        if new_response == 404:
            print(f"Could not find information for {serial}!")
            return None
        else:
            print(f"Targeted: {route}")
            return new_response.json()
    return response.json()

def get_cpu_model(element):
    installed = element['Installed']
    # There will ALWAYS be at least one CPU so we will just use the first element.
    model     = element['Processors'][0]['Model']
    return str(installed) + " x " + model

def dif(a, b):
    return [i for i in range(len(a)) if a[i] != b[i]]

""" Take in the JSON element and parse into CSV. Then return the output to append to the CSV file. """
def csv_response(element):
    #print("OS IP: " + element["OS IP"])
    temporary = {
        'Storage' : {
            'Onboard' : None,
            'Offboard': None
        }
    }
    template = {
	'Serial'        : element['serial'],
	'Model'         : element['System']['Motherboard Model'],
	'MB_Serial'     : element['System']['Motherboard Serial'],
	'Chassis_Serial': element['Chassis Serial'],
	'Memory'        : element['Memory']['Amount'],
	'CPU'           : get_cpu_model(element['CPU']),
	'BIOS'          : element['System']['BIOS'],
	'IPMI'          : element['BMC']['firmware'],
        'Storage'       : "",
        'Disk FW'       : "",
    }
    """ STORAGE SECTION """
    # Sort the list ahead of time to help with duplicates.
    # Check if the 'Onboard' key exists.
    #element = json.loads(element)
    if 'Onboard' not in element['Storage'].keys():
        element['Storage'] = sorted(element['Storage'], key=lambda d: d['model'])
        # Filter out multipath'd devices that can cause duplicates. This was detected with Dell EMC NVMe drives:
        # Model name where this occurred: (Dell Ent NVMe v2 AGN RI U.2 15.36TB).
        filtered_drives = filter_multipath_devices(element['Storage'])
        drive_count = get_storage(filtered_drives)
        # Get the firmware version for each different model drive. Append to CSV.
        fw_versions = get_storage_fw(filtered_drives)
        template['Storage'] = drive_count
        template['Disk FW'] += fw_versions
    else:
        onboard_drives = element['Storage']
        if onboard_drives['Onboard'] is not None:
            temporary = sorted(onboard_drives['Onboard'], key=lambda d: d['model'])
            filtered_drives = filter_multipath_devices(element['Storage']['Onboard'])
            drive_count = get_storage(filtered_drives)
            fw_versions = get_storage_fw(filtered_drives)
            template['Storage'] += drive_count
            template['Disk FW'] += fw_versions
            # Now check if the key 'Offboard' is null or not.
        if element['Storage']['Offboard'] is not None:
            # Grab JUST the physical drives.
            #print(json.dumps(element['Storage']['Offboard'], indent=4))
            temp = dict(element['Storage']['Offboard'])
            pd_drives = temp['info']['Physical Drives']['Drives']
            off_drive_count = get_storage(pd_drives)
            off_drive_fw_ver= get_storage_fw(pd_drives)
            template['Storage'] += off_drive_count
            template['Disk FW'] += off_drive_fw_ver

    """ NETWORK SECTION """
    ctr         = 0
    for net_element in element['Network']:
        mac_ctr = 'MAC ' + str(ctr)
        # Get the product name if it exists.
        # If it does, filter for the speed!
        manu = element['Network'][ctr]['manufacturer'].split(" ")[0]
        if 'Product Name' in element['Network'][ctr].keys():
            manu += " " + element['Network'][ctr]['Product Name']
        template[mac_ctr] = manu + "," + str(element['Network'][ctr]['mac']).upper()
        ctr += 1
    template['BMC_MAC'] = str(element['BMC']['mac']).upper()
    template['BMC_IP']  = element['BMC']['ip']
    template['OS IP']   = element['OS IP']
    template_str = ""
    for key in template:
        template_str += template[key] + ","
    return template_str[:-1] + "\n"

def filter_multipath_devices(devices):
    p = re.compile('c[0-9]n[0-9]', re.IGNORECASE)
    real_devices = []
    for device in devices:
        #print(device)
        check = p.search(device['name'])
        if not check:
            #print("Matched for: " + device['name'])
            real_devices.append(device)
    return real_devices

def get_storage(storage_list):
    #print(json.dumps(storage_list, indent=4))
    output_str = ""
    # Check if drive has appeared before. If it has, update the string.
    drive_count = []
    # We don't care about the name of the drive. Ignore that. Only check model and size.
    for drive in storage_list:
        if 'model' in drive.keys():
            temp_tuple = (drive['model'], drive['capacity'])
        else:
            temp_tuple = (drive['Model'], drive['Capacity'])
        drive_count.append(temp_tuple)
    # Now check the list for duplicate values in size.
    drive_set = set(drive_count)
    # Create a new list of dictionaries to represent the count for how many times a duplicate drive occurred.
    count_list = []
    # Check the set for duplicates that were removed. Update the count accordingly.
    for set_drive in sorted(drive_set):
        set_template = {
            'count' : 0,
            'model' : set_drive[0],
            'capacity'  : set_drive[1]
        }
        for drive in storage_list:
            # If these are both equal, we have an equivalent drive. Update the set_template count.
            keyname = 'model'
            capname = 'capacity'
            if 'Model' in drive.keys():
                keyname = 'Model'
                capname = 'Capacity'
            if drive[keyname] == set_template['model'] and drive[capname] == set_template['capacity']:
                set_template['count'] += 1
        # Once the update for the set_template count is completed, update the output string value.
        output_str += str(set_template['count']) + ' x ' + set_template['model'] + " " + set_template['capacity'] + " + "
    # Once the output string is complete, remove the trailing + sign and trailing whitespace.
    output_str = str(output_str[:-3])
    return output_str + " "

def get_storage_fw(storage_list):
    #print(json.dumps(storage_list, indent=4))
    output_str = ""
    # Check if drive has appeared before. If it has, update the string.
    drive_count = []
    # We don't care about the name of the drive. Ignore that. Only check model and size.
    for drive in storage_list:
        if 'firmware' in drive.keys():
            temp_tuple = (drive['firmware'], drive['model'])
        else:
            temp_tuple = (drive['Firmware'], drive['Model'])
        drive_count.append(temp_tuple)
    # Now check the list for duplicate values in size.
    drive_set = set(drive_count)
    # Create a new list of dictionaries to represent the count for how many times a duplicate drive occurred.
    count_list = []
    # Check the set for duplicates that were removed. Update the count accordingly.
    for set_drive in sorted(drive_set):
        set_template = {
            'count'    : 0,
            'firmware' : set_drive[0],
            'model'    : set_drive[1]
        }
        for drive in storage_list:
            # If these are both equal, we have an equivalent drive. Update the set_template count.
            keyname = 'firmware'
            if 'Firmware' in drive.keys():
                keyname = 'firmware'
            #if drive[keyname] == set_template['firmware']:
            #    set_template['count'] += 1
        # Once the update for the set_template count is completed, update the output string value.
        output_str += " " + set_template['firmware'] + " " + "(" + set_template['model'] + ")" + "|"
    # Once the output string is complete, remove the trailing + sign and trailing whitespace.
    output_str = str(output_str[:-1])
    return output_str + " "

def csv_build_inventory_file(order_num):
    pass

def build_inventory_file(order_num):
    result    = get_order(order_num)
    filename  = order_num + '.csv'
    # If the file already exists, remove it.
    with open(filename, 'a') as inv_file:
        inv_file.write(headers)
        ctr = 0
        for element in result:
            # A capital S is the keyname for Rack Serials. Check if the key even exists.
            if element["Serial"]:
                for unit in element["Units"]:
                    #print(unit)
                    # Check if the key 'Nodes' exists. If it does, then this is a multinode unit.
                    if "Nodes" in unit.keys():
                        # Iterate over each child element in the Nodes array.
                        for node in unit["Nodes"]:
                            #print(node['Hyperlink'])
                            information = requests.get(node['Hyperlink']).json()
                            for elem in information:
                                # I am totally cheating here. Just return the first index of the list!
                                information = elem
                                break
                            response   = csv_response(information)
                            inv_file.write(response)
                            ctr += 1
                    else:
                        #print(unit['Hyperlink'])
                        information= requests.get(unit['Hyperlink']).json()
                        for elem in information:
                            information = elem
                            break
                        response = csv_response(information)
                        inv_file.write(response)
                        ctr += 1
            else:
                response = csv_response(element)
                inv_file.write(response)
                ctr += 1
        #print(f"Wrote {ctr} items to {filename}")
"""
    Perform a lookup on the rack to get the sales order of the rack.
    Query the /rack/<rack order/<rack_serial> route to get rack object.
    Use the 'Units' array to perform lookup for each system in the rack.
"""
def get_rack(rack_serial: str):
    server         = 'http://10.0.7.170/'
    hyperlink      = server + rack_serial
    initial_lookup = requests.get(hyperlink)
    if initial_lookup.status_code == '404':
        print('Failed to lookup ' + rack_serial + '!')
        sys.exit(1)
    sales_order = initial_lookup.json()['order_number']
    response    = requests.get(server + 'rack/' + sales_order + '/' + rack_serial)
    if response.status_code == '404':
        print('Failed to find rack ' + rack_serial + '!')
        sys.exit(1)
    return response.json()

"""
    Perform a lookup on the 'Units' array within the rack object.
    Perform a lookup on the 'Hyperlink' key for each child object.
    Store the list of responses in a list to later return.
"""
def get_rack_units(rack_object: dict):
    inventories = []
    if "Units" not in rack_object.keys():
        print("Error! Failed to find units for this rack!")
        sys.exit(1)
    template = {
        'Rack_Serial' : rack_object['Serial'],
        'Rack_Order'  : rack_object['Order Number'],
        'Units'       : None
    }
    units = rack_object["Units"]
    for unit in units:
        inventory = None
        # Grab the Hyperlink key for each unit. TODO: This will be a bit more nested for multi-node systems in the future.
        if 'Hyperlink' not in unit.keys():
            print("Failed to find hyperlink for " + unit["Serial"] + "!")
        else:
            inventory = requests.get(unit["Hyperlink"])
            if inventory.status_code == '404':
                print("Nothing was found for hyperlink: " + unit["Hyperlink"] + "!")
            else:
                temp = inventory.json()
                inventories.append(temp)
    if len(inventories) > 0:
        template['Units'] = inventories
        return template
    print("Failed to find any units for this rack! Exiting...")
    sys.exit(1)

def ismac(element):
    if ":" in element:
        length = len(element.replace(":",""))
        if length == 12:
            return True
    return False

""" NOTE: MAC Address headers will need to be entered manually. """
if __name__ == '__main__':
    args=vars(parser.parse_args())
    serial      = args['serial']
    serials     = args['list']
    order_num   = args['oc']
    rack_serials = args['racks']
    ctr         = 0
    headers = "Serial,System Model,Motherboard SN,Chassis SN,Memory,CPU,BIOS,IPMI,Storage,Disk FW,"
    if order_num:
        build_inventory_file(order_num)
    elif serials:
        #ctr      = 0
        filename = input("Please enter a filename to save results to: ")
        if os.path.isfile(filename):
            print(f"{filename} currently exists! Deleting previous file...")
            os.remove(filename)
        print(f"Created {filename}. Beginning inventory collection. Please be patient; this may take a while...") 
        with open(filename, "a") as inventory:
            header_mac_tally = 0
            #inventory.write(headers)
            with serials as iplist:
                # Find the order for this unit.
                for system in iplist.readlines():
                    order_num = requests.get(f"http://10.0.7.170/{system.strip()}").json()
                    oc        = None
                    # If the order number is empty, then assume the collection containing the data should be under 'unclaimed'.
                    if order_num is None:
                        oc    = 'unclaimed'
                    else:
                        oc        = order_num['order_number']
                    unit      = get_unit(order_num=oc, serial=system.strip())
                    mac_header_ctr = 0
                    for element in unit:
                        if "Units" in element:
                            for hyperlink in element["Units"]:
                                data     = requests.get(hyperlink["Hyperlink"])
                                if data.status_code == 404:
                                    print(f"Failed to find information for {system}!")
                                    continue
                                else:
                                    info     = data.json()[0]
                                    response = csv_response(info)
                                    inventory.write(response)
                                    ctr += 1
                        else:
                            response = csv_response(element)
                            inventory.write(response)
                            ctr += 1
        data = None
        mac_header_ctr = 0
        with open(filename, "r") as invfile:
            data = invfile.readlines()
            for element in data[0].split(","):
                if ismac(element.strip()):
                    mac_header_ctr += 1
        # Lop off one digit for the BMC MAC address.
        with open(filename, "w") as invfile:
            for header in range(0,mac_header_ctr - 1):
                headers += f",MAC {header + 1},"
            # Remove a trailing comma
            headers = ",".join(headers.split(",")[:-1])
            # Finally, add in two more headers, one for BMC MAC and one for BMC IP.
            headers += ",BMC MAC,BMC IP, OS IP\n"
            invfile.write(headers)
            for line in data:
                invfile.write(line)
        print(f"Wrote {ctr} items to {filename}\n")
    elif rack_serials:
        filename = input("Please enter a filename to save results to: ")
        if os.path.isfile(filename):
            print(f"{filename} currently exists! Deleting previous file...")
            os.remove(filename)
        print(f"Created {filename}. Beginning inventory collection. Please be patient; this may take a while...") 
        with open(filename, "a") as inventory:
            header_mac_tally = 0
            #inventory.write(headers)
            with rack_serials as iplist:
                # Find the order for this unit.
                for system in iplist.readlines():
                    order_num = requests.get(f"http://10.0.7.170/{system.strip()}").json()
                    oc        = order_num['order_number']
                    unit      = get_unit(order_num=oc, serial=system.strip())
                    mac_header_ctr = 0
                    for element in unit:
                        if "Units" in element:
                            for hyperlink in element["Units"]:
                                data     = requests.get(hyperlink["Hyperlink"])
                                if data.status_code == 404:
                                    print(f"Failed to find information for {system}!")
                                    continue
                                else:
                                    info     = data.json()[0]
                                    response = csv_response(info)
                                    inventory.write(response)
                                    ctr += 1
                        else:
                            response = csv_response(element)
                            inventory.write(response)
                            ctr += 1
        data = None
        mac_header_ctr = 0
        with open(filename, "r") as invfile:
            data = invfile.readlines()
            for element in data[0].split(","):
                if ismac(element.strip()):
                    mac_header_ctr += 1
        # Lop off one digit for the BMC MAC address.
        with open(filename, "w") as invfile:
            for header in range(0,mac_header_ctr - 1):
                headers += f",MAC {header + 1},"
            # Remove a trailing comma
            headers = ",".join(headers.split(",")[:-1])
            # Finally, add in two more headers, one for BMC MAC and one for BMC IP.
            headers += ",BMC MAC,BMC IP\n"
            invfile.write(headers)
            for line in data:
                invfile.write(line)
        print(f"Wrote {ctr} items to {filename}\n")
