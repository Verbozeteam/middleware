#!/bin/sh
cd /home/pi/middleware

echo "Running the middleware..."
/usr/local/bin/python3.6 middleware.py -p 7990 -b blueprint_hotel.json 1> middleware_log 2>&1 &