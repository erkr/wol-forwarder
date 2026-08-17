#!/bin/sh
#Original source: https://heavydeck.net/blog/wake-on-lan-with-netcat/
#Extended with configurable port and SecureOn arguments
#Hardcoded values
PACKET_REPEATS=2

function usage()
{
    echo "Usage: $0 <MAC_ADDRESS> <HOST_ADDRESS> [<PORT> SECURE_ON]"
    echo "Examples:"
    echo "    $0 12:34:56:78:9A:BC 192.168.1.255"
    echo "    $0 12:34:56:78:9A:BC 192.168.1.255 7"
    echo "    $0 12:34:56:78:9A:BC 192.168.1.255 7 31:32:33:34:35:36"
}

# Parse CLI attributes
MAC_REGEX='^[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]:[0-9a-f][0-9a-f]$'
MAC_ADDR="$1"
MAC_ADDR=`echo "$MAC_ADDR" | grep -i "$MAC_REGEX"`
if [ -z "$MAC_ADDR" ]
then
    echo "Error: Bad MAC address!"
    usage
    exit 1
fi

HOST="$2"
if [ -z "$HOST" ]
then
    echo "Error: No host given!"
    usage
    exit 2
fi

# Port is default 9. Parameter is only mandatory when specifying the optional SecureOn
PORT_REGEX='^[0-9]$'
PORT="$3"
if [ -z "$PORT" ]
then
  PORT=9
fi

# Optional SecureOn in same format as MAC Adress
SECURE_ON="$4"
SECURE_ON=`echo "$SECURE_ON" | grep -i "$MAC_REGEX"`
if [ ! -z "$4" ] && [ -z "$SECURE_ON" ]
then
    echo "Error: Bad SecureOn argument!"
    usage
    exit 3
fi
# Check required programs (nc) exist
NC_WHEREIS=`whereis nc`
if [ -z "$NC_WHEREIS" ]
then
    echo "Warning: Could not verify if NetCat (nc) is on your system Path!"
fi

# Build the magic packet which consists of 0xFF 6 times then the MAC
# Address repeated 16 times
MAGIC_PACKET=':FF:FF:FF:FF:FF:FF'
for i in `seq 1 16`
do
    MAGIC_PACKET="$MAGIC_PACKET:$MAC_ADDR"
done

# Optionally extend with SecureON
if [ ! -z "$SECURE_ON" ]
then
    MAGIC_PACKET="$MAGIC_PACKET:$SECURE_ON"
    echo "Appended the optional SecureOn to the Magic packet"
fi

#Replace colons with escape sequences
MAGIC_PACKET=`echo "$MAGIC_PACKET" | sed 's|:|\\\\x|g'`
echo "Sending magic UDP packet for $MAC_ADDR to $HOST at port $PORT"
#echo -ne "$MAGIC_PACKET" | hexdump -C -v
for i in `seq 1 "$PACKET_REPEATS"`
do
    echo -ne "$MAGIC_PACKET" | nc -w 1 -v -v -u -b "$HOST" "$PORT" || exit 5
done