#! /bin/bash

if [ ! -f /etc/envmon/station ]; then
    echo "/etc/envmon/station does not exist"
    exit 1
fi

if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root"
    exit 1
fi

pigpiod -s 2 || echo "failed to install pgpiod -- already installed?"

cd /home/pi/envmon
STATION=`cat /etc/envmon/station`

su - pi -c "bash -c \"cd /home/pi/envmon && nohup python /home/pi/envmon/envmond.py -S $STATION -v --rrd --udp 198.0.0.55:1234 --prometheus 8000 -F 200 >> /tmp/envmond.log 2>&1 &\""
