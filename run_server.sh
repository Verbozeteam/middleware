#!/bin/sh
cd /home/pi/middleware

echo "Running the middleware..."
/usr/local/bin/python3.6 middleware.py -p 7990 -b blueprint_villa.json -i eth0 eth1 > middleware_log &
