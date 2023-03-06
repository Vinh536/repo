#!/usr/bin/python3
import argparse
from argparse import RawTextHelpFormatter
import time
from datetime import datetime
from collections import Counter
import json
import subprocess
import requests
import os

def usage():
        message = """ OPTIONS:
        This script will require a serial text file.
        Found on rear top of the rack.        
"""
        return message

parser=argparse.ArgumentParser(description="Inventory builder", formatter_class=RawTextHelpFormatter)
parser.add_argument('-l', '--list', help='Uses a text file containing serial numbers', type=argparse.FileType('r'), required=False)

args=vars(parser.parse_args())

serial_list = args['list']

#def create(serial_list):
 #   command = f'for i in $(cat serial_list); do curl -X GET http://10.0.7.170/$i; done'
  #  result  = subprocess.create(command, capture_output=True, shell=True)
   # stdout  = result.stdout.decode("utf-8")

create = subprocess.run(["for i in $(cat serial_list); do curl -X GET http://10.0.7.170/$i; done"])

print(create.returncode)
    