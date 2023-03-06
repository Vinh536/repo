#!/usr/bin/python3
import json
import requests
import operator
import sys

# If the user passes in any arguments, then expect that to be a file. Read over the file.
# File structure should be: SERVICE TAG (first column) RACK UNIT (second column)

def automatic_rack_creation(filename):
    rack           = {}
    ctr            = 0
    unit_qty       = 0
    unit           = {}
    rack["Serial"] = input("Enter Rack Serial (see barcode at rear top of rack: ")
    rack["Units"]  = []
    temp_list      = []
    with open(filename, "r") as rackfile:
        mylist = [line.rstrip() for line in rackfile]
        for line in mylist:
            line                 = line.replace("\t"," ")
            unit                 = {}
            unit["Serial"]       = line.split(" ")[0].strip()
            unit["Rack Unit"]    = int(line.split(" ")[1].strip())
            rack["Units"].append(unit)
            ctr += 1
    #print(json.dumps(rack))
    print("Writing rack to database. Please be patient...")
    response = requests.post("http://10.0.7.170/rack", data=json.dumps(rack))
    return response.text
    
# Example rack format.
"""
test_rack = {
    "Serial"   : "2202R0031",
    "Units"    : [
        {
            "Serial" : "HDH4LM3",
            "Rack Unit" : 1
        },
        {   "Serial" : "BFH4LM3",
            "Rack Unit" : 40
        }
    ],
    "Switches" : [
        {
            "Serial" : "123456789",
            "MAC"    : "AABBCCDDEEFF"
        }
    ],
    "PDUs"     : [
        {
            "Serial" : "000000000",
            "MAC"    : "000000000000"
        }
    ]
}
"""

def manual_rack_creation():
    rack           = {}
    ctr            = 0
    unit_qty       = 0
    unit           = {}
    rack["Serial"] = input("Enter Rack Serial (see barcode at rear top of rack: ")
    rack["Units"]  = []
    temp_list      = []
    try:
        unit_qty    = int(input("Enter number of units in rack: "))
    except ValueError as e:
        print("ERROR! Enter a number for number of units!")

    while ctr < unit_qty:
        unit                 = {}
        unit["Serial"]       = input("Enter serial number of system: ")
        unit["Rack Unit"]    = int(input("Enter Rack Unit (RU): "))
        rack["Units"].append(unit)
        ctr += 1
    print("Writing rack to database. Please be patient...")
    response = requests.post("http://10.0.7.170/rack", data=json.dumps(rack))
    return response.text

if __name__ == '__main__':
    result = None
    if len(sys.argv) < 2:
        result = manual_rack_creation()
    else:
        result = automatic_rack_creation(sys.argv[1])

    print(result)
