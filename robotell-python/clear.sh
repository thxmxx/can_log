#!/bin/bash 
for device in $( bluetoothctl devices | grep -o "[[:xdigit:]:]\{11,17\}"); do
    echo "removing bluetooth device: $device | $(bluetoothctl remove $device)"
done
