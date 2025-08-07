"""
Basic network receiver example using the easy_display and easy_radio libraries.

This script listens for incoming messages and displays them on the screen
along with basic stats like the group, time received, and RSSI value.

Pair this with the network_beacon.py example to see the messages being sent
and received and the information receieved as part of the packet.

Not shown is the sender MAC address to keep the line length down, but
this can be accessed via the packet['sender'] field if needed.
"""

from easy_radio import Radio
from easy_display import Display
import time

radio = Radio(group=5, channel=6)
display = Display()
display_lines = 240 // 11 - 1  # 240px height, each line is 11px tall
display_buffer = []

need_update = False

while True:
    packet = radio.receive()
    if packet:
        display_buffer.append(f"[{packet['group']}, {packet['time'] // 1000}, {packet['rssi']}]: {packet['text']}")
        if len(display_buffer) > display_lines:
            display_buffer.pop(0)
        need_update = True

    if need_update:
        display.show_text(display_buffer, color="white", background="black")
        need_update = False

    time.sleep(0.1)  # Poll every 100ms

        