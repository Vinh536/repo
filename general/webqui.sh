#!/usr/bin/bash


for i in $(cat bmcip); do google-chrome https://$i;done