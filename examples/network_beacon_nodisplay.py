
"""
Basic network beacon example using the easy_radio library.

This script sends out a ping message every 3 seconds and prints the ping
info to the console to verify that a message has been sent.

Pair this with the network_receiver.py example to see the messages along
with basic stats like the group, time received, and RSSI value.
"""

from easy_radio import Radio
import time

radio = Radio(group=5, channel=6)

while True:
    # send out a beacon message every 3 seconds
    radio.send("Ping!")
    # log the ping time in seconds since boot
    current_time = time.ticks_ms() // 1000
    print(f"Ping at {current_time} seconds")
    time.sleep(3)