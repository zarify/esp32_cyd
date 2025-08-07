
"""
Basic network receiver example using the easy_radio library.

This script listens for incoming messages and displays them to the console
along with basic stats like the group, time received, and RSSI value.

Pair this with the network_beacon.py example to see the messages being sent
and received and the information receieved as part of the packet.
"""

from easy_radio import Radio
import time

radio = Radio(group=5, channel=6)

while True:
    packet = radio.receive()
    if packet:
        print(f"[{packet['sender']}, {packet['group']}, {packet['time'] // 1000}, {packet['rssi']}]: {packet['text']}")
    time.sleep(0.1)  # Poll every 100ms
