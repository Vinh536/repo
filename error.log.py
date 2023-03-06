#!/usr/bin/python3
import time



#Make user manually create new save folder for error logs inside wanted destination. 
User promto create folder named OC#. 

#Save file path. 
Save destination 10.0.8.41:/home/vinh/errorlogs

#Create string to rename file into OC#Number.
str for i = OC#

#SSH connection to send out error logs. 
ssh = 10.0.8.41
ssh.connect(server, username=root, password= ocptester)
ssh_stdin, ssh_stdout, sshstderr = ssh.exec_command(cmd_to_execute)

#Script will run after 13 hours. Stresstest runs for 12 hours.
time.sleep(46800)

#Run script to make error log
./smc-finalscript.sh error > error.log

#Send error.log to remote folder.
scp error.log 10.0.8.41:/home/vinh/errorlogs



------------------------------------------------------------------------------------------------------------------------------

#Script to make error.log files, rename file, and send into remote server. 

Run script

Prompt user to enter save destination and as save.destination
Prompt user to enter OC Number

Script waits 46800 (13 Hours) then starts. 

Runs script to make error logs and saves new file as (OCNUMBER).error.log

Sends error long to remote folder.

# Get the svctag. This will be used to generate the file name.
def get_svc_tag(ip, username, password):
  # Use the '--nocertwarn' flag to disable those blasted security warning messages.
  # The warning message occurs because racadm uses a self-signed certificate to authenticate with the iDRAC.
  command = f"racadm -r {ip} -u {username} -p {password} getsysinfo | grep 'Service Tag' | grep -v 'Chassis' | cut -f 2 -d '='".strip()
  output = subprocess.check_output(command, shell=True)
  return output.decode('utf-8').strip()

























