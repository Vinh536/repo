#!/usr/bin/python3
import re
import csv
import subprocess

rx_dict= {
        'elementName':re.compile(r'ElementName = (?P<ElementName>.*)\n'),
        'version':re.compile(r'Current Version = (?P<Version>.*)\n'),
}

# Function that creates list of Dell Service Tags from inventory files

def file_location(path):
    cmd='cd {0}; ls *swinventory* | cut -f 1 -d "_" > {0}/svctag'.format(path)
    subprocess.check_output(cmd, shell=True)
    svctag_location=path+'/svctag'
    list_svctag=[]
    with open(svctag_location, 'r') as file1:
        file2=file1.readlines()
        for i in file2:
            list_svctag.append(i.strip('\n'))
    return list_svctag


def _parse_line(line):
    for key, rx in rx_dict.items():
        match=rx.search(line)
        if match:
            return key, match
    return None, None

def parse_file(filepath):
    data=[]
    with open(filepath, 'r') as file_object:
        lines=file_object.readlines()
        for line in lines:
            key, match = _parse_line(line)

            if key == 'elementName':
                ElementName = match.group('ElementName')

            if key == 'version':
                Version = match.group('Version')
                row = {
                        'ElementName': ElementName,
                        'Version': Version,
                }
                data.append(row)
    return data

def make_list(data, nodeid):
    list_of_data=[]
    dict1={}
    list_of_data.append(nodeid)
    for i in range(0,len(data)):
        dict1={}
        dict1=data[i]
        list_of_data.append(dict1['ElementName'])
        list_of_data.append(dict1['Version'])
    return list_of_data

def write_to_csv(list_of_data, path):
    with open('{0}/dell_firmware_inventory.csv'.format(path),'a+') as myfile:
        wr = csv.writer(myfile)
        wr.writerow(list_of_data)

if __name__ == '__main__':
    #path=input('Enter path location of inventory files: ')
    path=input("").strip("\n")
    list_svctag=file_location(path)
    for i in list_svctag:
        filename=path+i+'_swinventory.txt'
        data=parse_file(filename)
        list_of_data=make_list(data, i)
        write_to_csv(list_of_data, path)
    #print("Dell firmware inventory file has been created at '{0}' location".format(path))

