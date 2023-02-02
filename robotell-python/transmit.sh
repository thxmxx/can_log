#!/bin/bash

# send Standard data frame

json=$(cat << EOS
{
  "request": "Transmit",
  "id": "0x123",
  "type": "stdData",
  "data": [1,2]
}
EOS
)

echo "$json"
echo "$json"  | socat - udp-datagram:255.255.255.255:8200,broadcast

# send Extended data frame

json=$(cat << EOS
{
  "request": "Transmit",
  "id": "0x123",
  "type": "extData",
  "data": [10,11,12,13]
}
EOS
)

echo "$json"
echo "$json"  | socat - udp-datagram:255.255.255.255:8200,broadcast

# send Standard remote frame

json=$(cat << EOS
{
  "request": "Transmit",
  "id": "0xF23",
  "type": "stdRemote"
}
EOS
)

echo "$json"
echo "$json"  | socat - udp-datagram:255.255.255.255:8200,broadcast

# send Extended remote frame

json=$(cat << EOS
{
  "request": "Transmit",
  "id": "0xF23",
  "type": "extRemote"
}
EOS
)

echo "$json"
echo "$json"  | socat - udp-datagram:255.255.255.255:8200,broadcast
