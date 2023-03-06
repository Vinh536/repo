#!/usr/bin/python3
import requests
import json
import argparse
import sys
#import csv
# Argument Parser
parser=argparse.ArgumentParser(description="Build Inventory (CSV file)")
parser.add_argument('-s', '--serial', help='Single serial number of one system', required=False)
parser.add_argument('-l', '--list', help='List of serials or svctags (must be a text file)',type=argparse.FileType('r'), required=False)
parser.add_argument('-o', '--oc', help='Get ALL units of the OC number provided (can also provide rack serial instead)', required=False)
parser.add_argument('-r', '--rack', help='Target all the units in a SINGLE rack', required=False)

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
    template = {
	'Serial'        : element['serial'],
	'Model'         : element['System']['Motherboard Model'],
	'MB_Serial'     : element['System']['Motherboard Serial'],
	'Chassis_Serial': element['Chassis Serial'],
	'Memory'        : element['Memory']['Amount'],
	'CPU'           : get_cpu_model(element['CPU']),
	'BIOS'          : element['System']['BIOS'],
	'IPMI'          : element['BMC']['firmware'],
        'Storage'       : ""
    }
    """ STORAGE SECTION """
    storage_ctr = 0
    drive_template     = {'count':0, 'model':None}
    storage_devices = []
    #prev_storage_element = None
    model_and_capacity = ""
    # Sort the list ahead of time to help with duplicates.
    #element['Storage'] = sorted(element['Storage'], key=lambda d: d['model'])
    dupe_list = []
    for stor_element in element['Storage']:
        #print(element['Storage'][storage_ctr]['model'])
        model_and_capacity = str(element['Storage'][storage_ctr]['model']) + " " + str(element['Storage'][storage_ctr]['capacity']).upper()
        if model_and_capacity not in dupe_list:
            dupe_list.append(model_and_capacity)
        # This list will get every device.
        storage_devices.append(model_and_capacity)
    # Turn the duplicate list into a set to avoid redundancy.
    dupe_list = set(dupe_list)
    # Check the count of duplicates for each model.
    for model in dupe_list:
        dupes = storage_devices.count(model)
        template['Storage'] += str(dupes) + ' x ' + model + ' + '
    # Remove the trailing plus sign.
    template['Storage'] = template['Storage'][:-4]
    # Finish off by appending a comma to the end of the Storage key.
    """ NETWORK SECTION """
    ctr         = 0
    for net_element in element['Network']:
        mac_ctr = 'MAC_' + str(ctr)
        template[mac_ctr] = str(element['Network'][ctr]['mac']).upper()
        ctr += 1
    template['BMC_MAC'] = str(element['BMC']['mac']).upper()
    template['BMC_IP']  = element['BMC']['ip']
    template_str = ""
    for key in template:
        template_str += template[key] + ","
    return template_str[:-1] + "\n"

def csv_build_inventory_file(order_num):
    pass

def build_inventory_file(order_num):
    result    = get_order(order_num)
    filename  = order_num + '.csv'
    with open(filename, 'a') as inv_file:
        headers = "ASA SN,System Model,Motherboard SN,Chassis SN,Memory,CPU,BIOS,IPMI,Storage,Onboard MAC 1,Onboard MAC 2,BMC MAC,BMC IP\n"
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
        print(f"Wrote {ctr} items to {filename}")
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

if __name__ == '__main__':
    args=vars(parser.parse_args())
    serial      = args['serial']
    serials     = args['list']
    order_num   = args['oc']
    rack_serial = args['rack']
    if order_num:
        build_inventory_file(order_num)
    elif serials:
        ctr      = 0
        filename = input("Please enter a filename to save results to: ")
        with open(filename, "a") as inventory:
            headers = "Svctag,System Model,Motherboard SN,Chassis SN,Memory,CPU,BIOS,IPMI,Onboard MAC 1,Onboard MAC 2,BMC MAC,BMC IP\n"
            inventory.write(headers)
            with serials as iplist:
                # Find the order for this unit.
                for system in iplist.readlines():
                    order_num = requests.get(f"http://10.0.7.170/{system.strip()}").json()
                    oc        = order_num['order_number']
                    unit      = get_unit(order_num=oc, serial=system.strip())
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
        print(f"Wrote {ctr} items to {filename}")
    elif rack_serial:
        rack_object = get_rack(rack_serial)
        responses   = get_rack_units(rack_object)
